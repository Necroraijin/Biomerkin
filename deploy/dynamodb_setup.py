"""
DynamoDB setup for Biomerkin workflow state management
"""
import boto3
from typing import Dict, Any

class DynamoDBManager:
    def __init__(self, region='us-east-1'):
        self.dynamodb_client = boto3.client('dynamodb', region_name=region)
        self.region = region
    
    def create_table(self, table_name: str, key_schema: list, 
                    attribute_definitions: list, 
                    billing_mode: str = 'PAY_PER_REQUEST',
                    global_secondary_indexes: list = None) -> bool:
        """Create a DynamoDB table"""
        try:
            table_config = {
                'TableName': table_name,
                'KeySchema': key_schema,
                'AttributeDefinitions': attribute_definitions,
                'BillingMode': billing_mode
            }
            
            if global_secondary_indexes:
                table_config['GlobalSecondaryIndexes'] = global_secondary_indexes
            
            response = self.dynamodb_client.create_table(**table_config)
            
            # Wait for table to be created
            waiter = self.dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print(f"Table {table_name} created successfully")
            return True
            
        except self.dynamodb_client.exceptions.ResourceInUseException:
            print(f"Table {table_name} already exists")
            return True
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")
            return False
    
    def enable_point_in_time_recovery(self, table_name: str) -> bool:
        """Enable point-in-time recovery for a table"""
        try:
            self.dynamodb_client.update_continuous_backups(
                TableName=table_name,
                PointInTimeRecoverySpecification={
                    'PointInTimeRecoveryEnabled': True
                }
            )
            print(f"Point-in-time recovery enabled for {table_name}")
            return True
        except Exception as e:
            print(f"Error enabling point-in-time recovery for {table_name}: {e}")
            return False
    
    def create_workflow_table(self) -> bool:
        """Create the main workflow state table"""
        table_name = 'biomerkin-workflows'
        
        key_schema = [
            {
                'AttributeName': 'workflow_id',
                'KeyType': 'HASH'
            }
        ]
        
        attribute_definitions = [
            {
                'AttributeName': 'workflow_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'created_at',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'status',
                'AttributeType': 'S'
            }
        ]
        
        # Global Secondary Indexes for querying by user and status
        global_secondary_indexes = [
            {
                'IndexName': 'user-id-index',
                'KeySchema': [
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'created_at',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            },
            {
                'IndexName': 'status-index',
                'KeySchema': [
                    {
                        'AttributeName': 'status',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'created_at',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            }
        ]
        
        success = self.create_table(
            table_name=table_name,
            key_schema=key_schema,
            attribute_definitions=attribute_definitions,
            global_secondary_indexes=global_secondary_indexes
        )
        
        if success:
            self.enable_point_in_time_recovery(table_name)
        
        return success
    
    def create_analysis_results_table(self) -> bool:
        """Create table for storing analysis results"""
        table_name = 'biomerkin-analysis-results'
        
        key_schema = [
            {
                'AttributeName': 'workflow_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'agent_name',
                'KeyType': 'RANGE'
            }
        ]
        
        attribute_definitions = [
            {
                'AttributeName': 'workflow_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'agent_name',
                'AttributeType': 'S'
            }
        ]
        
        return self.create_table(
            table_name=table_name,
            key_schema=key_schema,
            attribute_definitions=attribute_definitions
        )
    
    def create_user_sessions_table(self) -> bool:
        """Create table for user session management"""
        table_name = 'biomerkin-user-sessions'
        
        key_schema = [
            {
                'AttributeName': 'session_id',
                'KeyType': 'HASH'
            }
        ]
        
        attribute_definitions = [
            {
                'AttributeName': 'session_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            }
        ]
        
        global_secondary_indexes = [
            {
                'IndexName': 'user-id-index',
                'KeySchema': [
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            }
        ]
        
        return self.create_table(
            table_name=table_name,
            key_schema=key_schema,
            attribute_definitions=attribute_definitions,
            global_secondary_indexes=global_secondary_indexes
        )
    
    def create_audit_log_table(self) -> bool:
        """Create table for audit logging"""
        table_name = 'biomerkin-audit-logs'
        
        key_schema = [
            {
                'AttributeName': 'log_id',
                'KeyType': 'HASH'
            }
        ]
        
        attribute_definitions = [
            {
                'AttributeName': 'log_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'timestamp',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            }
        ]
        
        global_secondary_indexes = [
            {
                'IndexName': 'timestamp-index',
                'KeySchema': [
                    {
                        'AttributeName': 'timestamp',
                        'KeyType': 'HASH'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            },
            {
                'IndexName': 'user-timestamp-index',
                'KeySchema': [
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            }
        ]
        
        return self.create_table(
            table_name=table_name,
            key_schema=key_schema,
            attribute_definitions=attribute_definitions,
            global_secondary_indexes=global_secondary_indexes
        )

def setup_dynamodb_tables() -> Dict[str, bool]:
    """Set up all DynamoDB tables for the Biomerkin system"""
    db_manager = DynamoDBManager()
    
    results = {}
    
    # Create all required tables
    tables_to_create = [
        ('workflows', db_manager.create_workflow_table),
        ('analysis_results', db_manager.create_analysis_results_table),
        ('user_sessions', db_manager.create_user_sessions_table),
        ('audit_logs', db_manager.create_audit_log_table)
    ]
    
    for table_name, create_function in tables_to_create:
        print(f"Creating {table_name} table...")
        results[table_name] = create_function()
    
    return results

def create_dynamodb_client_utility():
    """Create a utility class for DynamoDB operations"""
    client_code = '''
"""
DynamoDB client utility for Biomerkin workflow management
"""
import boto3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from boto3.dynamodb.conditions import Key, Attr

class BiomerkinDynamoDBClient:
    def __init__(self, region='us-east-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.workflows_table = self.dynamodb.Table('biomerkin-workflows')
        self.results_table = self.dynamodb.Table('biomerkin-analysis-results')
        self.sessions_table = self.dynamodb.Table('biomerkin-user-sessions')
        self.audit_table = self.dynamodb.Table('biomerkin-audit-logs')
    
    def create_workflow(self, user_id: str, dna_sequence: str, 
                       metadata: Dict[str, Any] = None) -> str:
        """Create a new workflow record"""
        workflow_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        workflow_item = {
            'workflow_id': workflow_id,
            'user_id': user_id,
            'status': 'INITIATED',
            'current_agent': 'genomics',
            'progress_percentage': 0,
            'dna_sequence': dna_sequence,
            'created_at': timestamp,
            'updated_at': timestamp,
            'metadata': metadata or {}
        }
        
        self.workflows_table.put_item(Item=workflow_item)
        
        # Log workflow creation
        self.log_audit_event(
            user_id=user_id,
            action='WORKFLOW_CREATED',
            resource_id=workflow_id,
            details={'dna_sequence_length': len(dna_sequence)}
        )
        
        return workflow_id
    
    def update_workflow_status(self, workflow_id: str, status: str, 
                              current_agent: str = None, 
                              progress_percentage: float = None,
                              error_message: str = None) -> bool:
        """Update workflow status"""
        try:
            update_expression = "SET #status = :status, updated_at = :timestamp"
            expression_values = {
                ':status': status,
                ':timestamp': datetime.utcnow().isoformat()
            }
            expression_names = {'#status': 'status'}
            
            if current_agent:
                update_expression += ", current_agent = :current_agent"
                expression_values[':current_agent'] = current_agent
            
            if progress_percentage is not None:
                update_expression += ", progress_percentage = :progress"
                expression_values[':progress'] = progress_percentage
            
            if error_message:
                update_expression += ", error_message = :error"
                expression_values[':error'] = error_message
            
            self.workflows_table.update_item(
                Key={'workflow_id': workflow_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names
            )
            return True
        except Exception as e:
            print(f"Error updating workflow status: {e}")
            return False
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID"""
        try:
            response = self.workflows_table.get_item(
                Key={'workflow_id': workflow_id}
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting workflow: {e}")
            return None
    
    def get_user_workflows(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get workflows for a specific user"""
        try:
            response = self.workflows_table.query(
                IndexName='user-id-index',
                KeyConditionExpression=Key('user_id').eq(user_id),
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting user workflows: {e}")
            return []
    
    def store_agent_results(self, workflow_id: str, agent_name: str, 
                           results: Dict[str, Any]) -> bool:
        """Store results from an agent"""
        try:
            item = {
                'workflow_id': workflow_id,
                'agent_name': agent_name,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.results_table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error storing agent results: {e}")
            return False
    
    def get_workflow_results(self, workflow_id: str) -> Dict[str, Any]:
        """Get all results for a workflow"""
        try:
            response = self.results_table.query(
                KeyConditionExpression=Key('workflow_id').eq(workflow_id)
            )
            
            results = {}
            for item in response.get('Items', []):
                results[item['agent_name']] = item['results']
            
            return results
        except Exception as e:
            print(f"Error getting workflow results: {e}")
            return {}
    
    def create_user_session(self, user_id: str, session_data: Dict[str, Any] = None) -> str:
        """Create a user session"""
        session_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        session_item = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': timestamp,
            'last_accessed': timestamp,
            'session_data': session_data or {}
        }
        
        self.sessions_table.put_item(Item=session_item)
        return session_id
    
    def log_audit_event(self, user_id: str, action: str, resource_id: str = None,
                       details: Dict[str, Any] = None) -> bool:
        """Log an audit event"""
        try:
            log_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            audit_item = {
                'log_id': log_id,
                'user_id': user_id,
                'action': action,
                'timestamp': timestamp,
                'resource_id': resource_id,
                'details': details or {}
            }
            
            self.audit_table.put_item(Item=audit_item)
            return True
        except Exception as e:
            print(f"Error logging audit event: {e}")
            return False
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get system-wide workflow statistics"""
        try:
            # Get counts by status
            status_counts = {}
            statuses = ['INITIATED', 'GENOMICS_PROCESSING', 'PROTEOMICS_PROCESSING', 
                       'LITERATURE_PROCESSING', 'DRUG_PROCESSING', 'REPORT_GENERATION',
                       'COMPLETED', 'FAILED']
            
            for status in statuses:
                response = self.workflows_table.query(
                    IndexName='status-index',
                    KeyConditionExpression=Key('status').eq(status),
                    Select='COUNT'
                )
                status_counts[status] = response['Count']
            
            return {
                'status_counts': status_counts,
                'total_workflows': sum(status_counts.values())
            }
        except Exception as e:
            print(f"Error getting workflow statistics: {e}")
            return {}
'''
    
    with open('biomerkin/utils/dynamodb_client.py', 'w') as f:
        f.write(client_code)

if __name__ == "__main__":
    results = setup_dynamodb_tables()
    create_dynamodb_client_utility()
    
    print("DynamoDB setup results:")
    for table, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {table}")