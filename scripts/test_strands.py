#!/usr/bin/env python3
"""
Test script for AWS Strands integration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from biomerkin.services.simple_strands_orchestrator import get_simple_strands_orchestrator


async def test_strands_basic():
    """Test basic Strands functionality."""
    print("🧬 Testing AWS Strands Integration")
    print("=" * 50)
    
    orchestrator = get_simple_strands_orchestrator()
    
    # Check status
    status = orchestrator.get_status()
    print(f"📊 Strands Status:")
    print(f"   Available: {status['strands_available']}")
    print(f"   Agents Created: {status['agents_created']}")
    print(f"   Agent Names: {status['agent_names']}")
    print(f"   Model Available: {status['model_available']}")
    
    if not status['strands_available']:
        print("❌ Strands not available - install with: pip install strands")
        return False
    
    if status['agents_created'] == 0:
        print("❌ No agents created - check AWS credentials and region")
        return False
    
    print("\n🚀 Running Simple Analysis...")
    
    # Test simple analysis
    analysis_result = await orchestrator.run_simple_analysis(
        "Analyze BRCA1 gene sequence for cancer susceptibility mutations"
    )
    
    if analysis_result['success']:
        print("✅ Simple analysis completed successfully!")
        print(f"   Agents used: {analysis_result['agents_used']}")
        
        # Print results summary
        results = analysis_result['results']
        for agent_type, result in results.items():
            print(f"   {agent_type}: {str(result)[:100]}...")
    else:
        print(f"❌ Simple analysis failed: {analysis_result.get('error', 'Unknown error')}")
        return False
    
    print("\n🔄 Testing Agent Communication...")
    
    # Test agent communication
    comm_result = await orchestrator.demonstrate_agent_communication()
    
    if comm_result['success']:
        print("✅ Agent communication demo completed!")
        demo = comm_result['communication_demo']
        print(f"   Step 1 (Genomics): {str(demo['step1_genomics'])[:100]}...")
        print(f"   Step 2 (Decision): {str(demo['step2_decision'])[:100]}...")
    else:
        print(f"❌ Agent communication failed: {comm_result.get('error', 'Unknown error')}")
    
    return True


async def test_strands_enhanced():
    """Test enhanced Strands functionality."""
    print("\n🎯 Testing Enhanced Features...")
    
    try:
        from biomerkin.services.enhanced_orchestrator import get_enhanced_orchestrator
        
        enhanced_orchestrator = get_enhanced_orchestrator()
        status = enhanced_orchestrator.get_enhanced_status()
        
        print(f"📈 Enhanced Status:")
        print(f"   Strands Enabled: {status['strands_enabled']}")
        print(f"   Active Agents: {status.get('active_agents', 0)}")
        
        if status['strands_enabled']:
            print("✅ Enhanced orchestrator with Strands is working!")
        else:
            print("⚠️ Enhanced orchestrator running without Strands")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced orchestrator test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🧬 Biomerkin - AWS Strands Integration Test")
    print("=" * 60)
    
    try:
        # Test basic functionality
        basic_success = asyncio.run(test_strands_basic())
        
        # Test enhanced functionality
        enhanced_success = asyncio.run(test_strands_enhanced())
        
        print("\n" + "=" * 60)
        if basic_success and enhanced_success:
            print("🎉 All Strands tests passed!")
            print("💡 You can now use:")
            print("   • biomerkin analyze sequence.fasta --enhanced")
            print("   • biomerkin demo --type comprehensive")
        else:
            print("⚠️ Some tests failed, but basic functionality may still work")
            print("💡 Try running: biomerkin status")
        
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()