#!/usr/bin/env python3
"""
SD Integration Test Suite for Opportunity to Upcoming Project Conversion Workflow
Testing the FIXED integration function and SD schema compatibility
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://service-delivery.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SDIntegrationTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_data = {}
        self.results = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
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
            
    async def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data["access_token"]
                    self.test_data["user"] = data["user"]
                    self.log_result("Authentication", True, "Admin login successful")
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("Authentication", False, f"Login failed: {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
            
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
        
    async def test_create_test_opportunity(self):
        """Create a test opportunity for conversion testing"""
        try:
            # First get required master data
            companies_response = await self.session.get(f"{API_BASE}/companies", headers=self.get_headers())
            if companies_response.status != 200:
                self.log_result("Create Test Opportunity", False, "Failed to fetch companies")
                return False
                
            companies = await companies_response.json()
            if not companies:
                self.log_result("Create Test Opportunity", False, "No companies available")
                return False
                
            company_id = companies[0]["id"]
            
            # Get stages
            stages_response = await self.session.get(f"{API_BASE}/mst/stages", headers=self.get_headers())
            if stages_response.status != 200:
                self.log_result("Create Test Opportunity", False, "Failed to fetch stages")
                return False
                
            stages = await stages_response.json()
            l1_stage = next((s for s in stages if s["stage_code"] == "L1"), None)
            if not l1_stage:
                self.log_result("Create Test Opportunity", False, "L1 stage not found")
                return False
                
            # Get currencies
            currencies_response = await self.session.get(f"{API_BASE}/mst/currencies", headers=self.get_headers())
            currencies = await currencies_response.json()
            inr_currency = next((c for c in currencies if c["currency_code"] == "INR"), None)
            if not inr_currency:
                self.log_result("Create Test Opportunity", False, "INR currency not found")
                return False
                
            # Create opportunity
            opportunity_data = {
                "stage_id": l1_stage["id"],
                "project_title": "SD Integration Test Opportunity",
                "company_id": company_id,
                "expected_revenue": 500000.0,
                "currency_id": inr_currency["id"],
                "lead_owner_id": self.test_data["user"]["id"],
                "win_probability": 10
            }
            
            async with self.session.post(f"{API_BASE}/opportunities", json=opportunity_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    opportunity = await response.json()
                    self.test_data["opportunity"] = opportunity
                    self.log_result("Create Test Opportunity", True, f"Created opportunity: {opportunity['opportunity_id']}")
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("Create Test Opportunity", False, f"Failed to create opportunity: {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("Create Test Opportunity", False, f"Error creating opportunity: {str(e)}")
            return False
            
    async def test_create_quotation(self):
        """Create a quotation for the test opportunity"""
        try:
            if "opportunity" not in self.test_data:
                self.log_result("Create Quotation", False, "No test opportunity available")
                return False
                
            opportunity_id = self.test_data["opportunity"]["id"]
            
            # Get rate cards
            rate_cards_response = await self.session.get(f"{API_BASE}/mst/rate-cards", headers=self.get_headers())
            if rate_cards_response.status != 200:
                self.log_result("Create Quotation", False, "Failed to fetch rate cards")
                return False
                
            rate_cards = await rate_cards_response.json()
            if not rate_cards:
                self.log_result("Create Quotation", False, "No rate cards available")
                return False
                
            rate_card = rate_cards[0]
            
            # Create quotation
            quotation_data = {
                "quotation_name": "SD Integration Test Quotation",
                "rate_card_id": rate_card["id"],
                "validity_date": "2024-12-31",
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Service",
                        "qty": 1,
                        "unit": "Service",
                        "unit_price": 500000.0,
                        "discount_percentage": 0,
                        "line_total": 500000.0,
                        "pricing_type": "one_time"
                    }
                ]
            }
            
            async with self.session.post(f"{API_BASE}/opportunities/{opportunity_id}/quotations", json=quotation_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    quotation = await response.json()
                    self.test_data["quotation"] = quotation
                    
                    # Mark quotation as selected
                    quotation_id = quotation["id"]
                    select_data = {"is_selected": True}
                    
                    async with self.session.put(f"{API_BASE}/opportunities/{opportunity_id}/quotations/{quotation_id}", json=select_data, headers=self.get_headers()) as select_response:
                        if select_response.status == 200:
                            self.log_result("Create Quotation", True, f"Created and selected quotation: {quotation['quotation_id']}")
                            return True
                        else:
                            self.log_result("Create Quotation", False, "Failed to select quotation")
                            return False
                else:
                    error_text = await response.text()
                    self.log_result("Create Quotation", False, f"Failed to create quotation: {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("Create Quotation", False, f"Error creating quotation: {str(e)}")
            return False
            
    async def test_progress_opportunity_to_l6(self):
        """Progress opportunity through stages to L6 (Won)"""
        try:
            if "opportunity" not in self.test_data:
                self.log_result("Progress to L6", False, "No test opportunity available")
                return False
                
            opportunity_id = self.test_data["opportunity"]["id"]
            
            # Get stages for progression
            stages_response = await self.session.get(f"{API_BASE}/mst/stages", headers=self.get_headers())
            stages = await stages_response.json()
            
            # Progress through L2, L3, L4, L5, then L6
            stage_progression = ["L2", "L3", "L4", "L5", "L6"]
            
            for stage_code in stage_progression:
                stage = next((s for s in stages if s["stage_code"] == stage_code), None)
                if not stage:
                    self.log_result("Progress to L6", False, f"Stage {stage_code} not found")
                    return False
                    
                # Prepare stage change data
                stage_data = {"target_stage": stage["stage_order"]}
                
                # Add commercial decision for L5 stage
                if stage_code == "L5":
                    stage_data["commercial_decision"] = "won"
                    
                async with self.session.put(f"{API_BASE}/opportunities/{opportunity_id}/change-stage", json=stage_data, headers=self.get_headers()) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.log_result("Progress to L6", False, f"Failed to progress to {stage_code}: {response.status}", {"error": error_text})
                        return False
                        
            self.log_result("Progress to L6", True, "Successfully progressed opportunity to L6 (Won)")
            return True
            
        except Exception as e:
            self.log_result("Progress to L6", False, f"Error progressing opportunity: {str(e)}")
            return False
            
    async def test_verify_upcoming_project_creation(self):
        """Verify that upcoming project was created automatically"""
        try:
            # Wait a moment for the integration function to complete
            await asyncio.sleep(2)
            
            # Get upcoming projects
            async with self.session.get(f"{API_BASE}/sd/upcoming-projects/", headers=self.get_headers()) as response:
                if response.status == 200:
                    upcoming_projects = await response.json()
                    
                    if not upcoming_projects:
                        self.log_result("Verify Upcoming Project Creation", False, "No upcoming projects found after opportunity won")
                        return False
                        
                    # Find our project by opportunity ID
                    opportunity_id = self.test_data["opportunity"]["opportunity_id"]
                    our_project = None
                    
                    for project in upcoming_projects:
                        if project.get("opp_id") == opportunity_id:
                            our_project = project
                            break
                            
                    if not our_project:
                        self.log_result("Verify Upcoming Project Creation", False, f"Upcoming project not found for opportunity {opportunity_id}")
                        return False
                        
                    self.test_data["upcoming_project"] = our_project
                    self.log_result("Verify Upcoming Project Creation", True, f"Found upcoming project: {our_project.get('pot_id')}")
                    return True
                    
                else:
                    error_text = await response.text()
                    self.log_result("Verify Upcoming Project Creation", False, f"Failed to fetch upcoming projects: {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("Verify Upcoming Project Creation", False, f"Error verifying upcoming project: {str(e)}")
            return False
            
    async def test_sd_schema_compatibility(self):
        """Test SD schema compatibility - verify required fields"""
        try:
            if "upcoming_project" not in self.test_data:
                self.log_result("SD Schema Compatibility", False, "No upcoming project to test")
                return False
                
            project = self.test_data["upcoming_project"]
            
            # Required SD schema fields
            required_fields = [
                "order_id",
                "opp_id", 
                "pot_id",
                "customer_name",
                "setup_cost"
            ]
            
            missing_fields = []
            field_details = {}
            
            for field in required_fields:
                if field not in project or project[field] is None:
                    missing_fields.append(field)
                else:
                    field_details[field] = project[field]
                    
            if missing_fields:
                self.log_result("SD Schema Compatibility", False, f"Missing required fields: {missing_fields}", {"project": project})
                return False
                
            # Verify field formats
            format_checks = []
            
            # Check order_id format (should be OA-XXXXXXXX)
            order_id = project["order_id"]
            if not order_id.startswith("OA-") or len(order_id) != 11:
                format_checks.append(f"order_id format incorrect: {order_id}")
                
            # Check pot_id format (should be POT-XXXXXXXX)
            pot_id = project["pot_id"]
            if not pot_id.startswith("POT-") or len(pot_id) != 12:
                format_checks.append(f"pot_id format incorrect: {pot_id}")
                
            # Check setup_cost is numeric
            setup_cost = project["setup_cost"]
            if not isinstance(setup_cost, (int, float)):
                format_checks.append(f"setup_cost not numeric: {setup_cost}")
                
            if format_checks:
                self.log_result("SD Schema Compatibility", False, f"Format issues: {format_checks}", {"field_details": field_details})
                return False
                
            self.log_result("SD Schema Compatibility", True, "All required SD schema fields present and correctly formatted", {"field_details": field_details})
            return True
            
        except Exception as e:
            self.log_result("SD Schema Compatibility", False, f"Error checking schema compatibility: {str(e)}")
            return False
            
    async def test_status_fields_alignment(self):
        """Test that status fields are set correctly"""
        try:
            if "upcoming_project" not in self.test_data:
                self.log_result("Status Fields Alignment", False, "No upcoming project to test")
                return False
                
            project = self.test_data["upcoming_project"]
            
            # Expected status values
            expected_statuses = {
                "loi_status": "Pending",
                "opp_status": "Won",
                "order_status": "Pending",
                "validation_status": "Pending GC Sign-off"
            }
            
            status_issues = []
            status_details = {}
            
            for status_field, expected_value in expected_statuses.items():
                actual_value = project.get(status_field)
                status_details[status_field] = actual_value
                
                if actual_value != expected_value:
                    status_issues.append(f"{status_field}: expected '{expected_value}', got '{actual_value}'")
                    
            if status_issues:
                self.log_result("Status Fields Alignment", False, f"Status field mismatches: {status_issues}", {"status_details": status_details})
                return False
                
            self.log_result("Status Fields Alignment", True, "All status fields correctly set", {"status_details": status_details})
            return True
            
        except Exception as e:
            self.log_result("Status Fields Alignment", False, f"Error checking status alignment: {str(e)}")
            return False
            
    async def test_datetime_serialization(self):
        """Test that datetime fields are properly serialized"""
        try:
            if "upcoming_project" not in self.test_data:
                self.log_result("Datetime Serialization", False, "No upcoming project to test")
                return False
                
            project = self.test_data["upcoming_project"]
            
            # Check datetime fields
            datetime_fields = ["created_at", "updated_at"]
            datetime_details = {}
            serialization_issues = []
            
            for field in datetime_fields:
                if field in project:
                    value = project[field]
                    datetime_details[field] = value
                    
                    # Check if it's a valid ISO string or datetime object
                    if isinstance(value, str):
                        try:
                            datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            serialization_issues.append(f"{field}: invalid datetime format '{value}'")
                    elif not isinstance(value, datetime):
                        serialization_issues.append(f"{field}: not a datetime or ISO string '{value}'")
                        
            if serialization_issues:
                self.log_result("Datetime Serialization", False, f"Datetime serialization issues: {serialization_issues}", {"datetime_details": datetime_details})
                return False
                
            self.log_result("Datetime Serialization", True, "Datetime fields properly serialized", {"datetime_details": datetime_details})
            return True
            
        except Exception as e:
            self.log_result("Datetime Serialization", False, f"Error checking datetime serialization: {str(e)}")
            return False
            
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow visibility"""
        try:
            # Test that the upcoming project appears in SD team interface
            async with self.session.get(f"{API_BASE}/sd/upcoming-projects/", headers=self.get_headers()) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.log_result("End-to-End Workflow", False, f"SD interface not accessible: {response.status}", {"error": error_text})
                    return False
                    
                upcoming_projects = await response.json()
                
                if not upcoming_projects:
                    self.log_result("End-to-End Workflow", False, "No projects visible in SD interface")
                    return False
                    
                # Verify our project is in the list
                opportunity_id = self.test_data["opportunity"]["opportunity_id"]
                our_project = next((p for p in upcoming_projects if p.get("opp_id") == opportunity_id), None)
                
                if not our_project:
                    self.log_result("End-to-End Workflow", False, f"Our project not visible in SD interface for opp_id: {opportunity_id}")
                    return False
                    
                # Test data mapping correctness
                mapping_checks = []
                
                # Check customer name mapping
                expected_customer = self.test_data["opportunity"].get("company_name", "Unknown")
                actual_customer = our_project.get("customer_name")
                if actual_customer != expected_customer and actual_customer == "Unknown Company":
                    mapping_checks.append(f"Customer name not properly mapped: expected '{expected_customer}', got '{actual_customer}'")
                    
                # Check setup cost mapping (should match quotation total or expected revenue)
                expected_cost = 500000.0  # From our test quotation
                actual_cost = our_project.get("setup_cost", 0)
                if abs(float(actual_cost) - expected_cost) > 0.01:
                    mapping_checks.append(f"Setup cost not properly mapped: expected {expected_cost}, got {actual_cost}")
                    
                if mapping_checks:
                    self.log_result("End-to-End Workflow", False, f"Data mapping issues: {mapping_checks}", {"project": our_project})
                    return False
                    
                self.log_result("End-to-End Workflow", True, "Complete workflow functional - project visible in SD interface with correct data mapping")
                return True
                
        except Exception as e:
            self.log_result("End-to-End Workflow", False, f"Error testing end-to-end workflow: {str(e)}")
            return False
            
    async def test_collection_consistency(self):
        """Test that both integration function and SD router use the same collection"""
        try:
            # This test verifies that the upcoming project created by the integration function
            # is accessible through the SD router, confirming they use the same collection
            
            if "upcoming_project" not in self.test_data:
                self.log_result("Collection Consistency", False, "No upcoming project to test")
                return False
                
            project_id = self.test_data["upcoming_project"]["id"]
            
            # Try to fetch the specific project through SD router
            async with self.session.get(f"{API_BASE}/sd/upcoming-projects/{project_id}", headers=self.get_headers()) as response:
                if response.status == 200:
                    project_detail = await response.json()
                    
                    # Verify it's the same project
                    if project_detail.get("opp_id") == self.test_data["opportunity"]["opportunity_id"]:
                        self.log_result("Collection Consistency", True, "Integration function and SD router use consistent collection")
                        return True
                    else:
                        self.log_result("Collection Consistency", False, "Project data inconsistent between integration and SD router")
                        return False
                        
                elif response.status == 404:
                    self.log_result("Collection Consistency", False, "Project created by integration not accessible through SD router")
                    return False
                else:
                    error_text = await response.text()
                    self.log_result("Collection Consistency", False, f"Error accessing project through SD router: {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("Collection Consistency", False, f"Error testing collection consistency: {str(e)}")
            return False
            
    async def test_data_migration_check(self):
        """Check for orphaned projects and verify new schema compliance"""
        try:
            # Get all upcoming projects
            async with self.session.get(f"{API_BASE}/sd/upcoming-projects/", headers=self.get_headers()) as response:
                if response.status != 200:
                    self.log_result("Data Migration Check", False, "Cannot access upcoming projects for migration check")
                    return False
                    
                all_projects = await response.json()
                
                if not all_projects:
                    self.log_result("Data Migration Check", True, "No existing projects to check for migration issues")
                    return True
                    
                # Check each project for schema compliance
                schema_issues = []
                old_schema_projects = []
                
                for project in all_projects:
                    # Check for old schema fields that should be migrated
                    if "project_name" in project or "opportunity_id" in project:
                        old_schema_projects.append(project.get("id", "unknown"))
                        
                    # Check for required new schema fields
                    required_fields = ["order_id", "opp_id", "pot_id", "customer_name", "setup_cost"]
                    missing_fields = [field for field in required_fields if field not in project or project[field] is None]
                    
                    if missing_fields:
                        schema_issues.append({
                            "project_id": project.get("id", "unknown"),
                            "missing_fields": missing_fields
                        })
                        
                if old_schema_projects:
                    self.log_result("Data Migration Check", False, f"Found {len(old_schema_projects)} projects with old schema", {"old_schema_projects": old_schema_projects})
                    return False
                    
                if schema_issues:
                    self.log_result("Data Migration Check", False, f"Found {len(schema_issues)} projects with schema issues", {"schema_issues": schema_issues})
                    return False
                    
                self.log_result("Data Migration Check", True, f"All {len(all_projects)} projects follow new SD schema correctly")
                return True
                
        except Exception as e:
            self.log_result("Data Migration Check", False, f"Error checking data migration: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting SD Integration: Opportunity to Upcoming Project Conversion Tests")
        print("=" * 80)
        
        await self.setup_session()
        
        try:
            # Authentication
            if not await self.authenticate():
                return
                
            # Test sequence
            test_sequence = [
                ("Create Test Opportunity", self.test_create_test_opportunity),
                ("Create Quotation", self.test_create_quotation),
                ("Progress to L6 (Won)", self.test_progress_opportunity_to_l6),
                ("Verify Upcoming Project Creation", self.test_verify_upcoming_project_creation),
                ("SD Schema Compatibility", self.test_sd_schema_compatibility),
                ("Status Fields Alignment", self.test_status_fields_alignment),
                ("Datetime Serialization", self.test_datetime_serialization),
                ("End-to-End Workflow", self.test_end_to_end_workflow),
                ("Collection Consistency", self.test_collection_consistency),
                ("Data Migration Check", self.test_data_migration_check)
            ]
            
            for test_name, test_func in test_sequence:
                print(f"\n🔍 Running: {test_name}")
                await test_func()
                
        finally:
            await self.cleanup_session()
            
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
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

async def main():
    """Main test runner"""
    tester = SDIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())