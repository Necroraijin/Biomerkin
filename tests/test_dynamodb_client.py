"""
Unit tests for the DynamoDBClient class.

Tests cover DynamoDB operations, serialization/deserialization,
error handling, and table management.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from biomerkin.services.dynamodb_client import DynamoDBClient, DecimalEncoder
from biomerkin.models.base import WorkflowState, WorkflowStatus, WorkflowError


class TestDynamoDBClient:
    """Test suite for DynamoDBClient class."""
    
    @pytest.fixture
    def mock_dynamodb_resource(self):
        """Create a mock DynamoDB resource."""
        mock_resource = Mock()
        mock_table = Mock()
        mock_resource.Table.return_value = mock_table
        mock_resource.create_table.return_value = mock_table
        return mock_resource, mock_table
    
    @pytest.fixture
    def sample_workflow_state(self):
        """Create a sample workflow state for testing."""
        return WorkflowState(
            workflow_id="test-workflow-123",
            status=WorkflowStatus.GENOMICS_PROCESSING,
            current_agent="genomics",
            progress_percentage=25.5,
            results={"genomics": {"genes_found": 3}},
            errors=[
                WorkflowError(
                    agent="genomics",
                    error_type="ValueError",
                    message="Test error",
                    timestamp=datetime(2023, 1, 1, 12, 0, 0)
                )
            ],
            input_data={"dna_sequence_file": "test.fasta", "user_id": "user123"},
            created_at=datetime(2023, 1, 1, 10, 0, 0),
            updated_at=datetime(2023, 1, 1, 12, 0, 0)
        )
    
    @patch('boto3.resource')
    def test_init_success(self, mock_boto3_resource, mock_dynamodb_resource):
        """Test successful DynamoDB client initialization."""
        # Arrange
        mock_resource, mock_table = mock_dynamodb_resource
        mock_boto3_resource.return_value = mock_resource
        
        # Act
        client = DynamoDBClient(table_name="test-table", region_name="us-west-2")
        
        # Assert
        assert client.table_name == "test-table"
        assert client.region_name == "us-west-2"
        assert client.dynamodb == mock_resource
        assert client.table == mock_table
        mock_boto3_resource.assert_called_once_with('dynamodb', region_name='us-west-2')
        mock_table.load.assert_called_once()
    
    @patch('boto3.resource')
    def test_init_no_credentials(self, mock_boto3_resource):
        """Test initialization when AWS credentials are not available."""
        # Arrange
        mock_boto3_resource.side_effect = NoCredentialsError()
        
        # Act
        client = DynamoDBClient()
        
        # Assert
        assert client.dynamodb is None
        assert client.table is None
    
    @patch('boto3.resource')
    def test_init_table_not_exists(self, mock_boto3_resource, mock_dynamodb_resource):
        """Test initialization when table doesn't exist and gets created."""
        # Arrange
        mock_resource, mock_table = mock_dynamodb_resource
        mock_boto3_resource.return_value = mock_resource
        
        # Simulate table not existing initially
        mock_table.load.side_effect = [
            ClientError({'Error': {'Code': 'ResourceNotFoundException'}}, 'DescribeTable'),
            None  # Second call succeeds after table creation
        ]
        mock_table.wait_until_exists.return_value = None
        
        # Act
        client = DynamoDBClient()
        
        # Assert
        mock_resource.create_table.assert_called_once()
        mock_table.wait_until_exists.assert_called_once()
    
    def test_save_workflow_state_success(self, mock_dynamodb_resource, sample_workflow_state):
        """Test successful workflow state saving."""
        # Arrange
        mock_resource, mock_table = mock_dynamodb_resource
        with patch('boto3.resource', return_value=mock_resource):
            client = DynamoDBClient()
        
        # Act
        client.save_workflow_state(sample_workflow_state)
        
        # Assert
        mock_table.put_item.assert_called_once()
        
        # Verify the item structure
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        
        assert item['workflow_id'] == "test-workflow-123"
        assert item['status'] == "genomics_processing"
        assert item['current_agent'] == "genomics"
        assert item['progress_percentage'] == Decimal('25.5')
        assert item['results'] == {"genomics": {"genes_found": 3}}
        assert len(item['errors']) == 1
        assert item['errors'][0]['agent'] == "genomics"
        assert item['input_data'] == {"dna_sequence_file": "test.fasta", "user_id": "user123"}
    
    def test_save_workflow_state_no_client(self):
        """Test saving workflow state when DynamoDB client is not initialized."""
        # Arrange
        client = DynamoDBClient()
        client.table = None
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="DynamoDB client not initialized"):
            client.save_workflow_state(Mock())
    
    def test_save_workflow_state_client_error(self, mock_dynamodb_resource, sample_workflow_state):
        """Test saving workflow state when DynamoDB operation fails."""
        # Arrange
        mock_resource, mock_table = mock_dynamodb_resource
        mock_table.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid item'}},
            'PutItem'
        )
        
        with patch('boto3.resource', return_value=mock_resource):
            client = DynamoDBClient()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to save workflow state"):
            client.save_workflow_state(sample_workflow_state)
    
    def test_load_workflow_state_success(self, mock_dynamodb_resource, sample_workflow_state):
        """Test successful workflow state loading."""
        # Arrange
        mock_resource, mock_table = mock_dynamodb_resource
        
        # Create DynamoDB item representation
        dynamodb_item = {
            'workflow_id': 'test-workflow-123',
            'status': 'genomics_processing',
            'current_agent': 'genomics',
            'progress_percentage': Decimal('25.5'),
            'results': {'genomics': {'genes_found': 3}},
            'errors': [{
                'agent': 'genomics',
                'error_type': 'ValueError',
                'message': 'Test error',
                'timestamp': '2023-01-01T12:00:00'
            }],
            'input_data': {'dna_sequence_file': 'test.fasta', 'user_id': 'user123'},
            'created_at': '2023-01-01T10:00:00',
            'updated_at': '2023-01-01T12:00:00'
        }
        
        mock_table.get_item.return_value = {'Item': dynamodb_item}
        
        with patch('boto3.resource', return_value=mock_resource):
            client = DynamoDBClient()
        
        # Act
        result = client.load_workflow_state("test-workflow-123")
        
        # Assert
        assert result is not None
        assert result.workflow_id == "test-workflow-123"
        assert result.status == WorkflowStatus.GENOMICS_PROCESSING
        assert result.current_agent == "genomics"
        assert result.progress_percentage == 25.5
        assert result.results == {"genomics": {"genes_found": 3}}
        assert len(result.errors) == 1
        assert result.errors[0].agent == "genomics"
        assert result.input_data == {"dna_sequence_file": "test.fasta", "user_id": "user123"}
        
        mock_table.get_item.assert_called_once_with(Key={'workflow_id': 'test-workflow-123'})
    
    def test_load_workflow_state_not_found(self, mock_dynamodb_resource):
        """Test loading workflow state when item doesn't exist."""
        # Arrange
        mock_resource, mock_table = mock_dynamodb_resource
        mock_table.get_item.return_value = {}  # No 'Item' key means not found
        
        with patch('boto3.resource', return_value=mock_resource):
            client = DynamoDBClient()
        
        # Act
        result = client.load_workflow_state("nonexistent-workflow")
        
        # Assert
        assert result is None
    
    def test_load_workflow_state_no_client(self):
        """Test loading workflow state when DynamoDB client is not initialized."""
        # Arrange
        client = DynamoDBClient()
        client.table = None
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="DynamoDB client not initialized"):
            client.load_workflow_state("test-workflow")
    
    def test_list_workflows_success(self, mock_dynamodb_resource):
        """Test successful workflow listing."""
        # Arrange
        mock_resource, mock_table = mock_dynamodb_resource
        
        mock_items = [
            {
                'workflow_id': 'workflow-1',
                'status': 'completed',
                'current_agent': 'decision',
                'progress_percentage': Decimal('100.0'),
                'results': {},
                'errors': [],
                'input_data': {'user_id': 'user123'},
                'created_at': '2023-01-01T10:00:00',
                'updated_at': '2023-01-01T12:00:00'
            },
            {
                'workflow_id': 'workflow-2',
                'status': 'failed',
                'current_agent': 'genomics',
                'progress_percentage': Decimal('10.0'),
                'results': {},
                'errors': [],
                'input_data': {'user_id': 'user123'},
                'created_at': '2023-01-01T11:00:00',
                'updated_at': '2023-01-01T11:30:00'
            }
        ]
        
        mock_table.scan.return_value = {'Items': mock_items}
        
        with patch('boto3.resource', return_value=mock_resource):
            client = DynamoDBClient()
        
        # Act
        workflows = client.list_workflows(user_id="user123", status=WorkflowStatus.COMPLETED)
        
        # Assert
        assert len(workflows) == 2
        assert workflows[0].workflow_id == "workflow-1"
        assert workflows[1].workflow_id == "workflow-2"
        
        # Verify scan was called with correct filter
        mock_table.scan.assert_called_once()
        call_kwargs = mock_table.scan.call_args[1]
        assert 'FilterExpression' in call_kwargs
        assert 'ExpressionAttributeValues' in call_kwargs
    
    def test_delete_workflow_success(self, mock_dynamodb_resource):
        """Test successful workflow deletion."""
        # Arrange
        mock_resource, mock_table = mock_dynamodb_resource
        mock_table.delete_item.return_value = {'Attributes': {'workflow_id': 'test-workflow'}}
        
        with patch('boto3.resource', return_value=mock_resource):
            client = DynamoDBClient()
        
        # Act
        result = client.delete_workflow("test-workflow")
        
        # Assert
        assert result is True
        mock_table.delete_item.assert_called_once_with(
            Key={'workflow_id': 'test-workflow'},
            ReturnValues='ALL_OLD'
        )
    
    def test_delete_workflow_not_found(self, mock_dynamodb_resource):
        """Test workflow deletion when item doesn't exist."""
        # Arrange
        mock_resource, mock_table = mock_dynamodb_resource
        mock_table.delete_item.return_value = {}  # No 'Attributes' means not found
        
        with patch('boto3.resource', return_value=mock_resource):
            client = DynamoDBClient()
        
        # Act
        result = client.delete_workflow("nonexistent-workflow")
        
        # Assert
        assert result is False
    
    def test_workflow_state_serialization_roundtrip(self, sample_workflow_state):
        """Test that workflow state can be serialized and deserialized correctly."""
        # Arrange
        client = DynamoDBClient()
        
        # Act - Convert to item and back
        item = client._workflow_state_to_item(sample_workflow_state)
        restored_state = client._item_to_workflow_state(item)
        
        # Assert
        assert restored_state.workflow_id == sample_workflow_state.workflow_id
        assert restored_state.status == sample_workflow_state.status
        assert restored_state.current_agent == sample_workflow_state.current_agent
        assert restored_state.progress_percentage == sample_workflow_state.progress_percentage
        assert restored_state.results == sample_workflow_state.results
        assert len(restored_state.errors) == len(sample_workflow_state.errors)
        assert restored_state.errors[0].agent == sample_workflow_state.errors[0].agent
        assert restored_state.input_data == sample_workflow_state.input_data
        assert restored_state.created_at == sample_workflow_state.created_at
        assert restored_state.updated_at == sample_workflow_state.updated_at


class TestDecimalEncoder:
    """Test suite for DecimalEncoder class."""
    
    def test_decimal_encoding(self):
        """Test that Decimal objects are properly encoded to float."""
        # Arrange
        encoder = DecimalEncoder()
        test_data = {
            'decimal_value': Decimal('123.45'),
            'regular_float': 67.89,
            'string_value': 'test'
        }
        
        # Act
        result = encoder.encode(test_data)
        
        # Assert
        import json
        parsed = json.loads(result)
        assert parsed['decimal_value'] == 123.45
        assert parsed['regular_float'] == 67.89
        assert parsed['string_value'] == 'test'
    
    def test_non_decimal_objects(self):
        """Test that non-Decimal objects are handled by default encoder."""
        # Arrange
        encoder = DecimalEncoder()
        
        # Act & Assert - Should not raise exception
        result = encoder.encode({'normal_value': 'test'})
        assert '"normal_value": "test"' in result


class TestDynamoDBClientErrorHandling:
    """Test suite for error handling in DynamoDBClient."""
    
    @pytest.fixture
    def mock_dynamodb_resource_error(self):
        """Create a mock DynamoDB resource for error testing."""
        mock_resource = Mock()
        mock_table = Mock()
        mock_resource.Table.return_value = mock_table
        return mock_resource, mock_table
    
    @patch('boto3.resource')
    def test_client_error_handling(self, mock_boto3_resource, mock_dynamodb_resource_error):
        """Test handling of various DynamoDB client errors."""
        # Arrange
        mock_resource, mock_table = mock_dynamodb_resource_error
        mock_boto3_resource.return_value = mock_resource
        
        client = DynamoDBClient()
        
        # Test different error scenarios
        error_scenarios = [
            ('ValidationException', 'Invalid request'),
            ('ResourceNotFoundException', 'Table not found'),
            ('ProvisionedThroughputExceededException', 'Throttled'),
        ]
        
        for error_code, error_message in error_scenarios:
            mock_table.put_item.side_effect = ClientError(
                {'Error': {'Code': error_code, 'Message': error_message}},
                'PutItem'
            )
            
            # Act & Assert
            with pytest.raises(RuntimeError, match="Failed to save workflow state"):
                client.save_workflow_state(Mock())
    
    @patch('boto3.resource')
    def test_unexpected_error_handling(self, mock_boto3_resource, mock_dynamodb_resource_error):
        """Test handling of unexpected errors."""
        # Arrange
        mock_resource, mock_table = mock_dynamodb_resource_error
        mock_boto3_resource.return_value = mock_resource
        
        client = DynamoDBClient()
        mock_table.put_item.side_effect = Exception("Unexpected error")
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to save workflow state"):
            client.save_workflow_state(Mock())