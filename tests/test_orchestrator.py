"""
Unit tests for the WorkflowOrchestrator class.

Tests cover workflow creation, state management, progress tracking,
error handling, and DynamoDB integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

from biomerkin.services.orchestrator import WorkflowOrchestrator
from biomerkin.services.dynamodb_client import DynamoDBClient
from biomerkin.models.base import WorkflowState, WorkflowStatus, WorkflowError


class TestWorkflowOrchestrator:
    """Test suite for WorkflowOrchestrator class."""
    
    @pytest.fixture
    def mock_dynamodb_client(self):
        """Create a mock DynamoDB client."""
        return Mock(spec=DynamoDBClient)
    
    @pytest.fixture
    def orchestrator(self, mock_dynamodb_client):
        """Create a WorkflowOrchestrator instance with mocked dependencies."""
        return WorkflowOrchestrator(dynamodb_client=mock_dynamodb_client)
    
    @pytest.fixture
    def sample_workflow_state(self):
        """Create a sample workflow state for testing."""
        return WorkflowState(
            workflow_id="test-workflow-123",
            status=WorkflowStatus.INITIATED,
            current_agent="genomics",
            progress_percentage=0.0,
            results={},
            errors=[],
            input_data={"dna_sequence_file": "test.fasta", "user_id": "user123"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    def test_start_analysis_success(self, orchestrator, mock_dynamodb_client):
        """Test successful workflow initiation."""
        # Arrange
        dna_file = "sample.fasta"
        user_id = "user123"
        
        # Act
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9012-123456789012')
            workflow_id = orchestrator.start_analysis(dna_file, user_id)
        
        # Assert
        assert workflow_id == "12345678-1234-5678-9012-123456789012"
        mock_dynamodb_client.save_workflow_state.assert_called_once()
        
        # Verify the saved workflow state
        saved_state = mock_dynamodb_client.save_workflow_state.call_args[0][0]
        assert saved_state.workflow_id == workflow_id
        assert saved_state.status == WorkflowStatus.INITIATED
        assert saved_state.current_agent == "genomics"
        assert saved_state.progress_percentage == 0.0
        assert saved_state.input_data["dna_sequence_file"] == dna_file
        assert saved_state.input_data["user_id"] == user_id
    
    def test_start_analysis_dynamodb_failure(self, orchestrator, mock_dynamodb_client):
        """Test workflow initiation when DynamoDB save fails."""
        # Arrange
        mock_dynamodb_client.save_workflow_state.side_effect = RuntimeError("DynamoDB error")
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Workflow initialization failed"):
            orchestrator.start_analysis("test.fasta")
    
    def test_get_analysis_status_success(self, orchestrator, mock_dynamodb_client, sample_workflow_state):
        """Test successful workflow status retrieval."""
        # Arrange
        workflow_id = "test-workflow-123"
        mock_dynamodb_client.load_workflow_state.return_value = sample_workflow_state
        
        # Act
        status = orchestrator.get_analysis_status(workflow_id)
        
        # Assert
        assert status == sample_workflow_state
        mock_dynamodb_client.load_workflow_state.assert_called_once_with(workflow_id)
    
    def test_get_analysis_status_not_found(self, orchestrator, mock_dynamodb_client):
        """Test workflow status retrieval when workflow not found."""
        # Arrange
        workflow_id = "nonexistent-workflow"
        mock_dynamodb_client.load_workflow_state.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Workflow .* not found"):
            orchestrator.get_analysis_status(workflow_id)
    
    def test_update_agent_progress_success(self, orchestrator, mock_dynamodb_client, sample_workflow_state):
        """Test successful agent progress update."""
        # Arrange
        workflow_id = "test-workflow-123"
        agent_name = "genomics"
        progress = 50.0
        results = {"genes_found": 5}
        
        mock_dynamodb_client.load_workflow_state.return_value = sample_workflow_state
        
        # Act
        orchestrator.update_agent_progress(workflow_id, agent_name, progress, results)
        
        # Assert
        mock_dynamodb_client.save_workflow_state.assert_called_once()
        
        # Verify the updated state
        saved_state = mock_dynamodb_client.save_workflow_state.call_args[0][0]
        assert saved_state.current_agent == agent_name
        assert saved_state.status == WorkflowStatus.GENOMICS_PROCESSING
        assert saved_state.results[agent_name] == results
        # Progress should be calculated based on agent sequence
        expected_progress = (0 / 5) * 100 + (50 / 100) * (100 / 5)  # 10%
        assert saved_state.progress_percentage == expected_progress
    
    def test_update_agent_progress_with_error(self, orchestrator, mock_dynamodb_client, sample_workflow_state):
        """Test agent progress update with error."""
        # Arrange
        workflow_id = "test-workflow-123"
        agent_name = "genomics"
        progress = 25.0
        error = ValueError("Test error")
        
        mock_dynamodb_client.load_workflow_state.return_value = sample_workflow_state
        
        # Act
        orchestrator.update_agent_progress(workflow_id, agent_name, progress, error=error)
        
        # Assert
        saved_state = mock_dynamodb_client.save_workflow_state.call_args[0][0]
        assert len(saved_state.errors) == 1
        assert saved_state.errors[0].agent == agent_name
        assert saved_state.errors[0].error_type == "ValueError"
        assert saved_state.errors[0].message == "Test error"
    
    def test_update_agent_progress_workflow_not_found(self, orchestrator, mock_dynamodb_client):
        """Test agent progress update when workflow not found."""
        # Arrange
        workflow_id = "nonexistent-workflow"
        mock_dynamodb_client.load_workflow_state.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Workflow .* not found"):
            orchestrator.update_agent_progress(workflow_id, "genomics", 50.0)
    
    def test_complete_workflow_success(self, orchestrator, mock_dynamodb_client, sample_workflow_state):
        """Test successful workflow completion."""
        # Arrange
        workflow_id = "test-workflow-123"
        final_results = {"report": "Generated medical report"}
        
        mock_dynamodb_client.load_workflow_state.return_value = sample_workflow_state
        
        # Act
        orchestrator.complete_workflow(workflow_id, final_results)
        
        # Assert
        saved_state = mock_dynamodb_client.save_workflow_state.call_args[0][0]
        assert saved_state.status == WorkflowStatus.COMPLETED
        assert saved_state.progress_percentage == 100.0
        assert saved_state.results["final"] == final_results
    
    def test_fail_workflow_success(self, orchestrator, mock_dynamodb_client, sample_workflow_state):
        """Test successful workflow failure marking."""
        # Arrange
        workflow_id = "test-workflow-123"
        error = RuntimeError("Critical system error")
        
        mock_dynamodb_client.load_workflow_state.return_value = sample_workflow_state
        
        # Act
        orchestrator.fail_workflow(workflow_id, error)
        
        # Assert
        saved_state = mock_dynamodb_client.save_workflow_state.call_args[0][0]
        assert saved_state.status == WorkflowStatus.FAILED
        assert len(saved_state.errors) == 1
        assert saved_state.errors[0].agent == "orchestrator"
        assert saved_state.errors[0].error_type == "RuntimeError"
        assert saved_state.errors[0].message == "Critical system error"
    
    def test_get_workflow_results_success(self, orchestrator, mock_dynamodb_client):
        """Test successful workflow results retrieval."""
        # Arrange
        workflow_id = "test-workflow-123"
        completed_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.COMPLETED,
            current_agent="decision",
            progress_percentage=100.0,
            results={"final": {"report": "Medical report"}},
            errors=[],
            input_data={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_dynamodb_client.load_workflow_state.return_value = completed_state
        
        # Act
        results = orchestrator.get_workflow_results(workflow_id)
        
        # Assert
        assert results == completed_state.results
    
    def test_get_workflow_results_not_completed(self, orchestrator, mock_dynamodb_client, sample_workflow_state):
        """Test workflow results retrieval when workflow not completed."""
        # Arrange
        workflow_id = "test-workflow-123"
        mock_dynamodb_client.load_workflow_state.return_value = sample_workflow_state
        
        # Act & Assert
        with pytest.raises(ValueError, match="Workflow .* is not completed"):
            orchestrator.get_workflow_results(workflow_id)
    
    def test_list_workflows_success(self, orchestrator, mock_dynamodb_client):
        """Test successful workflow listing."""
        # Arrange
        user_id = "user123"
        status = WorkflowStatus.COMPLETED
        expected_workflows = [Mock(), Mock()]
        
        mock_dynamodb_client.list_workflows.return_value = expected_workflows
        
        # Act
        workflows = orchestrator.list_workflows(user_id=user_id, status=status)
        
        # Assert
        assert workflows == expected_workflows
        mock_dynamodb_client.list_workflows.assert_called_once_with(user_id=user_id, status=status)
    
    def test_agent_sequence_and_status_mapping(self, orchestrator):
        """Test that agent sequence and status mapping are correctly defined."""
        # Assert
        expected_sequence = ['genomics', 'proteomics', 'literature', 'drug', 'decision']
        assert orchestrator.agent_sequence == expected_sequence
        
        expected_status_map = {
            'genomics': WorkflowStatus.GENOMICS_PROCESSING,
            'proteomics': WorkflowStatus.PROTEOMICS_PROCESSING,
            'literature': WorkflowStatus.LITERATURE_PROCESSING,
            'drug': WorkflowStatus.DRUG_PROCESSING,
            'decision': WorkflowStatus.REPORT_GENERATION
        }
        assert orchestrator.agent_status_map == expected_status_map
    
    def test_progress_calculation(self, orchestrator, mock_dynamodb_client, sample_workflow_state):
        """Test progress percentage calculation for different agents."""
        # Arrange
        workflow_id = "test-workflow-123"
        mock_dynamodb_client.load_workflow_state.return_value = sample_workflow_state
        
        # Test cases: (agent_name, agent_progress, expected_total_progress)
        test_cases = [
            ("genomics", 50.0, 10.0),    # (0/5)*100 + (50/100)*(100/5) = 0 + 10 = 10%
            ("proteomics", 75.0, 35.0),  # (1/5)*100 + (75/100)*(100/5) = 20 + 15 = 35%
            ("literature", 25.0, 45.0),  # (2/5)*100 + (25/100)*(100/5) = 40 + 5 = 45%
            ("drug", 100.0, 80.0),       # (3/5)*100 + (100/100)*(100/5) = 60 + 20 = 80%
            ("decision", 50.0, 90.0),    # (4/5)*100 + (50/100)*(100/5) = 80 + 10 = 90%
        ]
        
        for agent_name, agent_progress, expected_total in test_cases:
            # Act
            orchestrator.update_agent_progress(workflow_id, agent_name, agent_progress)
            
            # Assert
            saved_state = mock_dynamodb_client.save_workflow_state.call_args[0][0]
            assert saved_state.progress_percentage == expected_total, \
                f"Agent {agent_name} with {agent_progress}% should result in {expected_total}% total progress"
    
    @patch('biomerkin.services.orchestrator.logging')
    def test_logging_integration(self, mock_logging, orchestrator, mock_dynamodb_client):
        """Test that appropriate logging occurs during operations."""
        # Arrange
        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger
        
        # Create new orchestrator to trigger logger initialization
        orchestrator = WorkflowOrchestrator(dynamodb_client=mock_dynamodb_client)
        
        # Act
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9012-123456789012')
            workflow_id = orchestrator.start_analysis("test.fasta")
        
        # Assert
        mock_logger.info.assert_called_with(
            f"Started analysis workflow {workflow_id} for file test.fasta"
        )


class TestWorkflowOrchestratorErrorHandling:
    """Test suite for error handling in WorkflowOrchestrator."""
    
    @pytest.fixture
    def orchestrator_with_failing_db(self):
        """Create orchestrator with a DynamoDB client that always fails."""
        mock_client = Mock(spec=DynamoDBClient)
        mock_client.save_workflow_state.side_effect = RuntimeError("DB connection failed")
        mock_client.load_workflow_state.side_effect = RuntimeError("DB connection failed")
        return WorkflowOrchestrator(dynamodb_client=mock_client)
    
    def test_start_analysis_db_error_handling(self, orchestrator_with_failing_db):
        """Test error handling when database operations fail during workflow start."""
        with pytest.raises(RuntimeError, match="Workflow initialization failed"):
            orchestrator_with_failing_db.start_analysis("test.fasta")
    
    def test_get_status_db_error_handling(self, orchestrator_with_failing_db):
        """Test error handling when database operations fail during status retrieval."""
        with pytest.raises(RuntimeError, match="DB connection failed"):
            orchestrator_with_failing_db.get_analysis_status("test-workflow")
    
    def test_update_progress_db_error_handling(self, orchestrator_with_failing_db):
        """Test error handling when database operations fail during progress update."""
        with pytest.raises(RuntimeError, match="DB connection failed"):
            orchestrator_with_failing_db.update_agent_progress("test-workflow", "genomics", 50.0)