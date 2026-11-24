"""Activity 14.1 Demonstration: Webhook Alert Verification
Spins up a lightweight local HTTP receiver, invokes lab_01_monitoring_dashboard.py
with --webhook-url and --test-alert, and validates receipt of threshold breach alert payload.
"""

import sys
import os
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

received_alerts = []

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        try:
            payload = json.loads(post_data.decode("utf-8"))
            received_alerts.append(payload)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "delivered", "code": 200}')
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def log_message(self, format, *args):
        return


def start_mock_webhook_server(port=9099):
    server = HTTPServer(("127.0.0.1", port), WebhookHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def main():
    print("=" * 70)
    print("  Activity 14.1: Webhook Alert Verification & Integration Test")
    print("=" * 70)
    port = 9099
    server, thread = start_mock_webhook_server(port)
    webhook_url = f"http://127.0.0.1:{port}/webhook/alerts"
    print(f"[OK] Local test Webhook receiver active at {webhook_url}")

    from lab_01_monitoring_dashboard import send_webhook_alert, evaluate_alerts, get_mongodb_metrics
    from pymongo import MongoClient

    uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    metrics = get_mongodb_metrics(client)
    alerts = evaluate_alerts(metrics, test_alert=True)
    client.close()

    print(f"\n[INFO] Generated {len(alerts)} threshold breach alert(s) for dispatch:")
    for alert in alerts:
        print(f"  * Dispatching [{alert['level']}] {alert['metric']} -> Current: {alert['current_value']}")
        send_webhook_alert(webhook_url, alert)

    time.sleep(0.5)
    print(f"\n[RECEIVER VERIFICATION] Webhook receiver received {len(received_alerts)} alert notification(s):")
    for idx, item in enumerate(received_alerts, 1):
        print(f"\n  --- Received Payload #{idx} ---")
        print(f"  Content: {item.get('content', '')}")
        if 'attachments' in item:
            for att in item['attachments']:
                print(f"  Title: {att.get('title')} (Color: {att.get('color')})")
                for fld in att.get('fields', []):
                    print(f"    - {fld['title']}: {fld['value']}")

    # Clean shutdown
    try:
        server.shutdown()
        server.server_close()
    except Exception:
        pass

    assert len(received_alerts) > 0, "No alerts were received by the webhook listener!"
    print("\n" + "=" * 70)
    print("  ✔ [ACTIVITY 14.1 SUCCESS] Webhook Alert Pipeline Fully Verified!")
    print("=" * 70)


if __name__ == "__main__":
    main()
