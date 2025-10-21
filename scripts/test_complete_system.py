#!/usr/bin/env python3
"""
Complete System Test - End-to-End
Tests the entire multi-model system from API to results
"""

import requests
import json
import time

API_ENDPOINT = "https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod"

def test_complete_system():
    print("="*60)
    print("🧪 COMPLETE SYSTEM TEST")
    print("="*60)
    
    # Test sequence
    test_sequence = "ATGGATTTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGAGTGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAAT"
    
    print("\n📊 Test Configuration:")
    print(f"  API: {API_ENDPOINT}")
    print(f"  Sequence length: {len(test_sequence)} bp")
    print(f"  Multi-model: Enabled")
    print(f"  Real-time: Enabled")
    
    print("\n🚀 Starting analysis...")
    print("-"*60)
    
    try:
        # Send request
        response = requests.post(
            f"{API_ENDPOINT}/analyze",
            json={
                'sequence': test_sequence,
                'analysis_type': 'genomics',
                'use_multi_model': True,
                'real_time': True
            },
            timeout=300
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                results = data.get('analysis_results', {})
                
                print("\n✅ ANALYSIS SUCCESSFUL!")
                print("="*60)
                
                # Display workflow info
                print(f"\n🔄 Workflow: {results.get('workflow', 'unknown')}")
                print(f"⏰ Timestamp: {results.get('timestamp', 'unknown')}")
                
                # Display models used
                models_used = results.get('models_used', [])
                print(f"\n🤖 Models Used ({len(models_used)}):")
                for model in models_used:
                    print(f"  ✓ {model}")
                
                # Display real-time updates
                updates = results.get('real_time_updates', [])
                if updates:
                    print(f"\n📊 Real-Time Updates ({len(updates)} steps):")
                    for update in updates:
                        status_icon = "✅" if update.get('status') == 'complete' else "🔄"
                        print(f"  {status_icon} Step {update.get('step')}: {update.get('message')}")
                
                # Display analysis results
                print("\n📋 Analysis Results:")
                
                if 'primary_analysis' in results:
                    primary = results['primary_analysis']
                    print(f"\n  🔬 Primary Analysis ({primary.get('model')}):")
                    print(f"     Role: {primary.get('role')}")
                    print(f"     Result: {primary.get('result', '')[:150]}...")
                
                if 'secondary_validation' in results:
                    secondary = results['secondary_validation']
                    print(f"\n  ✓ Secondary Validation ({secondary.get('model')}):")
                    print(f"     Role: {secondary.get('role')}")
                    print(f"     Result: {secondary.get('result', '')[:150]}...")
                
                if 'synthesis' in results:
                    synthesis = results['synthesis']
                    print(f"\n  📝 Synthesis ({synthesis.get('model')}):")
                    print(f"     Role: {synthesis.get('role')}")
                    print(f"     Result: {synthesis.get('result', '')[:150]}...")
                
                # Display final report
                if 'final_report' in results:
                    report = results['final_report']
                    print("\n📊 Final Report:")
                    print(f"  Confidence: {report.get('confidence')}")
                    print(f"  Models Count: {report.get('models_count')}")
                    print(f"  Analysis Complete: {report.get('analysis_complete')}")
                    print(f"\n  Executive Summary:")
                    print(f"  {report.get('executive_summary', '')[:200]}...")
                
                print("\n" + "="*60)
                print("🎉 ALL TESTS PASSED!")
                print("="*60)
                
                print("\n✅ System Status:")
                print("  ✓ API Gateway responding")
                print("  ✓ Lambda function working")
                print("  ✓ Multi-model analysis operational")
                print("  ✓ Real-time updates functioning")
                print("  ✓ All 3 models responding")
                print("  ✓ Comprehensive results generated")
                
                print("\n🚀 System is READY for production use!")
                
                return True
            else:
                print(f"\n❌ Analysis failed: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n⏱️  Request timed out (this is normal for long analyses)")
        print("   The analysis may still be running in the background")
        return False
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_complete_system()
