#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class HospitalTokenSystemTester:
    def __init__(self, base_url="https://patientrack.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different users
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': [],
            'critical_issues': [],
            'test_details': []
        }
        
        # Demo credentials
        self.demo_users = {
            'patient': {'email': 'patient@demo.com', 'password': 'demo123'},
            'staff': {'email': 'staff@demo.com', 'password': 'demo123'},
            'admin': {'email': 'admin@demo.com', 'password': 'demo123'}
        }

    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        self.test_results['total_tests'] += 1
        
        test_detail = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        if response_data:
            test_detail['response_data'] = response_data
            
        self.test_results['test_details'].append(test_detail)
        
        if success:
            self.test_results['passed_tests'] += 1
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   Details: {details}")
        else:
            self.test_results['failed_tests'].append(test_name)
            print(f"❌ {test_name}: FAILED")
            print(f"   Error: {details}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    headers: Dict = None, user_role: str = None) -> tuple:
        """Make HTTP request with optional authentication"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Set up headers
        request_headers = {'Content-Type': 'application/json'}
        if headers:
            request_headers.update(headers)
            
        # Add authentication if user_role specified
        if user_role and user_role in self.tokens:
            request_headers['Authorization'] = f'Bearer {self.tokens[user_role]}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}"
                
            return True, response
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

    def test_health_check(self):
        """Test health check endpoint"""
        success, response = self.make_request('GET', '/health')
        
        if not success:
            self.log_test("Health Check", False, response)
            return False
            
        if response.status_code == 200:
            try:
                data = response.json()
                if 'status' in data and data['status'] == 'healthy':
                    self.log_test("Health Check", True, "API is healthy")
                    return True
                else:
                    self.log_test("Health Check", False, f"Unexpected response: {data}")
                    return False
            except json.JSONDecodeError:
                self.log_test("Health Check", False, "Invalid JSON response")
                return False
        else:
            self.log_test("Health Check", False, f"Status code: {response.status_code}")
            return False

    def test_user_authentication(self):
        """Test user login for all roles"""
        all_success = True
        
        for role, credentials in self.demo_users.items():
            success, response = self.make_request('POST', '/auth/login', credentials)
            
            if not success:
                self.log_test(f"Login - {role.title()}", False, response)
                all_success = False
                continue
                
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'access_token' in data and 'user' in data:
                        self.tokens[role] = data['access_token']
                        user_data = data['user']
                        
                        # Verify user role matches
                        if user_data.get('role') == role:
                            self.log_test(f"Login - {role.title()}", True, 
                                        f"User: {user_data.get('name', 'N/A')}")
                        else:
                            self.log_test(f"Login - {role.title()}", False, 
                                        f"Role mismatch: expected {role}, got {user_data.get('role')}")
                            all_success = False
                    else:
                        self.log_test(f"Login - {role.title()}", False, 
                                    f"Missing required fields in response: {data}")
                        all_success = False
                except json.JSONDecodeError:
                    self.log_test(f"Login - {role.title()}", False, "Invalid JSON response")
                    all_success = False
            else:
                self.log_test(f"Login - {role.title()}", False, 
                            f"Status code: {response.status_code}, Response: {response.text}")
                all_success = False
                
        return all_success

    def test_user_profile(self):
        """Test getting user profile for authenticated users"""
        all_success = True
        
        for role in self.tokens.keys():
            success, response = self.make_request('GET', '/auth/me', user_role=role)
            
            if not success:
                self.log_test(f"Get Profile - {role.title()}", False, response)
                all_success = False
                continue
                
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'user' in data:
                        user_data = data['user']
                        if user_data.get('role') == role:
                            self.log_test(f"Get Profile - {role.title()}", True, 
                                        f"Profile retrieved for {user_data.get('name')}")
                        else:
                            self.log_test(f"Get Profile - {role.title()}", False, 
                                        f"Role mismatch in profile")
                            all_success = False
                    else:
                        self.log_test(f"Get Profile - {role.title()}", False, 
                                    f"Missing user data: {data}")
                        all_success = False
                except json.JSONDecodeError:
                    self.log_test(f"Get Profile - {role.title()}", False, "Invalid JSON response")
                    all_success = False
            else:
                self.log_test(f"Get Profile - {role.title()}", False, 
                            f"Status code: {response.status_code}")
                all_success = False
                
        return all_success

    def test_token_creation(self):
        """Test token creation by patient"""
        if 'patient' not in self.tokens:
            self.log_test("Token Creation", False, "Patient not authenticated")
            return False
            
        token_data = {
            'category': 'regular_consultation',
            'symptoms': 'Test symptoms for automated testing'
        }
        
        success, response = self.make_request('POST', '/tokens', token_data, user_role='patient')
        
        if not success:
            self.log_test("Token Creation", False, response)
            return False
            
        if response.status_code == 200:
            try:
                data = response.json()
                required_fields = ['id', 'token_number', 'priority_level', 'position', 'status']
                
                if all(field in data for field in required_fields):
                    self.created_token_id = data['id']  # Store for later tests
                    self.log_test("Token Creation", True, 
                                f"Token created: {data['token_number']}, Priority: {data['priority_level']}")
                    return True
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Token Creation", False, 
                                f"Missing fields: {missing_fields}")
                    return False
            except json.JSONDecodeError:
                self.log_test("Token Creation", False, "Invalid JSON response")
                return False
        else:
            self.log_test("Token Creation", False, 
                        f"Status code: {response.status_code}, Response: {response.text}")
            return False

    def test_queue_retrieval(self):
        """Test queue retrieval"""
        success, response = self.make_request('GET', '/queue', user_role='patient')
        
        if not success:
            self.log_test("Queue Retrieval", False, response)
            return False
            
        if response.status_code == 200:
            try:
                data = response.json()
                if 'queue' in data and 'total_count' in data:
                    queue_length = len(data['queue'])
                    self.log_test("Queue Retrieval", True, 
                                f"Queue retrieved with {queue_length} tokens")
                    return True
                else:
                    self.log_test("Queue Retrieval", False, 
                                f"Missing required fields: {data}")
                    return False
            except json.JSONDecodeError:
                self.log_test("Queue Retrieval", False, "Invalid JSON response")
                return False
        else:
            self.log_test("Queue Retrieval", False, 
                        f"Status code: {response.status_code}")
            return False

    def test_staff_emergency_token(self):
        """Test staff creating emergency token"""
        if 'staff' not in self.tokens:
            self.log_test("Staff Emergency Token", False, "Staff not authenticated")
            return False
            
        emergency_token_data = {
            'patient_id': 'emergency_patient_001',
            'patient_name': 'Emergency Test Patient',
            'patient_phone': '9876543210',
            'category': 'emergency',
            'symptoms': 'Critical emergency test case'
        }
        
        success, response = self.make_request('POST', '/tokens', emergency_token_data, user_role='staff')
        
        if not success:
            self.log_test("Staff Emergency Token", False, response)
            return False
            
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('priority_level') == 1:  # Critical priority
                    self.emergency_token_id = data['id']
                    self.log_test("Staff Emergency Token", True, 
                                f"Emergency token created: {data['token_number']}")
                    return True
                else:
                    self.log_test("Staff Emergency Token", False, 
                                f"Wrong priority level: {data.get('priority_level')}")
                    return False
            except json.JSONDecodeError:
                self.log_test("Staff Emergency Token", False, "Invalid JSON response")
                return False
        else:
            self.log_test("Staff Emergency Token", False, 
                        f"Status code: {response.status_code}, Response: {response.text}")
            return False

    def test_token_completion(self):
        """Test staff completing a token"""
        if 'staff' not in self.tokens:
            self.log_test("Token Completion", False, "Staff not authenticated")
            return False
            
        if not hasattr(self, 'emergency_token_id'):
            self.log_test("Token Completion", False, "No token available to complete")
            return False
            
        success, response = self.make_request('PUT', f'/tokens/{self.emergency_token_id}/complete', 
                                            user_role='staff')
        
        if not success:
            self.log_test("Token Completion", False, response)
            return False
            
        if response.status_code == 200:
            try:
                data = response.json()
                if 'message' in data:
                    self.log_test("Token Completion", True, data['message'])
                    return True
                else:
                    self.log_test("Token Completion", False, f"Unexpected response: {data}")
                    return False
            except json.JSONDecodeError:
                self.log_test("Token Completion", False, "Invalid JSON response")
                return False
        else:
            self.log_test("Token Completion", False, 
                        f"Status code: {response.status_code}")
            return False

    def test_analytics_dashboard(self):
        """Test analytics dashboard (staff/admin access)"""
        success, response = self.make_request('GET', '/analytics/dashboard', user_role='staff')
        
        if not success:
            self.log_test("Analytics Dashboard", False, response)
            return False
            
        if response.status_code == 200:
            try:
                data = response.json()
                required_fields = ['total_tokens_today', 'active_tokens', 'completed_tokens_today', 
                                 'average_wait_time', 'priority_distribution']
                
                if all(field in data for field in required_fields):
                    self.log_test("Analytics Dashboard", True, 
                                f"Analytics retrieved - Total tokens: {data['total_tokens_today']}")
                    return True
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Analytics Dashboard", False, 
                                f"Missing fields: {missing_fields}")
                    return False
            except json.JSONDecodeError:
                self.log_test("Analytics Dashboard", False, "Invalid JSON response")
                return False
        else:
            self.log_test("Analytics Dashboard", False, 
                        f"Status code: {response.status_code}")
            return False

    def test_admin_user_management(self):
        """Test admin user management"""
        if 'admin' not in self.tokens:
            self.log_test("Admin User Management", False, "Admin not authenticated")
            return False
            
        # Test getting all users
        success, response = self.make_request('GET', '/users', user_role='admin')
        
        if not success:
            self.log_test("Admin User Management", False, response)
            return False
            
        if response.status_code == 200:
            try:
                users = response.json()
                if isinstance(users, list) and len(users) > 0:
                    self.log_test("Admin User Management", True, 
                                f"Retrieved {len(users)} users")
                    return True
                else:
                    self.log_test("Admin User Management", False, 
                                f"Unexpected users data: {users}")
                    return False
            except json.JSONDecodeError:
                self.log_test("Admin User Management", False, "Invalid JSON response")
                return False
        else:
            self.log_test("Admin User Management", False, 
                        f"Status code: {response.status_code}")
            return False

    def test_role_based_access_control(self):
        """Test role-based access control"""
        # Test patient trying to access admin endpoint
        success, response = self.make_request('GET', '/users', user_role='patient')
        
        if not success:
            self.log_test("RBAC - Patient Admin Access", False, response)
            return False
            
        if response.status_code == 403:
            self.log_test("RBAC - Patient Admin Access", True, 
                        "Patient correctly denied admin access")
            return True
        else:
            self.log_test("RBAC - Patient Admin Access", False, 
                        f"Expected 403, got {response.status_code}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🏥 Starting Hospital Token Management System Backend Tests")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("User Authentication", self.test_user_authentication),
            ("User Profile", self.test_user_profile),
            ("Token Creation", self.test_token_creation),
            ("Queue Retrieval", self.test_queue_retrieval),
            ("Staff Emergency Token", self.test_staff_emergency_token),
            ("Token Completion", self.test_token_completion),
            ("Analytics Dashboard", self.test_analytics_dashboard),
            ("Admin User Management", self.test_admin_user_management),
            ("Role-Based Access Control", self.test_role_based_access_control)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Test exception: {str(e)}")
                self.test_results['critical_issues'].append(f"{test_name}: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed_tests']}")
        print(f"Failed: {len(self.test_results['failed_tests'])}")
        
        if self.test_results['failed_tests']:
            print(f"\n❌ Failed Tests:")
            for test in self.test_results['failed_tests']:
                print(f"   - {test}")
        
        if self.test_results['critical_issues']:
            print(f"\n🚨 Critical Issues:")
            for issue in self.test_results['critical_issues']:
                print(f"   - {issue}")
        
        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100
        print(f"\n✅ Success Rate: {success_rate:.1f}%")
        
        return self.test_results

def main():
    tester = HospitalTokenSystemTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    if results['passed_tests'] == results['total_tests']:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {len(results['failed_tests'])} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())