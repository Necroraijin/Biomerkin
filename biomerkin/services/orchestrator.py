"""
Workflow Orchestrator for Biomerkin multi-agent system.

This module provides the core orchestration logic for managing the sequential
and parallel execution of bioinformatics agents and maintaining workflow state.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.base import WorkflowState, WorkflowStatus, WorkflowError
from ..utils.config import get_config
from .dynamodb_client import DynamoDBClient


@dataclass
class AgentExecutionResult:
    """Result of agent execution with timing and performance metrics."""
    agent_name: str
    success: bool
    results: Optional[Dict[str, Any]]
    error: Optional[Exception]
    execution_time: float
    start_time: datetime
    end_time: datetime
    memory_usage: Optional[float] = None


@dataclass
class ParallelExecutionMetrics:
    """Metrics for parallel agent execution."""
    total_execution_time: float
    sequential_time_estimate: float
    time_saved: float
    parallel_efficiency: float
    agents_executed: List[str]
    execution_results: List[AgentExecutionResult]


class WorkflowOrchestrator:
    """
    Orchestrates the execution of multiple bioinformatics agents in sequence and parallel.
    
    Manages workflow state, progress tracking, error handling, result aggregation,
    and parallel execution optimization across GenomicsAgent, ProteomicsAgent, 
    LiteratureAgent, DrugAgent, and DecisionAgent.
    """
    
    def __init__(self, dynamodb_client: Optional[DynamoDBClient] = None, 
                 enable_parallel_execution: bool = True, max_workers: int = 4):
        """
        Initialize the workflow orchestrator.
        
        Args:
            dynamodb_client: Optional DynamoDB client for state persistence
            enable_parallel_execution: Whether to enable parallel agent execution
            max_workers: Maximum number of worker threads for parallel execution
        """
        self.logger = logging.getLogger(__name__)
        self.config = get_config()
        self.dynamodb_client = dynamodb_client or DynamoDBClient()
        self.enable_parallel_execution = enable_parallel_execution
        self.max_workers = max_workers
        
        # Thread pool executor for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Define the agent execution sequence (for sequential parts)
        self.agent_sequence = [
            'genomics',
            'proteomics', 
            'literature',  # Can run in parallel with drug
            'drug',        # Can run in parallel with literature
            'decision'
        ]
        
        # Define parallel execution groups
        self.parallel_groups = {
            'literature_drug': ['literature', 'drug']  # These can run in parallel
        }
        
        # Map agents to workflow statuses
        self.agent_status_map = {
            'genomics': WorkflowStatus.GENOMICS_PROCESSING,
            'proteomics': WorkflowStatus.PROTEOMICS_PROCESSING,
            'literature': WorkflowStatus.LITERATURE_PROCESSING,
            'drug': WorkflowStatus.DRUG_PROCESSING,
            'decision': WorkflowStatus.REPORT_GENERATION
        }
        
        # Performance metrics storage
        self.execution_metrics: Dict[str, ParallelExecutionMetrics] = {}
    
    def start_analysis(self, dna_sequence_file: str, user_id: Optional[str] = None) -> str:
        """
        Initiates a new multi-agent analysis workflow.
        
        Args:
            dna_sequence_file: Path or identifier for the DNA sequence file
            user_id: Optional user identifier for tracking
            
        Returns:
            str: Unique workflow ID for tracking the analysis
            
        Raises:
            ValueError: If the DNA sequence file is invalid
            RuntimeError: If workflow initialization fails
        """
        try:
            # Generate unique workflow ID
            workflow_id = str(uuid.uuid4())
            
            # Create initial workflow state
            workflow_state = WorkflowState(
                workflow_id=workflow_id,
                status=WorkflowStatus.INITIATED,
                current_agent='genomics',
                progress_percentage=0.0,
                results={},
                errors=[],
                input_data={'dna_sequence_file': dna_sequence_file, 'user_id': user_id},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Persist initial state
            self._save_workflow_state(workflow_state)
            
            self.logger.info(f"Started analysis workflow {workflow_id} for file {dna_sequence_file}")
            
            return workflow_id
            
        except Exception as e:
            self.logger.error(f"Failed to start analysis workflow: {str(e)}")
            raise RuntimeError(f"Workflow initialization failed: {str(e)}")
    
    def get_analysis_status(self, workflow_id: str) -> WorkflowState:
        """
        Retrieves the current status of an analysis workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            
        Returns:
            WorkflowState: Current state of the workflow
            
        Raises:
            ValueError: If workflow ID is not found
        """
        try:
            workflow_state = self._load_workflow_state(workflow_id)
            if not workflow_state:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            return workflow_state
            
        except Exception as e:
            self.logger.error(f"Failed to get status for workflow {workflow_id}: {str(e)}")
            raise
    
    def update_agent_progress(self, workflow_id: str, agent_name: str, 
                            progress: float, results: Optional[Dict[str, Any]] = None,
                            error: Optional[Exception] = None) -> None:
        """
        Updates the progress of a specific agent within a workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            agent_name: Name of the agent reporting progress
            progress: Progress percentage (0.0 to 100.0)
            results: Optional results data from the agent
            error: Optional error that occurred during agent execution
        """
        try:
            workflow_state = self._load_workflow_state(workflow_id)
            if not workflow_state:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Update current agent and status
            workflow_state.current_agent = agent_name
            if agent_name in self.agent_status_map:
                workflow_state.status = self.agent_status_map[agent_name]
            
            # Calculate overall progress based on agent sequence
            agent_index = self.agent_sequence.index(agent_name) if agent_name in self.agent_sequence else 0
            base_progress = (agent_index / len(self.agent_sequence)) * 100
            agent_progress = (progress / 100) * (100 / len(self.agent_sequence))
            workflow_state.progress_percentage = base_progress + agent_progress
            
            # Update results
            if results:
                workflow_state.results[agent_name] = results
            
            # Handle errors
            if error:
                workflow_error = WorkflowError(
                    agent=agent_name,
                    error_type=type(error).__name__,
                    message=str(error),
                    timestamp=datetime.utcnow()
                )
                workflow_state.errors.append(workflow_error)
                self.logger.error(f"Agent {agent_name} error in workflow {workflow_id}: {str(error)}")
            
            workflow_state.updated_at = datetime.utcnow()
            
            # Save updated state
            self._save_workflow_state(workflow_state)
            
            self.logger.info(f"Updated progress for {agent_name} in workflow {workflow_id}: {progress}%")
            
        except Exception as e:
            self.logger.error(f"Failed to update agent progress: {str(e)}")
            raise
    
    def complete_workflow(self, workflow_id: str, final_results: Dict[str, Any]) -> None:
        """
        Marks a workflow as completed with final results.
        
        Args:
            workflow_id: Unique identifier for the workflow
            final_results: Final aggregated results from all agents
        """
        try:
            workflow_state = self._load_workflow_state(workflow_id)
            if not workflow_state:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow_state.status = WorkflowStatus.COMPLETED
            workflow_state.progress_percentage = 100.0
            workflow_state.results['final'] = final_results
            workflow_state.updated_at = datetime.utcnow()
            
            self._save_workflow_state(workflow_state)
            
            self.logger.info(f"Completed workflow {workflow_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to complete workflow {workflow_id}: {str(e)}")
            raise
    
    def fail_workflow(self, workflow_id: str, error: Exception) -> None:
        """
        Marks a workflow as failed due to an unrecoverable error.
        
        Args:
            workflow_id: Unique identifier for the workflow
            error: The error that caused the workflow to fail
        """
        try:
            workflow_state = self._load_workflow_state(workflow_id)
            if not workflow_state:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow_state.status = WorkflowStatus.FAILED
            
            workflow_error = WorkflowError(
                agent='orchestrator',
                error_type=type(error).__name__,
                message=str(error),
                timestamp=datetime.utcnow()
            )
            workflow_state.errors.append(workflow_error)
            workflow_state.updated_at = datetime.utcnow()
            
            self._save_workflow_state(workflow_state)
            
            self.logger.error(f"Failed workflow {workflow_id}: {str(error)}")
            
        except Exception as e:
            self.logger.error(f"Failed to mark workflow as failed: {str(e)}")
            raise
    
    def get_workflow_results(self, workflow_id: str) -> Dict[str, Any]:
        """
        Retrieves the results from a completed workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            
        Returns:
            Dict containing all results from the workflow
            
        Raises:
            ValueError: If workflow is not found or not completed
        """
        try:
            workflow_state = self._load_workflow_state(workflow_id)
            if not workflow_state:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            if workflow_state.status != WorkflowStatus.COMPLETED:
                raise ValueError(f"Workflow {workflow_id} is not completed (status: {workflow_state.status})")
            
            return workflow_state.results
            
        except Exception as e:
            self.logger.error(f"Failed to get results for workflow {workflow_id}: {str(e)}")
            raise
    
    def list_workflows(self, user_id: Optional[str] = None, 
                      status: Optional[WorkflowStatus] = None) -> List[WorkflowState]:
        """
        Lists workflows, optionally filtered by user ID and/or status.
        
        Args:
            user_id: Optional user ID to filter by
            status: Optional workflow status to filter by
            
        Returns:
            List of workflow states matching the criteria
        """
        try:
            return self.dynamodb_client.list_workflows(user_id=user_id, status=status)
        except Exception as e:
            self.logger.error(f"Failed to list workflows: {str(e)}")
            raise
    
    def _save_workflow_state(self, workflow_state: WorkflowState) -> None:
        """
        Persists workflow state to DynamoDB.
        
        Args:
            workflow_state: The workflow state to persist
        """
        try:
            self.dynamodb_client.save_workflow_state(workflow_state)
        except Exception as e:
            self.logger.error(f"Failed to save workflow state: {str(e)}")
            raise
    
    def _load_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """
        Loads workflow state from DynamoDB.
        
        Args:
            workflow_id: Unique identifier for the workflow
            
        Returns:
            WorkflowState if found, None otherwise
        """
        try:
            return self.dynamodb_client.load_workflow_state(workflow_id)
        except Exception as e:
            self.logger.error(f"Failed to load workflow state: {str(e)}")
            raise
    
    async def execute_agents_parallel(self, workflow_id: str, agent_configs: List[Dict[str, Any]]) -> ParallelExecutionMetrics:
        """
        Execute multiple agents in parallel with performance monitoring.
        
        Args:
            workflow_id: Unique identifier for the workflow
            agent_configs: List of agent configurations with agent_name, agent_instance, and input_data
            
        Returns:
            ParallelExecutionMetrics with execution results and performance data
        """
        self.logger.info(f"Starting parallel execution of {len(agent_configs)} agents for workflow {workflow_id}")
        
        start_time = time.time()
        execution_results = []
        
        try:
            # Create tasks for parallel execution
            tasks = []
            for config in agent_configs:
                task = asyncio.create_task(
                    self._execute_agent_async(
                        workflow_id=workflow_id,
                        agent_name=config['agent_name'],
                        agent_instance=config['agent_instance'],
                        input_data=config['input_data']
                    )
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            execution_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            processed_results = []
            for i, result in enumerate(execution_results):
                if isinstance(result, Exception):
                    # Convert exception to failed execution result
                    agent_name = agent_configs[i]['agent_name']
                    failed_result = AgentExecutionResult(
                        agent_name=agent_name,
                        success=False,
                        results=None,
                        error=result,
                        execution_time=0.0,
                        start_time=datetime.now(),
                        end_time=datetime.now()
                    )
                    processed_results.append(failed_result)
                    self.logger.error(f"Agent {agent_name} failed with exception: {str(result)}")
                else:
                    processed_results.append(result)
            
            total_execution_time = time.time() - start_time
            
            # Calculate performance metrics
            metrics = self._calculate_parallel_metrics(processed_results, total_execution_time)
            
            # Store metrics
            self.execution_metrics[workflow_id] = metrics
            
            self.logger.info(f"Parallel execution completed in {total_execution_time:.2f}s. "
                           f"Time saved: {metrics.time_saved:.2f}s, "
                           f"Efficiency: {metrics.parallel_efficiency:.2%}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error in parallel execution: {str(e)}")
            raise
    
    async def _execute_agent_async(self, workflow_id: str, agent_name: str, 
                                 agent_instance: Any, input_data: Dict[str, Any]) -> AgentExecutionResult:
        """
        Execute a single agent asynchronously with performance monitoring.
        
        Args:
            workflow_id: Unique identifier for the workflow
            agent_name: Name of the agent to execute
            agent_instance: Instance of the agent to execute
            input_data: Input data for the agent
            
        Returns:
            AgentExecutionResult with execution details and metrics
        """
        start_time = datetime.now()
        execution_start = time.time()
        
        try:
            self.logger.info(f"Starting async execution of {agent_name} for workflow {workflow_id}")
            
            # Update workflow progress
            self.update_agent_progress(workflow_id, agent_name, 0.0)
            
            # Execute agent in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            if agent_name == 'literature':
                results = await loop.run_in_executor(
                    self.executor,
                    self._execute_literature_agent,
                    agent_instance,
                    input_data
                )
            elif agent_name == 'drug':
                results = await loop.run_in_executor(
                    self.executor,
                    self._execute_drug_agent,
                    agent_instance,
                    input_data
                )
            else:
                # Generic agent execution
                results = await loop.run_in_executor(
                    self.executor,
                    self._execute_generic_agent,
                    agent_instance,
                    input_data
                )
            
            end_time = datetime.now()
            execution_time = time.time() - execution_start
            
            # Update workflow progress
            self.update_agent_progress(workflow_id, agent_name, 100.0, results)
            
            result = AgentExecutionResult(
                agent_name=agent_name,
                success=True,
                results=results,
                error=None,
                execution_time=execution_time,
                start_time=start_time,
                end_time=end_time
            )
            
            self.logger.info(f"Agent {agent_name} completed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = time.time() - execution_start
            
            # Update workflow with error
            self.update_agent_progress(workflow_id, agent_name, 0.0, error=e)
            
            result = AgentExecutionResult(
                agent_name=agent_name,
                success=False,
                results=None,
                error=e,
                execution_time=execution_time,
                start_time=start_time,
                end_time=end_time
            )
            
            self.logger.error(f"Agent {agent_name} failed after {execution_time:.2f}s: {str(e)}")
            return result
    
    def _execute_literature_agent(self, agent_instance, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute literature agent synchronously."""
        genomics_results = input_data.get('genomics_results')
        proteomics_results = input_data.get('proteomics_results')
        
        literature_results = agent_instance.analyze_literature(
            genomics_results=genomics_results,
            proteomics_results=proteomics_results
        )
        
        return {'literature_results': literature_results}
    
    def _execute_drug_agent(self, agent_instance, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute drug agent synchronously."""
        target_data = input_data.get('target_data', {})
        
        drug_results = agent_instance.find_drug_candidates(target_data=target_data)
        
        return {'drug_results': drug_results}
    
    def _execute_generic_agent(self, agent_instance, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic agent synchronously."""
        # This is a placeholder for other agents that might be added to parallel execution
        return {'results': 'completed'}
    
    def _calculate_parallel_metrics(self, execution_results: List[AgentExecutionResult], 
                                  total_execution_time: float) -> ParallelExecutionMetrics:
        """
        Calculate performance metrics for parallel execution.
        
        Args:
            execution_results: List of agent execution results
            total_execution_time: Total time for parallel execution
            
        Returns:
            ParallelExecutionMetrics with performance data
        """
        # Calculate sequential execution time estimate
        sequential_time_estimate = sum(result.execution_time for result in execution_results)
        
        # Calculate time saved
        time_saved = max(0, sequential_time_estimate - total_execution_time)
        
        # Calculate parallel efficiency
        parallel_efficiency = time_saved / sequential_time_estimate if sequential_time_estimate > 0 else 0.0
        
        # Get agent names
        agents_executed = [result.agent_name for result in execution_results]
        
        return ParallelExecutionMetrics(
            total_execution_time=total_execution_time,
            sequential_time_estimate=sequential_time_estimate,
            time_saved=time_saved,
            parallel_efficiency=parallel_efficiency,
            agents_executed=agents_executed,
            execution_results=execution_results
        )
    
    def execute_literature_and_drug_parallel(self, workflow_id: str, genomics_results: Any, 
                                           proteomics_results: Any, literature_agent: Any, 
                                           drug_agent: Any) -> Tuple[Dict[str, Any], Dict[str, Any], ParallelExecutionMetrics]:
        """
        Execute LiteratureAgent and DrugAgent in parallel.
        
        Args:
            workflow_id: Unique identifier for the workflow
            genomics_results: Results from genomics analysis
            proteomics_results: Results from proteomics analysis
            literature_agent: Instance of LiteratureAgent
            drug_agent: Instance of DrugAgent
            
        Returns:
            Tuple of (literature_results, drug_results, execution_metrics)
        """
        if not self.enable_parallel_execution:
            self.logger.info("Parallel execution disabled, running sequentially")
            return self._execute_literature_and_drug_sequential(
                workflow_id, genomics_results, proteomics_results, literature_agent, drug_agent
            )
        
        self.logger.info(f"Executing LiteratureAgent and DrugAgent in parallel for workflow {workflow_id}")
        
        # Prepare target data for drug agent
        target_data = self._prepare_drug_target_data(genomics_results, proteomics_results)
        
        # Prepare agent configurations
        agent_configs = [
            {
                'agent_name': 'literature',
                'agent_instance': literature_agent,
                'input_data': {
                    'genomics_results': genomics_results,
                    'proteomics_results': proteomics_results
                }
            },
            {
                'agent_name': 'drug',
                'agent_instance': drug_agent,
                'input_data': {
                    'target_data': target_data
                }
            }
        ]
        
        # Execute in parallel using asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            metrics = loop.run_until_complete(
                self.execute_agents_parallel(workflow_id, agent_configs)
            )
            
            # Extract results from execution results
            literature_results = None
            drug_results = None
            
            for result in metrics.execution_results:
                if result.agent_name == 'literature' and result.success:
                    literature_results = result.results.get('literature_results')
                elif result.agent_name == 'drug' and result.success:
                    drug_results = result.results.get('drug_results')
            
            return literature_results, drug_results, metrics
            
        finally:
            loop.close()
    
    def _execute_literature_and_drug_sequential(self, workflow_id: str, genomics_results: Any, 
                                              proteomics_results: Any, literature_agent: Any, 
                                              drug_agent: Any) -> Tuple[Dict[str, Any], Dict[str, Any], ParallelExecutionMetrics]:
        """
        Execute LiteratureAgent and DrugAgent sequentially (fallback).
        
        Args:
            workflow_id: Unique identifier for the workflow
            genomics_results: Results from genomics analysis
            proteomics_results: Results from proteomics analysis
            literature_agent: Instance of LiteratureAgent
            drug_agent: Instance of DrugAgent
            
        Returns:
            Tuple of (literature_results, drug_results, execution_metrics)
        """
        start_time = time.time()
        
        # Execute literature agent
        lit_start = time.time()
        literature_results = literature_agent.analyze_literature(
            genomics_results=genomics_results,
            proteomics_results=proteomics_results
        )
        lit_time = time.time() - lit_start
        
        # Execute drug agent
        drug_start = time.time()
        target_data = self._prepare_drug_target_data(genomics_results, proteomics_results)
        drug_results = drug_agent.find_drug_candidates(target_data=target_data)
        drug_time = time.time() - drug_start
        
        total_time = time.time() - start_time
        
        # Create execution results
        execution_results = [
            AgentExecutionResult(
                agent_name='literature',
                success=True,
                results={'literature_results': literature_results},
                error=None,
                execution_time=lit_time,
                start_time=datetime.now(),
                end_time=datetime.now()
            ),
            AgentExecutionResult(
                agent_name='drug',
                success=True,
                results={'drug_results': drug_results},
                error=None,
                execution_time=drug_time,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
        ]
        
        # Create metrics (no time saved in sequential execution)
        metrics = ParallelExecutionMetrics(
            total_execution_time=total_time,
            sequential_time_estimate=total_time,
            time_saved=0.0,
            parallel_efficiency=0.0,
            agents_executed=['literature', 'drug'],
            execution_results=execution_results
        )
        
        return literature_results, drug_results, metrics
    
    def _prepare_drug_target_data(self, genomics_results: Any, proteomics_results: Any) -> Dict[str, Any]:
        """
        Prepare target data for drug agent from genomics and proteomics results.
        
        Args:
            genomics_results: Results from genomics analysis
            proteomics_results: Results from proteomics analysis
            
        Returns:
            Dictionary with target data for drug agent
        """
        target_data = {
            'genes': [],
            'proteins': [],
            'pathways': [],
            'conditions': []
        }
        
        # Extract gene information
        if hasattr(genomics_results, 'genes'):
            target_data['genes'] = [gene.name for gene in genomics_results.genes if gene.name]
        
        # Extract protein information
        if proteomics_results and hasattr(proteomics_results, 'functional_annotations'):
            target_data['proteins'] = [
                annotation.description 
                for annotation in proteomics_results.functional_annotations 
                if annotation.description
            ]
        
        # Extract pathway information
        if proteomics_results and hasattr(proteomics_results, 'pathways'):
            try:
                target_data['pathways'] = [
                    pathway.name 
                    for pathway in proteomics_results.pathways 
                    if hasattr(pathway, 'name') and pathway.name
                ]
            except (TypeError, AttributeError):
                # Handle case where pathways is not iterable (e.g., Mock object)
                target_data['pathways'] = []
        
        # Extract conditions from mutations
        if hasattr(genomics_results, 'mutations'):
            target_data['conditions'] = [
                mutation.clinical_significance 
                for mutation in genomics_results.mutations 
                if mutation.clinical_significance and 'pathogenic' in mutation.clinical_significance.lower()
            ]
        
        return target_data
    
    def get_execution_metrics(self, workflow_id: str) -> Optional[ParallelExecutionMetrics]:
        """
        Get execution metrics for a workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            
        Returns:
            ParallelExecutionMetrics if available, None otherwise
        """
        return self.execution_metrics.get(workflow_id)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of performance metrics across all workflows.
        
        Returns:
            Dictionary with performance summary statistics
        """
        if not self.execution_metrics:
            return {
                'total_workflows': 0,
                'average_time_saved': 0.0,
                'average_efficiency': 0.0,
                'total_time_saved': 0.0,
                'parallel_execution_enabled': self.enable_parallel_execution
            }
        
        metrics_list = list(self.execution_metrics.values())
        
        total_workflows = len(metrics_list)
        total_time_saved = sum(m.time_saved for m in metrics_list)
        average_time_saved = total_time_saved / total_workflows
        average_efficiency = sum(m.parallel_efficiency for m in metrics_list) / total_workflows
        
        return {
            'total_workflows': total_workflows,
            'average_time_saved': average_time_saved,
            'average_efficiency': average_efficiency,
            'total_time_saved': total_time_saved,
            'parallel_execution_enabled': self.enable_parallel_execution
        }