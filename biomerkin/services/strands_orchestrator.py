"""
AWS Strands Agents Integration for Biomerkin Multi-Agent System.
Provides advanced agent communication and orchestration using Strands SDK.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import logging

# Strands Agents imports
try:
    from strands import Agent, tool
    from strands.models import BedrockModel
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False
    # Create dummy classes for type hints when Strands is not available
    class Agent:
        pass
    class BedrockModel:
        pass
    def tool(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    logging.warning("Strands Agents SDK not available. Install with: pip install strands-agents")

from ..utils.logging_config import get_logger
from ..utils.config import get_config
from ..models.base import WorkflowState, WorkflowStatus


class StrandsOrchestrator:
    """
    Advanced orchestrator using AWS Strands Agents for multi-agent communication.
    Provides agent-to-agent communication, swarms, and graph-based workflows.
    """
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize Strands orchestrator."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.region = region
        
        if not STRANDS_AVAILABLE:
            raise ImportError("Strands Agents SDK not available. Install with: pip install strands-agents")
        
        # Initialize Strands components
        self._initialize_strands_components()
        self.agents = {}
        self.workflows = {}
        
    def _initialize_strands_components(self):
        """Initialize Strands model providers and base components."""
        try:
            # Initialize Bedrock model provider
            self.bedrock_model = BedrockModel(
                model_id=self.config.aws.bedrock_model_id,
                region_name=self.region
            )
            
            # Initialize other model providers if needed
            self.model_providers = {
                'bedrock': self.bedrock_model
            }
            
            self.logger.info("Strands components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing Strands components: {e}")
            raise
    
    def create_biomerkin_agent(self, agent_name: str, agent_type: str, 
                              tools: List = None, 
                              system_prompt: str = None) -> Agent:
        """
        Create a specialized Biomerkin agent using Strands.
        
        Args:
            agent_name: Name of the agent
            agent_type: Type of agent (genomics, proteomics, literature, drug, decision)
            tools: List of tools available to the agent
            system_prompt: Custom system prompt for the agent
            
        Returns:
            Configured Strands Agent
        """
        if not system_prompt:
            system_prompt = self._get_default_system_prompt(agent_type)
        
        if not tools:
            tools = self._get_default_tools(agent_type)
        
        agent = Agent(
            name=agent_name,
            model=self.bedrock_model,
            system_prompt=system_prompt,
            tools=tools or [],
            max_iterations=10
        )
        
        self.agents[agent_name] = agent
        self.logger.info(f"Created Strands agent: {agent_name}")
        return agent
    
    def _get_default_system_prompt(self, agent_type: str) -> str:
        """Get default system prompt for agent type."""
        prompts = {
            'genomics': """
            You are a specialized genomics analysis agent. Your role is to:
            1. Analyze DNA sequences for genes, mutations, and variants
            2. Translate DNA to protein sequences
            3. Identify potential disease associations
            4. Provide detailed genomic insights
            
            Always provide structured, scientific analysis with confidence levels.
            """,
            
            'proteomics': """
            You are a proteomics analysis agent. Your role is to:
            1. Analyze protein structures and functions
            2. Predict protein-protein interactions
            3. Identify functional domains and motifs
            4. Assess therapeutic potential
            
            Focus on structural biology and functional annotation.
            """,
            
            'literature': """
            You are a scientific literature research agent. Your role is to:
            1. Search and analyze relevant scientific papers
            2. Summarize findings with AI-powered insights
            3. Identify key research trends and gaps
            4. Provide evidence-based recommendations
            
            Always cite sources and provide confidence assessments.
            """,
            
            'drug': """
            You are a drug discovery agent. Your role is to:
            1. Identify potential drug candidates
            2. Analyze clinical trial data
            3. Assess drug interactions and safety
            4. Recommend therapeutic strategies
            
            Focus on evidence-based drug discovery and safety.
            """,
            
            'decision': """
            You are a medical decision support agent. Your role is to:
            1. Synthesize all analysis results
            2. Generate comprehensive medical reports
            3. Provide treatment recommendations
            4. Assess risk factors and prognosis
            
            Always include appropriate medical disclaimers and confidence levels.
            """
        }
        
        return prompts.get(agent_type, "You are a specialized bioinformatics agent.")
    
    def _get_default_tools(self, agent_type: str) -> List:
        """Get default tools for agent type."""
        # This would include actual tool implementations
        # For now, return empty list - tools will be added separately
        return []
    
    def create_agent_swarm(self, agent_names: List[str], 
                          swarm_prompt: str = None):
        """
        Create a swarm of agents for collaborative analysis.
        
        Args:
            agent_names: List of agent names to include in swarm
            swarm_prompt: Custom prompt for swarm coordination
            
        Returns:
            Configured Strands Agent Swarm
        """
        if not swarm_prompt:
            swarm_prompt = """
            You are coordinating a swarm of bioinformatics agents. Your goal is to:
            1. Distribute tasks efficiently among agents
            2. Ensure comprehensive analysis coverage
            3. Synthesize results from multiple agents
            4. Maintain quality and consistency
            
            Coordinate effectively and provide unified results.
            """
        
        agents = [self.agents[name] for name in agent_names if name in self.agents]
        
        if not agents:
            raise ValueError(f"No valid agents found for swarm: {agent_names}")
        
        # Create a simple agent coordination structure
        swarm = {
            'agents': agents,
            'model': self.bedrock_model,
            'system_prompt': swarm_prompt,
            'max_iterations': 15
        }
        
        self.logger.info(f"Created agent swarm with {len(agents)} agents")
        return swarm
    
    def create_workflow_graph(self, workflow_config: Dict[str, Any]) -> Graph:
        """
        Create a graph-based workflow for complex multi-agent processes.
        
        Args:
            workflow_config: Configuration defining agent relationships and flow
            
        Returns:
            Configured Strands Graph workflow
        """
        # Define agent relationships based on workflow config
        nodes = {}
        edges = []
        
        for agent_name, config in workflow_config.get('agents', {}).items():
            if agent_name in self.agents:
                nodes[agent_name] = self.agents[agent_name]
        
        for edge_config in workflow_config.get('edges', []):
            edges.append((
                edge_config['from'],
                edge_config['to'],
                edge_config.get('condition', None)
            ))
        
        graph = Graph(
            nodes=nodes,
            edges=edges,
            model=self.bedrock_model,
            system_prompt=workflow_config.get('system_prompt', 
                "Coordinate multi-agent bioinformatics workflow efficiently.")
        )
        
        self.logger.info(f"Created workflow graph with {len(nodes)} nodes and {len(edges)} edges")
        return graph
    
    async def execute_agent_handoff(self, from_agent: str, to_agent: str, 
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent-to-agent handoff with context transfer.
        
        Args:
            from_agent: Source agent name
            to_agent: Target agent name
            context: Context data to transfer
            
        Returns:
            Handoff result
        """
        if from_agent not in self.agents or to_agent not in self.agents:
            raise ValueError(f"Invalid agent names: {from_agent} -> {to_agent}")
        
        try:
            # Create A2A communication
            a2a = Agent2Agent(
                sender=self.agents[from_agent],
                receiver=self.agents[to_agent],
                model=self.bedrock_model
            )
            
            # Execute handoff
            handoff_message = f"""
            Context from {from_agent}:
            {json.dumps(context, indent=2)}
            
            Please continue the analysis based on this context.
            """
            
            result = await a2a.send_message(handoff_message)
            
            self.logger.info(f"Successful handoff: {from_agent} -> {to_agent}")
            return {
                'success': True,
                'handoff_result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Handoff failed: {from_agent} -> {to_agent}: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def execute_swarm_analysis(self, swarm: Dict[str, Any], 
                                   analysis_request: str) -> Dict[str, Any]:
        """
        Execute collaborative analysis using agent swarm.
        
        Args:
            swarm: Configured agent swarm
            analysis_request: Analysis request description
            
        Returns:
            Agent swarm analysis results
        """
        try:
            self.logger.info("Starting swarm analysis")
            
            result = await swarm.run(analysis_request)
            
            self.logger.info("Agent swarm analysis completed successfully")
            return {
                'success': True,
                'swarm_result': result,
                'participating_agents': [agent.name for agent in swarm.agents],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Swarm analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def execute_graph_workflow(self, graph: Graph, 
                                   initial_input: str) -> Dict[str, Any]:
        """
        Execute graph-based workflow.
        
        Args:
            graph: Configured workflow graph
            initial_input: Initial input for the workflow
            
        Returns:
            Workflow execution results
        """
        try:
            self.logger.info("Starting graph workflow execution")
            
            result = await graph.run(initial_input)
            
            self.logger.info("Graph workflow completed successfully")
            return {
                'success': True,
                'workflow_result': result,
                'execution_path': graph.get_execution_path(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Graph workflow failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def add_custom_tool(self, agent_name: str, tool: Tool):
        """Add a custom tool to an agent."""
        if agent_name in self.agents:
            self.agents[agent_name].add_tool(tool)
            self.logger.info(f"Added custom tool to agent: {agent_name}")
        else:
            raise ValueError(f"Agent not found: {agent_name}")
    
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status information for an agent."""
        if agent_name not in self.agents:
            return {'error': f'Agent not found: {agent_name}'}
        
        agent = self.agents[agent_name]
        return {
            'name': agent.name,
            'status': 'active',
            'tools_count': len(agent.tools),
            'model': str(agent.model),
            'memory_enabled': agent.enable_memory,
            'max_iterations': agent.max_iterations
        }
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get overall orchestrator status."""
        return {
            'strands_available': STRANDS_AVAILABLE,
            'active_agents': len(self.agents),
            'agent_names': list(self.agents.keys()),
            'model_providers': list(self.model_providers.keys()),
            'region': self.region,
            'timestamp': datetime.now().isoformat()
        }


# Global orchestrator instance
strands_orchestrator = None

def get_strands_orchestrator() -> StrandsOrchestrator:
    """Get global Strands orchestrator instance."""
    global strands_orchestrator
    if strands_orchestrator is None:
        strands_orchestrator = StrandsOrchestrator()
    return strands_orchestrator
