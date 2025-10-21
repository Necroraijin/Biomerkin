#!/usr/bin/env python3
"""
Cleanup unnecessary documentation files
Keep only essential files and one comprehensive README.md
"""

import os
import glob

# Files to DELETE (temporary fix/status documents)
files_to_delete = [
    # Status/Fix documents
    "PERFECT_INTEGRATION_CONFIRMED.md",
    "ALL_ISSUES_FIXED_SUMMARY.md",
    "DEPLOYMENT_SUCCESS_FINAL.md",
    "AUDIT_COMPLETE.md",
    "DEPLOY_NOW.md",
    "AI_ML_DEVELOPER_AUDIT_SUMMARY.md",
    "PRODUCTION_READINESS_PLAN.md",
    "COMPREHENSIVE_AUDIT_FINDINGS.md",
    "FINAL_DEPLOYMENT_STATUS.md",
    "DEPLOYMENT_CHECKLIST.md",
    "QUICK_START_AFTER_FIX.md",
    "BUGS_FIXED_SUMMARY.md",
    "COMPLETE_FIX_GUIDE.md",
    "FRONTEND_FIX_SUMMARY.md",
    "FINAL_CORS_FIX_COMPLETE.md",
    "REACT_APP_FIXED.md",
    "US_EAST_1_DEPLOYMENT_COMPLETE.md",
    "FRONTEND_FIX_GUIDE.md",
    "CORS_COMPLETE_FIX.md",
    "CORS_ISSUE_FIXED.md",
    "EVERYTHING_WORKING_NOW.md",
    "SIMPLE_WORKING_FRONTEND_READY.md",
    "FRONTEND_FIXED_FINAL.md",
    "API_GATEWAY_FIXED_AND_WORKING.md",
    "SYSTEM_FULLY_INTEGRATED_AND_WORKING.md",
    "REAL_TIME_MULTI_MODEL_SYSTEM_LIVE.md",
    "MULTI_MODEL_SYSTEM_READY.md",
    "BEDROCK_CONFIRMED_WORKING.md",
    "BEDROCK_AI_DEPLOYED.md",
    "EVERYTHING_WORKING_FINAL.md",
    "COMPLETE_SOLUTION_READY.md",
    "FINAL_WORKING_SOLUTION.md",
    "SYSTEM_NOW_WORKING.md",
    "FINAL_FIX_COMPLETE.md",
    "CLEAR_CACHE_AND_TEST.md",
    "FRONTEND_FIXED_NEW_ENDPOINT.md",
    "SYSTEM_FULLY_CONNECTED_FINAL.md",
    "FINAL_SOLUTION_CONNECT_FRONTEND_BACKEND.md",
    "YOUR_LIVE_PROJECT_URLS.md",
    "FRONTEND_ACCESS_SOLUTION.md",
    "PROJECT_LINKS_FOR_JUDGES.md",
    "AWS_DEPLOYMENT_READINESS_REPORT.md",
    
    # Task summaries (keep in .kiro/specs instead)
    "TASK_28_ADVANCED_BEDROCK_FEATURES_SUMMARY.md",
    "TASK_27_ENHANCED_ORCHESTRATION_SUMMARY.md",
    "TASK_26_DECISION_BEDROCK_AGENT_SUMMARY.md",
    "TASK_25_DRUG_BEDROCK_AGENT_SUMMARY.md",
    "TASK_24_LITERATURE_BEDROCK_AGENT_SUMMARY.md",
    "TASK_23_PROTEOMICS_BEDROCK_AGENT_SUMMARY.md",
    "TASK_22_IMPLEMENTATION_SUMMARY.md",
    
    # Test/completion summaries
    "TEST_COMPLETION_SUMMARY.md",
    "CHIMPANZEE_TEST_SUMMARY.md",
    "FINAL_SYSTEM_STATUS.md",
    
    # Duplicate/old integration docs
    "BEDROCK_INTEGRATION_COMPLETE.md",
    "QUICK_START_BEDROCK_INTEGRATION.md",
    "AWS_BEDROCK_FULL_INTEGRATION_GUIDE.md",
    "QUICK_TEST_GUIDE.md",
    "JOHN_SNOW_LABS_SETUP_GUIDE.md",
    
    # Deployment info JSON
    "deployment_info_20251014-224917.json",
    
    # Other files
    "chimpanzee.txt",
    "test.html",  # Keep on S3, delete from root
]

def cleanup_files():
    """Delete unnecessary documentation files"""
    print("=" * 60)
    print("🧹 Cleaning Up Unnecessary Documentation Files")
    print("=" * 60)
    
    deleted_count = 0
    not_found_count = 0
    
    for filename in files_to_delete:
        filepath = filename
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"✅ Deleted: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error deleting {filename}: {str(e)}")
        else:
            not_found_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Cleanup Summary")
    print("=" * 60)
    print(f"✅ Deleted: {deleted_count} files")
    print(f"ℹ️  Not found: {not_found_count} files")
    print(f"📝 Total processed: {len(files_to_delete)} files")
    print("\n✨ Cleanup complete!")
    print("\n📋 Remaining documentation:")
    print("   - README.md (comprehensive)")
    print("   - TECHNICAL_DOCUMENTATION.md")
    print("   - HACKATHON_PRESENTATION.md")
    print("   - BEDROCK_AGENTS_EXPLANATION.md")
    print("   - BEDROCK_AGENTS_QUICK_REFERENCE.md")
    print("   - AWS_SETUP_GUIDE_FOR_BEGINNERS.md")
    print("   - demo/DEMO_VIDEO_SCRIPT.md")

if __name__ == "__main__":
    cleanup_files()
