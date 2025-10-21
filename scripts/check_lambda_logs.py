#!/usr/bin/env python3
"""
Check Lambda function logs to see what's wrong
"""
import boto3
import time
from datetime import datetime, timedelta

def check_lambda_logs():
    """Check recent Lambda logs"""
    print("🔍 Checking Lambda Logs...")
    
    logs_client = boto3.client('logs', region_name='ap-south-1')
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Get Lambda function info
    try:
        response = lambda_client.get_function(FunctionName='biomerkin-orchestrator')
        print(f"✅ Lambda Function: {response['Configuration']['FunctionName']}")
        print(f"   Runtime: {response['Configuration']['Runtime']}")
        print(f"   Last Modified: {response['Configuration']['LastModified']}")
        print(f"   Memory: {response['Configuration']['MemorySize']} MB")
        print(f"   Timeout: {response['Configuration']['Timeout']} seconds")
    except Exception as e:
        print(f"❌ Error getting Lambda info: {e}")
        return
    
    # Get log group
    log_group = '/aws/lambda/biomerkin-orchestrator'
    
    print(f"\n📋 Checking logs from: {log_group}")
    
    try:
        # Get recent log streams
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if not streams_response['logStreams']:
            print("⚠️  No log streams found")
            return
        
        print(f"\n📝 Recent Log Streams:")
        for stream in streams_response['logStreams'][:3]:
            print(f"   - {stream['logStreamName']}")
            print(f"     Last Event: {datetime.fromtimestamp(stream['lastEventTime']/1000)}")
        
        # Get logs from most recent stream
        latest_stream = streams_response['logStreams'][0]['logStreamName']
        print(f"\n📖 Reading logs from: {latest_stream}")
        print("="*60)
        
        events_response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=latest_stream,
            limit=50,
            startFromHead=False
        )
        
        for event in events_response['events'][-20:]:  # Last 20 events
            timestamp = datetime.fromtimestamp(event['timestamp']/1000)
            message = event['message'].strip()
            print(f"[{timestamp.strftime('%H:%M:%S')}] {message}")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error reading logs: {e}")

if __name__ == '__main__':
    check_lambda_logs()
