#!/usr/bin/env python3
"""
Get the correct frontend URL and test alternatives.
"""

import boto3
import requests
import time

def get_frontend_urls():
    """Get all possible frontend URLs."""
    
    print("🔍 FINDING CORRECT FRONTEND URL")
    print("="*35)
    
    try:
        s3_client = boto3.client('s3')
        
        # Find bucket
        response = s3_client.list_buckets()
        bucket_name = None
        
        for bucket in response['Buckets']:
            if 'biomerkin-frontend' in bucket['Name']:
                bucket_name = bucket['Name']
                break
        
        if not bucket_name:
            print("❌ No bucket found")
            return []
        
        print(f"📦 Bucket: {bucket_name}")
        
        # Get bucket region
        try:
            bucket_location = s3_client.get_bucket_location(Bucket=bucket_name)
            region = bucket_location.get('LocationConstraint') or 'us-east-1'
        except:
            region = 'ap-south-1'  # Default to your configured region
        
        print(f"🌍 Region: {region}")
        
        # Generate possible URLs
        urls = [
            f"http://{bucket_name}.s3-website-{region}.amazonaws.com",
            f"http://{bucket_name}.s3-website.{region}.amazonaws.com",
            f"https://{bucket_name}.s3.{region}.amazonaws.com/index.html",
            f"https://{bucket_name}.s3.amazonaws.com/index.html"
        ]
        
        return urls, bucket_name
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], None

def test_urls(urls):
    """Test which URL works."""
    
    print(f"\n🧪 TESTING URLS")
    print("="*15)
    
    working_urls = []
    
    for url in urls:
        try:
            print(f"Testing: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ WORKING: {url}")
                working_urls.append(url)
            else:
                print(f"❌ Status {response.status_code}: {url}")
                
        except Exception as e:
            print(f"❌ Failed: {url} - {e}")
    
    return working_urls

def create_direct_s3_link(bucket_name):
    """Create direct S3 object URL."""
    
    print(f"\n🔗 CREATING DIRECT S3 LINKS")
    print("="*30)
    
    try:
        s3_client = boto3.client('s3')
        
        # Check if index.html exists
        try:
            s3_client.head_object(Bucket=bucket_name, Key='index.html')
            print("✅ index.html exists in bucket")
        except:
            print("❌ index.html not found in bucket")
            return None
        
        # Generate presigned URL (works for sure)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': 'index.html'},
            ExpiresIn=3600  # 1 hour
        )
        
        print(f"🔗 Presigned URL (1 hour): {presigned_url}")
        
        return presigned_url
        
    except Exception as e:
        print(f"❌ Error creating presigned URL: {e}")
        return None

def main():
    """Main URL fixing function."""
    
    urls, bucket_name = get_frontend_urls()
    
    if not urls:
        print("❌ Could not generate URLs")
        return
    
    print(f"\n📋 POSSIBLE URLS:")
    for i, url in enumerate(urls, 1):
        print(f"   {i}. {url}")
    
    # Test URLs
    working_urls = test_urls(urls)
    
    if working_urls:
        print(f"\n🎉 WORKING FRONTEND URLS:")
        for url in working_urls:
            print(f"   ✅ {url}")
        
        print(f"\n🎯 USE THIS URL FOR HACKATHON:")
        print(f"   {working_urls[0]}")
        
    else:
        print(f"\n⚠️ No URLs working yet (DNS propagation delay)")
        print(f"💡 Try these solutions:")
        
        # Create presigned URL as backup
        if bucket_name:
            presigned = create_direct_s3_link(bucket_name)
            if presigned:
                print(f"\n🔗 BACKUP URL (use this for now):")
                print(f"   {presigned}")
        
        print(f"\n⏰ Wait 5-10 minutes for DNS propagation, then try:")
        for url in urls:
            print(f"   {url}")

if __name__ == "__main__":
    main()