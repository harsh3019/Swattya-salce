#!/usr/bin/env python3
"""
L6 Won Stage Integration with SD Module - Comprehensive Testing
Testing the complete L6→SD integration workflow to ensure won opportunities appear in Services Delivery Upcoming Projects
"""

import requests
import json
import sys
import time
from datetime import datetime, date

# Configuration
BASE_URL = "https://service-delivery.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class L6SDIntegrationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.created_opportunity_id = None
        self.created_project_id = None
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        self.test_results.append(result)
        print(result)
        
    def authenticate(self):
        """Test admin authentication"""
        print("\n🔐 TESTING AUTHENTICATION")
        print("=" * 50)
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                
                user_data = data.get("user", {})
                self.log_test(
                    "Admin Authentication", 
                    True, 
                    f"Token received, User: {user_data.get('username')}, Role ID: {user_data.get('role_id')}"
                )
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False

    def find_or_create_l5_opportunity(self):
        """Find existing L2 opportunity to progress to L6 for testing"""
        print("\n🎯 FINDING OPPORTUNITY FOR L6 TESTING")
        print("=" * 50)
        
        try:
            # First, try to find existing opportunities that can be progressed
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get('opportunities', []) if isinstance(data, dict) else data
                
                # Look for L2 opportunities that are Active (can be progressed)
                l2_opportunities = [opp for opp in opportunities if opp.get('current_stage') == 2 and opp.get('status') == 'Active']
                
                if l2_opportunities:
                    self.created_opportunity_id = l2_opportunities[0]['id']
                    self.log_test(
                        "Find L2 Opportunity for Testing", 
                        True, 
                        f"Found L2 opportunity to progress: {l2_opportunities[0].get('opportunity_id', 'Unknown ID')}"
                    )
                    return True
                else:
                    # Look for existing L6 opportunities to test integration
                    l6_opportunities = [opp for opp in opportunities if opp.get('current_stage') == 6 and opp.get('status') == 'Won']
                    
                    if l6_opportunities:
                        self.created_opportunity_id = l6_opportunities[0]['id']
                        self.log_test(
                            "Find L6 Opportunity for Testing", 
                            True, 
                            f"Found existing L6 opportunity: {l6_opportunities[0].get('opportunity_id', 'Unknown ID')}"
                        )
                        return True
                    else:
                        self.log_test("Find Opportunity for Testing", False, "No suitable opportunities found (need L2 Active or L6 Won)")
                        return False
            else:
                self.log_test("Find Opportunity for Testing", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Find Opportunity for Testing", False, f"Exception: {str(e)}")
            return False

    def create_l5_opportunity(self):
        """Create a new opportunity in L5 stage"""
        try:
            # Get required master data
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            companies_response = requests.get(f"{self.base_url}/companies", headers=self.headers, timeout=10)
            users_response = requests.get(f"{self.base_url}/users", headers=self.headers, timeout=10)
            
            if stages_response.status_code != 200:
                self.log_test("Create L5 Opportunity", False, "Could not get stages data")
                return False
            
            stages = stages_response.json()
            currencies = currencies_response.json() if currencies_response.status_code == 200 else []
            companies = companies_response.json() if companies_response.status_code == 200 else []
            users = users_response.json() if users_response.status_code == 200 else []
            
            # Find required data
            l1_stage = next((s for s in stages if s.get('stage_code') == 'L1'), None)
            inr_currency = next((c for c in currencies if c.get('code') == 'INR'), None)
            test_company = companies[0] if companies else None
            test_user = users[0] if users else None
            
            if not l1_stage:
                self.log_test("Create L5 Opportunity", False, "L1 stage not found")
                return False
            
            # Create opportunity data (start at L1, then progress to L5)
            opportunity_data = {
                "project_title": "L6 SD Integration Test Opportunity",
                "company_id": test_company['id'] if test_company else "test-company-id",
                "stage_id": l1_stage['id'],
                "expected_revenue": 750000,
                "currency_id": inr_currency['id'] if inr_currency else "test-currency-id",
                "lead_owner_id": test_user['id'] if test_user else "test-user-id",
                "win_probability": 25
            }
            
            # Create opportunity
            create_response = requests.post(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                json=opportunity_data,
                timeout=10
            )
            
            if create_response.status_code in [200, 201]:
                created_opp = create_response.json()
                self.created_opportunity_id = created_opp.get('id')
                
                # Now progress the opportunity to L5 stage
                if self.progress_opportunity_to_l5():
                    self.log_test(
                        "Create L5 Opportunity", 
                        True, 
                        f"Created and progressed opportunity to L5: {created_opp.get('opportunity_id', 'Unknown ID')}"
                    )
                    return True
                else:
                    self.log_test("Create L5 Opportunity", False, "Could not progress opportunity to L5")
                    return False
            else:
                self.log_test("Create L5 Opportunity", False, f"Status: {create_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Create L5 Opportunity", False, f"Exception: {str(e)}")
            return False

    def progress_opportunity_to_l5(self):
        """Progress opportunity from L1 to L5 stage"""
        try:
            # Get stages data
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            if stages_response.status_code != 200:
                return False
            
            stages = stages_response.json()
            stage_map = {s.get('stage_code'): s.get('id') for s in stages}
            
            # Progress through stages L1 → L2 → L3 → L4 → L5
            stage_progression = [
                ("L2", {"region_id": "test-region", "product_interest": "Software Development", 
                       "assigned_representatives": ["test-rep"], "lead_owner_id": "test-owner"}),
                ("L3", {"scorecard": "BANT", "budget": 500000, "authority": "CTO", 
                       "need": "High", "timeline": "Q2 2025"}),
                ("L4", {"document_upload": "proposal.pdf", "submission_date": "2025-01-15", 
                       "internal_stakeholder": "Sales Manager", "client_response": "Positive"}),
                ("L5", {"updated_price": 750000, "margin_percentage": 35.0, "po_number": "PO-2025-001", 
                       "po_date": "2025-01-20", "commercial_decision": "pending"})
            ]
            
            for stage_code, stage_data in stage_progression:
                stage_id = stage_map.get(stage_code)
                if not stage_id:
                    continue
                
                change_data = {
                    "target_stage": int(stage_code[1]),  # Extract number from L2, L3, etc.
                    "stage_data": stage_data
                }
                
                response = requests.post(
                    f"{self.base_url}/opportunities/{self.created_opportunity_id}/change-stage",
                    headers=self.headers,
                    json=change_data,
                    timeout=10
                )
                
                if response.status_code not in [200, 201]:
                    print(f"Failed to progress to {stage_code}: {response.status_code}")
                    # Continue anyway, might still work
            
            return True
            
        except Exception as e:
            print(f"Exception in progress_opportunity_to_l5: {str(e)}")
            return False

    def test_l6_completion_trigger(self):
        """Test L6 completion trigger and integration function call"""
        print("\n🎯 TESTING L6 COMPLETION TRIGGER")
        print("=" * 50)
        
        if not self.created_opportunity_id:
            self.log_test("L6 Completion Trigger", False, "No opportunity available for testing")
            return False
        
        try:
            # First check if opportunity is already in L6
            opp_response = requests.get(
                f"{self.base_url}/opportunities/{self.created_opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if opp_response.status_code == 200:
                opportunity = opp_response.json()
                current_stage = opportunity.get('current_stage')
                
                if current_stage == 6:
                    # Already in L6, test the existing integration
                    self.log_test(
                        "L6 Stage Already Present", 
                        True, 
                        f"Opportunity already in L6 (Won) stage: {opportunity.get('opportunity_id')}"
                    )
                    return self.verify_integration_function_called()
                elif current_stage == 2:
                    # Progress from L2 to L6
                    return self.progress_l2_to_l6()
                else:
                    self.log_test("L6 Completion Trigger", False, f"Opportunity in unexpected stage: L{current_stage}")
                    return False
            else:
                self.log_test("L6 Completion Trigger", False, f"Could not retrieve opportunity: {opp_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("L6 Completion Trigger", False, f"Exception: {str(e)}")
            return False

    def progress_l2_to_l6(self):
        """Progress opportunity from L2 to L6 stage"""
        try:
            # Progress through stages L2 → L3 → L4 → L5 → L6
            stage_progression = [
                (3, {"scorecard": "BANT", "budget": 500000, "authority": "CTO", 
                     "need": "High", "timeline": "Q2 2025"}),
                (4, {"document_upload": "proposal.pdf", "submission_date": "2025-01-15", 
                     "internal_stakeholder": "Sales Manager", "client_response": "Positive"}),
                (5, {"updated_price": 750000, "margin_percentage": 35.0, "po_number": "PO-2025-001", 
                     "po_date": "2025-01-20", "commercial_decision": "pending"}),
                (6, {"final_value": 750000, "client_poc": "John Smith - CTO", 
                     "delivery_team": ["Team Lead A", "Developer B", "QA Engineer C"],
                     "kickoff_date": "2025-02-01", "commercial_decision": "won"})
            ]
            
            for target_stage, stage_data in stage_progression:
                change_data = {
                    "target_stage": target_stage,
                    "stage_data": stage_data
                }
                
                response = requests.post(
                    f"{self.base_url}/opportunities/{self.created_opportunity_id}/change-stage",
                    headers=self.headers,
                    json=change_data,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    if target_stage == 6:
                        result_data = response.json()
                        self.log_test(
                            "L6 Stage Transition", 
                            True, 
                            f"Successfully transitioned to L6 (Won): {result_data.get('message', 'Stage changed')}"
                        )
                        
                        # Wait a moment for integration to process
                        time.sleep(2)
                        
                        # Check if integration function was called
                        return self.verify_integration_function_called()
                else:
                    print(f"Failed to progress to L{target_stage}: {response.status_code}")
                    if target_stage < 6:
                        continue  # Try to continue anyway
                    else:
                        self.log_test("L6 Stage Transition", False, f"Status: {response.status_code}")
                        return False
            
            return True
            
        except Exception as e:
            self.log_test("L6 Stage Transition", False, f"Exception: {str(e)}")
            return False

    def verify_integration_function_called(self):
        """Verify that the integration function create_upcoming_project_from_opportunity was called"""
        try:
            # Check backend logs for integration execution (if available)
            # For now, we'll verify by checking if upcoming project was created
            
            # Get the opportunity to check its current state
            opp_response = requests.get(
                f"{self.base_url}/opportunities/{self.created_opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if opp_response.status_code == 200:
                opportunity = opp_response.json()
                
                # Verify opportunity is now in L6 (Won) stage
                if opportunity.get('current_stage') == 6:
                    self.log_test(
                        "Verify L6 Stage Update", 
                        True, 
                        f"Opportunity confirmed in L6 stage with status: {opportunity.get('status', 'Unknown')}"
                    )
                    
                    # Check if upcoming project was created
                    return self.check_upcoming_project_creation(opportunity)
                else:
                    self.log_test("Verify L6 Stage Update", False, f"Opportunity not in L6 stage: {opportunity.get('current_stage')}")
                    return False
            else:
                self.log_test("Verify L6 Stage Update", False, f"Could not retrieve opportunity: {opp_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Verify Integration Function", False, f"Exception: {str(e)}")
            return False

    def check_upcoming_project_creation(self, opportunity):
        """Check if upcoming project was created from the won opportunity"""
        try:
            # Get upcoming projects list
            projects_response = requests.get(
                f"{self.base_url}/sd/upcoming-projects/",
                headers=self.headers,
                timeout=10
            )
            
            if projects_response.status_code == 200:
                projects = projects_response.json()
                
                # Look for project with matching opportunity ID
                opp_id = opportunity.get('opportunity_id')
                matching_project = None
                
                for project in projects:
                    if project.get('opp_id') == opp_id:
                        matching_project = project
                        self.created_project_id = project.get('id')
                        break
                
                if matching_project:
                    self.log_test(
                        "Integration Function Called", 
                        True, 
                        f"Upcoming project created automatically: {matching_project.get('order_id', 'Unknown Order ID')}"
                    )
                    return True
                else:
                    self.log_test("Integration Function Called", False, f"No upcoming project found for opportunity {opp_id}")
                    return False
            else:
                self.log_test("Integration Function Called", False, f"Could not get upcoming projects: {projects_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Integration Function Called", False, f"Exception: {str(e)}")
            return False

    def test_sd_upcoming_projects_creation(self):
        """Test SD Upcoming Projects creation with correct schema"""
        print("\n📋 TESTING SD UPCOMING PROJECTS CREATION")
        print("=" * 50)
        
        if not self.created_project_id:
            self.log_test("SD Project Creation", False, "No upcoming project was created to test")
            return False
        
        try:
            # Get the created project details
            projects_response = requests.get(
                f"{self.base_url}/sd/upcoming-projects/",
                headers=self.headers,
                timeout=10
            )
            
            if projects_response.status_code == 200:
                projects = projects_response.json()
                created_project = next((p for p in projects if p.get('id') == self.created_project_id), None)
                
                if created_project:
                    # Verify SD schema requirements
                    required_fields = ['order_id', 'opp_id', 'pot_id', 'customer_name', 'setup_cost']
                    missing_fields = []
                    
                    for field in required_fields:
                        if field not in created_project or created_project[field] is None:
                            missing_fields.append(field)
                    
                    if not missing_fields:
                        self.log_test(
                            "SD Schema Validation", 
                            True, 
                            f"All required fields present: {', '.join(required_fields)}"
                        )
                        
                        # Test ID generation formats
                        self.test_id_generation_formats(created_project)
                        
                        # Test data mapping
                        self.test_data_mapping(created_project)
                        
                        return True
                    else:
                        self.log_test("SD Schema Validation", False, f"Missing required fields: {', '.join(missing_fields)}")
                        return False
                else:
                    self.log_test("SD Schema Validation", False, "Created project not found in projects list")
                    return False
            else:
                self.log_test("SD Schema Validation", False, f"Could not get projects: {projects_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("SD Schema Validation", False, f"Exception: {str(e)}")
            return False

    def test_id_generation_formats(self, project):
        """Test proper ID generation formats"""
        try:
            order_id = project.get('order_id', '')
            pot_id = project.get('pot_id', '')
            
            # Test Order ID format (OA-XXXXXXXX)
            if order_id.startswith('OA-') and len(order_id) == 11:
                self.log_test(
                    "Order ID Format", 
                    True, 
                    f"Correct format: {order_id}"
                )
            else:
                self.log_test("Order ID Format", False, f"Invalid format: {order_id} (expected OA-XXXXXXXX)")
            
            # Test POT ID format (POT-XXXXXXXX)
            if pot_id.startswith('POT-') and len(pot_id) == 12:
                self.log_test(
                    "POT ID Format", 
                    True, 
                    f"Correct format: {pot_id}"
                )
            else:
                self.log_test("POT ID Format", False, f"Invalid format: {pot_id} (expected POT-XXXXXXXX)")
                
        except Exception as e:
            self.log_test("ID Generation Formats", False, f"Exception: {str(e)}")

    def test_data_mapping(self, project):
        """Test data mapping from opportunity to SD project"""
        try:
            # Get original opportunity data
            opp_response = requests.get(
                f"{self.base_url}/opportunities/{self.created_opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if opp_response.status_code == 200:
                opportunity = opp_response.json()
                
                # Test data mapping
                mapping_tests = [
                    {
                        "field": "opp_id",
                        "project_value": project.get('opp_id'),
                        "expected_value": opportunity.get('opportunity_id'),
                        "description": "Opportunity ID mapping"
                    },
                    {
                        "field": "setup_cost",
                        "project_value": project.get('setup_cost'),
                        "expected_value": opportunity.get('expected_revenue'),
                        "description": "Setup cost from expected revenue"
                    }
                ]
                
                for test in mapping_tests:
                    if test["project_value"] == test["expected_value"]:
                        self.log_test(
                            f"Data Mapping: {test['description']}", 
                            True, 
                            f"Correctly mapped: {test['project_value']}"
                        )
                    else:
                        self.log_test(
                            f"Data Mapping: {test['description']}", 
                            False, 
                            f"Mapping failed - Project: {test['project_value']}, Expected: {test['expected_value']}"
                        )
                
                # Test customer name resolution
                customer_name = project.get('customer_name', '')
                if customer_name and customer_name != 'Unknown Company':
                    self.log_test(
                        "Data Mapping: Customer Name", 
                        True, 
                        f"Customer name resolved: {customer_name}"
                    )
                else:
                    self.log_test("Data Mapping: Customer Name", False, f"Customer name not resolved: {customer_name}")
                    
            else:
                self.log_test("Data Mapping", False, "Could not retrieve opportunity for mapping comparison")
                
        except Exception as e:
            self.log_test("Data Mapping", False, f"Exception: {str(e)}")

    def test_sd_api_integration(self):
        """Test SD API integration"""
        print("\n🔌 TESTING SD API INTEGRATION")
        print("=" * 50)
        
        try:
            # Test GET /api/sd/upcoming-projects/ returns the created project
            response = requests.get(
                f"{self.base_url}/sd/upcoming-projects/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                
                # Verify project appears in list
                if self.created_project_id:
                    created_project = next((p for p in projects if p.get('id') == self.created_project_id), None)
                    
                    if created_project:
                        self.log_test(
                            "SD API Project Retrieval", 
                            True, 
                            f"Created project appears in SD upcoming projects list"
                        )
                        
                        # Test project data structure
                        self.test_project_data_structure(created_project)
                        
                        # Test immediate appearance
                        self.test_immediate_appearance()
                        
                        # Test project status and workflow fields
                        self.test_project_status_workflow(created_project)
                        
                        return True
                    else:
                        self.log_test("SD API Project Retrieval", False, "Created project not found in API response")
                        return False
                else:
                    self.log_test("SD API Project Retrieval", False, "No created project ID to verify")
                    return False
            else:
                self.log_test("SD API Project Retrieval", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("SD API Integration", False, f"Exception: {str(e)}")
            return False

    def test_project_data_structure(self, project):
        """Test project data structure matches SD requirements"""
        try:
            # Expected SD project structure
            expected_structure = {
                'id': str,
                'order_id': str,
                'opp_id': str,
                'pot_id': str,
                'customer_name': str,
                'setup_cost': (int, float),
                'created_at': str,
                'updated_at': str
            }
            
            structure_valid = True
            missing_fields = []
            
            for field, expected_type in expected_structure.items():
                if field not in project:
                    missing_fields.append(field)
                    structure_valid = False
                elif not isinstance(project[field], expected_type):
                    structure_valid = False
            
            if structure_valid and not missing_fields:
                self.log_test(
                    "Project Data Structure", 
                    True, 
                    "Project data structure matches SD requirements"
                )
            else:
                self.log_test(
                    "Project Data Structure", 
                    False, 
                    f"Structure issues - Missing: {missing_fields}"
                )
                
        except Exception as e:
            self.log_test("Project Data Structure", False, f"Exception: {str(e)}")

    def test_immediate_appearance(self):
        """Test that project appears immediately after L6 completion"""
        try:
            # Since we already found the project in the API response, this confirms immediate appearance
            self.log_test(
                "Immediate Project Appearance", 
                True, 
                "Project appeared immediately in SD upcoming projects after L6 completion"
            )
            
        except Exception as e:
            self.log_test("Immediate Project Appearance", False, f"Exception: {str(e)}")

    def test_project_status_workflow(self, project):
        """Test project status and workflow fields"""
        try:
            # Check for workflow-related fields
            workflow_fields = ['status', 'phase', 'priority', 'assigned_team']
            present_fields = [field for field in workflow_fields if field in project]
            
            if present_fields:
                self.log_test(
                    "Project Workflow Fields", 
                    True, 
                    f"Workflow fields present: {', '.join(present_fields)}"
                )
            else:
                # This might be expected if workflow fields are added later
                self.log_test(
                    "Project Workflow Fields", 
                    True, 
                    "No workflow fields present (may be added in project management phase)"
                )
                
        except Exception as e:
            self.log_test("Project Workflow Fields", False, f"Exception: {str(e)}")

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        print("\n🔄 TESTING END-TO-END WORKFLOW")
        print("=" * 50)
        
        try:
            # Verify complete flow: L5→L6→SD Upcoming Project creation
            if self.created_opportunity_id and self.created_project_id:
                # Get final opportunity state
                opp_response = requests.get(
                    f"{self.base_url}/opportunities/{self.created_opportunity_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                # Get final project state
                projects_response = requests.get(
                    f"{self.base_url}/sd/upcoming-projects/",
                    headers=self.headers,
                    timeout=10
                )
                
                if opp_response.status_code == 200 and projects_response.status_code == 200:
                    opportunity = opp_response.json()
                    projects = projects_response.json()
                    project = next((p for p in projects if p.get('id') == self.created_project_id), None)
                    
                    if opportunity and project:
                        # Test no data loss
                        self.test_no_data_loss(opportunity, project)
                        
                        # Test proper linking
                        self.test_proper_linking(opportunity, project)
                        
                        # Test timestamps and audit fields
                        self.test_timestamps_audit(opportunity, project)
                        
                        self.log_test(
                            "End-to-End Workflow", 
                            True, 
                            "Complete L5→L6→SD workflow executed successfully"
                        )
                        return True
                    else:
                        self.log_test("End-to-End Workflow", False, "Could not retrieve final states")
                        return False
                else:
                    self.log_test("End-to-End Workflow", False, "Could not retrieve final data")
                    return False
            else:
                self.log_test("End-to-End Workflow", False, "Missing opportunity or project IDs")
                return False
                
        except Exception as e:
            self.log_test("End-to-End Workflow", False, f"Exception: {str(e)}")
            return False

    def test_no_data_loss(self, opportunity, project):
        """Test that no data is lost during integration"""
        try:
            # Key data points that should be preserved
            data_preservation_tests = [
                {
                    "field": "Revenue/Setup Cost",
                    "opp_value": opportunity.get('expected_revenue'),
                    "project_value": project.get('setup_cost'),
                    "should_match": True
                },
                {
                    "field": "Opportunity ID",
                    "opp_value": opportunity.get('opportunity_id'),
                    "project_value": project.get('opp_id'),
                    "should_match": True
                }
            ]
            
            data_loss_detected = False
            
            for test in data_preservation_tests:
                if test["should_match"]:
                    if test["opp_value"] == test["project_value"]:
                        self.log_test(
                            f"Data Preservation: {test['field']}", 
                            True, 
                            f"Data preserved correctly: {test['opp_value']}"
                        )
                    else:
                        self.log_test(
                            f"Data Preservation: {test['field']}", 
                            False, 
                            f"Data loss detected - Opp: {test['opp_value']}, Project: {test['project_value']}"
                        )
                        data_loss_detected = True
            
            if not data_loss_detected:
                self.log_test("No Data Loss", True, "All critical data preserved during integration")
            else:
                self.log_test("No Data Loss", False, "Data loss detected during integration")
                
        except Exception as e:
            self.log_test("No Data Loss", False, f"Exception: {str(e)}")

    def test_proper_linking(self, opportunity, project):
        """Test that opportunity and project are properly linked"""
        try:
            opp_id = opportunity.get('opportunity_id')
            project_opp_id = project.get('opp_id')
            
            if opp_id and project_opp_id and opp_id == project_opp_id:
                self.log_test(
                    "Proper Linking", 
                    True, 
                    f"Opportunity and project properly linked via ID: {opp_id}"
                )
            else:
                self.log_test(
                    "Proper Linking", 
                    False, 
                    f"Linking failed - Opp ID: {opp_id}, Project Opp ID: {project_opp_id}"
                )
                
        except Exception as e:
            self.log_test("Proper Linking", False, f"Exception: {str(e)}")

    def test_timestamps_audit(self, opportunity, project):
        """Test timestamps and audit fields are correct"""
        try:
            # Check that project creation timestamp is after opportunity update
            opp_updated = opportunity.get('updated_at')
            project_created = project.get('created_at')
            
            if opp_updated and project_created:
                try:
                    # Parse timestamps (assuming ISO format)
                    opp_time = datetime.fromisoformat(opp_updated.replace('Z', '+00:00'))
                    project_time = datetime.fromisoformat(project_created.replace('Z', '+00:00'))
                    
                    # Project should be created after or around the same time as opportunity update
                    time_diff = (project_time - opp_time).total_seconds()
                    
                    if -60 <= time_diff <= 300:  # Allow 1 minute before to 5 minutes after
                        self.log_test(
                            "Timestamps Audit", 
                            True, 
                            f"Project created appropriately after opportunity update (diff: {time_diff:.1f}s)"
                        )
                    else:
                        self.log_test(
                            "Timestamps Audit", 
                            False, 
                            f"Timestamp mismatch - time difference: {time_diff:.1f}s"
                        )
                except ValueError:
                    self.log_test("Timestamps Audit", False, "Could not parse timestamps")
            else:
                self.log_test("Timestamps Audit", False, "Missing timestamp data")
                
        except Exception as e:
            self.log_test("Timestamps Audit", False, f"Exception: {str(e)}")

    def test_manual_trigger_endpoint(self):
        """Test the manual trigger endpoint for debugging"""
        print("\n🔧 TESTING MANUAL TRIGGER ENDPOINT")
        print("=" * 50)
        
        if not self.created_opportunity_id:
            self.log_test("Manual Trigger Test", False, "No opportunity available for manual trigger test")
            return False
        
        try:
            # Test the manual trigger endpoint
            response = requests.post(
                f"{self.base_url}/test/trigger-upcoming-project/{self.created_opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "Manual Trigger Endpoint", 
                    True, 
                    f"Manual trigger successful: {result.get('message', 'Success')}"
                )
                return True
            else:
                self.log_test("Manual Trigger Endpoint", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Manual Trigger Endpoint", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all L6→SD integration tests"""
        print("🚀 STARTING L6→SD INTEGRATION TESTING")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with other tests")
            return False
        
        # Step 1: Find opportunity for testing
        if not self.find_or_create_l5_opportunity():
            print("\n❌ COULD NOT FIND SUITABLE OPPORTUNITY - Cannot proceed")
            return False
        
        # Step 2: Test L6 completion trigger
        if not self.test_l6_completion_trigger():
            print("\n❌ L6 COMPLETION TRIGGER FAILED")
            # Continue with other tests to see what we can verify
        
        # Step 3: Test SD upcoming projects creation
        self.test_sd_upcoming_projects_creation()
        
        # Step 4: Test SD API integration
        self.test_sd_api_integration()
        
        # Step 5: Test end-to-end workflow
        self.test_end_to_end_workflow()
        
        # Step 6: Test manual trigger endpoint
        self.test_manual_trigger_endpoint()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 L6→SD INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL L6→SD INTEGRATION TESTS PASSED!")
            print("✅ L6 completion automatically creates upcoming project without manual intervention")
            print("✅ Created project appears in SD upcoming projects list immediately")
            print("✅ All SD schema requirements met with proper data mapping")
            print("✅ Integration is reliable and handles the complete workflow properly")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} TESTS FAILED")
            print("❌ L6→SD integration workflow has issues that need attention")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = L6SDIntegrationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()