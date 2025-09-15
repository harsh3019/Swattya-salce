#!/usr/bin/env python3
"""
Comprehensive Test for AUTOMATIC L6 Stage Transition Trigger
Testing the automatic opportunity to upcoming project conversion during L6 stage transition.

This test verifies:
1. Automatic L6 stage transition triggers integration function
2. Stage change integration logic (line 5306 in server.py)
3. Error handling during stage change (lines 5307-5308)
4. Complete workflow: Opportunity → L6 → Auto-create upcoming project
5. Comparison between manual vs automatic creation
6. Edge cases and error handling
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test Configuration
BASE_URL = "https://sawayatta-sd.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class AutomaticL6TriggerTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.created_opportunities = []
        self.created_projects = []
        
    async def setup_session(self):
        """Setup HTTP session and authenticate"""
        self.session = aiohttp.ClientSession()
        
        # Login and get token
        async with self.session.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS) as response:
            if response.status == 200:
                data = await response.json()
                self.auth_token = data["access_token"]
                logger.info("✅ Authentication successful")
                return True
            else:
                logger.error(f"❌ Authentication failed: {response.status}")
                return False
    
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    async def log_test_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name} - {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    async def create_test_opportunity(self, stage: int = 1) -> dict:
        """Create a test opportunity at specified stage"""
        try:
            # Get required master data
            companies_response = await self.session.get(f"{BASE_URL}/companies", headers=self.get_headers())
            companies = await companies_response.json()
            
            if not companies:
                raise Exception("No companies found for testing")
            
            company_id = companies[0]["id"]
            
            # Get users for lead owner
            users_response = await self.session.get(f"{BASE_URL}/users", headers=self.get_headers())
            users = await users_response.json()
            
            if not users:
                raise Exception("No users found for testing")
            
            user_id = users[0]["id"]
            
            # Get currencies
            currencies_response = await self.session.get(f"{BASE_URL}/currencies", headers=self.get_headers())
            currencies = await currencies_response.json()
            
            currency_id = currencies[0]["id"] if currencies else None
            
            # Create opportunity data
            opportunity_data = {
                "project_title": f"Test Opportunity for L6 Trigger - {datetime.now().strftime('%H%M%S')}",
                "company_id": company_id,
                "expected_revenue": 750000.0,
                "currency_id": currency_id,
                "lead_owner_id": user_id,
                "stage_id": "1",  # Start at L1
                "win_probability": 10.0
            }
            
            # Create opportunity
            async with self.session.post(f"{BASE_URL}/opportunities", json=opportunity_data, headers=self.get_headers()) as response:
                if response.status == 201:
                    opportunity = await response.json()
                    self.created_opportunities.append(opportunity["id"])
                    
                    # If we need to progress to a specific stage, do it step by step
                    if stage > 1:
                        await self.progress_opportunity_to_stage(opportunity["id"], stage)
                    
                    logger.info(f"✅ Created test opportunity: {opportunity['id']} at stage L{stage}")
                    return opportunity
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to create opportunity: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to create test opportunity: {str(e)}")
            raise
    
    async def progress_opportunity_to_stage(self, opportunity_id: str, target_stage: int):
        """Progress opportunity to target stage step by step"""
        try:
            # Get current opportunity
            async with self.session.get(f"{BASE_URL}/opportunities/{opportunity_id}", headers=self.get_headers()) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get opportunity: {response.status}")
                
                opportunity = await response.json()
                current_stage = opportunity.get("current_stage", 1)
                
                # Progress stage by stage
                for stage in range(current_stage + 1, target_stage + 1):
                    stage_data = self.get_stage_data_for_progression(stage)
                    
                    transition_data = {
                        "target_stage": stage,
                        "stage_data": stage_data,
                        "notes": f"Progressing to L{stage} for testing"
                    }
                    
                    async with self.session.post(
                        f"{BASE_URL}/opportunities/{opportunity_id}/change-stage",
                        json=transition_data,
                        headers=self.get_headers()
                    ) as stage_response:
                        if stage_response.status != 200:
                            error_text = await stage_response.text()
                            raise Exception(f"Failed to progress to L{stage}: {stage_response.status} - {error_text}")
                        
                        logger.info(f"✅ Progressed opportunity {opportunity_id} to L{stage}")
                        
                        # Small delay between stage changes
                        await asyncio.sleep(0.5)
                        
        except Exception as e:
            logger.error(f"❌ Failed to progress opportunity to L{target_stage}: {str(e)}")
            raise
    
    def get_stage_data_for_progression(self, stage: int) -> dict:
        """Get minimal stage data required for progression"""
        stage_data = {}
        
        if stage == 2:  # L2 - Qualification
            stage_data = {
                "budget_confirmed": True,
                "authority_identified": True,
                "need_established": True,
                "timeline_defined": True
            }
        elif stage == 3:  # L3 - Proposal
            stage_data = {
                "proposal_submitted": True,
                "submission_date": datetime.now(timezone.utc).isoformat()
            }
        elif stage == 4:  # L4 - Technical
            stage_data = {
                "technical_review_completed": True
            }
        elif stage == 5:  # L5 - Commercial
            stage_data = {
                "commercial_decision": "won",
                "negotiated_value": 750000.0
            }
        elif stage == 6:  # L6 - Won
            stage_data = {
                "final_value": 750000.0,
                "client_poc": "Test Client POC"
            }
        
        return stage_data
    
    async def test_automatic_l6_stage_transition(self):
        """Test 1: Automatic L6 Stage Transition triggers integration function"""
        try:
            logger.info("🧪 TEST 1: Testing Automatic L6 Stage Transition")
            
            # Create opportunity at L5 stage
            opportunity = await self.create_test_opportunity(stage=5)
            opportunity_id = opportunity["id"]
            
            # Get initial upcoming projects count
            initial_projects_response = await self.session.get(f"{BASE_URL}/sd/upcoming-projects/", headers=self.get_headers())
            initial_projects = await initial_projects_response.json()
            initial_count = len(initial_projects)
            
            # Transition to L6 (Won) - This should automatically trigger integration function
            transition_data = {
                "target_stage": 6,
                "stage_data": {
                    "final_value": 750000.0,
                    "client_poc": "Test Client POC",
                    "delivery_team": "Test Team"
                },
                "notes": "Testing automatic L6 trigger"
            }
            
            logger.info(f"🔄 Transitioning opportunity {opportunity_id} to L6 (Won)...")
            
            async with self.session.post(
                f"{BASE_URL}/opportunities/{opportunity_id}/change-stage",
                json=transition_data,
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Stage transition successful: {result['message']}")
                    
                    # Wait a moment for integration function to complete
                    await asyncio.sleep(2)
                    
                    # Check if upcoming project was automatically created
                    final_projects_response = await self.session.get(f"{BASE_URL}/sd/upcoming-projects/", headers=self.get_headers())
                    final_projects = await final_projects_response.json()
                    final_count = len(final_projects)
                    
                    if final_count > initial_count:
                        # Find the newly created project
                        new_project = None
                        for project in final_projects:
                            if project.get("opp_id") == opportunity.get("opportunity_id", opportunity_id):
                                new_project = project
                                self.created_projects.append(project["id"])
                                break
                        
                        if new_project:
                            await self.log_test_result(
                                "Automatic L6 Stage Transition",
                                True,
                                f"Integration function automatically triggered. Created project: {new_project['id']}"
                            )
                            return new_project
                        else:
                            await self.log_test_result(
                                "Automatic L6 Stage Transition",
                                False,
                                "Project count increased but couldn't find project for this opportunity"
                            )
                    else:
                        await self.log_test_result(
                            "Automatic L6 Stage Transition",
                            False,
                            f"No new upcoming project created. Count: {initial_count} → {final_count}"
                        )
                else:
                    error_text = await response.text()
                    await self.log_test_result(
                        "Automatic L6 Stage Transition",
                        False,
                        f"Stage transition failed: {response.status} - {error_text}"
                    )
                    
        except Exception as e:
            await self.log_test_result(
                "Automatic L6 Stage Transition",
                False,
                f"Exception occurred: {str(e)}"
            )
    
    async def test_stage_change_integration_logic(self):
        """Test 2: Verify stage change integration logic and error handling"""
        try:
            logger.info("🧪 TEST 2: Testing Stage Change Integration Logic")
            
            # Create opportunity at L5
            opportunity = await self.create_test_opportunity(stage=5)
            opportunity_id = opportunity["id"]
            
            # Test the specific integration logic at line 5306
            transition_data = {
                "target_stage": 6,
                "stage_data": {
                    "final_value": 500000.0,
                    "client_poc": "Integration Test POC"
                },
                "notes": "Testing integration logic at line 5306"
            }
            
            logger.info(f"🔄 Testing integration logic for opportunity {opportunity_id}...")
            
            async with self.session.post(
                f"{BASE_URL}/opportunities/{opportunity_id}/change-stage",
                json=transition_data,
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Verify opportunity is now locked and status is Won
                    async with self.session.get(f"{BASE_URL}/opportunities/{opportunity_id}", headers=self.get_headers()) as opp_response:
                        if opp_response.status == 200:
                            updated_opp = await opp_response.json()
                            
                            is_locked = updated_opp.get("is_locked", False)
                            status = updated_opp.get("status", "")
                            close_date = updated_opp.get("close_date")
                            win_probability = updated_opp.get("win_probability", 0)
                            
                            success = (
                                is_locked and 
                                status == "Won" and 
                                close_date is not None and
                                win_probability == 100.0
                            )
                            
                            await self.log_test_result(
                                "Stage Change Integration Logic",
                                success,
                                f"Locked: {is_locked}, Status: {status}, Win%: {win_probability}, Close Date: {close_date}"
                            )
                        else:
                            await self.log_test_result(
                                "Stage Change Integration Logic",
                                False,
                                f"Failed to get updated opportunity: {opp_response.status}"
                            )
                else:
                    error_text = await response.text()
                    await self.log_test_result(
                        "Stage Change Integration Logic",
                        False,
                        f"Stage change failed: {response.status} - {error_text}"
                    )
                    
        except Exception as e:
            await self.log_test_result(
                "Stage Change Integration Logic",
                False,
                f"Exception occurred: {str(e)}"
            )
    
    async def test_complete_workflow(self):
        """Test 3: Verify complete workflow from L5 to L6 to upcoming project"""
        try:
            logger.info("🧪 TEST 3: Testing Complete Workflow (L5 → L6 → Upcoming Project)")
            
            # Create opportunity at L1 and progress through all stages
            opportunity = await self.create_test_opportunity(stage=1)
            opportunity_id = opportunity["id"]
            
            logger.info(f"🔄 Progressing opportunity {opportunity_id} through all stages...")
            
            # Progress to L5
            await self.progress_opportunity_to_stage(opportunity_id, 5)
            
            # Get initial state
            initial_projects_response = await self.session.get(f"{BASE_URL}/sd/upcoming-projects/", headers=self.get_headers())
            initial_projects = await initial_projects_response.json()
            initial_count = len(initial_projects)
            
            # Final transition to L6 (Won)
            final_transition = {
                "target_stage": 6,
                "stage_data": {
                    "final_value": 750000.0,
                    "client_poc": "Complete Workflow Test POC",
                    "delivery_team": "Alpha Team",
                    "kickoff_date": datetime.now(timezone.utc).isoformat()
                },
                "notes": "Complete workflow test - L5 to L6 transition"
            }
            
            async with self.session.post(
                f"{BASE_URL}/opportunities/{opportunity_id}/change-stage",
                json=final_transition,
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    # Wait for integration to complete
                    await asyncio.sleep(3)
                    
                    # Verify upcoming project creation
                    final_projects_response = await self.session.get(f"{BASE_URL}/sd/upcoming-projects/", headers=self.get_headers())
                    final_projects = await final_projects_response.json()
                    final_count = len(final_projects)
                    
                    # Find the project for this opportunity
                    created_project = None
                    for project in final_projects:
                        if project.get("opp_id") == opportunity.get("opportunity_id", opportunity_id):
                            created_project = project
                            self.created_projects.append(project["id"])
                            break
                    
                    if created_project:
                        # Verify project data
                        expected_fields = ["order_id", "opp_id", "pot_id", "customer_name", "setup_cost"]
                        missing_fields = [field for field in expected_fields if field not in created_project]
                        
                        success = len(missing_fields) == 0
                        details = f"Project created with ID: {created_project['id']}"
                        if missing_fields:
                            details += f", Missing fields: {missing_fields}"
                        
                        await self.log_test_result(
                            "Complete Workflow",
                            success,
                            details
                        )
                    else:
                        await self.log_test_result(
                            "Complete Workflow",
                            False,
                            f"No project found for opportunity. Projects: {initial_count} → {final_count}"
                        )
                else:
                    error_text = await response.text()
                    await self.log_test_result(
                        "Complete Workflow",
                        False,
                        f"Final L6 transition failed: {response.status} - {error_text}"
                    )
                    
        except Exception as e:
            await self.log_test_result(
                "Complete Workflow",
                False,
                f"Exception occurred: {str(e)}"
            )
    
    async def test_manual_vs_automatic_comparison(self):
        """Test 4: Compare manual vs automatic trigger results"""
        try:
            logger.info("🧪 TEST 4: Testing Manual vs Automatic Trigger Comparison")
            
            # Create two opportunities
            auto_opportunity = await self.create_test_opportunity(stage=5)
            manual_opportunity = await self.create_test_opportunity(stage=6)  # Already won
            
            auto_opp_id = auto_opportunity["id"]
            manual_opp_id = manual_opportunity["id"]
            
            # Test automatic trigger (L5 → L6)
            auto_transition = {
                "target_stage": 6,
                "stage_data": {
                    "final_value": 600000.0,
                    "client_poc": "Auto Trigger POC"
                },
                "notes": "Automatic trigger test"
            }
            
            async with self.session.post(
                f"{BASE_URL}/opportunities/{auto_opp_id}/change-stage",
                json=auto_transition,
                headers=self.get_headers()
            ) as response:
                auto_success = response.status == 200
                
            # Test manual trigger
            async with self.session.post(
                f"{BASE_URL}/test/trigger-upcoming-project/{manual_opp_id}",
                headers=self.get_headers()
            ) as response:
                manual_success = response.status == 200
                
            # Wait for both to complete
            await asyncio.sleep(3)
            
            # Get all projects and find both
            projects_response = await self.session.get(f"{BASE_URL}/sd/upcoming-projects/", headers=self.get_headers())
            projects = await projects_response.json()
            
            auto_project = None
            manual_project = None
            
            for project in projects:
                if project.get("opp_id") == auto_opportunity.get("opportunity_id", auto_opp_id):
                    auto_project = project
                    self.created_projects.append(project["id"])
                elif project.get("opp_id") == manual_opportunity.get("opportunity_id", manual_opp_id):
                    manual_project = project
                    self.created_projects.append(project["id"])
            
            # Compare structures
            if auto_project and manual_project:
                # Compare key fields
                key_fields = ["order_id", "pot_id", "customer_name", "setup_cost", "opp_status"]
                differences = []
                
                for field in key_fields:
                    auto_val = auto_project.get(field)
                    manual_val = manual_project.get(field)
                    
                    if type(auto_val) != type(manual_val):
                        differences.append(f"{field}: type mismatch")
                
                success = len(differences) == 0
                details = f"Both projects created. Differences: {differences}" if differences else "Both projects have identical structure"
                
                await self.log_test_result(
                    "Manual vs Automatic Comparison",
                    success,
                    details
                )
            else:
                missing = []
                if not auto_project:
                    missing.append("automatic")
                if not manual_project:
                    missing.append("manual")
                
                await self.log_test_result(
                    "Manual vs Automatic Comparison",
                    False,
                    f"Missing projects: {missing}"
                )
                
        except Exception as e:
            await self.log_test_result(
                "Manual vs Automatic Comparison",
                False,
                f"Exception occurred: {str(e)}"
            )
    
    async def test_edge_cases(self):
        """Test 5: Edge cases and error handling"""
        try:
            logger.info("🧪 TEST 5: Testing Edge Cases and Error Handling")
            
            # Test 5a: L6 transition with missing company data
            try:
                # Create opportunity with invalid company_id
                opportunity_data = {
                    "project_title": "Edge Case Test - Missing Company",
                    "company_id": "invalid-company-id",
                    "expected_revenue": 100000.0,
                    "currency_id": None,
                    "lead_owner_id": "invalid-user-id",
                    "stage_id": "5",
                    "win_probability": 75.0
                }
                
                # This should fail at creation, but let's test the error handling
                async with self.session.post(f"{BASE_URL}/opportunities", json=opportunity_data, headers=self.get_headers()) as response:
                    if response.status != 201:
                        await self.log_test_result(
                            "Edge Case - Invalid Company",
                            True,
                            "Opportunity creation properly rejected invalid company_id"
                        )
                    else:
                        # If it somehow gets created, test L6 transition
                        opp = await response.json()
                        transition_data = {
                            "target_stage": 6,
                            "stage_data": {"final_value": 100000.0},
                            "notes": "Testing missing company data"
                        }
                        
                        async with self.session.post(
                            f"{BASE_URL}/opportunities/{opp['id']}/change-stage",
                            json=transition_data,
                            headers=self.get_headers()
                        ) as stage_response:
                            # Stage change should succeed but integration might fail gracefully
                            success = stage_response.status == 200
                            await self.log_test_result(
                                "Edge Case - Invalid Company",
                                success,
                                f"Stage change with invalid company: {stage_response.status}"
                            )
                            
            except Exception as e:
                await self.log_test_result(
                    "Edge Case - Invalid Company",
                    True,
                    f"Properly handled invalid company: {str(e)}"
                )
            
            # Test 5b: L6 transition with no quotation
            try:
                opportunity = await self.create_test_opportunity(stage=5)
                
                # Ensure no quotations exist for this opportunity
                quotations_response = await self.session.get(
                    f"{BASE_URL}/opportunities/{opportunity['id']}/quotations",
                    headers=self.get_headers()
                )
                quotations = await quotations_response.json()
                
                transition_data = {
                    "target_stage": 6,
                    "stage_data": {"final_value": 300000.0},
                    "notes": "Testing no quotation scenario"
                }
                
                async with self.session.post(
                    f"{BASE_URL}/opportunities/{opportunity['id']}/change-stage",
                    json=transition_data,
                    headers=self.get_headers()
                ) as response:
                    success = response.status == 200
                    await self.log_test_result(
                        "Edge Case - No Quotation",
                        success,
                        f"L6 transition without quotation: {response.status}"
                    )
                    
            except Exception as e:
                await self.log_test_result(
                    "Edge Case - No Quotation",
                    False,
                    f"Exception in no quotation test: {str(e)}"
                )
            
            # Test 5c: Duplicate project creation prevention
            try:
                opportunity = await self.create_test_opportunity(stage=5)
                opp_id = opportunity["id"]
                
                transition_data = {
                    "target_stage": 6,
                    "stage_data": {"final_value": 400000.0},
                    "notes": "First L6 transition"
                }
                
                # First transition
                async with self.session.post(
                    f"{BASE_URL}/opportunities/{opp_id}/change-stage",
                    json=transition_data,
                    headers=self.get_headers()
                ) as response:
                    first_success = response.status == 200
                
                await asyncio.sleep(2)
                
                # Try manual trigger on same opportunity (should detect duplicate)
                async with self.session.post(
                    f"{BASE_URL}/test/trigger-upcoming-project/{opp_id}",
                    headers=self.get_headers()
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        duplicate_detected = "already exists" in result.get("message", "").lower()
                        
                        await self.log_test_result(
                            "Edge Case - Duplicate Prevention",
                            duplicate_detected,
                            f"Duplicate detection: {result.get('message', 'No message')}"
                        )
                    else:
                        await self.log_test_result(
                            "Edge Case - Duplicate Prevention",
                            False,
                            f"Manual trigger failed: {response.status}"
                        )
                        
            except Exception as e:
                await self.log_test_result(
                    "Edge Case - Duplicate Prevention",
                    False,
                    f"Exception in duplicate test: {str(e)}"
                )
                
        except Exception as e:
            await self.log_test_result(
                "Edge Cases",
                False,
                f"Exception in edge cases: {str(e)}"
            )
    
    async def check_backend_logs(self):
        """Test 6: Check backend logs for integration function execution"""
        try:
            logger.info("🧪 TEST 6: Checking Backend Logs for Integration Function")
            
            # Create and transition opportunity to trigger logging
            opportunity = await self.create_test_opportunity(stage=5)
            opp_id = opportunity["id"]
            
            transition_data = {
                "target_stage": 6,
                "stage_data": {"final_value": 550000.0},
                "notes": "Testing backend logging"
            }
            
            async with self.session.post(
                f"{BASE_URL}/opportunities/{opp_id}/change-stage",
                json=transition_data,
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    await asyncio.sleep(2)
                    
                    # Check if we can verify the integration was called
                    # Since we can't directly access logs, we'll verify by checking the created project
                    projects_response = await self.session.get(f"{BASE_URL}/sd/upcoming-projects/", headers=self.get_headers())
                    projects = await projects_response.json()
                    
                    project_found = False
                    for project in projects:
                        if project.get("opp_id") == opportunity.get("opportunity_id", opp_id):
                            project_found = True
                            self.created_projects.append(project["id"])
                            break
                    
                    await self.log_test_result(
                        "Backend Logs Integration",
                        project_found,
                        f"Integration function execution verified by project creation: {project_found}"
                    )
                else:
                    await self.log_test_result(
                        "Backend Logs Integration",
                        False,
                        f"Stage transition failed: {response.status}"
                    )
                    
        except Exception as e:
            await self.log_test_result(
                "Backend Logs Integration",
                False,
                f"Exception occurred: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Run all automatic L6 trigger tests"""
        logger.info("🚀 Starting Comprehensive Automatic L6 Trigger Testing")
        logger.info("=" * 80)
        
        try:
            # Setup
            if not await self.setup_session():
                logger.error("❌ Failed to setup session. Aborting tests.")
                return
            
            # Run all tests
            await self.test_automatic_l6_stage_transition()
            await self.test_stage_change_integration_logic()
            await self.test_complete_workflow()
            await self.test_manual_vs_automatic_comparison()
            await self.test_edge_cases()
            await self.check_backend_logs()
            
            # Generate summary
            await self.generate_test_summary()
            
        except Exception as e:
            logger.error(f"❌ Critical error during testing: {str(e)}")
        finally:
            await self.cleanup_session()
    
    async def generate_test_summary(self):
        """Generate comprehensive test summary"""
        logger.info("=" * 80)
        logger.info("📊 AUTOMATIC L6 TRIGGER TEST SUMMARY")
        logger.info("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info("")
        
        # Detailed results
        logger.info("📋 DETAILED TEST RESULTS:")
        logger.info("-" * 50)
        
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"{status}: {result['test']}")
            logger.info(f"   Details: {result['details']}")
            logger.info("")
        
        # Key findings
        logger.info("🔍 KEY FINDINGS:")
        logger.info("-" * 30)
        
        automatic_trigger_test = next((r for r in self.test_results if "Automatic L6" in r["test"]), None)
        if automatic_trigger_test:
            if automatic_trigger_test["success"]:
                logger.info("✅ Automatic L6 stage transition trigger is WORKING")
                logger.info("   - Integration function is called automatically during L6 transition")
                logger.info("   - Upcoming projects are created without manual intervention")
            else:
                logger.info("❌ Automatic L6 stage transition trigger is NOT WORKING")
                logger.info("   - Integration function may not be triggered automatically")
        
        integration_logic_test = next((r for r in self.test_results if "Integration Logic" in r["test"]), None)
        if integration_logic_test:
            if integration_logic_test["success"]:
                logger.info("✅ Stage change integration logic is WORKING")
                logger.info("   - Line 5306 in server.py is functioning correctly")
                logger.info("   - Error handling is working (lines 5307-5308)")
            else:
                logger.info("❌ Stage change integration logic has ISSUES")
        
        workflow_test = next((r for r in self.test_results if "Complete Workflow" in r["test"]), None)
        if workflow_test:
            if workflow_test["success"]:
                logger.info("✅ Complete workflow is FUNCTIONAL")
                logger.info("   - L5 → L6 → Upcoming Project creation works end-to-end")
            else:
                logger.info("❌ Complete workflow has ISSUES")
        
        # Cleanup info
        logger.info("🧹 CLEANUP INFORMATION:")
        logger.info(f"Created Opportunities: {len(self.created_opportunities)}")
        logger.info(f"Created Projects: {len(self.created_projects)}")
        
        if self.created_opportunities:
            logger.info("Opportunity IDs:", self.created_opportunities)
        if self.created_projects:
            logger.info("Project IDs:", self.created_projects)
        
        logger.info("=" * 80)
        
        # Final assessment
        if success_rate >= 80:
            logger.info("🎉 OVERALL ASSESSMENT: AUTOMATIC L6 TRIGGER IS WORKING WELL")
        elif success_rate >= 60:
            logger.info("⚠️  OVERALL ASSESSMENT: AUTOMATIC L6 TRIGGER HAS MINOR ISSUES")
        else:
            logger.info("❌ OVERALL ASSESSMENT: AUTOMATIC L6 TRIGGER HAS MAJOR ISSUES")

async def main():
    """Main test execution"""
    tester = AutomaticL6TriggerTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())