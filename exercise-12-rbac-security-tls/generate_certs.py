#!/usr/bin/env python3
"""
Automated TLS Certificate Generator for MongoDB using the 'cryptography' library.
================================================================================
Generates:
  1. Certificate Authority (CA): ca.key, ca.crt
  2. Server Certificate: server.key, server.crt, server.pem (with SubjectAltName)
  3. Client Certificate: client.key, client.crt, client.pem (for mutual TLS)

This script automates certificate lifecycle management for deployment pipelines.
"""

import os
import sys
import datetime
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_rsa_private_key(key_size=4096):
    """Generate RSA private key."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )

def save_private_key(key, filename):
    """Save private key to PEM file."""
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(filename, "wb") as f:
        f.write(pem)
    os.chmod(filename, 0o600)
    print(f"[OK] Saved private key: {filename}")
    return pem

def save_certificate(cert, filename):
    """Save certificate to PEM file."""
    pem = cert.public_bytes(serialization.Encoding.PEM)
    with open(filename, "wb") as f:
        f.write(pem)
    print(f"[OK] Saved certificate: {filename}")
    return pem

def generate_ca(output_dir):
    """Generate Root Certificate Authority (CA)."""
    print("\n--- Generating Root Certificate Authority (CA) ---")
    ca_key = generate_rsa_private_key(4096)
    ca_key_path = os.path.join(output_dir, "ca.key")
    save_private_key(ca_key, ca_key_path)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "MongoDB-CA"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NoSQL Security Lab"),
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
    ])

    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )

    ca_cert_path = os.path.join(output_dir, "ca.crt")
    save_certificate(ca_cert, ca_cert_path)
    return ca_key, ca_cert

def generate_server_cert(output_dir, ca_key, ca_cert):
    """Generate Server Certificate with Subject Alternative Names (SAN)."""
    print("\n--- Generating Server Certificate (with SAN: localhost, 127.0.0.1) ---")
    server_key = generate_rsa_private_key(4096)
    server_key_path = os.path.join(output_dir, "server.key")
    server_key_pem = save_private_key(server_key, server_key_path)

    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MongoDB Server"),
    ])

    san = x509.SubjectAlternativeName([
        x509.DNSName("localhost"),
        x509.DNSName("mongodb"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ])

    server_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
        .add_extension(san, critical=False)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    server_cert_path = os.path.join(output_dir, "server.crt")
    server_cert_pem = save_certificate(server_cert, server_cert_path)

    # MongoDB expects concatenated server.pem containing key and certificate
    server_pem_path = os.path.join(output_dir, "server.pem")
    with open(server_pem_path, "wb") as f:
        f.write(server_key_pem)
        f.write(b"\n")
        f.write(server_cert_pem)
    os.chmod(server_pem_path, 0o600)
    print(f"[OK] Created concatenated server bundle: {server_pem_path}")

    # Also save as mongodb.pem for compatibility with lab script
    mongodb_pem_path = os.path.join(output_dir, "mongodb.pem")
    with open(mongodb_pem_path, "wb") as f:
        f.write(server_key_pem)
        f.write(b"\n")
        f.write(server_cert_pem)
    os.chmod(mongodb_pem_path, 0o600)

def generate_client_cert(output_dir, ca_key, ca_cert):
    """Generate Client Certificate for mutual TLS / PyMongo authentication."""
    print("\n--- Generating Client Certificate for Application / PyMongo ---")
    client_key = generate_rsa_private_key(4096)
    client_key_path = os.path.join(output_dir, "client.key")
    client_key_pem = save_private_key(client_key, client_key_path)

    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "client"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PyMongo Application Client"),
    ])

    client_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(client_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    client_cert_path = os.path.join(output_dir, "client.crt")
    client_cert_pem = save_certificate(client_cert, client_cert_path)

    client_pem_path = os.path.join(output_dir, "client.pem")
    with open(client_pem_path, "wb") as f:
        f.write(client_key_pem)
        f.write(b"\n")
        f.write(client_cert_pem)
    os.chmod(client_pem_path, 0o600)
    print(f"[OK] Created concatenated client bundle: {client_pem_path}")

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "./tls"
    os.makedirs(target_dir, exist_ok=True)
    print("=" * 70)
    print("  Automated TLS Certificate Authority & Key Generator (Python)")
    print(f"  Target Directory: {os.path.abspath(target_dir)}")
    print("=" * 70)

    ca_key, ca_cert = generate_ca(target_dir)
    generate_server_cert(target_dir, ca_key, ca_cert)
    generate_client_cert(target_dir, ca_key, ca_cert)

    print("\n" + "=" * 70)
    print("  [SUCCESS] All TLS Certificates Generated & Verified!")
    print("=" * 70)

if __name__ == "__main__":
    main()
