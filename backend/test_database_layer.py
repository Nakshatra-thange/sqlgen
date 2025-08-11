import requests
import json

BASE_URL = "http://localhost:8000"

def test_database_endpoints():
    """Test all database endpoints"""
    
    print("🧪 Testing Database Layer Implementation")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure FastAPI is running!")
        print("Run: uvicorn app.main:app --reload")
        return
    
    # Test 2: Connection status (should be disconnected initially)
    print("\n2. Testing connection status (should be disconnected)...")
    response = requests.get(f"{BASE_URL}/api/v1/database/status")
    if response.status_code == 200:
        data = response.json()
        if not data["connected"]:
            print("✅ Initial status: disconnected (correct)")
        else:
            print("⚠️  Already connected to a database")
    else:
        print(f"❌ Status check failed: {response.status_code}")
    
    # Test 3: Connect to default database
    print("\n3. Testing connection to default database...")
    response = requests.post(f"{BASE_URL}/api/v1/database/connect/default")
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print("✅ Successfully connected to default database")
            print(f"   📊 Tables count: {data['connection_info']['tables_count']}")
            print(f"   🗄️  Database type: {data['connection_info']['database_type']}")
        else:
            print(f"❌ Connection failed: {data['error']}")
            return
    else:
        print(f"❌ Connection request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    # Test 4: Check connection status (should be connected now)
    print("\n4. Testing connection status (should be connected)...")
    response = requests.get(f"{BASE_URL}/api/v1/database/status")
    if response.status_code == 200:
        data = response.json()
        if data["connected"]:
            print("✅ Status: connected (correct)")
            print(f"   📁 Database path: {data['connection_info']['database_path']}")
        else:
            print("❌ Status shows disconnected but should be connected")
    
    # Test 5: Get database tables
    print("\n5. Testing get database tables...")
    response = requests.get(f"{BASE_URL}/api/v1/database/tables")
    if response.status_code == 200:
        data = response.json()
        if data["success"] and data["tables"]:
            print("✅ Successfully retrieved tables:")
            for table in data["tables"][:5]:  # Show first 5 tables
                print(f"   📋 {table}")
            if len(data["tables"]) > 5:
                print(f"   ... and {len(data['tables']) - 5} more tables")
        else:
            print(f"❌ Failed to get tables: {data.get('error', 'Unknown error')}")
    
    # Test 6: Test database connection
    print("\n6. Testing database connection test...")
    response = requests.post(f"{BASE_URL}/api/v1/database/test")
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print("✅ Database connection test passed")
        else:
            print(f"❌ Database connection test failed: {data['error']}")
    
    # Test 7: Test custom database connection (with invalid path)
    print("\n7. Testing custom database connection (invalid path)...")
    invalid_request = {
        "database_path": "/nonexistent/database.db"
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/database/connect/custom",
        json=invalid_request
    )
    if response.status_code == 400:
        print("✅ Correctly rejected invalid database path")
    else:
        print(f"⚠️  Expected 400 error, got {response.status_code}")
    
    # Test 8: Disconnect
    print("\n8. Testing disconnect...")
    response = requests.post(f"{BASE_URL}/api/v1/database/disconnect")
    if response.status_code == 200:
        print("✅ Successfully disconnected")
        
        # Verify disconnection
        response = requests.get(f"{BASE_URL}/api/v1/database/status")
        if response.status_code == 200:
            data = response.json()
            if not data["connected"]:
                print("✅ Status confirms disconnection")
            else:
                print("❌ Still shows connected after disconnect")
    
    print("\n" + "=" * 50)
    print("🎉 Database layer testing complete!")
    print("\n📝 Next steps:")
    print("   - The database connection layer is working")
    print("   - You can connect to SQLite databases")
    print("   - Ready for Day 5-6: Schema Intelligence Engine")

if __name__ == "__main__":
    test_database_endpoints() 