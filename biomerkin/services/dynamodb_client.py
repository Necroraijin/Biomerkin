"""
DynamoDB client for workflow state persistence.

This module provides DynamoDB integration for storing and retrieving
workflow states in the Biomerkin multi-agent system.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..models.base import WorkflowState, WorkflowStatus, WorkflowError
from ..utils.config import get_config


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from DynamoDB."""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class DynamoDBClient:
    """
    Client for managing workflow state persistence in DynamoDB.
    
    Handles serialization/deserialization of workflow states and provides
    CRUD operations for workflow management.
    """
    
    def __init__(self, table_name: Optional[str] = None, region_name: Optional[str] = None):
        """
        Initialize the DynamoDB client.
        
        Args:
            table_name: Name of the DynamoDB table (defaults to config value)
            region_name: AWS region name (defaults to config value)
        """
        self.logger = logging.getLogger(__name__)
        self.config = get_config()
        
        self.table_name = table_name or self.config.database.dynamodb_table_name
        self.region_name = region_name or self.config.aws.region
        
        try:
            # Initialize DynamoDB resource
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
            self.table = self.dynamodb.Table(self.table_name)
            
            # Test connection
            self._ensure_table_exists()
            
        except NoCredentialsError:
            self.logger.warning("AWS credentials not found. DynamoDB operations will fail.")
            self.dynamodb = None
            self.table = None
        except Exception as e:
            self.logger.error(f"Failed to initialize DynamoDB client: {str(e)}")
            self.dynamodb = None
            self.table = None
    
    def save_workflow_state(self, workflow_state: WorkflowState) -> None:
        """
        Saves a workflow state to DynamoDB.
        
        Args:
            workflow_state: The workflow state to save
            
        Raises:
            RuntimeError: If DynamoDB is not available or save fails
        """
        if not self.table:
            raise RuntimeError("DynamoDB client not initialized")
        
        try:
            # Convert workflow state to DynamoDB item
            item = self._workflow_state_to_item(workflow_state)
            
            # Save to DynamoDB
            self.table.put_item(Item=item)
            
            self.logger.debug(f"Saved workflow state for {workflow_state.workflow_id}")
            
        except ClientError as e:
            self.logger.error(f"DynamoDB error saving workflow state: {e.response['Error']['Message']}")
            raise RuntimeError(f"Failed to save workflow state: {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"Unexpected error saving workflow state: {str(e)}")
            raise RuntimeError(f"Failed to save workflow state: {str(e)}")
    
    def load_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """
        Loads a workflow state from DynamoDB.
        
        Args:
            workflow_id: Unique identifier for the workflow
            
        Returns:
            WorkflowState if found, None otherwise
            
        Raises:
            RuntimeError: If DynamoDB is not available or load fails
        """
        if not self.table:
            raise RuntimeError("DynamoDB client not initialized")
        
        try:
            # Get item from DynamoDB
            response = self.table.get_item(Key={'workflow_id': workflow_id})
            
            if 'Item' not in response:
                return None
            
            # Convert DynamoDB item to workflow state
            workflow_state = self._item_to_workflow_state(response['Item'])
            
            self.logger.debug(f"Loaded workflow state for {workflow_id}")
            
            return workflow_state
            
        except ClientError as e:
            self.logger.error(f"DynamoDB error loading workflow state: {e.response['Error']['Message']}")
            raise RuntimeError(f"Failed to load workflow state: {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"Unexpected error loading workflow state: {str(e)}")
            raise RuntimeError(f"Failed to load workflow state: {str(e)}")
    
    def list_workflows(self, user_id: Optional[str] = None, 
                      status: Optional[WorkflowStatus] = None) -> List[WorkflowState]:
        """
        Lists workflows, optionally filtered by user ID and/or status.
        
        Args:
            user_id: Optional user ID to filter by
            status: Optional workflow status to filter by
            
        Returns:
            List of workflow states matching the criteria
            
        Raises:
            RuntimeError: If DynamoDB is not available or scan fails
        """
        if not self.table:
            raise RuntimeError("DynamoDB client not initialized")
        
        try:
            # Build scan parameters
            scan_kwargs = {}
            filter_expressions = []
            expression_values = {}
            
            if user_id:
                filter_expressions.append("input_data.user_id = :user_id")
                expression_values[':user_id'] = user_id
            
            if status:
                filter_expressions.append("#status = :status")
                expression_values[':status'] = status.value
                scan_kwargs['ExpressionAttributeNames'] = {'#status': 'status'}
            
            if filter_expressions:
                scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
                scan_kwargs['ExpressionAttributeValues'] = expression_values
            
            # Scan table
            response = self.table.scan(**scan_kwargs)
            
            # Convert items to workflow states
            workflows = []
            for item in response.get('Items', []):
                workflow_state = self._item_to_workflow_state(item)
                workflows.append(workflow_state)
            
            self.logger.debug(f"Listed {len(workflows)} workflows")
            
            return workflows
            
        except ClientError as e:
            self.logger.error(f"DynamoDB error listing workflows: {e.response['Error']['Message']}")
            raise RuntimeError(f"Failed to list workflows: {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"Unexpected error listing workflows: {str(e)}")
            raise RuntimeError(f"Failed to list workflows: {str(e)}")
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Deletes a workflow from DynamoDB.
        
        Args:
            workflow_id: Unique identifier for the workflow
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RuntimeError: If DynamoDB is not available or delete fails
        """
        if not self.table:
            raise RuntimeError("DynamoDB client not initialized")
        
        try:
            # Delete item from DynamoDB
            response = self.table.delete_item(
                Key={'workflow_id': workflow_id},
                ReturnValues='ALL_OLD'
            )
            
            deleted = 'Attributes' in response
            
            if deleted:
                self.logger.debug(f"Deleted workflow {workflow_id}")
            else:
                self.logger.debug(f"Workflow {workflow_id} not found for deletion")
            
            return deleted
            
        except ClientError as e:
            self.logger.error(f"DynamoDB error deleting workflow: {e.response['Error']['Message']}")
            raise RuntimeError(f"Failed to delete workflow: {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"Unexpected error deleting workflow: {str(e)}")
            raise RuntimeError(f"Failed to delete workflow: {str(e)}")
    
    def _workflow_state_to_item(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """
        Converts a WorkflowState object to a DynamoDB item.
        
        Args:
            workflow_state: The workflow state to convert
            
        Returns:
            Dictionary representing the DynamoDB item
        """
        return {
            'workflow_id': workflow_state.workflow_id,
            'status': workflow_state.status.value,
            'current_agent': workflow_state.current_agent,
            'progress_percentage': Decimal(str(workflow_state.progress_percentage)),
            'results': workflow_state.results,
            'errors': [
                {
                    'agent': error.agent,
                    'error_type': error.error_type,
                    'message': error.message,
                    'timestamp': error.timestamp.isoformat()
                }
                for error in workflow_state.errors
            ],
            'input_data': workflow_state.input_data,
            'created_at': workflow_state.created_at.isoformat(),
            'updated_at': workflow_state.updated_at.isoformat()
        }
    
    def _item_to_workflow_state(self, item: Dict[str, Any]) -> WorkflowState:
        """
        Converts a DynamoDB item to a WorkflowState object.
        
        Args:
            item: The DynamoDB item to convert
            
        Returns:
            WorkflowState object
        """
        # Convert errors
        errors = []
        for error_data in item.get('errors', []):
            error = WorkflowError(
                agent=error_data['agent'],
                error_type=error_data['error_type'],
                message=error_data['message'],
                timestamp=datetime.fromisoformat(error_data['timestamp'])
            )
            errors.append(error)
        
        return WorkflowState(
            workflow_id=item['workflow_id'],
            status=WorkflowStatus(item['status']),
            current_agent=item['current_agent'],
            progress_percentage=float(item['progress_percentage']),
            results=item.get('results', {}),
            errors=errors,
            input_data=item.get('input_data', {}),
            created_at=datetime.fromisoformat(item['created_at']),
            updated_at=datetime.fromisoformat(item['updated_at'])
        )
    
    def _ensure_table_exists(self) -> None:
        """
        Ensures the DynamoDB table exists, creates it if it doesn't.
        
        Raises:
            RuntimeError: If table creation fails
        """
        try:
            # Try to describe the table
            self.table.load()
            self.logger.debug(f"DynamoDB table {self.table_name} exists")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, create it
                self.logger.info(f"Creating DynamoDB table {self.table_name}")
                self._create_table()
            else:
                raise RuntimeError(f"Failed to access DynamoDB table: {e.response['Error']['Message']}")
    
    def _create_table(self) -> None:
        """
        Creates the DynamoDB table for workflow states.
        
        Raises:
            RuntimeError: If table creation fails
        """
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'workflow_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'workflow_id',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            
            self.logger.info(f"Created DynamoDB table {self.table_name}")
            
        except ClientError as e:
            raise RuntimeError(f"Failed to create DynamoDB table: {e.response['Error']['Message']}")
        except Exception as e:
            raise RuntimeError(f"Failed to create DynamoDB table: {str(e)}")