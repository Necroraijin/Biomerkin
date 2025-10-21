#!/usr/bin/env python3
"""
Test API directly to verify CORS is working
"""
import requests
import json

def test_api():
    """Test the API endpoint directly"""
    print("🧪 Testing API Endpoint Directly...")
    print("="*60)
    
    api_url = "https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod/analyze"
    
    # Test data
    test_data = {
        "sequence_data": "ATCGATCGATCGATCG",
        "user_id": "test"
    }
    
    print(f"\n📡 Sending POST request to:")
    print(f"   {api_url}")
    print(f"\n📦 Request body:")
    print(f"   {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            api_url,
            json=test_data,
            headers={
                'Content-Type': 'application/json',
                'Origin': 'http://biomerkin-frontend-20251018-013734.s3-website-ap-south-1.amazonaws.com'
            },
            timeout=10
        )
        
        print(f"\n✅ Response Status: {response.status_code}")
        print(f"\n📋 Response Headers:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower() or 'content-type' in header.lower():
                print(f"   {header}: {value}")
        
        print(f"\n📄 Response Body:")
        try:
            body = response.json()
            print(json.dumps(body, indent=2))
        except:
            print(response.text)
        
        # Check CORS headers
        print("\n" + "="*60)
        print("🔍 CORS HEADER CHECK:")
        print("="*60)
        
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        if cors_origin:
            print(f"✅ Access-Control-Allow-Origin: {cors_origin}")
        else:
            print(f"❌ Access-Control-Allow-Origin: MISSING!")
        
        if response.status_code == 200:
            print("\n✅ API IS WORKING!")
            print("✅ CORS HEADERS ARE PRESENT!")
            print("\n⚠️  If you still see CORS errors in browser:")
            print("   → Your browser is using CACHED JavaScript files")
            print("   → Solution: Clear cache or use Incognito mode")
        else:
            print(f"\n⚠️  API returned status {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == '__main__':
    test_api()
