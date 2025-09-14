#!/usr/bin/env python3

import asyncio
import aiohttp
import json
from datetime import datetime, timezone

class FinalOpportunityConversionTest:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.backend_url = "https://service-delivery.preview.emergentagent.com"
        self.api_base = f"{self.backend_url}/api"
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def authenticate(self):
        """Authenticate as admin user"""
        try:
            login_data = {"username": "admin", "password": "admin123"}
            async with self.session.post(f"{self.api_base}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data["access_token"]
                    print("✅ Authentication successful")
                    return True
                else:
                    print(f"❌ Authentication failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
            
    def get_headers(self):
        """Get headers with authentication"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
    async def test_current_integration_status(self):
        """Test 1: Check current integration status"""
        print("\n🔍 TEST 1: Current Integration Status")
        print("=" * 50)
        
        try:
            # Get current upcoming projects
            async with self.session.get(f"{self.api_base}/sd/upcoming-projects/", headers=self.get_headers()) as response:
                if response.status == 200:
                    upcoming_projects = await response.json()
                    print(f"📊 Found {len(upcoming_projects)} upcoming projects")
                    
                    # Analyze schema compliance
                    correct_schema_count = 0
                    old_schema_count = 0
                    incorrect_order_id_count = 0
                    
                    for project in upcoming_projects:
                        # Check for correct SD schema fields
                        required_fields = ['order_id', 'opp_id', 'pot_id', 'customer_name', 'setup_cost']
                        has_correct_schema = all(field in project for field in required_fields)
                        
                        if has_correct_schema:
                            correct_schema_count += 1
                            
                            # Check order_id format
                            order_id = project.get('order_id', '')
                            if order_id.startswith('TEST-ORDER-'):
                                incorrect_order_id_count += 1
                                print(f"⚠️  Project {project.get('id', 'unknown')[:8]}... has TEST-ORDER format: {order_id}")
                            elif not order_id.startswith('OA-'):
                                print(f"⚠️  Project {project.get('id', 'unknown')[:8]}... has unexpected order_id format: {order_id}")
                        else:
                            old_schema_count += 1
                            print(f"⚠️  Project {project.get('id', 'unknown')[:8]}... using old schema")
                    
                    print(f"\n📈 Schema Analysis:")
                    print(f"   - Correct SD schema: {correct_schema_count}/{len(upcoming_projects)} ({correct_schema_count/len(upcoming_projects)*100:.1f}%)")
                    print(f"   - Old schema: {old_schema_count}/{len(upcoming_projects)}")
                    print(f"   - Incorrect order_id format: {incorrect_order_id_count}/{len(upcoming_projects)}")
                    
                else:
                    print(f"❌ Failed to get upcoming projects: {response.status}")
                    
            # Get won opportunities count
            async with self.session.get(f"{self.api_base}/opportunities", headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    opportunities = data.get('opportunities', [])
                    won_opportunities = [opp for opp in opportunities if opp.get('current_stage') == 6]
                    print(f"📊 Found {len(won_opportunities)} won opportunities (L6 stage)")
                    
                    # Check which won opportunities have corresponding projects
                    projects_with_opp_link = 0
                    for project in upcoming_projects:
                        opp_id = project.get('opp_id')
                        if opp_id and opp_id != 'N/A':
                            # Check if this opp_id exists in won opportunities
                            matching_opp = next((opp for opp in won_opportunities if opp.get('id') == opp_id or opp.get('opportunity_id') == opp_id), None)
                            if matching_opp:
                                projects_with_opp_link += 1
                    
                    print(f"📊 Projects linked to won opportunities: {projects_with_opp_link}/{len(won_opportunities)}")
                    
                    if len(won_opportunities) > 0:
                        conversion_rate = projects_with_opp_link / len(won_opportunities) * 100
                        print(f"📊 Conversion rate: {conversion_rate:.1f}%")
                    
                else:
                    print(f"❌ Failed to get opportunities: {response.status}")
                    
        except Exception as e:
            print(f"❌ Test 1 failed: {str(e)}")
            
    async def test_new_opportunity_conversion(self):
        """Test 2: Create new opportunity and test conversion workflow"""
        print("\n🔄 TEST 2: New Opportunity Conversion End-to-End")
        print("=" * 50)
        
        try:
            # Get required master data
            print("📝 Getting master data...")
            
            # Get companies
            async with self.session.get(f"{self.api_base}/companies", headers=self.get_headers()) as response:
                companies = await response.json() if response.status == 200 else []
                if not companies:
                    print("❌ No companies found")
                    return
                test_company_id = companies[0]['id']
                print(f"✅ Using company: {companies[0].get('company_name', 'Unknown')}")
            
            # Get users
            async with self.session.get(f"{self.api_base}/users", headers=self.get_headers()) as response:
                users = await response.json() if response.status == 200 else []
                if not users:
                    print("❌ No users found")
                    return
                test_user_id = users[0]['id']
                print(f"✅ Using user: {users[0].get('username', 'Unknown')}")
            
            # Get currencies
            async with self.session.get(f"{self.api_base}/currencies", headers=self.get_headers()) as response:
                currencies = await response.json() if response.status == 200 else []
                inr_currency = next((c for c in currencies if c.get('code') == 'INR'), currencies[0] if currencies else None)
                if not inr_currency:
                    print("❌ No currencies found")
                    return
                print(f"✅ Using currency: {inr_currency.get('code', 'Unknown')}")
            
            # Create test opportunity
            print("\n📝 Creating test opportunity...")
            opportunity_data = {
                "stage_id": "1",
                "project_title": f"Final Test Conversion {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "company_id": test_company_id,
                "expected_revenue": 1000000.0,
                "currency_id": inr_currency['id'],
                "lead_owner_id": test_user_id,
                "win_probability": 10
            }
            
            async with self.session.post(f"{self.api_base}/opportunities", json=opportunity_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    opportunity = await response.json()
                    opportunity_id = opportunity['id']
                    print(f"✅ Created opportunity: {opportunity_id}")
                else:
                    print(f"❌ Failed to create opportunity: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    return
                    
            # Progress through stages L1 → L6
            print("\n🚀 Progressing through stages...")
            
            # First complete L1 data
            l1_data = {
                "target_stage": 1,
                "region_id": "faacaad8-1143-4e6a-8b1a-868bd0ec9756",
                "product_interest": "Test Product for Final Conversion",
                "assigned_representatives": [test_user_id],
                "lead_owner_id": test_user_id
            }
            
            async with self.session.put(f"{self.api_base}/opportunities/{opportunity_id}/stage", json=l1_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    print("✅ L1 data completed")
                else:
                    print(f"❌ Failed to complete L1: {response.status}")
                    return
            
            # Progress to L2
            l2_data = {
                "target_stage": 2,
                "scorecard": "BANT",
                "budget": "₹1,000,000",
                "authority": "CTO approved",
                "need": "Critical business need",
                "timeline": "Q1 2025",
                "qualification_status": "Qualified"
            }
            
            async with self.session.put(f"{self.api_base}/opportunities/{opportunity_id}/stage", json=l2_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    print("✅ Moved to L2 (Qualification)")
                else:
                    print(f"❌ Failed to move to L2: {response.status}")
                    return
            
            # Progress to L3
            l3_data = {
                "target_stage": 3,
                "proposal_documents": ["test-proposal.pdf"],
                "submission_date": "2025-01-15",
                "internal_stakeholder_id": test_user_id,
                "client_response": "Proposal approved"
            }
            
            async with self.session.put(f"{self.api_base}/opportunities/{opportunity_id}/stage", json=l3_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    print("✅ Moved to L3 (Proposal)")
                else:
                    print(f"❌ Failed to move to L3: {response.status}")
                    return
            
            # Progress to L4
            l4_data = {
                "target_stage": 4,
                "selected_quotation_id": "test-quotation-final"
            }
            
            async with self.session.put(f"{self.api_base}/opportunities/{opportunity_id}/stage", json=l4_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    print("✅ Moved to L4 (Technical)")
                else:
                    print(f"❌ Failed to move to L4: {response.status}")
                    return
            
            # Progress to L5
            l5_data = {
                "target_stage": 5,
                "updated_price": 950000.0,
                "margin": 20.0,
                "po_number": "PO-FINAL-TEST-001",
                "po_date": "2025-01-20"
            }
            
            async with self.session.put(f"{self.api_base}/opportunities/{opportunity_id}/stage", json=l5_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    print("✅ Moved to L5 (Commercial)")
                else:
                    print(f"❌ Failed to move to L5: {response.status}")
                    return
            
            # Finally move to L6 (Won) - this should trigger the integration
            print("\n🎯 Moving to L6 (Won) - Integration should trigger...")
            l6_data = {
                "target_stage": 6,
                "commercial_decision": "won",
                "final_value": 950000.0,
                "client_poc": "John Doe",
                "delivery_team": [test_user_id]
            }
            
            async with self.session.put(f"{self.api_base}/opportunities/{opportunity_id}/stage", json=l6_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    print("✅ Moved to L6 (Won)")
                    
                    # Wait for integration function to run
                    print("⏳ Waiting for integration function...")
                    await asyncio.sleep(3)
                    
                    # Check if upcoming project was created
                    print("🔍 Checking for created upcoming project...")
                    async with self.session.get(f"{self.api_base}/sd/upcoming-projects/", headers=self.get_headers()) as projects_response:
                        if projects_response.status == 200:
                            projects = await projects_response.json()
                            
                            # Look for project with our opportunity ID
                            matching_project = None
                            for project in projects:
                                if project.get('opp_id') == opportunity_id:
                                    matching_project = project
                                    break
                            
                            if matching_project:
                                print(f"✅ SUCCESS: Upcoming project created!")
                                print(f"   - Project ID: {matching_project['id'][:8]}...")
                                print(f"   - Order ID: {matching_project.get('order_id', 'N/A')}")
                                print(f"   - POT ID: {matching_project.get('pot_id', 'N/A')}")
                                print(f"   - Customer: {matching_project.get('customer_name', 'N/A')}")
                                print(f"   - Setup Cost: ₹{matching_project.get('setup_cost', 0):,.2f}")
                                
                                # Validate schema
                                self.validate_project_schema(matching_project)
                                
                                return True
                            else:
                                print(f"❌ FAILURE: No upcoming project found for opportunity {opportunity_id}")
                                return False
                        else:
                            print(f"❌ Failed to check upcoming projects: {projects_response.status}")
                            return False
                else:
                    print(f"❌ Failed to move to L6: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Test 2 failed: {str(e)}")
            return False
            
    def validate_project_schema(self, project):
        """Validate project schema compliance"""
        print("\n🔍 Schema Validation:")
        
        required_fields = ['order_id', 'opp_id', 'pot_id', 'customer_name', 'setup_cost']
        missing_fields = []
        
        for field in required_fields:
            if field not in project or project[field] is None:
                missing_fields.append(field)
                
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
        else:
            print("✅ All required SD fields present")
            
        # Check order_id format
        order_id = project.get('order_id', '')
        if order_id.startswith('OA-') and len(order_id) == 11:
            print(f"✅ Order ID format correct: {order_id}")
        else:
            print(f"❌ Order ID format incorrect: {order_id} (expected OA-XXXXXXXX)")
            
        # Check pot_id format
        pot_id = project.get('pot_id', '')
        if pot_id.startswith('POT-') and len(pot_id) == 12:
            print(f"✅ POT ID format correct: {pot_id}")
        else:
            print(f"❌ POT ID format incorrect: {pot_id} (expected POT-XXXXXXXX)")
            
        # Check setup_cost
        setup_cost = project.get('setup_cost', 0)
        if isinstance(setup_cost, (int, float)) and setup_cost > 0:
            print(f"✅ Setup cost properly calculated: ₹{setup_cost:,.2f}")
        else:
            print(f"⚠️  Setup cost may be incorrect: {setup_cost}")
            
    async def test_integration_function_edge_cases(self):
        """Test 3: Integration function edge cases"""
        print("\n🧪 TEST 3: Integration Function Edge Cases")
        print("=" * 50)
        
        try:
            # Check existing won opportunities without projects
            async with self.session.get(f"{self.api_base}/opportunities", headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    opportunities = data.get('opportunities', [])
                    won_opportunities = [opp for opp in opportunities if opp.get('current_stage') == 6]
                    
                    async with self.session.get(f"{self.api_base}/sd/upcoming-projects/", headers=self.get_headers()) as projects_response:
                        if projects_response.status == 200:
                            projects = await projects_response.json()
                            
                            orphaned_opportunities = []
                            for opp in won_opportunities:
                                opp_id = opp.get('id') or opp.get('opportunity_id')
                                matching_project = next((p for p in projects if p.get('opp_id') == opp_id), None)
                                if not matching_project:
                                    orphaned_opportunities.append(opp)
                            
                            print(f"📊 Found {len(orphaned_opportunities)} won opportunities without projects:")
                            for opp in orphaned_opportunities:
                                opp_id = opp.get('id') or opp.get('opportunity_id')
                                title = opp.get('project_title', 'Unknown')
                                print(f"   - {opp_id}: {title}")
                            
                            if orphaned_opportunities:
                                print("⚠️  These opportunities should have triggered project creation")
                            else:
                                print("✅ All won opportunities have corresponding projects")
                                
        except Exception as e:
            print(f"❌ Test 3 failed: {str(e)}")
            
    async def generate_final_report(self):
        """Generate final status report"""
        print("\n📊 FINAL STATUS REPORT")
        print("=" * 60)
        
        try:
            # Get current counts
            async with self.session.get(f"{self.api_base}/opportunities", headers=self.get_headers()) as response:
                data = await response.json() if response.status == 200 else {'opportunities': []}
                opportunities = data.get('opportunities', [])
                won_opportunities = [opp for opp in opportunities if opp.get('current_stage') == 6]
                
            async with self.session.get(f"{self.api_base}/sd/upcoming-projects/", headers=self.get_headers()) as response:
                upcoming_projects = await response.json() if response.status == 200 else []
                
            print(f"📈 Current Status:")
            print(f"   - Total Opportunities: {len(opportunities)}")
            print(f"   - Won Opportunities (L6): {len(won_opportunities)}")
            print(f"   - Upcoming Projects: {len(upcoming_projects)}")
            
            if won_opportunities:
                # Check conversion rate
                projects_with_opp_link = 0
                for project in upcoming_projects:
                    opp_id = project.get('opp_id')
                    if opp_id and opp_id != 'N/A':
                        matching_opp = next((opp for opp in won_opportunities if opp.get('id') == opp_id or opp.get('opportunity_id') == opp_id), None)
                        if matching_opp:
                            projects_with_opp_link += 1
                
                conversion_rate = projects_with_opp_link / len(won_opportunities) * 100
                print(f"   - Conversion Rate: {conversion_rate:.1f}% ({projects_with_opp_link}/{len(won_opportunities)})")
            else:
                print(f"   - Conversion Rate: N/A (no won opportunities)")
            
            # Schema analysis
            correct_schema_projects = 0
            for project in upcoming_projects:
                required_fields = ['order_id', 'opp_id', 'pot_id', 'customer_name', 'setup_cost']
                has_all_fields = all(field in project and project[field] is not None for field in required_fields)
                order_id_valid = project.get('order_id', '').startswith('OA-') and len(project.get('order_id', '')) == 11
                pot_id_valid = project.get('pot_id', '').startswith('POT-') and len(project.get('pot_id', '')) == 12
                
                if has_all_fields and order_id_valid and pot_id_valid:
                    correct_schema_projects += 1
                    
            if upcoming_projects:
                schema_compliance = correct_schema_projects / len(upcoming_projects) * 100
                print(f"   - Schema Compliance: {schema_compliance:.1f}% ({correct_schema_projects}/{len(upcoming_projects)})")
            else:
                print(f"   - Schema Compliance: N/A (no projects)")
            
            # Final assessment
            print(f"\n🎯 User Issue Resolution Assessment:")
            
            if won_opportunities and upcoming_projects:
                conversion_rate = projects_with_opp_link / len(won_opportunities)
                schema_compliance_rate = correct_schema_projects / len(upcoming_projects) if upcoming_projects else 0
                
                if conversion_rate >= 0.8 and schema_compliance_rate >= 0.8:
                    print("✅ ISSUE RESOLVED: Opportunity to upcoming project conversion is working correctly")
                    print("   - High conversion rate (≥80%)")
                    print("   - High schema compliance (≥80%)")
                elif conversion_rate < 0.8:
                    print("❌ ISSUE PARTIALLY RESOLVED: Conversion rate is low")
                    print(f"   - Only {conversion_rate*100:.1f}% of won opportunities create projects")
                    print("   - Integration function may not be triggering consistently")
                elif schema_compliance_rate < 0.8:
                    print("❌ ISSUE PARTIALLY RESOLVED: Schema compliance is low")
                    print(f"   - Only {schema_compliance_rate*100:.1f}% of projects have correct schema")
                    print("   - Data structure migration incomplete")
                else:
                    print("⚠️  ISSUE STATUS UNCLEAR: Mixed results")
            elif not won_opportunities:
                print("⚠️  CANNOT ASSESS: No won opportunities to test conversion")
            elif not upcoming_projects:
                print("❌ ISSUE NOT RESOLVED: No upcoming projects found despite won opportunities")
            else:
                print("❌ ISSUE NOT RESOLVED: Conversion workflow not functioning")
                
        except Exception as e:
            print(f"❌ Failed to generate final report: {str(e)}")
            
    async def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("🚀 FINAL COMPREHENSIVE OPPORTUNITY TO UPCOMING PROJECT CONVERSION TEST")
        print("=" * 80)
        
        await self.setup_session()
        
        try:
            # Authenticate
            if not await self.authenticate():
                return
                
            # Run all tests
            await self.test_current_integration_status()
            conversion_success = await self.test_new_opportunity_conversion()
            await self.test_integration_function_edge_cases()
            
            # Generate final report
            await self.generate_final_report()
            
            # Summary
            print(f"\n🏁 TEST COMPLETION SUMMARY")
            print("=" * 40)
            if conversion_success:
                print("✅ NEW CONVERSION TEST: PASSED")
                print("   - Successfully created opportunity and progressed to Won")
                print("   - Integration function triggered and created upcoming project")
                print("   - Schema validation passed")
            else:
                print("❌ NEW CONVERSION TEST: FAILED")
                print("   - Integration function did not work as expected")
            
        finally:
            await self.cleanup_session()

async def main():
    """Main test function"""
    tester = FinalOpportunityConversionTest()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())