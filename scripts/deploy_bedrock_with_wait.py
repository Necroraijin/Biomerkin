#!/usr/bin/env python3
"""
Deploy Bedrock Lambda with proper waiting
"""
import boto3
import time

def wait_and_deploy():
    """Wait for Lambda to be ready then deploy"""
    print("⏳ Waiting for Lambda to be ready...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Wait for function to be ready
    max_wait = 60
    waited = 0
    while waited < max_wait:
        try:
            response = lambda_client.get_function(FunctionName='biomerkin-orchestrator')
            state = response['Configuration']['State']
            last_update_status = response['Configuration']['LastUpdateStatus']
            
            print(f"   State: {state}, Update Status: {last_update_status}")
            
            if state == 'Active' and last_update_status == 'Successful':
                print("✅ Lambda is ready!")
                break
            
            time.sleep(5)
            waited += 5
        except Exception as e:
            print(f"   Error checking status: {e}")
            time.sleep(5)
            waited += 5
    
    if waited >= max_wait:
        print("⚠️  Timeout waiting for Lambda")
        return False
    
    # Now run the deployment
    print("\n🚀 Running deployment...")
    import subprocess
    result = subprocess.run(['python', 'scripts/deploy_real_bedrock_lambda.py'], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0

if __name__ == '__main__':
    wait_and_deploy()
