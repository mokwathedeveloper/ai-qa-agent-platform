#!/usr/bin/env python3
"""
System Integration Test Script
Tests WebSocket connections, authentication flow, and API calls
"""

import asyncio
import websockets
import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

class SystemTester:
    def __init__(self):
        self.token = None
        self.job_id = None
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def test_health_check(self):
        """Test basic API connectivity"""
        self.log("Testing health check...")
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                self.log("✅ Health check passed")
                return True
            else:
                self.log(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Health check error: {e}")
            return False
    
    def test_authentication(self):
        """Test user registration and login"""
        self.log("Testing authentication flow...")
        
        # Test registration
        test_user = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpass123"
        }
        
        try:
            # Register
            response = requests.post(f"{API_URL}/register", json=test_user, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.log("✅ Registration successful")
            else:
                self.log(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
                
            # Test login with same credentials
            login_data = {"username": test_user["username"], "password": test_user["password"]}
            response = requests.post(f"{API_URL}/login", json=login_data, timeout=10)
            if response.status_code == 200:
                self.log("✅ Login successful")
                return True
            else:
                self.log(f"❌ Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {e}")
            return False
    
    def test_protected_endpoint(self):
        """Test accessing protected endpoints"""
        self.log("Testing protected endpoint access...")
        
        if not self.token:
            self.log("❌ No token available for protected endpoint test")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{API_URL}/bugs", headers=headers, timeout=10)
            if response.status_code == 200:
                self.log("✅ Protected endpoint access successful")
                return True
            else:
                self.log(f"❌ Protected endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Protected endpoint error: {e}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection and message handling"""
        self.log("Testing WebSocket connection...")
        
        if not self.job_id:
            self.log("❌ No job ID available for WebSocket test")
            return False
            
        try:
            uri = f"{WS_URL}/ws/{self.job_id}"
            async with websockets.connect(uri, timeout=10) as websocket:
                self.log("✅ WebSocket connection established")
                
                # Wait for potential messages (with timeout)
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    self.log(f"✅ Received WebSocket message: {data.get('status', 'unknown')}")
                    return True
                except asyncio.TimeoutError:
                    self.log("⚠️  No WebSocket messages received (timeout)")
                    return True  # Connection worked, just no messages
                    
        except Exception as e:
            self.log(f"❌ WebSocket connection error: {e}")
            return False
    
    def test_job_creation(self):
        """Test creating a test job"""
        self.log("Testing job creation...")
        
        if not self.token:
            self.log("❌ No token available for job creation")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            job_data = {
                "test_url": "https://example.com",
                "cycle_overview": "Test cycle for system verification",
                "testing_instructions": "Basic functionality test",
                "provider": "uTest"
            }
            
            response = requests.post(f"{API_URL}/run-tests", json=job_data, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                self.job_id = data.get("id")
                self.log(f"✅ Job created successfully: {self.job_id}")
                return True
            else:
                self.log(f"❌ Job creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Job creation error: {e}")
            return False
    
    def test_job_status(self):
        """Test job status retrieval"""
        self.log("Testing job status retrieval...")
        
        if not self.token or not self.job_id:
            self.log("❌ Missing token or job ID for status test")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{API_URL}/jobs/{self.job_id}", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Job status retrieved: {data.get('status', 'unknown')}")
                return True
            else:
                self.log(f"❌ Job status failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Job status error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all system tests"""
        self.log("🚀 Starting system integration tests...")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Authentication", self.test_authentication),
            ("Protected Endpoint", self.test_protected_endpoint),
            ("Job Creation", self.test_job_creation),
            ("Job Status", self.test_job_status),
        ]
        
        results = {}
        for test_name, test_func in tests:
            results[test_name] = test_func()
            time.sleep(1)  # Brief pause between tests
        
        # Test WebSocket after job creation
        if self.job_id:
            results["WebSocket Connection"] = await self.test_websocket_connection()
        
        # Print summary
        self.log("\n" + "="*50)
        self.log("TEST SUMMARY")
        self.log("="*50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
            if result:
                passed += 1
        
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! System is working correctly.")
        else:
            self.log("⚠️  Some tests failed. Check the logs above for details.")
        
        return passed == total

async def main():
    tester = SystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())