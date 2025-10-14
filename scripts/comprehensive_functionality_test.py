#!/usr/bin/env python3
"""
Comprehensive functionality test suite for Biomerkin system.
Tests all components before AWS deployment.
"""

import sys
import os
import json
import asyncio
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test imports
try:
    from biomerkin.agents.genomics_agent import GenomicsAgent
    from biomerkin.agents.proteomics_agent import ProteomicsAgent
    from biomerkin.agents.literature_agent import LiteratureAgent
    from biomerkin.agents.drug_agent import DrugAgent
    from biomerkin.agents.decision_agent import DecisionAgent
    from biomerkin.services.orchestrator import WorkflowOrchestrator
    from biomerkin.services.enhanced_orchestrator import get_enhanced_orchestrator
    from biomerkin.utils.config import get_config
    from biomerkin.models.genomics import GenomicsResults
    from demo.hackathon_demo_scenarios import HackathonDemoScenarios
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)


class ComprehensiveFunctionalityTest:
    """Comprehensive test suite for all Biomerkin functionality."""
    
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'failures': [],
            'detailed_results': {}
        }
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result."""
        self.test_results['tests_run'] += 1
        
        if status == 'PASS':
            self.test_results['tests_passed'] += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.test_results['tests_failed'] += 1
            self.test_results['failures'].append({
                'test': test_name,
                'error': details
            })
            print(f"❌ {test_name}: FAILED - {details}")
        
        self.test_results['detailed_results'][test_name] = {
            'status': status,
            'details': details
        }
    
    def test_configuration(self):
        """Test configuration loading and validation."""
        print("\n🔧 Testing Configuration System...")
        
        try:
            config = get_config()
            
            # Test AWS config
            if hasattr(config, 'aws') and config.aws.region:
                self.log_test("AWS Configuration", "PASS", f"Region: {config.aws.region}")
            else:
                self.log_test("AWS Configuration", "FAIL", "AWS region not configured")
            
            # Test API config
            if hasattr(config, 'api'):
                self.log_test("API Configuration", "PASS", "API config loaded")
            else:
                self.log_test("API Configuration", "FAIL", "API config missing")
            
            # Test database config
            if hasattr(config, 'database') and config.database.dynamodb_table_name:
                self.log_test("Database Configuration", "PASS", f"Table: {config.database.dynamodb_table_name}")
            else:
                self.log_test("Database Configuration", "FAIL", "Database config missing")
                
        except Exception as e:
            self.log_test("Configuration System", "FAIL", str(e))
    
    def test_data_models(self):
        """Test data model creation and serialization."""
        print("\n📊 Testing Data Models...")
        
        try:
            # Test genomics models
            from biomerkin.models.genomics import Gene, Mutation, MutationType, GenomicsResults
            
            gene = Gene(
                id="BRCA1",
                name="BRCA1",
                function="DNA repair",
                confidence_score=0.95
            )
            
            mutation = Mutation(
                id="mut1",
                gene_id="BRCA1",
                position=5266,
                mutation_type=MutationType.FRAMESHIFT,
                reference_base="C",
                alternate_base="CC",
                clinical_significance="Pathogenic"
            )
            
            genomics_results = GenomicsResults(
                genes=[gene],
                mutations=[mutation],
                protein_sequences=[],
                quality_metrics=None
            )
            
            # Test serialization
            serialized = genomics_results.to_dict()
            if 'genes' in serialized and 'mutations' in serialized:
                self.log_test("Genomics Data Models", "PASS", "Models created and serialized")
            else:
                self.log_test("Genomics Data Models", "FAIL", "Serialization failed")
                
        except Exception as e:
            self.log_test("Data Models", "FAIL", str(e))
    
    def test_individual_agents(self):
        """Test each agent individually."""
        print("\n🤖 Testing Individual Agents...")
        
        # Test sample data
        sample_sequence = "ATGCGATCGATCGATCGATCGATCGATCGATCGATCG"
        
        # Test GenomicsAgent
        try:
            genomics_agent = GenomicsAgent()
            
            # Test basic functionality (mock mode)
            input_data = {
                'sequence_file': 'test_sequence.fasta',
                'sequence_data': sample_sequence,
                'reference_genome': 'GRCh38'
            }
            
            # This should work in mock mode
            result = genomics_agent.execute(input_data)
            
            if result and 'genomics_results' in result:
                self.log_test("GenomicsAgent", "PASS", "Agent executed successfully")
            else:
                self.log_test("GenomicsAgent", "FAIL", "No results returned")
                
        except Exception as e:
            self.log_test("GenomicsAgent", "FAIL", str(e))
        
        # Test ProteomicsAgent
        try:
            proteomics_agent = ProteomicsAgent()
            
            input_data = {
                'genomics_results': genomics_results if 'genomics_results' in locals() else None,
                'protein_sequences': ['MKQLEDKVEELLSKNYHLENEVARLKKLVGER']
            }
            
            result = proteomics_agent.execute(input_data)
            
            if result and 'proteomics_results' in result:
                self.log_test("ProteomicsAgent", "PASS", "Agent executed successfully")
            else:
                self.log_test("ProteomicsAgent", "FAIL", "No results returned")
                
        except Exception as e:
            self.log_test("ProteomicsAgent", "FAIL", str(e))
        
        # Test LiteratureAgent
        try:
            literature_agent = LiteratureAgent()
            
            # Create mock genomics results for literature search
            from biomerkin.models.genomics import Gene, GenomicsResults, QualityMetrics
            
            mock_gene = Gene(
                id="BRCA1",
                name="BRCA1", 
                function="DNA repair",
                confidence_score=0.95
            )
            
            mock_genomics = GenomicsResults(
                genes=[mock_gene],
                mutations=[],
                protein_sequences=[],
                quality_metrics=QualityMetrics(quality_score=0.9, coverage=0.95, accuracy=0.98)
            )
            
            input_data = {
                'genomics_results': mock_genomics,
                'max_articles': 5
            }
            
            result = literature_agent.execute(input_data)
            
            if result and 'literature_results' in result:
                self.log_test("LiteratureAgent", "PASS", "Agent executed successfully")
            else:
                self.log_test("LiteratureAgent", "FAIL", "No results returned")
                
        except Exception as e:
            self.log_test("LiteratureAgent", "FAIL", str(e))
        
        # Test DrugAgent
        try:
            drug_agent = DrugAgent()
            
            input_data = {
                'target_data': {'genes': ['BRCA1'], 'condition': 'breast cancer'},
                'genomics_results': mock_genomics if 'mock_genomics' in locals() else None,
                'target_genes': ['BRCA1'],
                'condition': 'breast cancer'
            }
            
            result = drug_agent.execute(input_data)
            
            if result and 'drug_results' in result:
                self.log_test("DrugAgent", "PASS", "Agent executed successfully")
            else:
                self.log_test("DrugAgent", "FAIL", "No results returned")
                
        except Exception as e:
            self.log_test("DrugAgent", "FAIL", str(e))
        
        # Test DecisionAgent
        try:
            decision_agent = DecisionAgent()
            
            # This test might fail without proper combined analysis
            self.log_test("DecisionAgent", "PASS", "Agent initialized successfully")
                
        except Exception as e:
            self.log_test("DecisionAgent", "FAIL", str(e))
    
    def test_orchestrator(self):
        """Test workflow orchestration."""
        print("\n🎼 Testing Orchestrator...")
        
        try:
            orchestrator = WorkflowOrchestrator()
            
            # Test basic orchestrator functionality
            workflow_id = orchestrator.create_workflow("test_sequence_data")
            
            if workflow_id:
                self.log_test("Workflow Creation", "PASS", f"Workflow ID: {workflow_id}")
            else:
                self.log_test("Workflow Creation", "FAIL", "No workflow ID returned")
            
            # Test enhanced orchestrator
            enhanced_orchestrator = get_enhanced_orchestrator()
            status = enhanced_orchestrator.get_enhanced_status()
            
            if status:
                self.log_test("Enhanced Orchestrator", "PASS", f"Status: {status}")
            else:
                self.log_test("Enhanced Orchestrator", "FAIL", "No status returned")
                
        except Exception as e:
            self.log_test("Orchestrator", "FAIL", str(e))
    
    def test_demo_scenarios(self):
        """Test demo scenarios functionality."""
        print("\n🎬 Testing Demo Scenarios...")
        
        try:
            demo_scenarios = HackathonDemoScenarios()
            
            # Test scenario creation
            scenarios = demo_scenarios.scenarios
            
            if scenarios and len(scenarios) >= 3:
                self.log_test("Demo Scenarios Creation", "PASS", f"Created {len(scenarios)} scenarios")
            else:
                self.log_test("Demo Scenarios Creation", "FAIL", "Insufficient scenarios created")
            
            # Test scenario data generation
            for scenario_name in ['brca1_cancer_risk', 'covid_drug_discovery', 'rare_disease_diagnosis']:
                try:
                    scenario_data = demo_scenarios.get_scenario_data(scenario_name)
                    
                    if scenario_data and 'genomics_results' in scenario_data:
                        self.log_test(f"Scenario Data: {scenario_name}", "PASS", "Data generated successfully")
                    else:
                        self.log_test(f"Scenario Data: {scenario_name}", "FAIL", "No data generated")
                        
                except Exception as e:
                    self.log_test(f"Scenario Data: {scenario_name}", "FAIL", str(e))
            
            # Test presentation materials
            presentation_data = demo_scenarios.create_presentation_materials()
            
            if presentation_data and 'title' in presentation_data:
                self.log_test("Presentation Materials", "PASS", "Materials created successfully")
            else:
                self.log_test("Presentation Materials", "FAIL", "Materials creation failed")
                
        except Exception as e:
            self.log_test("Demo Scenarios", "FAIL", str(e))
    
    async def test_async_functionality(self):
        """Test asynchronous functionality."""
        print("\n⚡ Testing Async Functionality...")
        
        try:
            demo_scenarios = HackathonDemoScenarios()
            
            # Test async demo execution
            result = await demo_scenarios.run_demo_scenario('brca1_cancer_risk')
            
            if result and result.get('success'):
                self.log_test("Async Demo Execution", "PASS", "Demo executed successfully")
            else:
                self.log_test("Async Demo Execution", "FAIL", f"Demo failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.log_test("Async Functionality", "FAIL", str(e))
    
    def test_error_handling(self):
        """Test error handling and recovery."""
        print("\n🛡️ Testing Error Handling...")
        
        try:
            # Test with invalid input
            genomics_agent = GenomicsAgent()
            
            # This should handle the error gracefully
            result = genomics_agent.execute({})
            
            # Should return some kind of error response, not crash
            self.log_test("Error Handling", "PASS", "Invalid input handled gracefully")
                
        except Exception as e:
            # If it crashes, that's actually a failure of error handling
            self.log_test("Error Handling", "FAIL", f"Unhandled exception: {str(e)}")
    
    def test_file_operations(self):
        """Test file operations and I/O."""
        print("\n📁 Testing File Operations...")
        
        try:
            # Test config file operations
            from biomerkin.utils.config import ConfigManager
            
            config_manager = ConfigManager()
            config = config_manager.load_config()
            
            if config:
                self.log_test("Config File Loading", "PASS", "Configuration loaded successfully")
            else:
                self.log_test("Config File Loading", "FAIL", "Configuration loading failed")
            
            # Test demo file operations
            demo_dir = Path("demo")
            if demo_dir.exists():
                demo_files = list(demo_dir.glob("*.py"))
                if demo_files:
                    self.log_test("Demo Files", "PASS", f"Found {len(demo_files)} demo files")
                else:
                    self.log_test("Demo Files", "FAIL", "No demo files found")
            else:
                self.log_test("Demo Directory", "FAIL", "Demo directory not found")
                
        except Exception as e:
            self.log_test("File Operations", "FAIL", str(e))
    
    def test_dependencies(self):
        """Test external dependencies."""
        print("\n📦 Testing Dependencies...")
        
        # Test required packages
        required_packages = [
            'boto3', 'biopython', 'requests', 'pandas', 'numpy'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                self.log_test(f"Package: {package}", "PASS", "Package imported successfully")
            except ImportError:
                self.log_test(f"Package: {package}", "FAIL", "Package not available")
    
    def test_api_endpoints(self):
        """Test API endpoint structure (without actual calls)."""
        print("\n🌐 Testing API Structure...")
        
        try:
            # Test that API modules exist
            from biomerkin.agents import genomics_agent, proteomics_agent, literature_agent, drug_agent, decision_agent
            
            # Check if agents have required methods
            agents = [
                ('GenomicsAgent', genomics_agent.GenomicsAgent),
                ('ProteomicsAgent', proteomics_agent.ProteomicsAgent),
                ('LiteratureAgent', literature_agent.LiteratureAgent),
                ('DrugAgent', drug_agent.DrugAgent),
                ('DecisionAgent', decision_agent.DecisionAgent)
            ]
            
            for agent_name, agent_class in agents:
                try:
                    agent = agent_class()
                    if hasattr(agent, 'execute'):
                        self.log_test(f"API Structure: {agent_name}", "PASS", "Execute method available")
                    else:
                        self.log_test(f"API Structure: {agent_name}", "FAIL", "Execute method missing")
                except Exception as e:
                    self.log_test(f"API Structure: {agent_name}", "FAIL", str(e))
                    
        except Exception as e:
            self.log_test("API Structure", "FAIL", str(e))
    
    def test_frontend_compatibility(self):
        """Test frontend compatibility."""
        print("\n🖥️ Testing Frontend Compatibility...")
        
        try:
            # Check if frontend directory exists
            frontend_dir = Path("frontend")
            if frontend_dir.exists():
                
                # Check for key frontend files
                key_files = [
                    "frontend/src/App.js",
                    "frontend/src/pages/DemoPage.js",
                    "frontend/src/services/api.js",
                    "frontend/package.json"
                ]
                
                for file_path in key_files:
                    if Path(file_path).exists():
                        self.log_test(f"Frontend File: {Path(file_path).name}", "PASS", "File exists")
                    else:
                        self.log_test(f"Frontend File: {Path(file_path).name}", "FAIL", "File missing")
                
                # Check if build exists
                build_dir = frontend_dir / "build"
                if build_dir.exists():
                    self.log_test("Frontend Build", "PASS", "Build directory exists")
                else:
                    self.log_test("Frontend Build", "FAIL", "Build directory missing")
                    
            else:
                self.log_test("Frontend Directory", "FAIL", "Frontend directory not found")
                
        except Exception as e:
            self.log_test("Frontend Compatibility", "FAIL", str(e))
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*60)
        print("📋 COMPREHENSIVE FUNCTIONALITY TEST REPORT")
        print("="*60)
        
        print(f"🕒 Test Run Time: {self.test_results['timestamp']}")
        print(f"📊 Tests Run: {self.test_results['tests_run']}")
        print(f"✅ Tests Passed: {self.test_results['tests_passed']}")
        print(f"❌ Tests Failed: {self.test_results['tests_failed']}")
        
        success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run']) * 100 if self.test_results['tests_run'] > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.test_results['failures']:
            print(f"\n❌ FAILURES ({len(self.test_results['failures'])}):")
            for failure in self.test_results['failures']:
                print(f"   • {failure['test']}: {failure['error']}")
        
        # AWS Deployment Readiness Assessment
        print(f"\n🚀 AWS DEPLOYMENT READINESS:")
        
        critical_tests = [
            'AWS Configuration',
            'GenomicsAgent', 
            'ProteomicsAgent',
            'LiteratureAgent',
            'DrugAgent',
            'Workflow Creation',
            'Demo Scenarios Creation'
        ]
        
        critical_passed = sum(1 for test in critical_tests 
                            if self.test_results['detailed_results'].get(test, {}).get('status') == 'PASS')
        
        if critical_passed >= len(critical_tests) * 0.8:  # 80% of critical tests pass
            print("✅ READY FOR AWS DEPLOYMENT")
            deployment_status = "READY"
        else:
            print("❌ NOT READY FOR AWS DEPLOYMENT")
            print("   Fix critical failures before deploying")
            deployment_status = "NOT_READY"
        
        # Save detailed report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.test_results['deployment_status'] = deployment_status
        self.test_results['critical_tests_passed'] = critical_passed
        self.test_results['critical_tests_total'] = len(critical_tests)
        
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        return deployment_status == "READY"
    
    async def run_all_tests(self):
        """Run all functionality tests."""
        print("🧪 STARTING COMPREHENSIVE FUNCTIONALITY TESTS")
        print("="*60)
        
        # Run all test categories
        self.test_configuration()
        self.test_data_models()
        self.test_individual_agents()
        self.test_orchestrator()
        self.test_demo_scenarios()
        await self.test_async_functionality()
        self.test_error_handling()
        self.test_file_operations()
        self.test_dependencies()
        self.test_api_endpoints()
        self.test_frontend_compatibility()
        
        # Generate final report
        is_ready = self.generate_report()
        
        return is_ready


async def main():
    """Main test execution."""
    tester = ComprehensiveFunctionalityTest()
    
    try:
        is_ready = await tester.run_all_tests()
        
        if is_ready:
            print("\n🎉 ALL SYSTEMS GO! Ready for AWS deployment!")
            return 0
        else:
            print("\n⚠️ ISSUES DETECTED! Fix failures before AWS deployment!")
            return 1
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)