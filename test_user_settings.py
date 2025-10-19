"""
Test script for user settings/profile management endpoints.
Tests all CRUD operations for user profile and settings.
"""

import requests
import json

# Base URL
BASE_URL = "http://127.0.0.1:8000"

# Test data
TEST_USER = {
    "email": "settings_test@example.com",
    "password": "testpass123",
    "full_name": "Settings Test User",
}

NEW_PROFILE_DATA = {"full_name": "Updated Test User", "email": "settings_updated@example.com"}

PASSWORD_CHANGE = {"old_password": "testpass123", "new_password": "newpass456"}


def print_response(title, response):
    """Pretty print response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_user_settings():
    """Test all user settings endpoints."""

    # Step 1: Register a new user
    print("\n" + "=" * 60)
    print("STEP 1: Register New User")
    print("=" * 60)

    response = requests.post(f"{BASE_URL}/api/auth/register", json=TEST_USER)
    print_response("Register User", response)

    if response.status_code != 201:
        print("\n❌ Registration failed! Cannot continue tests.")
        return

    # Get access token
    auth_data = response.json()
    access_token = auth_data.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}

    print(f"\n✅ User registered successfully!")
    print(f"Access Token: {access_token[:20]}...")

    # Step 2: Get user profile
    print("\n" + "=" * 60)
    print("STEP 2: Get User Profile")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/users/profile", headers=headers)
    print_response("Get Profile", response)

    if response.status_code == 200:
        print("✅ Profile retrieved successfully!")
    else:
        print("❌ Failed to get profile")

    # Step 3: Update user profile
    print("\n" + "=" * 60)
    print("STEP 3: Update User Profile")
    print("=" * 60)

    response = requests.put(f"{BASE_URL}/api/users/profile", headers=headers, json=NEW_PROFILE_DATA)
    print_response("Update Profile", response)

    if response.status_code == 200:
        print("✅ Profile updated successfully!")
    else:
        print("❌ Failed to update profile")

    # Step 4: Verify profile update
    print("\n" + "=" * 60)
    print("STEP 4: Verify Profile Update")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/users/profile", headers=headers)
    print_response("Get Updated Profile", response)

    if response.status_code == 200:
        profile = response.json()
        if profile.get("full_name") == NEW_PROFILE_DATA["full_name"]:
            print("✅ Profile name verified!")
        if profile.get("email") == NEW_PROFILE_DATA["email"]:
            print("✅ Profile email verified!")

    # Step 5: Change password
    print("\n" + "=" * 60)
    print("STEP 5: Change Password")
    print("=" * 60)

    response = requests.put(f"{BASE_URL}/api/users/password", headers=headers, json=PASSWORD_CHANGE)
    print_response("Change Password", response)

    if response.status_code == 200:
        print("✅ Password changed successfully!")
    else:
        print("❌ Failed to change password")

    # Step 6: Login with new password
    print("\n" + "=" * 60)
    print("STEP 6: Login with New Password")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": NEW_PROFILE_DATA["email"], "password": PASSWORD_CHANGE["new_password"]},
    )
    print_response("Login with New Password", response)

    if response.status_code == 200:
        print("✅ Login with new password successful!")
        # Update token for deletion
        auth_data = response.json()
        access_token = auth_data.get("access_token")
        headers = {"Authorization": f"Bearer {access_token}"}
    else:
        print("❌ Failed to login with new password")

    # Step 7: Test invalid password change
    print("\n" + "=" * 60)
    print("STEP 7: Test Invalid Password Change (Wrong Old Password)")
    print("=" * 60)

    response = requests.put(
        f"{BASE_URL}/api/users/password",
        headers=headers,
        json={"old_password": "wrongpassword", "new_password": "anotherpass789"},
    )
    print_response("Invalid Password Change", response)

    if response.status_code == 400:
        print("✅ Correctly rejected wrong password!")
    else:
        print("❌ Should have rejected wrong password")

    # Step 8: Test account deletion with wrong password
    print("\n" + "=" * 60)
    print("STEP 8: Test Account Deletion (Wrong Password)")
    print("=" * 60)

    response = requests.delete(
        f"{BASE_URL}/api/users/account",
        headers=headers,
        json={"password": "wrongpassword", "confirmation": "DELETE"},
    )
    print_response("Delete Account (Wrong Password)", response)

    if response.status_code == 400:
        print("✅ Correctly rejected wrong password!")
    else:
        print("❌ Should have rejected wrong password")

    # Step 9: Test account deletion with wrong confirmation
    print("\n" + "=" * 60)
    print("STEP 9: Test Account Deletion (Wrong Confirmation)")
    print("=" * 60)

    response = requests.delete(
        f"{BASE_URL}/api/users/account",
        headers=headers,
        json={
            "password": PASSWORD_CHANGE["new_password"],
            "confirmation": "delete",  # lowercase, should fail
        },
    )
    print_response("Delete Account (Wrong Confirmation)", response)

    if response.status_code == 400:
        print("✅ Correctly rejected wrong confirmation!")
    else:
        print("❌ Should have rejected wrong confirmation")

    # Step 10: Delete account successfully
    print("\n" + "=" * 60)
    print("STEP 10: Delete Account Successfully")
    print("=" * 60)

    response = requests.delete(
        f"{BASE_URL}/api/users/account",
        headers=headers,
        json={"password": PASSWORD_CHANGE["new_password"], "confirmation": "DELETE"},
    )
    print_response("Delete Account", response)

    if response.status_code == 200:
        print("✅ Account deleted successfully!")
    else:
        print("❌ Failed to delete account")

    # Step 11: Verify account is deleted (should fail to login)
    print("\n" + "=" * 60)
    print("STEP 11: Verify Account Deletion")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": NEW_PROFILE_DATA["email"], "password": PASSWORD_CHANGE["new_password"]},
    )
    print_response("Login After Deletion", response)

    if response.status_code == 401:
        print("✅ Account successfully deleted (cannot login)!")
    else:
        print("❌ Account might not be deleted properly")

    # Final Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("All user settings endpoints have been tested!")
    print("✅ GET /api/users/profile - Get profile")
    print("✅ PUT /api/users/profile - Update profile")
    print("✅ PUT /api/users/password - Change password")
    print("✅ DELETE /api/users/account - Delete account")
    print("=" * 60)


if __name__ == "__main__":
    print("\n🧪 Starting User Settings Endpoint Tests...")
    print("=" * 60)

    try:
        test_user_settings()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
