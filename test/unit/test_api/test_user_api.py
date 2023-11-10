import json
import pytest
from flask import Flask
from uniride_sme import app

# Import your UserBO and other necessary modules for testing

# Create a test Flask app for testing
@pytest.fixture
def test_app():
    app.config['TESTING'] = True
    return app.test_client()

# Define a test for the user registration endpoint
def test_register(test_app):
    # Prepare test data
    data = {
        'login': 'testuser',
        'firstname': 'Test',
        'lastname': 'User',
        'student_email': 'test@example.com',
        'password': 'testpassword',
        'password_confirmation': 'testpassword',
        'gender': 'Male',
        'phone_number': '1234567890',
        'description': 'Test Description'
    }

    # Make a POST request to the registration endpoint
    response = test_app.post('/user/register', data=data)

    # Check the response status code and JSON content
    assert response.status_code == 200
    assert json.loads(response.data) == {'message': 'USER_CREATED_SUCCESSFULLY'}

    # Add assertions to check if the user was actually created in the database
    # You might need to query your database to verify the user's existence

# Similar test functions can be defined for other endpoints (authentificate, save_pfp, etc.)

# Define a test for the user authentication endpoint
def test_authenticate(test_app):
    # Prepare test data
    data = {
        'login': 'testuser',
        'password': 'testpassword'
    }

    # Make a POST request to the authentication endpoint
    response = test_app.post('/user/auth', json=data)

    # Check the response status code and JSON content
    assert response.status_code == 200
    assert json.loads(response.data).get('message') == 'AUTHENTIFIED_SUCCESSFULLY'

    # Add assertions to verify the JWT token and user authentication

# You can define similar tests for other endpoints like save_pfp, save_license, save_id_card, etc.

# Define test functions for other endpoints in a similar manner

# Run the tests with pytest by executing pytest in your terminal
