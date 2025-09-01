#!/usr/bin/env python3
"""
Test script for the MCP proxy OIDC authentication
"""

import requests
import json
import time


def test_health_endpoint():
    """Test the health endpoint (should not require auth)"""
    try:
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health endpoint accessible without authentication")
            return True
        else:
            print(f"✗ Health endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health endpoint not accessible: {e}")
        return False


def test_mcp_endpoint_without_auth():
    """Test MCP endpoint without authentication (should fail)"""
    try:
        response = requests.get("http://127.0.0.1:8001/mcp", timeout=5)
        if response.status_code == 401:
            print("✓ MCP endpoint correctly requires authentication")
            return True
        else:
            print(f"✗ MCP endpoint returned unexpected status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing MCP endpoint: {e}")
        return False


def test_mcp_endpoint_with_invalid_token():
    """Test MCP endpoint with invalid token (should fail)"""
    try:
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get("http://127.0.0.1:8001/mcp", headers=headers, timeout=5)
        if response.status_code == 401:
            print("✓ MCP endpoint correctly rejects invalid tokens")
            return True
        else:
            print(f"✗ MCP endpoint returned unexpected status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing MCP endpoint with invalid token: {e}")
        return False


if __name__ == "__main__":
    print("Testing MCP Proxy OIDC Authentication")
    print("=" * 40)

    # Note: These tests assume the server is NOT running
    # They test the endpoint accessibility when server is down

    print("\nTesting endpoint accessibility (server should be stopped):")
    health_ok = test_health_endpoint()
    mcp_auth_ok = test_mcp_endpoint_without_auth()
    mcp_invalid_ok = test_mcp_endpoint_with_invalid_token()

    print(f"\nTest Results:")
    print(f"Health endpoint: {'PASS' if health_ok else 'FAIL'}")
    print(f"MCP auth required: {'PASS' if mcp_auth_ok else 'FAIL'}")
    print(f"Invalid token rejected: {'PASS' if mcp_invalid_ok else 'FAIL'}")

    print(f"\nNote: To test with a running server, start the proxy with:")
    print(f"python mcp_proxy.py http --host 127.0.0.1 --port 8001")
