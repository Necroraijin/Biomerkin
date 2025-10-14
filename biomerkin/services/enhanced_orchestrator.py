"""
Enhanced Workflow Orchestrator with AWS Strands Agents Integration.
Provides advanced multi-agent coordination and communication.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from ..utils.logging_config import get_logger
from ..utils.config import get_config
from ..models.base import WorkflowState, WorkflowStatus
from ..models.analysis import AnalysisResults

# Import Strands orchestrator
try:
    from .simple_strands_orchestrator import get_simple_strands_orchestrator
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False

from .orchestrator import WorkflowOrchestrator


class EnhancedWorkflowOrchestrator(WorkflowOrchestrator):
    """
    Enhanced orchestrator with AWS Strands Agents integration.
    Provides advanced agent communication, swarms, and graph workflows.
    """
    
    def __init__(self, dynamodb_client=None, enable_parallel_execution=True, 
                 max_workers=4, enable_strands=True):
        """Initialize enhanced orchestrator."""
        super().__init__(dynamodb_client, enable_parallel_execution, max_workers)
        
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.enable_strands = enable_strands and STRANDS_AVAILABLE
        
        if self.enable_strands:
            try:
                self.strands_orchestrator = get_simple_strands_orchestrator()
                self.logger.info("Enhanced orchestrator initialized with Simple Strands Agents")
            except Exception as e:
                self.logger.error(f"Failed to initialize Strands: {e}")
                self.enable_strands = False
        else:
            self.logger.info("Enhanced orchestrator initialized without Strands Agents")
    
    # Removed _initialize_strands_agents - using simple orchestrator instead
    
    async def execute_enhanced_workflow(self, workflow_state: WorkflowState) -> AnalysisResults:
        """
        Execute enhanced workflow with Strands Agents integration.
        
        Args:
            workflow_state: Initial workflow state
            
        Returns:
            Enhanced analysis results
        """
        self.logger.info(f"Starting enhanced workflow: {workflow_state.workflow_id}")
        
        if self.enable_strands:
            return await self._execute_strands_workflow(workflow_state)
        else:
            # Fallback to standard orchestrator
            return await self.execute_workflow(workflow_state)
    
    async def _execute_strands_workflow(self, workflow_state: WorkflowState) -> AnalysisResults:
        """Execute workflow using Simple Strands Agents."""
        try:
            # Prepare analysis request
            analysis_request = f"""
            Please perform comprehensive bioinformatics analysis on the following data:
            
            Workflow ID: {workflow_state.workflow_id}
            Input Data: {json.dumps(workflow_state.input_data, indent=2)}
            
            Analysis Requirements:
            1. Genomics: Analyze DNA sequence for genes, mutations, and protein translation
            2. Literature: Research relevant scientific literature
            3. Medical Report: Generate comprehensive medical report with recommendations
            
            Provide detailed, scientific analysis with confidence levels and recommendations.
            """
            
            # Execute simple analysis
            strands_result = await self.strands_orchestrator.run_simple_analysis(analysis_request)
            
            if strands_result['success']:
                # Create enhanced results
                enhanced_results = AnalysisResults(
                    workflow_id=workflow_state.workflow_id,
                    success=True,
                    results={
                        'strands_analysis': strands_result['results'],
                        'agents_used': strands_result['agents_used'],
                        'strands_enhanced': True
                    },
                    execution_time=datetime.now() - workflow_state.created_at,
                    warnings=[],
                    error_message=None
                )
                
                self.logger.info(f"Enhanced workflow completed successfully: {workflow_state.workflow_id}")
                return enhanced_results
            
            else:
                # Fallback to standard workflow on Strands failure
                self.logger.warning("Strands workflow failed, falling back to standard orchestrator")
                return await self.execute_workflow(workflow_state)
                
        except Exception as e:
            self.logger.error(f"Enhanced workflow failed: {e}")
            # Fallback to standard workflow
            return await self.execute_workflow(workflow_state)
    
    async def execute_agent_handoff_workflow(self, workflow_id: str, 
                                           handoff_sequence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute workflow with explicit agent handoffs.
        
        Args:
            workflow_id: Workflow identifier
            handoff_sequence: Sequence of agent handoffs with context
            
        Returns:
            Handoff workflow results
        """
        if not self.enable_strands:
            return {'error': 'Strands Agents not available'}
        
        self.logger.info(f"Starting agent handoff workflow: {workflow_id}")
        
        try:
            results = []
            current_context = {}
            
            for i, handoff in enumerate(handoff_sequence):
                from_agent = handoff['from_agent']
                to_agent = handoff['to_agent']
                context = handoff.get('context', {})
                
                # Merge context
                current_context.update(context)
                
                # Execute handoff
                handoff_result = await self.strands_orchestrator.execute_agent_handoff(
                    from_agent, to_agent, current_context
                )
                
                results.append(handoff_result)
                
                if not handoff_result['success']:
                    self.logger.error(f"Handoff failed at step {i}: {from_agent} -> {to_agent}")
                    break
                
                # Update context with handoff result
                current_context['handoff_result'] = handoff_result['handoff_result']
            
            return {
                'workflow_id': workflow_id,
                'success': all(r['success'] for r in results),
                'handoff_results': results,
                'final_context': current_context,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Agent handoff workflow failed: {e}")
            return {
                'workflow_id': workflow_id,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def execute_graph_workflow(self, workflow_id: str, 
                                   graph_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute graph-based workflow.
        
        Args:
            workflow_id: Workflow identifier
            graph_config: Graph workflow configuration
            
        Returns:
            Graph workflow results
        """
        if not self.enable_strands:
            return {'error': 'Strands Agents not available'}
        
        self.logger.info(f"Starting graph workflow: {workflow_id}")
        
        try:
            # Create graph workflow
            graph = self.strands_orchestrator.create_workflow_graph(graph_config)
            
            # Execute graph workflow
            initial_input = graph_config.get('initial_input', 
                f"Execute bioinformatics analysis workflow: {workflow_id}")
            
            result = await self.strands_orchestrator.execute_graph_workflow(
                graph, initial_input
            )
            
            return {
                'workflow_id': workflow_id,
                'graph_result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Graph workflow failed: {e}")
            return {
                'workflow_id': workflow_id,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get enhanced orchestrator status."""
        base_status = {
            'orchestrator_type': 'enhanced',
            'strands_available': STRANDS_AVAILABLE,
            'strands_enabled': self.enable_strands,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.enable_strands:
            base_status.update(self.strands_orchestrator.get_status())
        
        return base_status
    
    async def create_demo_workflow(self, demo_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Create a demo workflow for hackathon presentation.
        
        Args:
            demo_type: Type of demo workflow
            
        Returns:
            Demo workflow configuration
        """
        demo_configs = {
            'comprehensive': {
                'name': 'Comprehensive Bioinformatics Analysis',
                'description': 'Full analysis pipeline with all agents',
                'handoff_sequence': [
                    {
                        'from_agent': 'GenomicsAgent',
                        'to_agent': 'ProteomicsAgent',
                        'context': {'analysis_type': 'genomics_complete'}
                    },
                    {
                        'from_agent': 'ProteomicsAgent', 
                        'to_agent': 'LiteratureAgent',
                        'context': {'analysis_type': 'proteomics_complete'}
                    },
                    {
                        'from_agent': 'LiteratureAgent',
                        'to_agent': 'DrugAgent',
                        'context': {'analysis_type': 'literature_complete'}
                    },
                    {
                        'from_agent': 'DrugAgent',
                        'to_agent': 'DecisionAgent',
                        'context': {'analysis_type': 'drug_discovery_complete'}
                    }
                ]
            },
            'swarm': {
                'name': 'Collaborative Swarm Analysis',
                'description': 'All agents working together in swarm mode',
                'swarm_agents': ['GenomicsAgent', 'ProteomicsAgent', 'LiteratureAgent', 'DrugAgent']
            },
            'graph': {
                'name': 'Graph-Based Workflow',
                'description': 'Complex graph workflow with conditional branching',
                'graph_config': {
                    'agents': {
                        'GenomicsAgent': {'type': 'genomics'},
                        'ProteomicsAgent': {'type': 'proteomics'},
                        'LiteratureAgent': {'type': 'literature'},
                        'DrugAgent': {'type': 'drug'},
                        'DecisionAgent': {'type': 'decision'}
                    },
                    'edges': [
                        {'from': 'GenomicsAgent', 'to': 'ProteomicsAgent'},
                        {'from': 'GenomicsAgent', 'to': 'LiteratureAgent'},
                        {'from': 'ProteomicsAgent', 'to': 'DrugAgent'},
                        {'from': 'LiteratureAgent', 'to': 'DrugAgent'},
                        {'from': 'DrugAgent', 'to': 'DecisionAgent'}
                    ],
                    'system_prompt': 'Execute bioinformatics analysis with parallel processing where possible'
                }
            }
        }
        
        return demo_configs.get(demo_type, demo_configs['comprehensive'])


# Global enhanced orchestrator instance
enhanced_orchestrator = None

def get_enhanced_orchestrator() -> EnhancedWorkflowOrchestrator:
    """Get global enhanced orchestrator instance."""
    global enhanced_orchestrator
    if enhanced_orchestrator is None:
        enhanced_orchestrator = EnhancedWorkflowOrchestrator()
    return enhanced_orchestrator

