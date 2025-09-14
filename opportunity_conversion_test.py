#!/usr/bin/env python3
"""
Backend Test Suite for Opportunity to Upcoming Project Conversion Workflow
Testing the critical workflow reported by user as not working.
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import sys
import os

# Configuration
BACKEND_URL = "https://service-delivery.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class OpportunityToProjectWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        })
        
        if not success:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_test("Authentication", True, "Admin login successful")
                return True
            else:
                self.log_test("Authentication", False, f"Login failed: {response.status_code}", 
                            {"response": response.text})
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_opportunity_management_endpoints(self):
        """Test if opportunity management endpoints exist and work"""
        print("\n=== TESTING OPPORTUNITY MANAGEMENT ENDPOINTS ===")
        
        # Test GET opportunities
        try:
            response = self.session.get(f"{BACKEND_URL}/opportunities")
            if response.status_code == 200:
                opportunities = response.json()
                self.log_test("GET Opportunities", True, 
                            f"Found {len(opportunities)} opportunities")
            else:
                self.log_test("GET Opportunities", False, 
                            f"Failed to get opportunities: {response.status_code}")
        except Exception as e:
            self.log_test("GET Opportunities", False, f"Error: {str(e)}")
        
        # Test opportunity stage endpoints
        try:
            response = self.session.get(f"{BACKEND_URL}/mst/stages")
            if response.status_code == 200:
                stages = response.json()
                l6_stage = next((s for s in stages if s.get("stage_code") == "L6"), None)
                if l6_stage:
                    self.log_test("L6 Won Stage", True, "L6 (Won) stage found in master data")
                else:
                    self.log_test("L6 Won Stage", False, "L6 (Won) stage not found")
            else:
                self.log_test("Stage Master Data", False, 
                            f"Failed to get stages: {response.status_code}")
        except Exception as e:
            self.log_test("Stage Master Data", False, f"Error: {str(e)}")
    
    def test_upcoming_projects_endpoints(self):
        """Test upcoming projects endpoints"""
        print("\n=== TESTING UPCOMING PROJECTS ENDPOINTS ===")
        
        # Test GET upcoming projects
        try:
            response = self.session.get(f"{BACKEND_URL}/sd/upcoming-projects/")
            if response.status_code == 200:
                projects = response.json()
                self.log_test("GET Upcoming Projects", True, 
                            f"Endpoint working, found {len(projects)} projects")
            else:
                self.log_test("GET Upcoming Projects", False, 
                            f"Failed: {response.status_code}", {"response": response.text})
        except Exception as e:
            self.log_test("GET Upcoming Projects", False, f"Error: {str(e)}")
        
        # Test POST upcoming projects (manual creation)
        try:
            test_project_data = {
                "order_id": f"TEST-ORDER-{uuid.uuid4().hex[:8]}",
                "opp_id": f"TEST-OPP-{uuid.uuid4().hex[:8]}",
                "pot_id": f"POT-{uuid.uuid4().hex[:8]}",
                "customer_name": "Test Customer for Manual Creation",
                "setup_cost": 50000.0,
                "loi_status": "Pending"
            }
            
            response = self.session.post(f"{BACKEND_URL}/sd/upcoming-projects/", 
                                       json=test_project_data)
            
            if response.status_code == 200:
                created_project = response.json()
                self.log_test("POST Upcoming Projects", True, 
                            "Manual upcoming project creation works",
                            {"project_id": created_project.get("id")})
                return created_project.get("id")
            else:
                self.log_test("POST Upcoming Projects", False, 
                            f"Failed: {response.status_code}", {"response": response.text})
                return None
                
        except Exception as e:
            self.log_test("POST Upcoming Projects", False, f"Error: {str(e)}")
            return None
    
    def get_or_create_test_opportunity(self):
        """Get existing opportunity or create one via lead conversion"""
        print("\n=== GETTING OR CREATING TEST OPPORTUNITY ===")
        
        try:
            # First, check if there are existing opportunities we can use
            response = self.session.get(f"{BACKEND_URL}/opportunities")
            if response.status_code == 200:
                data = response.json()
                
                # Handle both direct list and nested structure
                if isinstance(data, dict) and "opportunities" in data:
                    opportunities = data["opportunities"]
                elif isinstance(data, list):
                    opportunities = data
                else:
                    opportunities = []
                
                # Look for an opportunity in L1 stage that we can progress
                for opp in opportunities:
                    if isinstance(opp, dict) and opp.get("current_stage", 1) == 1:  # L1 stage
                        self.log_test("Use Existing L1 Opportunity", True, 
                                    f"Using existing L1 opportunity: {opp.get('opportunity_id')}",
                                    {"opportunity_id": opp.get("id")})
                        return opp
                
                # If no L1 opportunities, use any opportunity and note its current stage
                if opportunities:
                    test_opp = opportunities[0]
                    if isinstance(test_opp, dict):
                        self.log_test("Use Existing Opportunity", True, 
                                    f"Using existing opportunity at stage L{test_opp.get('current_stage', 1)}: {test_opp.get('opportunity_id')}",
                                    {"opportunity_id": test_opp.get("id")})
                        return test_opp
            
            # If no opportunities exist, try to create one via lead conversion
            return self.create_opportunity_via_lead_conversion()
                
        except Exception as e:
            self.log_test("Get Test Opportunity", False, f"Error: {str(e)}")
            return None
    
    def create_opportunity_via_lead_conversion(self):
        """Create opportunity by first creating and converting a lead"""
        print("\n=== CREATING OPPORTUNITY VIA LEAD CONVERSION ===")
        
        try:
            # Get required master data
            companies_response = self.session.get(f"{BACKEND_URL}/companies")
            if companies_response.status_code != 200:
                self.log_test("Get Companies for Lead", False, "Failed to get companies")
                return None
            
            companies = companies_response.json()
            if not companies:
                self.log_test("Get Companies for Lead", False, "No companies found")
                return None
            
            test_company = companies[0]
            
            # Get product services
            services_response = self.session.get(f"{BACKEND_URL}/product-services")
            services = services_response.json() if services_response.status_code == 200 else []
            service_id = services[0]["id"] if services else str(uuid.uuid4())
            
            # Create a test lead first
            lead_data = {
                "tender_type": "Tender",
                "billing_type": "Project Based",
                "project_title": f"Test Lead for Conversion - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "company_id": test_company["id"],
                "state": "Maharashtra",
                "lead_subtype": "New Business",
                "source": "Website",
                "product_service_id": service_id,
                "expected_orc": 100000.0,
                "revenue": 100000.0,
                "lead_owner": "admin"
            }
            
            # Create lead
            lead_response = self.session.post(f"{BACKEND_URL}/leads", json=lead_data)
            
            if lead_response.status_code != 200:
                self.log_test("Create Lead", False, f"Failed to create lead: {lead_response.status_code}")
                return None
            
            lead = lead_response.json()
            lead_id = lead.get("id")
            
            self.log_test("Create Lead", True, f"Created lead: {lead.get('lead_id')}")
            
            # Approve the lead first
            approve_response = self.session.post(f"{BACKEND_URL}/leads/{lead_id}/status", 
                                               json={"status": "approved"})
            
            if approve_response.status_code == 200:
                self.log_test("Approve Lead", True, "Lead approved successfully")
            else:
                self.log_test("Approve Lead", False, f"Failed to approve lead: {approve_response.status_code}")
            
            # Convert lead to opportunity
            convert_response = self.session.post(f"{BACKEND_URL}/leads/{lead_id}/convert?opportunity_date={datetime.now().date()}")
            
            if convert_response.status_code == 200:
                conversion_result = convert_response.json()
                opportunity_id = conversion_result.get("opportunity_id")
                
                # Get the created opportunity
                opp_response = self.session.get(f"{BACKEND_URL}/opportunities/{opportunity_id}")
                if opp_response.status_code == 200:
                    opportunity = opp_response.json()
                    self.log_test("Convert Lead to Opportunity", True, 
                                f"Successfully converted lead to opportunity: {opportunity.get('opportunity_id')}")
                    return opportunity
                else:
                    self.log_test("Get Converted Opportunity", False, 
                                f"Failed to get converted opportunity: {opp_response.status_code}")
                    return None
            else:
                self.log_test("Convert Lead to Opportunity", False, 
                            f"Failed to convert lead: {convert_response.status_code}",
                            {"response": convert_response.text})
                return None
                
        except Exception as e:
            self.log_test("Create Opportunity via Lead", False, f"Error: {str(e)}")
            return None
    
    def progress_opportunity_to_l6(self, opportunity):
        """Progress opportunity through stages to L6 (Won)"""
        print("\n=== PROGRESSING OPPORTUNITY TO L6 (WON) ===")
        
        if not opportunity:
            self.log_test("Progress to L6", False, "No opportunity provided")
            return False
        
        opportunity_id = opportunity.get("id")
        current_stage = opportunity.get("current_stage", 1)
        
        try:
            # Define all stages we might need to progress through
            all_stages = [
                {"stage": 2, "name": "L2 - Qualification", "data": {"region_id": str(uuid.uuid4())}},
                {"stage": 3, "name": "L3 - Proposal", "data": {"proposal_submitted": True}},
                {"stage": 4, "name": "L4 - Technical", "data": {"technical_review": "Completed"}},
                {"stage": 5, "name": "L5 - Commercial", "data": {"commercial_decision": "won"}},
                {"stage": 6, "name": "L6 - Won", "data": {
                    "final_value": 95000.0,
                    "client_poc": "John Doe",
                    "delivery_team": "Team Alpha"
                }}
            ]
            
            # Only progress through stages we haven't reached yet
            stages_to_progress = [s for s in all_stages if s["stage"] > current_stage]
            
            if not stages_to_progress:
                self.log_test("Already at L6", True, f"Opportunity already at stage L{current_stage}")
                if current_stage == 6:
                    # Check if upcoming project was created
                    return self.verify_upcoming_project_creation(opportunity_id)
                return False
            
            for stage_info in stages_to_progress:
                stage_transition_data = {
                    "target_stage": stage_info["stage"],
                    "stage_data": stage_info["data"],
                    "notes": f"Test progression to {stage_info['name']}"
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/opportunities/{opportunity_id}/change-stage",
                    json=stage_transition_data
                )
                
                if response.status_code == 200:
                    self.log_test(f"Progress to {stage_info['name']}", True, 
                                f"Successfully moved to {stage_info['name']}")
                    
                    # Special check for L6 - this should trigger upcoming project creation
                    if stage_info["stage"] == 6:
                        # Wait a moment for the async operation
                        import time
                        time.sleep(3)
                        
                        # Check if upcoming project was created
                        return self.verify_upcoming_project_creation(opportunity_id)
                else:
                    self.log_test(f"Progress to {stage_info['name']}", False, 
                                f"Failed: {response.status_code}", {"response": response.text})
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("Progress to L6", False, f"Error: {str(e)}")
            return False
    
    def verify_upcoming_project_creation(self, opportunity_id):
        """Verify that an upcoming project was created from the won opportunity"""
        print("\n=== VERIFYING UPCOMING PROJECT CREATION ===")
        
        try:
            # Get all upcoming projects
            response = self.session.get(f"{BACKEND_URL}/sd/upcoming-projects/")
            
            if response.status_code != 200:
                self.log_test("Get Upcoming Projects for Verification", False, 
                            f"Failed to get projects: {response.status_code}")
                return False
            
            projects = response.json()
            
            # Look for project created from our opportunity
            matching_project = None
            for project in projects:
                if project.get("opportunity_id") == opportunity_id:
                    matching_project = project
                    break
            
            if matching_project:
                self.log_test("Automatic Project Creation", True, 
                            "Upcoming project automatically created from won opportunity",
                            {
                                "project_id": matching_project.get("id"),
                                "project_name": matching_project.get("project_name"),
                                "opportunity_id": opportunity_id
                            })
                return True
            else:
                self.log_test("Automatic Project Creation", False, 
                            "No upcoming project found for the won opportunity",
                            {
                                "opportunity_id": opportunity_id,
                                "total_projects": len(projects),
                                "projects": [p.get("id") for p in projects]
                            })
                return False
                
        except Exception as e:
            self.log_test("Verify Project Creation", False, f"Error: {str(e)}")
            return False
    
    def test_integration_function_exists(self):
        """Test if the integration function exists by checking server logs or database"""
        print("\n=== TESTING INTEGRATION FUNCTION ===")
        
        # We can't directly test the function existence, but we can test the workflow
        # The function should be called when an opportunity moves to L6
        
        # Check if there are any existing upcoming projects from opportunities
        try:
            response = self.session.get(f"{BACKEND_URL}/sd/upcoming-projects/")
            if response.status_code == 200:
                projects = response.json()
                opportunity_projects = [p for p in projects if p.get("opportunity_id")]
                
                if opportunity_projects:
                    self.log_test("Integration Function Evidence", True, 
                                f"Found {len(opportunity_projects)} projects with opportunity_id",
                                {"sample_project": opportunity_projects[0] if opportunity_projects else None})
                else:
                    self.log_test("Integration Function Evidence", False, 
                                "No projects found with opportunity_id - integration may not be working")
            else:
                self.log_test("Integration Function Check", False, 
                            f"Could not check projects: {response.status_code}")
                
        except Exception as e:
            self.log_test("Integration Function Check", False, f"Error: {str(e)}")
    
    def debug_database_state(self):
        """Debug the current state of opportunities and upcoming projects"""
        print("\n=== DEBUGGING DATABASE STATE ===")
        
        try:
            # Check opportunities
            opp_response = self.session.get(f"{BACKEND_URL}/opportunities")
            if opp_response.status_code == 200:
                opportunities = opp_response.json()
                won_opportunities = []
                
                for opp in opportunities:
                    if isinstance(opp, dict):  # Ensure it's a dictionary
                        if opp.get("current_stage") == 6 or opp.get("status") == "Won":
                            won_opportunities.append(opp)
                
                self.log_test("Won Opportunities Check", True, 
                            f"Found {len(won_opportunities)} won opportunities out of {len(opportunities)} total",
                            {"won_opps": [o.get("opportunity_id", "unknown") for o in won_opportunities]})
            
            # Check upcoming projects
            proj_response = self.session.get(f"{BACKEND_URL}/sd/upcoming-projects/")
            if proj_response.status_code == 200:
                projects = proj_response.json()
                self.log_test("Upcoming Projects Check", True, 
                            f"Found {len(projects)} upcoming projects",
                            {"project_ids": [p.get("id", "unknown") for p in projects if isinstance(p, dict)]})
                
                # Check for orphaned data
                projects_with_opp_id = []
                for p in projects:
                    if isinstance(p, dict) and p.get("opportunity_id"):
                        projects_with_opp_id.append(p)
                        
                self.log_test("Projects with Opportunity Link", True, 
                            f"Found {len(projects_with_opp_id)} projects linked to opportunities")
            
        except Exception as e:
            self.log_test("Database State Debug", False, f"Error: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("🚀 STARTING COMPREHENSIVE OPPORTUNITY TO UPCOMING PROJECT CONVERSION TEST")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 2: Test opportunity management endpoints
        self.test_opportunity_management_endpoints()
        
        # Step 3: Test upcoming projects endpoints
        manual_project_id = self.test_upcoming_projects_endpoints()
        
        # Step 4: Test integration function evidence
        self.test_integration_function_exists()
        
        # Step 5: Debug current database state
        self.debug_database_state()
        
        # Step 6: Test the complete workflow
        test_opportunity = self.get_or_create_test_opportunity()
        if test_opportunity:
            conversion_success = self.progress_opportunity_to_l6(test_opportunity)
        else:
            conversion_success = False
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  ❌ {test['test']}: {test['message']}")
        
        # Critical workflow assessment
        print("\n🎯 CRITICAL WORKFLOW ASSESSMENT:")
        if conversion_success:
            print("✅ OPPORTUNITY TO UPCOMING PROJECT CONVERSION: WORKING")
        else:
            print("❌ OPPORTUNITY TO UPCOMING PROJECT CONVERSION: NOT WORKING")
            print("   This is the critical issue reported by the user!")
        
        return conversion_success

if __name__ == "__main__":
    tester = OpportunityToProjectWorkflowTester()
    success = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)