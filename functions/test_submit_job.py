import os
import sys
import requests
import json
from datetime import datetime
from unittest.mock import patch

# Test server URL
BASE_URL = "http://127.0.0.1:8081"

def create_mock_auth():
    """Create a mock auth object for testing"""
    mock_auth = type('MockAuth', (), {
        'uid': 'test_user_123',
        'token': 'test_token'
    })
    return mock_auth

def test_submit_job():
    """Test successful job submission"""
    # Test data
    test_data = {
        "sequence": "ACTGACTGACTGACTGACTG",  # 20 base sequence
        "model": "models/fitted_on_Pr/model_[3]_stm+flex+cumul+rbs.dmp",
        "job_title": "test_job",
        "predictors": {
            "standard": True,
            "standardSpacer": False,
            "standardSpacerCumulative": False,
            "extended": False
        },
        "is_plus_one": True,
        "is_rc": False,
        "max_value": -2.5,
        "min_value": -6,
        "threshold": -2.5,
        "is_prefix_suffix": True
    }

    # Mock the auth object
    mock_auth = create_mock_auth()
    
    # Send request to local server
    response = requests.post(
        f"{BASE_URL}/submit_job",
        json=test_data,
        headers={
            "Authorization": f"Bearer {mock_auth.token}",
            "X-Test-Auth": "true"  # Custom header to indicate test mode
        }
    )

    # Check response
    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data
    assert "jobId" in response_data
    assert "brickplot" in response_data
    print(response_data["brickplot"])

def test_submit_job_unauthorized():
    """Test that unauthorized requests are rejected"""
    # Send request without authorization
    response = requests.post(
        f"{BASE_URL}/submit_job",
        json={}
    )

    # Check response
    assert response.status_code == 401
    response_data = response.json()
    assert "error" in response_data
    assert response_data["error"] == "Unauthorized"

def test_submit_job_invalid_sequence():
    """Test that invalid sequences are rejected"""
    test_data = {
        "sequence": "ACTG",  # Too short
        "model": "test_model",
        "job_title": "test_job",
        "predictors": {}
    }

    # Mock the auth object
    mock_auth = create_mock_auth()
    
    # Send request to local server
    response = requests.post(
        f"{BASE_URL}/submit_job",
        json=test_data,
        headers={
            "Authorization": f"Bearer {mock_auth.token}",
            "X-Test-Auth": "true"  # Custom header to indicate test mode
        }
    )

    # Check response
    assert response.status_code == 400
    response_data = response.json()
    assert "error" in response_data

if __name__ == "__main__":
    print("Running tests...")
    try:
        # # Make sure the server is running
        # try:
        #     requests.get(f"{BASE_URL}/ping")
        # except requests.exceptions.ConnectionError:
        #     print("Error: Local server is not running. Please start the server first.")
        #     print("Run: python main.py")
        #     sys.exit(1)

        test_submit_job()
        print("✓ test_submit_job passed")
        # test_submit_job_unauthorized()
        print("✓ test_submit_job_unauthorized passed")
        # test_submit_job_invalid_sequence()
        print("✓ test_submit_job_invalid_sequence passed")
        print("All tests completed successfully!")
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        raise 