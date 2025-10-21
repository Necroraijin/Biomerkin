#!/usr/bin/env python3
"""
Find John Snow Labs Medical LLM in AWS
Searches across Bedrock, SageMaker, and Marketplace
"""

import boto3
import json
from botocore.exceptions import ClientError

def search_bedrock():
    """Search for John Snow Labs in Bedrock"""
    print("🔍 Searching AWS Bedrock...")
    
    try:
        bedrock = boto3.client('bedrock', region_name='ap-south-1')
        response = bedrock.list_foundation_models()
        
        # Search for John Snow Labs or medical models
        found = []
        for model in response['modelSummaries']:
            provider = model.get('providerName', '').lower()
            model_name = model.get('modelName', '').lower()
            model_id = model.get('modelId', '').lower()
            
            if any(term in provider + model_name + model_id for term in 
                   ['john', 'snow', 'medical', 'healthcare', 'clinical']):
                found.append({
                    'service': 'Bedrock',
                    'provider': model.get('providerName'),
                    'name': model.get('modelName'),
                    'id': model.get('modelId'),
                    'status': model.get('modelLifecycle', {}).get('status')
                })
        
        if found:
            print(f"✅ Found {len(found)} models in Bedrock:")
            for m in found:
                print(f"   - {m['provider']}: {m['name']} ({m['id']})")
        else:
            print("❌ No John Snow Labs models found in Bedrock")
        
        return found
        
    except Exception as e:
        print(f"❌ Bedrock search error: {str(e)}")
        return []

def search_sagemaker_endpoints():
    """Search for existing SageMaker endpoints"""
    print("\n🔍 Searching SageMaker Endpoints...")
    
    try:
        sagemaker = boto3.client('sagemaker', region_name='ap-south-1')
        response = sagemaker.list_endpoints(MaxResults=100)
        
        found = []
        for endpoint in response.get('Endpoints', []):
            name = endpoint.get('EndpointName', '').lower()
            if any(term in name for term in ['john', 'snow', 'medical', 'healthcare', 'clinical']):
                found.append({
                    'service': 'SageMaker Endpoint',
                    'name': endpoint.get('EndpointName'),
                    'status': endpoint.get('EndpointStatus'),
                    'created': str(endpoint.get('CreationTime'))
                })
        
        if found:
            print(f"✅ Found {len(found)} endpoints:")
            for e in found:
                print(f"   - {e['name']} (Status: {e['status']})")
        else:
            print("❌ No John Snow Labs endpoints found")
        
        return found
        
    except Exception as e:
        print(f"❌ SageMaker endpoint search error: {str(e)}")
        return []

def search_sagemaker_models():
    """Search for SageMaker models"""
    print("\n🔍 Searching SageMaker Models...")
    
    try:
        sagemaker = boto3.client('sagemaker', region_name='ap-south-1')
        response = sagemaker.list_models(MaxResults=100)
        
        found = []
        for model in response.get('Models', []):
            name = model.get('ModelName', '').lower()
            if any(term in name for term in ['john', 'snow', 'medical', 'healthcare', 'clinical']):
                found.append({
                    'service': 'SageMaker Model',
                    'name': model.get('ModelName'),
                    'arn': model.get('ModelArn'),
                    'created': str(model.get('CreationTime'))
                })
        
        if found:
            print(f"✅ Found {len(found)} models:")
            for m in found:
                print(f"   - {m['name']}")
        else:
            print("❌ No John Snow Labs models found")
        
        return found
        
    except Exception as e:
        print(f"❌ SageMaker model search error: {str(e)}")
        return []

def search_model_packages():
    """Search for model packages (marketplace)"""
    print("\n🔍 Searching SageMaker Model Packages (Marketplace)...")
    
    try:
        sagemaker = boto3.client('sagemaker', region_name='ap-south-1')
        response = sagemaker.list_model_packages(MaxResults=100)
        
        found = []
        for pkg in response.get('ModelPackageSummaryList', []):
            name = pkg.get('ModelPackageName', '').lower()
            desc = pkg.get('ModelPackageDescription', '').lower()
            
            if any(term in name + desc for term in ['john', 'snow', 'medical', 'healthcare', 'clinical']):
                found.append({
                    'service': 'Model Package',
                    'name': pkg.get('ModelPackageName'),
                    'arn': pkg.get('ModelPackageArn'),
                    'status': pkg.get('ModelPackageStatus')
                })
        
        if found:
            print(f"✅ Found {len(found)} model packages:")
            for p in found:
                print(f"   - {p['name']} (Status: {p['status']})")
        else:
            print("❌ No John Snow Labs model packages found")
        
        return found
        
    except Exception as e:
        print(f"❌ Model package search error: {str(e)}")
        return []

def check_marketplace_subscriptions():
    """Check marketplace subscriptions"""
    print("\n🔍 Checking AWS Marketplace Subscriptions...")
    
    try:
        marketplace = boto3.client('marketplace-entitlement', region_name='us-east-1')
        response = marketplace.get_entitlements(ProductCode='*')
        
        found = []
        for entitlement in response.get('Entitlements', []):
            product = entitlement.get('ProductCode', '').lower()
            if any(term in product for term in ['john', 'snow', 'medical']):
                found.append({
                    'service': 'Marketplace',
                    'product': entitlement.get('ProductCode'),
                    'dimension': entitlement.get('Dimension')
                })
        
        if found:
            print(f"✅ Found {len(found)} subscriptions:")
            for s in found:
                print(f"   - {s['product']}")
        else:
            print("❌ No John Snow Labs subscriptions found")
        
        return found
        
    except Exception as e:
        print(f"⚠️  Marketplace check: {str(e)}")
        return []

def provide_guidance(all_results):
    """Provide guidance based on search results"""
    print("\n" + "="*60)
    print("📋 SEARCH RESULTS SUMMARY")
    print("="*60)
    
    total_found = sum(len(results) for results in all_results.values())
    
    if total_found > 0:
        print(f"\n✅ Found {total_found} John Snow Labs resources!")
        print("\nNext steps:")
        print("1. Review the resources listed above")
        print("2. If it's a SageMaker endpoint, use the endpoint name")
        print("3. If it's a Bedrock model, use the model ID")
        print("4. Run the integration script with the resource details")
    else:
        print("\n❌ No John Snow Labs Medical LLM found in your AWS account")
        print("\n📝 TO SUBSCRIBE:")
        print("\n1. Visit AWS Marketplace:")
        print("   https://aws.amazon.com/marketplace/search/results?searchTerms=john+snow+labs")
        
        print("\n2. Or check SageMaker JumpStart:")
        print("   - Open AWS Console → SageMaker → JumpStart")
        print("   - Search for 'John Snow Labs' or 'Medical'")
        
        print("\n3. Common John Snow Labs Products:")
        print("   - Healthcare NLP for SageMaker")
        print("   - Spark NLP for Healthcare")
        print("   - Clinical NLP Models")
        
        print("\n4. After subscribing:")
        print("   - Deploy the model/endpoint")
        print("   - Run this script again to detect it")
        print("   - I'll help integrate it into your system")
        
        print("\n💡 ALTERNATIVE (Recommended for hackathon):")
        print("   Use Amazon Nova Pro - already available!")
        print("   Model ID: amazon.nova-pro-v1:0")
        print("   Excellent for medical/genomics analysis")
    
    print("\n" + "="*60)

def main():
    print("🚀 Searching for John Snow Labs Medical LLM\n")
    
    results = {
        'bedrock': search_bedrock(),
        'endpoints': search_sagemaker_endpoints(),
        'models': search_sagemaker_models(),
        'packages': search_model_packages(),
        'marketplace': check_marketplace_subscriptions()
    }
    
    provide_guidance(results)
    
    # Save results
    with open('johnsnow_search_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n💾 Results saved to: johnsnow_search_results.json")

if __name__ == "__main__":
    main()
