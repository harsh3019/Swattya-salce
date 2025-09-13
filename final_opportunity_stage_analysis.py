#!/usr/bin/env python3
"""
Final Comprehensive Analysis of Opportunity Stage Management Issues
"""

import requests
import json

# Configuration
BASE_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def comprehensive_analysis():
    print("🔍 COMPREHENSIVE OPPORTUNITY STAGE MANAGEMENT ANALYSIS")
    print("=" * 65)
    
    # Step 1: Authenticate
    print("\n1. Authentication Test...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=ADMIN_CREDENTIALS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Admin authentication successful")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 2: Analyze Opportunities List API
    print("\n2. Opportunities List API Analysis...")
    try:
        response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
        
        if response.status_code == 200:
            opportunities_data = response.json()
            opportunities = opportunities_data.get('opportunities', [])
            total_count = opportunities_data.get('total', 0)
            
            print(f"✅ GET /api/opportunities successful")
            print(f"   Response format: {type(opportunities_data)}")
            print(f"   Total opportunities: {total_count}")
            print(f"   Opportunities array length: {len(opportunities)}")
            
            # Analyze current_stage values
            print(f"\n   📊 CURRENT STAGE ANALYSIS:")
            stage_counts = {}
            
            for i, opp in enumerate(opportunities):
                current_stage = opp.get('current_stage')
                opp_id = opp.get('opportunity_id') or opp.get('id')
                project_title = opp.get('project_title', 'N/A')
                
                if current_stage not in stage_counts:
                    stage_counts[current_stage] = 0
                stage_counts[current_stage] += 1
                
                print(f"   Opp {i+1}: ID={opp_id}, current_stage={current_stage}, title={project_title}")
            
            print(f"\n   📈 STAGE DISTRIBUTION:")
            for stage, count in sorted(stage_counts.items()):
                print(f"   Stage {stage}: {count} opportunities")
            
            # Issue 1: Check if opportunities show current stage correctly
            beyond_l1_count = sum(count for stage, count in stage_counts.items() if stage and stage > 1)
            
            if beyond_l1_count == 0:
                print(f"\n   ❌ ISSUE 1 IDENTIFIED: All opportunities stuck at L1 stage")
                print(f"   ❌ This explains why 'Manage Stages' always opens at L1")
            else:
                print(f"\n   ✅ ISSUE 1 RESOLVED: {beyond_l1_count} opportunities beyond L1")
                
        else:
            print(f"❌ GET /api/opportunities failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error analyzing opportunities: {e}")
        return
    
    # Step 3: Test Individual Opportunity API
    print("\n3. Individual Opportunity API Analysis...")
    
    if opportunities:
        test_opp = opportunities[0]
        test_opp_id = test_opp.get('opportunity_id') or test_opp.get('id')
        
        try:
            response = requests.get(f"{BASE_URL}/opportunities/{test_opp_id}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                opp_detail = response.json()
                detail_stage = opp_detail.get('current_stage')
                list_stage = test_opp.get('current_stage')
                
                print(f"✅ GET /api/opportunities/{test_opp_id} successful")
                print(f"   List API current_stage: {list_stage}")
                print(f"   Detail API current_stage: {detail_stage}")
                
                if detail_stage == list_stage:
                    print(f"   ✅ Stage consistency: Both APIs return same stage")
                else:
                    print(f"   ❌ ISSUE 2 IDENTIFIED: Stage inconsistency between list and detail APIs")
                    
            else:
                print(f"❌ GET /api/opportunities/{test_opp_id} failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing individual opportunity: {e}")
    
    # Step 4: Test Stage Master Data
    print("\n4. Stage Master Data Analysis...")
    try:
        response = requests.get(f"{BASE_URL}/mst/stages", headers=headers, timeout=10)
        
        if response.status_code == 200:
            stages = response.json()
            print(f"✅ GET /api/mst/stages successful")
            print(f"   Total stages: {len(stages)}")
            
            print(f"\n   📋 STAGE DEFINITIONS:")
            expected_stages = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8']
            found_stages = []
            
            for stage in stages:
                stage_code = stage.get('code', 'N/A')
                stage_name = stage.get('name', 'N/A')
                stage_order = stage.get('stage_order', 'N/A')
                print(f"   Order {stage_order}: {stage_code} - {stage_name}")
                
                if stage_code in expected_stages:
                    found_stages.append(stage_code)
            
            missing_stages = [stage for stage in expected_stages if stage not in found_stages]
            
            if missing_stages:
                print(f"\n   ❌ ISSUE 3 IDENTIFIED: Missing stage codes: {missing_stages}")
                print(f"   ❌ Stage display format may not show 'L1 - Qualification' format")
            else:
                print(f"\n   ✅ All expected L1-L8 stage codes found")
                
        else:
            print(f"❌ GET /api/mst/stages failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error analyzing stage master data: {e}")
    
    # Step 5: Test Stage Progression
    print("\n5. Stage Progression Testing...")
    
    if opportunities:
        test_opp = opportunities[0]
        test_opp_id = test_opp.get('opportunity_id') or test_opp.get('id')
        
        print(f"   Testing stage progression for opportunity: {test_opp_id}")
        
        # Try to progress from L1 to L2
        stage_data = {
            "target_stage": 2,
            "stage_data": {
                "region_id": "test-region",
                "product_interest": "CRM Software",
                "assigned_representatives": ["Test Rep"],
                "lead_owner_id": "test-user"
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/opportunities/{test_opp_id}/change-stage",
                headers=headers,
                json=stage_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Stage progression successful: {result.get('message', 'Success')}")
                
                # Verify stage change
                verify_response = requests.get(f"{BASE_URL}/opportunities/{test_opp_id}", headers=headers, timeout=10)
                if verify_response.status_code == 200:
                    updated_opp = verify_response.json()
                    new_stage = updated_opp.get('current_stage')
                    print(f"   ✅ Stage verified: Now at L{new_stage}")
                    
                    if new_stage > 1:
                        print(f"   ✅ ISSUE 1 PARTIALLY RESOLVED: Opportunity can progress beyond L1")
                    
            else:
                print(f"   ❌ ISSUE 4 IDENTIFIED: Stage progression failed: {response.status_code}")
                print(f"   ❌ Error details: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error testing stage progression: {e}")
    
    # Step 6: Summary of Issues Found
    print("\n" + "=" * 65)
    print("🎯 SUMMARY OF ISSUES IDENTIFIED")
    print("=" * 65)
    
    issues_found = []
    
    # Check if all opportunities are at L1
    if opportunities:
        all_at_l1 = all(opp.get('current_stage', 1) == 1 for opp in opportunities)
        if all_at_l1:
            issues_found.append({
                'issue': 'All opportunities stuck at L1 stage',
                'impact': 'Manage Stages always opens at L1, stage display shows L1 for all',
                'root_cause': 'Opportunities are not progressing beyond L1 after conversion from leads'
            })
    
    # Check stage master data format
    try:
        response = requests.get(f"{BASE_URL}/mst/stages", headers=headers, timeout=10)
        if response.status_code == 200:
            stages = response.json()
            stage_codes = [stage.get('code', '') for stage in stages]
            if not any(code.startswith('L') for code in stage_codes):
                issues_found.append({
                    'issue': 'Stage codes not in L1-L8 format',
                    'impact': 'Stage display may not show "L2 - Qualification" format',
                    'root_cause': 'Master data stage codes are not properly formatted'
                })
    except:
        pass
    
    if issues_found:
        for i, issue in enumerate(issues_found, 1):
            print(f"\n{i}. ISSUE: {issue['issue']}")
            print(f"   IMPACT: {issue['impact']}")
            print(f"   ROOT CAUSE: {issue['root_cause']}")
    else:
        print(f"\n✅ No critical issues found - system appears to be working correctly")
    
    print(f"\n🔧 RECOMMENDED ACTIONS:")
    if issues_found:
        print(f"1. Fix stage progression logic to allow opportunities to move beyond L1")
        print(f"2. Update stage master data to use L1-L8 format with proper names")
        print(f"3. Test 'Manage Stages' form to ensure it opens at current stage, not L1")
        print(f"4. Verify stage display in opportunities list shows correct format")
    else:
        print(f"1. System appears to be working correctly")
        print(f"2. Test frontend 'Manage Stages' functionality")
    
    print(f"\n🎉 ANALYSIS COMPLETED!")

if __name__ == "__main__":
    comprehensive_analysis()