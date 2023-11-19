import json

from flask import Flask


def test_register(test_client: Flask):
    data = {
        "login": "testuser",
        "firstname": "Test",
        "lastname": "User",
        "student_email": "test@iut.univ-paris8.fr",
        "password": "111AAaa@",
        "password_confirmation": "111AAaa@",
        "gender": "H",
        "phone_number": "123456789",
        "description": "Test Description",
    }
    response = test_client.post("/user/register", data=data)

    assert response.status_code == 200
    assert json.loads(response.data) == {"message": "USER_CREATED_SUCCESSFULLY"}


def test_authenticate(test_client):
    data = {"login": "testuser", "password": "111AAaa@"}

    # Make a POST request to the authentication endpoint
    response = test_client.post("/user/auth", json=data)
    # Check the response status code and JSON content
    assert response.status_code == 200
    assert json.loads(response.data).get("message") == "AUTHENTIFIED_SUCCESSFULLY"


# Test for successful email send
def test_send_email_confirmation_success(test_client, get_token):
    response = test_client.get("/user/email-confirmation", headers={"Authorization": f"Bearer {get_token}"})
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["message"] == "EMAIL_SEND_SUCCESSFULLY"
