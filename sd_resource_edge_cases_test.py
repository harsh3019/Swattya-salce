#!/usr/bin/env python3
"""
SD Resource Management APIs - Edge Cases and Advanced Testing
Additional comprehensive testing for edge cases and advanced scenarios.
"""

import requests
import json
import sys
from datetime import datetime, date

# Configuration
BASE_URL = "https://sawayatta-sd.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class SDResourceEdgeCaseTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {"test": test_name, "status": status, "details": details}
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        print()

    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                return True
            return False
        except Exception:
            return False

    def test_resource_validation_edge_cases(self):
        """Test resource creation with edge case data"""
        try:
            # Test with minimal required data
            minimal_resource = {
                "type": "software",
                "name": "Minimal Test Resource",
                "available_qty": 1.0
            }
            
            response = self.session.post(f"{BASE_URL}/sd/resources/", json=minimal_resource)
            if response.status_code == 200:
                self.log_result("Resource Creation - Minimal Data", True, "Created with minimal required fields")
                return response.json()["id"]
            else:
                self.log_result("Resource Creation - Minimal Data", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_result("Resource Creation - Minimal Data", False, f"Exception: {str(e)}")
            return None

    def test_resource_with_complex_specifications(self):
        """Test resource with complex specifications object"""
        try:
            complex_resource = {
                "type": "hardware",
                "name": "Complex Server Configuration",
                "available_qty": 5.0,
                "unit_cost": 2500.0,
                "specifications": {
                    "cpu": {
                        "model": "Intel Xeon Gold 6248R",
                        "cores": 24,
                        "threads": 48,
                        "base_frequency": "3.0 GHz",
                        "max_frequency": "4.0 GHz"
                    },
                    "memory": {
                        "total": "128 GB",
                        "type": "DDR4-2933",
                        "slots": 16,
                        "ecc": True
                    },
                    "storage": [
                        {"type": "NVMe SSD", "capacity": "1TB", "quantity": 2},
                        {"type": "SATA SSD", "capacity": "4TB", "quantity": 4}
                    ],
                    "network": {
                        "ethernet_ports": 4,
                        "speed": "10 Gbps",
                        "protocols": ["TCP/IP", "iSCSI", "FCoE"]
                    }
                },
                "tags": ["high-performance", "enterprise", "mission-critical"]
            }
            
            response = self.session.post(f"{BASE_URL}/sd/resources/", json=complex_resource)
            if response.status_code == 200:
                resource = response.json()
                self.log_result("Resource Creation - Complex Specifications", True, 
                              f"Created with complex specs: {resource['name']}")
                return resource["id"]
            else:
                self.log_result("Resource Creation - Complex Specifications", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_result("Resource Creation - Complex Specifications", False, f"Exception: {str(e)}")
            return None

    def test_resource_filtering_advanced(self):
        """Test advanced filtering capabilities"""
        try:
            # Test multiple filters
            response = self.session.get(f"{BASE_URL}/sd/resources/?type=hardware&status=Active&limit=5")
            if response.status_code == 200:
                resources = response.json()
                self.log_result("Advanced Resource Filtering", True, f"Found {len(resources)} hardware resources")
            else:
                self.log_result("Advanced Resource Filtering", False, f"Status: {response.status_code}")
            
            # Test high utilization filter
            response = self.session.get(f"{BASE_URL}/sd/resources/?high_utilization=true")
            if response.status_code == 200:
                high_util_resources = response.json()
                self.log_result("High Utilization Filter", True, f"Found {len(high_util_resources)} high utilization resources")
            else:
                self.log_result("High Utilization Filter", False, f"Status: {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Advanced Resource Filtering", False, f"Exception: {str(e)}")
            return False

    def test_purchase_request_workflow_states(self):
        """Test purchase request status transitions"""
        try:
            # Create a purchase request
            pr_data = {
                "sku": "WORKFLOW-TEST-001",
                "description": "Testing workflow state transitions",
                "quantity": 1.0,
                "estimated_cost": 1000.0,
                "justification": "Testing purchase request workflow"
            }
            
            response = self.session.post(f"{BASE_URL}/sd/resources/purchase-requests/", json=pr_data)
            if response.status_code != 200:
                self.log_result("PR Workflow - Creation", False, f"Status: {response.status_code}")
                return False
            
            pr = response.json()
            pr_id = pr["id"]
            
            # Test status transitions
            statuses = ["Approved", "Ordered", "Received"]
            for status in statuses:
                update_data = {"status": status}
                response = self.session.put(f"{BASE_URL}/sd/resources/purchase-requests/{pr_id}", json=update_data)
                if response.status_code == 200:
                    updated_pr = response.json()
                    self.log_result(f"PR Status Transition to {status}", True, 
                                  f"Status updated to: {updated_pr['status']}")
                else:
                    self.log_result(f"PR Status Transition to {status}", False, f"Status: {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("PR Workflow Testing", False, f"Exception: {str(e)}")
            return False

    def test_resource_summary_accuracy(self):
        """Test resource summary calculations accuracy"""
        try:
            # Get current summary
            response = self.session.get(f"{BASE_URL}/sd/resources/summary")
            if response.status_code != 200:
                self.log_result("Resource Summary Accuracy", False, f"Status: {response.status_code}")
                return False
            
            summary = response.json()
            
            # Get all resources to verify counts
            response = self.session.get(f"{BASE_URL}/sd/resources/?limit=1000")
            if response.status_code != 200:
                self.log_result("Resource Summary Accuracy", False, "Could not fetch resources for verification")
                return False
            
            resources = response.json()
            
            # Verify total count
            actual_total = len(resources)
            summary_total = summary["total_resources"]
            
            if actual_total == summary_total:
                self.log_result("Resource Summary - Total Count", True, 
                              f"Accurate: {actual_total} resources")
            else:
                self.log_result("Resource Summary - Total Count", False, 
                              f"Mismatch: Summary={summary_total}, Actual={actual_total}")
            
            # Verify active count
            active_resources = [r for r in resources if r.get("status") == "Active"]
            actual_active = len(active_resources)
            summary_active = summary["active_resources"]
            
            if actual_active == summary_active:
                self.log_result("Resource Summary - Active Count", True, 
                              f"Accurate: {actual_active} active resources")
            else:
                self.log_result("Resource Summary - Active Count", False, 
                              f"Mismatch: Summary={summary_active}, Actual={actual_active}")
            
            return True
        except Exception as e:
            self.log_result("Resource Summary Accuracy", False, f"Exception: {str(e)}")
            return False

    def test_allocation_date_validation(self):
        """Test allocation with various date scenarios"""
        try:
            # Create a test resource first
            resource_data = {
                "type": "license",
                "name": "Date Validation Test License",
                "available_qty": 10.0
            }
            
            response = self.session.post(f"{BASE_URL}/sd/resources/", json=resource_data)
            if response.status_code != 200:
                self.log_result("Allocation Date Validation Setup", False, "Could not create test resource")
                return False
            
            resource_id = response.json()["id"]
            
            # Create a test project
            project_data = {
                "name": "Date Validation Test Project",
                "customer_name": "Test Customer"
            }
            
            response = self.session.post(f"{BASE_URL}/sd/projects/", json=project_data)
            if response.status_code != 200:
                self.log_result("Allocation Date Validation Setup", False, "Could not create test project")
                return False
            
            project_id = response.json()["id"]
            
            # Test allocation with past start date
            allocation_data = {
                "resource_id": resource_id,
                "project_id": project_id,
                "allocated_qty": 2.0,
                "start_date": "2023-01-01",
                "end_date": "2024-12-31",
                "purpose": "Testing past start date"
            }
            
            response = self.session.post(f"{BASE_URL}/sd/resources/{resource_id}/allocate", json=allocation_data)
            if response.status_code == 200:
                self.log_result("Allocation - Past Start Date", True, "Accepted past start date")
            else:
                self.log_result("Allocation - Past Start Date", False, f"Status: {response.status_code}")
            
            # Test allocation with future dates
            allocation_data = {
                "resource_id": resource_id,
                "project_id": project_id,
                "allocated_qty": 1.0,
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "purpose": "Testing future dates"
            }
            
            response = self.session.post(f"{BASE_URL}/sd/resources/{resource_id}/allocate", json=allocation_data)
            if response.status_code == 200:
                self.log_result("Allocation - Future Dates", True, "Accepted future dates")
            else:
                self.log_result("Allocation - Future Dates", False, f"Status: {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Allocation Date Validation", False, f"Exception: {str(e)}")
            return False

    def run_edge_case_tests(self):
        """Run all edge case tests"""
        print("=" * 80)
        print("SD RESOURCE MANAGEMENT APIs - EDGE CASES & ADVANCED TESTING")
        print("=" * 80)
        print()
        
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        print("🧪 TESTING EDGE CASES AND ADVANCED SCENARIOS")
        print("-" * 50)
        
        self.test_resource_validation_edge_cases()
        self.test_resource_with_complex_specifications()
        self.test_resource_filtering_advanced()
        self.test_purchase_request_workflow_states()
        self.test_resource_summary_accuracy()
        self.test_allocation_date_validation()
        
        # Generate summary
        print("=" * 80)
        print("EDGE CASE TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅ PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Edge Case Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("FAILED TESTS:")
            print("-" * 40)
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"❌ {result['test']}: {result['details']}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = SDResourceEdgeCaseTester()
    success = tester.run_edge_case_tests()
    sys.exit(0 if success else 1)