#!/usr/bin/env python3
"""
Services Delivery (SD) Resource Management APIs Testing
Testing newly implemented SD Resource Management APIs as requested in review.

Test Coverage:
1. Resource Management APIs (5 endpoints)
2. Resource Allocation APIs (4 endpoints) 
3. Purchase Request APIs (3 endpoints)

Authentication: admin/admin123
Expected ID Formats: RES-XXXXXXXX, ALL-XXXXXXXX, PR-XXXXXXXX
"""

import requests
import json
import sys
from datetime import datetime, date
import uuid

# Configuration
BASE_URL = "https://service-delivery.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class SDResourceTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.created_resources = []
        self.created_allocations = []
        self.created_purchase_requests = []
        self.created_projects = []
        
    def log_result(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
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
                self.log_result("Admin Authentication", True, f"Token obtained for user: {data['user']['username']}")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False

    def create_test_project(self):
        """Create a test project for allocation testing"""
        try:
            project_data = {
                "name": "SD Resource Test Project",
                "description": "Test project for resource allocation testing",
                "customer_name": "Test Customer Corp",
                "budget": 50000.0,
                "priority": "High",
                "tags": ["testing", "sd-resources"]
            }
            
            response = self.session.post(f"{BASE_URL}/sd/projects/", json=project_data)
            
            if response.status_code == 200:
                project = response.json()
                self.created_projects.append(project["id"])
                self.log_result("Create Test Project", True, f"Project ID: {project.get('project_id', project['id'])}")
                return project["id"]
            else:
                self.log_result("Create Test Project", False, f"Status: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result("Create Test Project", False, f"Exception: {str(e)}")
            return None

    # ==================== RESOURCE MANAGEMENT TESTS ====================
    
    def test_get_resources_list(self):
        """Test GET /api/sd/resources/ - List resources with filtering"""
        try:
            # Test basic list
            response = self.session.get(f"{BASE_URL}/sd/resources/")
            
            if response.status_code == 200:
                resources = response.json()
                self.log_result("GET Resources List", True, f"Found {len(resources)} resources")
                
                # Test with filters
                response = self.session.get(f"{BASE_URL}/sd/resources/?type=cloud&limit=10")
                if response.status_code == 200:
                    filtered_resources = response.json()
                    self.log_result("GET Resources List (Filtered)", True, f"Cloud resources: {len(filtered_resources)}")
                else:
                    self.log_result("GET Resources List (Filtered)", False, f"Status: {response.status_code}")
                
                return True
            else:
                self.log_result("GET Resources List", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("GET Resources List", False, f"Exception: {str(e)}")
            return False

    def test_get_resources_summary(self):
        """Test GET /api/sd/resources/summary - Get resource summary/statistics"""
        try:
            response = self.session.get(f"{BASE_URL}/sd/resources/summary")
            
            if response.status_code == 200:
                summary = response.json()
                expected_fields = [
                    "total_resources", "active_resources", "high_utilization_resources",
                    "low_stock_resources", "pending_purchase_requests", 
                    "total_allocated_value", "average_utilization"
                ]
                
                missing_fields = [field for field in expected_fields if field not in summary]
                if not missing_fields:
                    self.log_result("GET Resources Summary", True, 
                                  f"Total: {summary['total_resources']}, Active: {summary['active_resources']}, "
                                  f"High Util: {summary['high_utilization_resources']}, Avg Util: {summary['average_utilization']}%")
                else:
                    self.log_result("GET Resources Summary", False, f"Missing fields: {missing_fields}")
                return True
            else:
                self.log_result("GET Resources Summary", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("GET Resources Summary", False, f"Exception: {str(e)}")
            return False

    def test_create_resource(self):
        """Test POST /api/sd/resources/ - Create new resource"""
        try:
            resource_data = {
                "type": "cloud",
                "name": "AWS EC2 Test Instance",
                "description": "Test cloud instance for SD resource testing",
                "sku": "AWS-EC2-T3-MEDIUM",
                "available_qty": 10.0,
                "unit_cost": 50.0,
                "currency": "USD",
                "specifications": {
                    "cpu": "2 vCPUs",
                    "memory": "4 GB",
                    "storage": "20 GB SSD"
                },
                "vendor": "Amazon Web Services",
                "model": "t3.medium",
                "location": "us-east-1",
                "procurement_date": "2024-01-15",
                "warranty_expiry": "2025-01-15",
                "tags": ["cloud", "compute", "testing"],
                "notes": "Created for SD resource management testing"
            }
            
            response = self.session.post(f"{BASE_URL}/sd/resources/", json=resource_data)
            
            if response.status_code == 200:
                resource = response.json()
                resource_id = resource.get("resource_id", "")
                
                # Verify ID format (RES-XXXXXXXX)
                if resource_id.startswith("RES-") and len(resource_id) == 12:
                    self.created_resources.append(resource["id"])
                    self.log_result("POST Create Resource", True, 
                                  f"Resource ID: {resource_id}, Name: {resource['name']}")
                    return resource["id"]
                else:
                    self.log_result("POST Create Resource", False, f"Invalid ID format: {resource_id}")
                    return None
            else:
                self.log_result("POST Create Resource", False, f"Status: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result("POST Create Resource", False, f"Exception: {str(e)}")
            return None

    def test_get_specific_resource(self, resource_id):
        """Test GET /api/sd/resources/{resource_id} - Get specific resource"""
        try:
            response = self.session.get(f"{BASE_URL}/sd/resources/{resource_id}")
            
            if response.status_code == 200:
                resource = response.json()
                self.log_result("GET Specific Resource", True, 
                              f"Retrieved resource: {resource['name']}, Status: {resource.get('status', 'N/A')}")
                return True
            elif response.status_code == 404:
                self.log_result("GET Specific Resource", False, "Resource not found")
                return False
            else:
                self.log_result("GET Specific Resource", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("GET Specific Resource", False, f"Exception: {str(e)}")
            return False

    def test_update_resource(self, resource_id):
        """Test PUT /api/sd/resources/{resource_id} - Update resource"""
        try:
            update_data = {
                "name": "AWS EC2 Test Instance (Updated)",
                "available_qty": 15.0,
                "unit_cost": 55.0,
                "notes": "Updated during SD resource management testing"
            }
            
            response = self.session.put(f"{BASE_URL}/sd/resources/{resource_id}", json=update_data)
            
            if response.status_code == 200:
                resource = response.json()
                self.log_result("PUT Update Resource", True, 
                              f"Updated resource: {resource['name']}, Qty: {resource['available_qty']}")
                return True
            else:
                self.log_result("PUT Update Resource", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("PUT Update Resource", False, f"Exception: {str(e)}")
            return False

    # ==================== RESOURCE ALLOCATION TESTS ====================
    
    def test_get_resource_allocations(self, resource_id):
        """Test GET /api/sd/resources/{resource_id}/allocations - Get resource allocations"""
        try:
            response = self.session.get(f"{BASE_URL}/sd/resources/{resource_id}/allocations")
            
            if response.status_code == 200:
                allocations = response.json()
                self.log_result("GET Resource Allocations", True, f"Found {len(allocations)} allocations")
                return True
            else:
                self.log_result("GET Resource Allocations", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("GET Resource Allocations", False, f"Exception: {str(e)}")
            return False

    def test_allocate_resource(self, resource_id, project_id):
        """Test POST /api/sd/resources/{resource_id}/allocate - Allocate resource to project"""
        try:
            allocation_data = {
                "resource_id": resource_id,
                "project_id": project_id,
                "allocated_qty": 3.0,
                "start_date": "2024-02-01",
                "end_date": "2024-04-30",
                "purpose": "Testing resource allocation functionality",
                "notes": "Allocated during SD resource management testing"
            }
            
            response = self.session.post(f"{BASE_URL}/sd/resources/{resource_id}/allocate", json=allocation_data)
            
            if response.status_code == 200:
                allocation = response.json()
                allocation_id = allocation.get("allocation_id", "")
                
                # Verify ID format (ALL-XXXXXXXX)
                if allocation_id.startswith("ALL-") and len(allocation_id) == 12:
                    self.created_allocations.append(allocation["id"])
                    self.log_result("POST Allocate Resource", True, 
                                  f"Allocation ID: {allocation_id}, Qty: {allocation['allocated_qty']}")
                    return allocation["id"]
                else:
                    self.log_result("POST Allocate Resource", False, f"Invalid ID format: {allocation_id}")
                    return None
            else:
                self.log_result("POST Allocate Resource", False, f"Status: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result("POST Allocate Resource", False, f"Exception: {str(e)}")
            return None

    def test_update_allocation(self, allocation_id):
        """Test PUT /api/sd/resources/allocations/{allocation_id} - Update allocation"""
        try:
            update_data = {
                "allocated_qty": 5.0,
                "end_date": "2024-05-31",
                "notes": "Updated allocation during SD resource management testing"
            }
            
            response = self.session.put(f"{BASE_URL}/sd/resources/allocations/{allocation_id}", json=update_data)
            
            if response.status_code == 200:
                allocation = response.json()
                self.log_result("PUT Update Allocation", True, 
                              f"Updated allocation qty: {allocation['allocated_qty']}")
                return True
            else:
                self.log_result("PUT Update Allocation", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("PUT Update Allocation", False, f"Exception: {str(e)}")
            return False

    def test_release_allocation(self, allocation_id):
        """Test DELETE /api/sd/resources/allocations/{allocation_id} - Release allocation"""
        try:
            response = self.session.delete(f"{BASE_URL}/sd/resources/allocations/{allocation_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log_result("DELETE Release Allocation", True, result.get("message", "Allocation released"))
                return True
            else:
                self.log_result("DELETE Release Allocation", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("DELETE Release Allocation", False, f"Exception: {str(e)}")
            return False

    # ==================== PURCHASE REQUEST TESTS ====================
    
    def test_get_purchase_requests(self):
        """Test GET /api/sd/resources/purchase-requests/ - List purchase requests"""
        try:
            # Test basic list
            response = self.session.get(f"{BASE_URL}/sd/resources/purchase-requests/")
            
            if response.status_code == 200:
                purchase_requests = response.json()
                self.log_result("GET Purchase Requests List", True, f"Found {len(purchase_requests)} purchase requests")
                
                # Test with filters
                response = self.session.get(f"{BASE_URL}/sd/resources/purchase-requests/?status=Pending&limit=10")
                if response.status_code == 200:
                    filtered_prs = response.json()
                    self.log_result("GET Purchase Requests (Filtered)", True, f"Pending PRs: {len(filtered_prs)}")
                else:
                    self.log_result("GET Purchase Requests (Filtered)", False, f"Status: {response.status_code}")
                
                return True
            else:
                self.log_result("GET Purchase Requests List", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("GET Purchase Requests List", False, f"Exception: {str(e)}")
            return False

    def test_create_purchase_request(self, project_id=None):
        """Test POST /api/sd/resources/purchase-requests/ - Create purchase request"""
        try:
            pr_data = {
                "project_id": project_id,
                "sku": "DELL-SRV-R740",
                "description": "Dell PowerEdge R740 Server for testing",
                "quantity": 2.0,
                "estimated_cost": 8000.0,
                "unit_cost": 4000.0,
                "currency": "USD",
                "justification": "Required for SD resource management testing and development",
                "priority": "High",
                "required_by": "2024-03-15",
                "specifications": {
                    "cpu": "Intel Xeon Silver 4214",
                    "memory": "32 GB DDR4",
                    "storage": "2x 1TB SSD"
                },
                "tags": ["hardware", "server", "testing"],
                "comments": "Created during SD resource management API testing"
            }
            
            response = self.session.post(f"{BASE_URL}/sd/resources/purchase-requests/", json=pr_data)
            
            if response.status_code == 200:
                purchase_request = response.json()
                pr_id = purchase_request.get("pr_id", "")
                
                # Verify ID format (PR-XXXXXXXX)
                if pr_id.startswith("PR-") and len(pr_id) == 11:
                    self.created_purchase_requests.append(purchase_request["id"])
                    self.log_result("POST Create Purchase Request", True, 
                                  f"PR ID: {pr_id}, Description: {purchase_request['description']}")
                    return purchase_request["id"]
                else:
                    self.log_result("POST Create Purchase Request", False, f"Invalid ID format: {pr_id}")
                    return None
            else:
                self.log_result("POST Create Purchase Request", False, f"Status: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result("POST Create Purchase Request", False, f"Exception: {str(e)}")
            return None

    def test_update_purchase_request(self, pr_id):
        """Test PUT /api/sd/resources/purchase-requests/{pr_id} - Update purchase request"""
        try:
            update_data = {
                "quantity": 3.0,
                "estimated_cost": 12000.0,
                "unit_cost": 4000.0,
                "priority": "Critical",
                "comments": "Updated during SD resource management testing - increased quantity"
            }
            
            response = self.session.put(f"{BASE_URL}/sd/resources/purchase-requests/{pr_id}", json=update_data)
            
            if response.status_code == 200:
                purchase_request = response.json()
                self.log_result("PUT Update Purchase Request", True, 
                              f"Updated PR qty: {purchase_request['quantity']}, Priority: {purchase_request['priority']}")
                return True
            else:
                self.log_result("PUT Update Purchase Request", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("PUT Update Purchase Request", False, f"Exception: {str(e)}")
            return False

    # ==================== BUSINESS LOGIC VALIDATION TESTS ====================
    
    def test_resource_utilization_calculation(self, resource_id):
        """Test resource utilization calculations"""
        try:
            # Get resource details to check utilization
            response = self.session.get(f"{BASE_URL}/sd/resources/{resource_id}")
            
            if response.status_code == 200:
                resource = response.json()
                available_qty = resource.get("available_qty", 0)
                assigned_qty = resource.get("assigned_qty", 0)
                utilization = resource.get("utilization", 0)
                
                # Calculate expected utilization
                expected_utilization = (assigned_qty / available_qty * 100) if available_qty > 0 else 0
                
                if abs(utilization - expected_utilization) < 0.1:  # Allow small floating point differences
                    self.log_result("Resource Utilization Calculation", True, 
                                  f"Utilization: {utilization}% (Expected: {expected_utilization:.1f}%)")
                else:
                    self.log_result("Resource Utilization Calculation", False, 
                                  f"Utilization mismatch: {utilization}% vs Expected: {expected_utilization:.1f}%")
                return True
            else:
                self.log_result("Resource Utilization Calculation", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Resource Utilization Calculation", False, f"Exception: {str(e)}")
            return False

    def test_insufficient_capacity_validation(self, resource_id, project_id):
        """Test business logic validation for insufficient capacity"""
        try:
            # Try to allocate more than available capacity
            allocation_data = {
                "resource_id": resource_id,
                "project_id": project_id,
                "allocated_qty": 999.0,  # Intentionally large number
                "purpose": "Testing capacity validation"
            }
            
            response = self.session.post(f"{BASE_URL}/sd/resources/{resource_id}/allocate", json=allocation_data)
            
            if response.status_code == 400:
                error_message = response.json().get("detail", "")
                if "Insufficient resources" in error_message:
                    self.log_result("Insufficient Capacity Validation", True, f"Correctly rejected: {error_message}")
                else:
                    self.log_result("Insufficient Capacity Validation", False, f"Wrong error message: {error_message}")
                return True
            else:
                self.log_result("Insufficient Capacity Validation", False, 
                              f"Should have returned 400, got: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Insufficient Capacity Validation", False, f"Exception: {str(e)}")
            return False

    # ==================== ERROR HANDLING TESTS ====================
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        try:
            # Test invalid resource ID
            response = self.session.get(f"{BASE_URL}/sd/resources/invalid-resource-id")
            if response.status_code == 404:
                self.log_result("Error Handling - Invalid Resource ID", True, "Correctly returned 404")
            else:
                self.log_result("Error Handling - Invalid Resource ID", False, f"Expected 404, got {response.status_code}")
            
            # Test invalid allocation ID
            response = self.session.put(f"{BASE_URL}/sd/resources/allocations/invalid-allocation-id", json={"allocated_qty": 1.0})
            if response.status_code == 404:
                self.log_result("Error Handling - Invalid Allocation ID", True, "Correctly returned 404")
            else:
                self.log_result("Error Handling - Invalid Allocation ID", False, f"Expected 404, got {response.status_code}")
            
            # Test invalid purchase request ID
            response = self.session.put(f"{BASE_URL}/sd/resources/purchase-requests/invalid-pr-id", json={"quantity": 1.0})
            if response.status_code == 404:
                self.log_result("Error Handling - Invalid PR ID", True, "Correctly returned 404")
            else:
                self.log_result("Error Handling - Invalid PR ID", False, f"Expected 404, got {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Error Handling Tests", False, f"Exception: {str(e)}")
            return False

    # ==================== MAIN TEST EXECUTION ====================
    
    def run_all_tests(self):
        """Run all SD Resource Management API tests"""
        print("=" * 80)
        print("SERVICES DELIVERY (SD) RESOURCE MANAGEMENT APIs TESTING")
        print("=" * 80)
        print(f"Testing against: {BASE_URL}")
        print(f"Authentication: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Create test project for allocations
        project_id = self.create_test_project()
        
        # Step 3: Resource Management Tests
        print("🔧 TESTING RESOURCE MANAGEMENT APIs")
        print("-" * 50)
        
        self.test_get_resources_list()
        self.test_get_resources_summary()
        
        resource_id = self.test_create_resource()
        if resource_id:
            self.test_get_specific_resource(resource_id)
            self.test_update_resource(resource_id)
        
        # Step 4: Resource Allocation Tests
        print("📊 TESTING RESOURCE ALLOCATION APIs")
        print("-" * 50)
        
        if resource_id and project_id:
            self.test_get_resource_allocations(resource_id)
            allocation_id = self.test_allocate_resource(resource_id, project_id)
            if allocation_id:
                self.test_update_allocation(allocation_id)
                # Don't release allocation yet - keep for utilization test
        
        # Step 5: Purchase Request Tests
        print("🛒 TESTING PURCHASE REQUEST APIs")
        print("-" * 50)
        
        self.test_get_purchase_requests()
        pr_id = self.test_create_purchase_request(project_id)
        if pr_id:
            self.test_update_purchase_request(pr_id)
        
        # Step 6: Business Logic Validation Tests
        print("⚖️ TESTING BUSINESS LOGIC VALIDATION")
        print("-" * 50)
        
        if resource_id:
            self.test_resource_utilization_calculation(resource_id)
            if project_id:
                self.test_insufficient_capacity_validation(resource_id, project_id)
        
        # Step 7: Error Handling Tests
        print("🚨 TESTING ERROR HANDLING")
        print("-" * 50)
        
        self.test_error_handling()
        
        # Step 8: Cleanup (release allocation)
        if self.created_allocations:
            for allocation_id in self.created_allocations:
                self.test_release_allocation(allocation_id)
        
        # Step 9: Generate Summary
        self.generate_summary()
        
        return True

    def generate_summary(self):
        """Generate test summary"""
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅ PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
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
            print()
        
        print("CREATED RESOURCES:")
        print(f"- Resources: {len(self.created_resources)}")
        print(f"- Allocations: {len(self.created_allocations)}")
        print(f"- Purchase Requests: {len(self.created_purchase_requests)}")
        print(f"- Projects: {len(self.created_projects)}")
        print()
        
        # Key findings
        print("KEY FINDINGS:")
        print("-" * 40)
        
        # Check ID format compliance
        resource_ids_correct = any("RES-" in r["details"] for r in self.test_results if "Create Resource" in r["test"] and "✅" in r["status"])
        allocation_ids_correct = any("ALL-" in r["details"] for r in self.test_results if "Allocate Resource" in r["test"] and "✅" in r["status"])
        pr_ids_correct = any("PR-" in r["details"] for r in self.test_results if "Create Purchase Request" in r["test"] and "✅" in r["status"])
        
        print(f"✅ Resource ID Format (RES-XXXXXXXX): {'Compliant' if resource_ids_correct else 'Non-compliant'}")
        print(f"✅ Allocation ID Format (ALL-XXXXXXXX): {'Compliant' if allocation_ids_correct else 'Non-compliant'}")
        print(f"✅ Purchase Request ID Format (PR-XXXXXXXX): {'Compliant' if pr_ids_correct else 'Non-compliant'}")
        
        # Check business logic
        utilization_working = any("Utilization Calculation" in r["test"] and "✅" in r["status"] for r in self.test_results)
        validation_working = any("Capacity Validation" in r["test"] and "✅" in r["status"] for r in self.test_results)
        
        print(f"✅ Utilization Calculations: {'Working' if utilization_working else 'Issues detected'}")
        print(f"✅ Business Logic Validation: {'Working' if validation_working else 'Issues detected'}")
        
        print()
        print("=" * 80)
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: SD Resource Management APIs are working excellently!")
        elif success_rate >= 75:
            print("✅ GOOD: SD Resource Management APIs are working well with minor issues.")
        elif success_rate >= 50:
            print("⚠️ MODERATE: SD Resource Management APIs have some issues that need attention.")
        else:
            print("❌ CRITICAL: SD Resource Management APIs have significant issues requiring immediate attention.")

if __name__ == "__main__":
    tester = SDResourceTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)