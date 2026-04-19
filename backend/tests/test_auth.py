#!/usr/bin/env python3

"""
Test script to verify the authentication system
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_authentication():
    print("🧪 Testing Learn Your Way Authentication System")
    print("=" * 50)

    # Test data
    test_user = {
        "email": "test@example2.com",
        "username": "testuser2",
        "password": "Test123456",
        "full_name": "Test User",
        "grade_level": 6
    }

    try:
        # 1. Register a new user
        print("1. Registering new user...")
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)

        if response.status_code == 201:
            print("✅ User registration successful!")
            data = response.json()
            token = data['access_token']
            print(f"   Token received: {token[:20]}...")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

        # 2. Test login with the same user
        print("\n2. Testing user login...")
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }

        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)

        if response.status_code == 200:
            print("✅ Login successful!")
            data = response.json()
            token = data['access_token']
            user = data['user']
            print(f"   Welcome, {user['username']}!")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

        # 3. Test protected endpoint
        print("\n3. Testing protected endpoint...")
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)

        if response.status_code == 200:
            print("✅ Protected endpoint access successful!")
            user_data = response.json()
            print(f"   User ID: {user_data['id']}")
            print(f"   Email: {user_data['email']}")
        else:
            print(f"❌ Protected endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

        # 4. Test token verification
        print("\n4. Testing token verification...")
        response = requests.post(f"{BASE_URL}/api/auth/verify-token", headers=headers)

        if response.status_code == 200:
            print("✅ Token verification successful!")
        else:
            print(f"❌ Token verification failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

        # 5. Test logout
        print("\n5. Testing logout...")
        response = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)

        if response.status_code == 200:
            print("✅ Logout successful!")
        else:
            print(f"❌ Logout failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

        print("\n" + "=" * 50)
        print("🎉 All authentication tests passed!")
        return True

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the backend server.")
        print("   Make sure the backend is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_authentication()
    exit(0 if success else 1)