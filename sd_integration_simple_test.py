#!/usr/bin/env python3
"""
Simple SD Integration Test - Using existing data to verify the integration
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://sawayatta-sd.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class SimpleSDIntegrationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
            
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = requests.post(f"{self.base_url}/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_result("Authentication", True, "Admin login successful")
                return True
            else:
                self.log_result("Authentication", False, f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
            
    def test_sd_upcoming_projects_endpoint(self):
        """Test that SD upcoming projects endpoint is accessible"""
        try:
            response = requests.get(f"{self.base_url}/sd/upcoming-projects/", headers=self.headers)
            if response.status_code == 200:
                projects = response.json()
                self.log_result("SD Upcoming Projects Endpoint", True, f"Found {len(projects)} upcoming projects")
                return projects
            else:
                self.log_result("SD Upcoming Projects Endpoint", False, f"Endpoint failed: {response.status_code}")
                return []
        except Exception as e:
            self.log_result("SD Upcoming Projects Endpoint", False, f"Error: {str(e)}")
            return []
            
    def test_schema_migration_status(self, projects):
        """Test schema migration status"""
        try:
            if not projects:
                self.log_result("Schema Migration Status", False, "No projects to analyze")
                return False
                
            new_schema_count = 0
            old_schema_count = 0
            
            for project in projects:
                # Check for new schema fields
                if all(field in project for field in ["order_id", "opp_id", "pot_id", "customer_name", "setup_cost"]):
                    new_schema_count += 1
                # Check for old schema fields
                elif "project_name" in project or "opportunity_id" in project:
                    old_schema_count += 1
                    
            total_projects = len(projects)
            migration_percentage = (new_schema_count / total_projects) * 100
            
            if old_schema_count > 0:
                self.log_result("Schema Migration Status", False, 
                              f"Found {old_schema_count} projects with old schema, {new_schema_count} with new schema ({migration_percentage:.1f}% migrated)",
                              {"old_schema": old_schema_count, "new_schema": new_schema_count})
                return False
            else:
                self.log_result("Schema Migration Status", True, 
                              f"All {new_schema_count} projects use new SD schema")
                return True
                
        except Exception as e:
            self.log_result("Schema Migration Status", False, f"Error analyzing schema: {str(e)}")
            return False
            
    def test_integration_function_results(self, projects):
        """Test that integration function created projects with correct schema"""
        try:
            if not projects:
                self.log_result("Integration Function Results", False, "No projects to analyze")
                return False
                
            # Look for projects that were created by the integration function
            integration_projects = []
            for project in projects:
                # Check if this looks like it was created by integration function
                if (project.get("opp_status") == "Won" and 
                    project.get("order_status") == "Pending" and
                    project.get("validation_status") == "Pending GC Sign-off"):
                    integration_projects.append(project)
                    
            if not integration_projects:
                self.log_result("Integration Function Results", False, "No projects found that appear to be created by integration function")
                return False
                
            # Verify schema compliance for integration projects
            schema_compliant = 0
            schema_issues = []
            
            for project in integration_projects:
                required_fields = ["order_id", "opp_id", "pot_id", "customer_name", "setup_cost"]
                missing_fields = [field for field in required_fields if field not in project or project[field] is None]
                
                if not missing_fields:
                    schema_compliant += 1
                    
                    # Check field formats
                    format_issues = []
                    if not project["order_id"].startswith("OA-"):
                        format_issues.append(f"order_id format: {project['order_id']}")
                    if not project["pot_id"].startswith("POT-"):
                        format_issues.append(f"pot_id format: {project['pot_id']}")
                    if not isinstance(project["setup_cost"], (int, float)):
                        format_issues.append(f"setup_cost type: {type(project['setup_cost'])}")
                        
                    if format_issues:
                        schema_issues.append({
                            "project_id": project.get("id"),
                            "format_issues": format_issues
                        })
                else:
                    schema_issues.append({
                        "project_id": project.get("id"),
                        "missing_fields": missing_fields
                    })
                    
            if schema_issues:
                self.log_result("Integration Function Results", False, 
                              f"Found {len(schema_issues)} projects with schema issues out of {len(integration_projects)} integration projects",
                              {"issues": schema_issues})
                return False
            else:
                self.log_result("Integration Function Results", True, 
                              f"All {schema_compliant} integration projects have correct SD schema")
                return True
                
        except Exception as e:
            self.log_result("Integration Function Results", False, f"Error analyzing integration results: {str(e)}")
            return False
            
    def test_won_opportunities_integration(self):
        """Test that Won opportunities have corresponding upcoming projects"""
        try:
            # Get Won opportunities
            response = requests.get(f"{self.base_url}/opportunities", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Won Opportunities Integration", False, "Failed to fetch opportunities")
                return False
                
            opportunities_data = response.json()
            opportunities = opportunities_data.get("opportunities", [])
            
            won_opportunities = [opp for opp in opportunities if opp.get("status") == "Won"]
            
            if not won_opportunities:
                self.log_result("Won Opportunities Integration", False, "No Won opportunities found to test")
                return False
                
            # Get upcoming projects
            response = requests.get(f"{self.base_url}/sd/upcoming-projects/", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Won Opportunities Integration", False, "Failed to fetch upcoming projects")
                return False
                
            upcoming_projects = response.json()
            
            # Check if Won opportunities have corresponding upcoming projects
            matched_count = 0
            unmatched_opportunities = []
            
            for opp in won_opportunities:
                opp_id = opp.get("opportunity_id")
                
                # Look for corresponding upcoming project
                found_project = None
                for project in upcoming_projects:
                    if (project.get("opp_id") == opp_id or 
                        project.get("opportunity_id") == opp_id):  # Check both new and old schema
                        found_project = project
                        break
                        
                if found_project:
                    matched_count += 1
                else:
                    unmatched_opportunities.append(opp_id)
                    
            total_won = len(won_opportunities)
            match_percentage = (matched_count / total_won) * 100
            
            if unmatched_opportunities:
                self.log_result("Won Opportunities Integration", False, 
                              f"Only {matched_count}/{total_won} Won opportunities have upcoming projects ({match_percentage:.1f}%)",
                              {"unmatched": unmatched_opportunities})
                return False
            else:
                self.log_result("Won Opportunities Integration", True, 
                              f"All {matched_count} Won opportunities have corresponding upcoming projects")
                return True
                
        except Exception as e:
            self.log_result("Won Opportunities Integration", False, f"Error testing integration: {str(e)}")
            return False
            
    def test_data_mapping_accuracy(self, projects):
        """Test that data mapping from opportunities to projects is accurate"""
        try:
            if not projects:
                self.log_result("Data Mapping Accuracy", False, "No projects to test")
                return False
                
            # Get opportunities for comparison
            response = requests.get(f"{self.base_url}/opportunities", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Data Mapping Accuracy", False, "Failed to fetch opportunities for comparison")
                return False
                
            opportunities_data = response.json()
            opportunities = opportunities_data.get("opportunities", [])
            
            # Create opportunity lookup
            opp_lookup = {opp.get("opportunity_id"): opp for opp in opportunities}
            
            mapping_issues = []
            correct_mappings = 0
            
            for project in projects:
                opp_id = project.get("opp_id") or project.get("opportunity_id")
                if not opp_id:
                    continue
                    
                corresponding_opp = opp_lookup.get(opp_id)
                if not corresponding_opp:
                    continue
                    
                # Check data mapping accuracy
                issues = []
                
                # Check customer name mapping
                if "customer_name" in project:
                    expected_customer = corresponding_opp.get("company_name", "Unknown Company")
                    actual_customer = project.get("customer_name")
                    if actual_customer == "Unknown Company" and expected_customer != "Unknown Company":
                        issues.append(f"Customer name not mapped: expected '{expected_customer}', got '{actual_customer}'")
                        
                # Check setup cost mapping
                if "setup_cost" in project:
                    expected_revenue = corresponding_opp.get("expected_revenue", 0)
                    actual_cost = project.get("setup_cost", 0)
                    # Allow some tolerance for currency conversion or quotation differences
                    if abs(float(actual_cost) - float(expected_revenue)) > float(expected_revenue) * 0.1:  # 10% tolerance
                        issues.append(f"Setup cost mapping issue: expected ~{expected_revenue}, got {actual_cost}")
                        
                if issues:
                    mapping_issues.append({
                        "project_id": project.get("id"),
                        "opp_id": opp_id,
                        "issues": issues
                    })
                else:
                    correct_mappings += 1
                    
            total_testable = correct_mappings + len(mapping_issues)
            
            if mapping_issues:
                accuracy_percentage = (correct_mappings / total_testable) * 100
                self.log_result("Data Mapping Accuracy", False, 
                              f"Data mapping accuracy: {correct_mappings}/{total_testable} ({accuracy_percentage:.1f}%)",
                              {"mapping_issues": mapping_issues})
                return False
            else:
                self.log_result("Data Mapping Accuracy", True, 
                              f"All {correct_mappings} testable projects have accurate data mapping")
                return True
                
        except Exception as e:
            self.log_result("Data Mapping Accuracy", False, f"Error testing data mapping: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Simple SD Integration Tests")
        print("=" * 60)
        
        # Authentication
        if not self.authenticate():
            return
            
        # Test SD endpoint
        projects = self.test_sd_upcoming_projects_endpoint()
        
        # Run tests
        self.test_schema_migration_status(projects)
        self.test_integration_function_results(projects)
        self.test_won_opportunities_integration()
        self.test_data_mapping_accuracy(projects)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if "✅ PASS" in r["status"])
        failed = sum(1 for r in self.results if "❌ FAIL" in r["status"])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if "❌ FAIL" in result["status"]:
                    print(f"  • {result['test']}: {result['message']}")
                    
        print("\n✅ PASSED TESTS:")
        for result in self.results:
            if "✅ PASS" in result["status"]:
                print(f"  • {result['test']}: {result['message']}")

if __name__ == "__main__":
    tester = SimpleSDIntegrationTester()
    tester.run_all_tests()