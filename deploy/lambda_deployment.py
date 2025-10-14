"""
Lambda function deployment for Biomerkin multi-agent system
"""
import boto3
import zipfile
import os
import json
from typing import Dict, Any

class LambdaDeployer:
    def __init__(self, region='us-east-1'):
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.region = region
    
    def create_deployment_package(self, source_dir: str, output_file: str) -> str:
        """Create a deployment package for Lambda function"""
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
        return output_file
    
    def deploy_lambda_function(self, function_name: str, role_arn: str, 
                             handler: str, zip_file: str, 
                             environment_vars: Dict[str, str] = None,
                             timeout: int = 300, memory_size: int = 512) -> str:
        """Deploy a Lambda function"""
        
        with open(zip_file, 'rb') as f:
            zip_content = f.read()
        
        function_config = {
            'FunctionName': function_name,
            'Runtime': 'python3.9',
            'Role': role_arn,
            'Handler': handler,
            'Code': {'ZipFile': zip_content},
            'Description': f'Biomerkin {function_name} agent',
            'Timeout': timeout,
            'MemorySize': memory_size,
            'Publish': True
        }
        
        if environment_vars:
            function_config['Environment'] = {'Variables': environment_vars}
        
        try:
            response = self.lambda_client.create_function(**function_config)
            return response['FunctionArn']
        except self.lambda_client.exceptions.ResourceConflictException:
            # Function already exists, update it
            response = self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            # Update configuration
            self.lambda_client.update_function_configuration(
                FunctionName=function_name,
                Role=role_arn,
                Handler=handler,
                Description=f'Biomerkin {function_name} agent',
                Timeout=timeout,
                MemorySize=memory_size,
                Environment={'Variables': environment_vars} if environment_vars else {}
            )
            
            return response['FunctionArn']
        except Exception as e:
            print(f"Error deploying function {function_name}: {e}")
            return None
    
    def create_lambda_layer(self, layer_name: str, zip_file: str, 
                           compatible_runtimes: list = None) -> str:
        """Create a Lambda layer for shared dependencies"""
        if compatible_runtimes is None:
            compatible_runtimes = ['python3.9']
        
        with open(zip_file, 'rb') as f:
            zip_content = f.read()
        
        try:
            response = self.lambda_client.publish_layer_version(
                LayerName=layer_name,
                Description='Biomerkin shared dependencies layer',
                Content={'ZipFile': zip_content},
                CompatibleRuntimes=compatible_runtimes
            )
            return response['LayerVersionArn']
        except Exception as e:
            print(f"Error creating layer {layer_name}: {e}")
            return None

def create_lambda_handlers():
    """Create Lambda handler files for each agent"""
    
    # Orchestrator Lambda handler
    orchestrator_handler = '''
import json
import boto3
from biomerkin.services.orchestrator import WorkflowOrchestrator

def lambda_handler(event, context):
    """Lambda handler for workflow orchestration"""
    try:
        orchestrator = WorkflowOrchestrator()
        
        if event.get('httpMethod') == 'POST':
            # Start new workflow
            body = json.loads(event.get('body', '{}'))
            dna_sequence = body.get('dna_sequence')
            workflow_id = orchestrator.start_analysis(dna_sequence)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'workflow_id': workflow_id})
            }
        
        elif event.get('httpMethod') == 'GET':
            # Get workflow status
            workflow_id = event.get('pathParameters', {}).get('workflow_id')
            status = orchestrator.get_analysis_status(workflow_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(status.__dict__)
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
'''
    
    # Genomics Agent Lambda handler
    genomics_handler = '''
import json
from biomerkin.agents.genomics_agent import GenomicsAgent

def lambda_handler(event, context):
    """Lambda handler for genomics analysis"""
    try:
        agent = GenomicsAgent()
        
        # Extract sequence data from event
        sequence_data = event.get('sequence_data')
        if not sequence_data:
            raise ValueError("No sequence data provided")
        
        # Perform genomics analysis
        results = agent.analyze_sequence(sequence_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps(results.__dict__, default=str)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''
    
    # Proteomics Agent Lambda handler
    proteomics_handler = '''
import json
from biomerkin.agents.proteomics_agent import ProteomicsAgent

def lambda_handler(event, context):
    """Lambda handler for proteomics analysis"""
    try:
        agent = ProteomicsAgent()
        
        # Extract protein sequences from event
        protein_sequences = event.get('protein_sequences', [])
        if not protein_sequences:
            raise ValueError("No protein sequences provided")
        
        # Perform proteomics analysis
        results = []
        for sequence in protein_sequences:
            result = agent.analyze_protein(sequence)
            results.append(result.__dict__)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'results': results}, default=str)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''
    
    # Literature Agent Lambda handler
    literature_handler = '''
import json
from biomerkin.agents.literature_agent import LiteratureAgent

def lambda_handler(event, context):
    """Lambda handler for literature research"""
    try:
        agent = LiteratureAgent()
        
        # Extract search terms from genomics/proteomics data
        gene_data = event.get('gene_data', {})
        protein_data = event.get('protein_data', {})
        
        # Generate search terms and perform literature search
        search_terms = agent.generate_search_terms(gene_data, protein_data)
        articles = agent.search_literature(search_terms)
        summary = agent.summarize_findings(articles)
        
        return {
            'statusCode': 200,
            'body': json.dumps(summary.__dict__, default=str)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''
    
    # Drug Agent Lambda handler
    drug_handler = '''
import json
from biomerkin.agents.drug_agent import DrugAgent

def lambda_handler(event, context):
    """Lambda handler for drug discovery"""
    try:
        agent = DrugAgent()
        
        # Extract target data from previous analyses
        target_data = event.get('target_data', {})
        if not target_data:
            raise ValueError("No target data provided")
        
        # Find drug candidates and trial information
        drug_candidates = agent.find_drug_candidates(target_data)
        
        # Get trial information for each candidate
        for candidate in drug_candidates:
            trial_info = agent.get_trial_information(candidate.drug_id)
            candidate.trial_information = trial_info
        
        return {
            'statusCode': 200,
            'body': json.dumps([c.__dict__ for c in drug_candidates], default=str)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''
    
    # Decision Agent Lambda handler
    decision_handler = '''
import json
from biomerkin.agents.decision_agent import DecisionAgent

def lambda_handler(event, context):
    """Lambda handler for report generation"""
    try:
        agent = DecisionAgent()
        
        # Extract combined analysis data
        analysis_data = event.get('analysis_data', {})
        if not analysis_data:
            raise ValueError("No analysis data provided")
        
        # Generate comprehensive medical report
        report = agent.generate_report(analysis_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps(report.__dict__, default=str)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''
    
    handlers = {
        'orchestrator': orchestrator_handler,
        'genomics': genomics_handler,
        'proteomics': proteomics_handler,
        'literature': literature_handler,
        'drug': drug_handler,
        'decision': decision_handler
    }
    
    # Write handler files
    os.makedirs('lambda_functions', exist_ok=True)
    for agent, handler_code in handlers.items():
        with open(f'lambda_functions/{agent}_handler.py', 'w') as f:
            f.write(handler_code)

def deploy_all_lambda_functions(role_arns: Dict[str, str]):
    """Deploy all Lambda functions for the Biomerkin system"""
    deployer = LambdaDeployer()
    
    # Create handler files
    create_lambda_handlers()
    
    # Environment variables for all functions
    common_env_vars = {
        'DYNAMODB_TABLE': 'biomerkin-workflows',
        'S3_BUCKET': 'biomerkin-data',
        'AWS_REGION': 'us-east-1'
    }
    
    # Function configurations
    function_configs = {
        'biomerkin-orchestrator': {
            'handler': 'orchestrator_handler.lambda_handler',
            'timeout': 900,
            'memory_size': 1024,
            'env_vars': common_env_vars
        },
        'biomerkin-genomics': {
            'handler': 'genomics_handler.lambda_handler',
            'timeout': 600,
            'memory_size': 2048,
            'env_vars': common_env_vars
        },
        'biomerkin-proteomics': {
            'handler': 'proteomics_handler.lambda_handler',
            'timeout': 600,
            'memory_size': 1536,
            'env_vars': {**common_env_vars, 'PDB_API_URL': 'https://data.rcsb.org/rest/v1/core/entry/'}
        },
        'biomerkin-literature': {
            'handler': 'literature_handler.lambda_handler',
            'timeout': 600,
            'memory_size': 1024,
            'env_vars': {**common_env_vars, 'PUBMED_API_URL': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'}
        },
        'biomerkin-drug': {
            'handler': 'drug_handler.lambda_handler',
            'timeout': 600,
            'memory_size': 1024,
            'env_vars': {**common_env_vars, 'DRUGBANK_API_URL': 'https://go.drugbank.com/api/v1/'}
        },
        'biomerkin-decision': {
            'handler': 'decision_handler.lambda_handler',
            'timeout': 600,
            'memory_size': 1024,
            'env_vars': common_env_vars
        }
    }
    
    deployed_functions = {}
    
    for function_name, config in function_configs.items():
        agent_name = function_name.replace('biomerkin-', '')
        role_arn = role_arns.get(agent_name)
        
        if not role_arn:
            print(f"No role ARN found for {agent_name}")
            continue
        
        # Create deployment package
        zip_file = f"{function_name}.zip"
        deployer.create_deployment_package('biomerkin', zip_file)
        
        # Deploy function
        function_arn = deployer.deploy_lambda_function(
            function_name=function_name,
            role_arn=role_arn,
            handler=config['handler'],
            zip_file=zip_file,
            environment_vars=config['env_vars'],
            timeout=config['timeout'],
            memory_size=config['memory_size']
        )
        
        if function_arn:
            deployed_functions[function_name] = function_arn
            print(f"Deployed {function_name}: {function_arn}")
        
        # Clean up zip file
        if os.path.exists(zip_file):
            os.remove(zip_file)
    
    return deployed_functions

if __name__ == "__main__":
    # This would be called with role ARNs from IAM setup
    role_arns = {
        'orchestrator': 'arn:aws:iam::123456789012:role/biomerkin-orchestrator-lambda-role',
        'genomics': 'arn:aws:iam::123456789012:role/biomerkin-genomics-lambda-role',
        'proteomics': 'arn:aws:iam::123456789012:role/biomerkin-proteomics-lambda-role',
        'literature': 'arn:aws:iam::123456789012:role/biomerkin-literature-lambda-role',
        'drug': 'arn:aws:iam::123456789012:role/biomerkin-drug-lambda-role',
        'decision': 'arn:aws:iam::123456789012:role/biomerkin-decision-lambda-role'
    }
    deploy_all_lambda_functions(role_arns)