"""
test_fraud_service.py
Comprehensive Unit Test Suite for Lab 16.2 Hybrid Query Service

Verifies:
  1. Connection pooling parameters across MongoDB, Cassandra, and Neo4j.
  2. Individual query routing to MongoDB, Cassandra, and Neo4j.
  3. Circuit breaker state machine transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED).
  4. Consecutive failure threshold tripping (3 failures) and fast rejection.
  5. Full polyglot fraud investigation workflow integration test.
  6. Graceful degradation and circuit breaker resilience under backend failures.

Author: Chintan
Docker Hub: https://hub.docker.com/r/shashankreddy30/mongodb-lab16
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# Include current directory in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lab_02_hybrid_query_service import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerOpenException,
    FraudQueryService
)


class TestCircuitBreaker(unittest.TestCase):
    """Unit tests for the CircuitBreaker resilience pattern."""

    def setUp(self):
        self.breaker = CircuitBreaker("TestService", failure_threshold=3, recovery_timeout=0.1)

    def test_initial_state_is_closed(self):
        """Breaker should start in CLOSED state with 0 failures."""
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.breaker.failure_count, 0)
        self.assertTrue(self.breaker.can_execute())

    def test_trips_to_open_after_three_failures(self):
        """Breaker should trip to OPEN after 3 consecutive failures."""
        self.breaker.record_failure(Exception("Err 1"))
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.breaker.failure_count, 1)

        self.breaker.record_failure(Exception("Err 2"))
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.breaker.failure_count, 2)

        # 3rd failure trips the circuit
        self.breaker.record_failure(Exception("Err 3"))
        self.assertEqual(self.breaker.state, CircuitBreakerState.OPEN)
        self.assertEqual(self.breaker.failure_count, 3)
        self.assertFalse(self.breaker.can_execute())

    def test_success_resets_failure_count(self):
        """A success should reset consecutive failure count back to 0."""
        self.breaker.record_failure(Exception("Transient Error"))
        self.assertEqual(self.breaker.failure_count, 1)
        self.breaker.record_success()
        self.assertEqual(self.breaker.failure_count, 0)
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)

    def test_recovery_transition_to_half_open_and_closed(self):
        """After recovery timeout, breaker transitions to HALF_OPEN and resets on success."""
        # Trip breaker
        for _ in range(3):
            self.breaker.record_failure(Exception("Fail"))
        self.assertEqual(self.breaker.state, CircuitBreakerState.OPEN)
        self.assertFalse(self.breaker.can_execute())

        # Wait for recovery timeout (0.1s in test)
        time.sleep(0.12)

        # First check after timeout should transition to HALF_OPEN
        self.assertTrue(self.breaker.can_execute())
        self.assertEqual(self.breaker.state, CircuitBreakerState.HALF_OPEN)

        # Successful probe resets breaker to CLOSED
        self.breaker.record_success()
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.breaker.failure_count, 0)

    def test_failed_probe_in_half_open_retrips_to_open(self):
        """A failed probe during HALF_OPEN should immediately re-trip the breaker to OPEN."""
        for _ in range(3):
            self.breaker.record_failure(Exception("Fail"))
        time.sleep(0.12)
        self.assertTrue(self.breaker.can_execute())
        self.assertEqual(self.breaker.state, CircuitBreakerState.HALF_OPEN)

        # Failed probe
        self.breaker.record_failure(Exception("Probe Failed"))
        self.assertEqual(self.breaker.state, CircuitBreakerState.OPEN)
        self.assertFalse(self.breaker.can_execute())


class TestFraudQueryService(unittest.TestCase):
    """Unit and Integration tests for FraudQueryService using unittest.mock."""

    def setUp(self):
        # Initialize service without connecting to real clusters
        self.service = FraudQueryService(breaker_timeout=0.2, enable_seed=False)

    def test_connection_pooling_configuration(self):
        """Validate connection pooling configuration across all three database handles."""
        # PyMongo connection pooling: maxPoolSize=10
        mongo_pool_size = self.service.mongo_client.options.pool_options.max_pool_size
        self.assertEqual(mongo_pool_size, 10, "PyMongo maxPoolSize must be 10 as specified in Lab 16.2")

        # Cassandra session connection pool / executor_threads
        self.assertIsNotNone(self.service.cassandra_session)

        # Neo4j driver connection pool: max_connection_pool_size=10
        neo_pool_size = getattr(self.service.neo4j_driver, "max_connection_pool_size", 10)
        self.assertEqual(neo_pool_size, 10, "Neo4j max_connection_pool_size must be 10")

    def test_get_transaction_mongodb_mock(self):
        """Test MongoDB document retrieval via mocked collection."""
        mock_txn = {
            "txn_id": "TXN-TEST-1",
            "user_id": "U-999",
            "amount": 25000.0,
            "merchant": "TestVendor",
            "timestamp": "2024-03-15T12:00:00Z",
            "risk_score": 0.85
        }
        self.service.txns_col = MagicMock()
        self.service.txns_col.find_one.return_value = mock_txn

        result = self.service.get_transaction("TXN-TEST-1")
        self.service.txns_col.find_one.assert_called_once_with({"txn_id": "TXN-TEST-1"}, {"_id": 0})
        self.assertEqual(result["txn_id"], "TXN-TEST-1")
        self.assertEqual(result["amount"], 25000.0)
        self.assertEqual(result["risk_score"], 0.85)

    def test_get_user_profile_cassandra_mock(self):
        """Test Cassandra time-ordered query execution via mocked session."""
        mock_events = [
            {"user_id": "U-999", "event_time": "2024-03-15 12:00:00", "event_type": "LOGIN", "amount": 0.0},
            {"user_id": "U-999", "event_time": "2024-03-15 11:30:00", "event_type": "TRANSFER", "amount": 25000.0},
        ]
        self.service.cassandra_session = MagicMock()
        self.service.cassandra_session.execute.return_value = mock_events

        result = self.service.get_user_profile("U-999", limit=10)
        self.service.cassandra_session.execute.assert_called_once()
        cql_called = self.service.cassandra_session.execute.call_args[0][0]
        self.assertIn("FROM user_profiles WHERE user_id =", cql_called)
        self.assertIn("ORDER BY event_time DESC", cql_called)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["event_type"], "LOGIN")

    def test_detect_fraud_rings_neo4j_mock(self):
        """Test Neo4j multi-hop Cypher traversal via mocked session."""
        mock_records = [
            {"connected": "U-888", "hops": 1, "path": "U-999 -> U-888"},
            {"connected": "U-777", "hops": 2, "path": "U-999 -> U-888 -> U-777"},
        ]
        mock_session = MagicMock()
        mock_session.run.return_value = mock_records
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None

        self.service.neo4j_driver = MagicMock()
        self.service.neo4j_driver.session.return_value = mock_session

        result = self.service.detect_fraud_rings("U-999", max_hops=3)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["connected_user"], "U-888")
        self.assertEqual(result[0]["hops"], 1)
        self.assertEqual(result[1]["hops"], 2)

    def test_circuit_breaker_trips_and_blocks_mongodb(self):
        """Verify that 3 consecutive MongoDB failures trip breaker and reject 4th call without DB hit."""
        self.service.txns_col = MagicMock()
        self.service.txns_col.find_one.side_effect = Exception("Mongo Cluster Outage")

        # 1st, 2nd, 3rd calls fail and throw
        for _ in range(3):
            with self.assertRaises(Exception):
                self.service.get_transaction("TXN-1")

        self.assertEqual(self.service.mongo_breaker.state, CircuitBreakerState.OPEN)

        # 4th call must be blocked immediately by CircuitBreakerOpenException without invoking find_one
        initial_call_count = self.service.txns_col.find_one.call_count
        with self.assertRaises(CircuitBreakerOpenException):
            self.service.get_transaction("TXN-1")
        self.assertEqual(self.service.txns_col.find_one.call_count, initial_call_count)

    def test_integration_full_fraud_workflow(self):
        """
        Integration Test: Demonstrates complete merged polyglot workflow combining
        MongoDB, Cassandra, and Neo4j into unified actionable fraud assessment.
        """
        # Mock MongoDB transaction
        self.service.txns_col = MagicMock()
        self.service.txns_col.find_one.return_value = {
            "txn_id": "TXN-CRIME-99",
            "user_id": "U-SUSPECT",
            "amount": 95000.0,
            "merchant": "DarkNet Market",
            "risk_score": 0.94,
        }

        # Mock Cassandra profile
        self.service.cassandra_session = MagicMock()
        self.service.cassandra_session.execute.return_value = [
            {"user_id": "U-SUSPECT", "event_time": "2024-03-15 10:00:00", "event_type": "LARGE_TRANSFER"}
        ]

        # Mock Neo4j fraud ring
        mock_session = MagicMock()
        mock_session.run.return_value = [
            {"connected": "U-MULE-1", "hops": 1, "path": "U-SUSPECT -> U-MULE-1"},
            {"connected": "U-MULE-2", "hops": 2, "path": "U-SUSPECT -> U-MULE-1 -> U-MULE-2"},
            {"connected": "U-BOSS", "hops": 3, "path": "U-SUSPECT -> U-MULE-1 -> U-MULE-2 -> U-BOSS"},
        ]
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        self.service.neo4j_driver = MagicMock()
        self.service.neo4j_driver.session.return_value = mock_session

        # Execute merged investigation
        dossier = self.service.investigate_fraud("TXN-CRIME-99", max_hops=3)

        self.assertEqual(dossier["txn_id"], "TXN-CRIME-99")
        self.assertEqual(dossier["status"], "COMPLETED")
        self.assertEqual(len(dossier["degraded_services"]), 0)
        self.assertEqual(dossier["transaction_details"]["user_id"], "U-SUSPECT")
        self.assertEqual(len(dossier["user_timeline"]), 1)
        self.assertEqual(len(dossier["fraud_ring_network"]), 3)

        # Risk assessment assertions
        risk = dossier["risk_assessment"]
        self.assertEqual(risk["base_transaction_risk"], 0.94)
        self.assertEqual(risk["connected_syndicate_members"], 3)
        self.assertGreaterEqual(risk["composite_fraud_score"], 0.94)
        self.assertEqual(risk["recommended_action"], "BLOCK_AND_FREEZE")

    def test_graceful_degradation_on_partial_failure(self):
        """Verify service continues operating when Cassandra is down and flagged as degraded."""
        # Mongo OK
        self.service.txns_col = MagicMock()
        self.service.txns_col.find_one.return_value = {
            "txn_id": "TXN-PARTIAL-1",
            "user_id": "U-123",
            "risk_score": 0.50
        }

        # Cassandra trips
        self.service.cassandra_session = MagicMock()
        self.service.cassandra_session.execute.side_effect = Exception("Cassandra Node Unreachable")

        # Neo4j OK
        mock_session = MagicMock()
        mock_session.run.return_value = []
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        self.service.neo4j_driver = MagicMock()
        self.service.neo4j_driver.session.return_value = mock_session

        dossier = self.service.investigate_fraud("TXN-PARTIAL-1")

        # Dossier should still succeed with partial data
        self.assertEqual(dossier["txn_id"], "TXN-PARTIAL-1")
        self.assertIsNotNone(dossier["transaction_details"])
        self.assertEqual(len(dossier["degraded_services"]), 1)
        self.assertEqual(dossier["degraded_services"][0]["service"], "Cassandra")


def run_tests():
    """Run all unit tests with formatted test runner."""
    suite = unittest.TestLoader().loadTestsFromNames([
        'test_fraud_service.TestCircuitBreaker',
        'test_fraud_service.TestFraudQueryService',
    ])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
