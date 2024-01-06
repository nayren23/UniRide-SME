# import pytest
# from unittest.mock import MagicMock, patch, ANY, Mock
# from uniride_sme.service.documents_service import document_user, document_to_verify, document_check
# from uniride_sme.connect_pg import connect
# from uniride_sme.utils.exception.documents_exceptions import DocumentsTypeException
# from datetime import datetime


# @pytest.fixture
# def mock_connect():
#     with patch("uniride_sme.connect_pg.connect") as mock:
#         yield mock


# @pytest.fixture
# def mock_get_query():
#     with patch("uniride_sme.connect_pg.get_query") as mock:
#         yield mock


# @pytest.fixture
# def mock_disconnect():
#     with patch("uniride_sme.connect_pg.disconnect") as mock:
#         yield mock


# @pytest.fixture
# def mock_execute_command():
#     with patch("uniride_sme.connect_pg.execute_command") as mock:
#         yield mock


# def test_document_user_valid(mock_connect, mock_get_query, mock_disconnect):
#     user_id = 123
#     mock_document_data = [
#         {"u_id": user_id, "d_license": "license_url", "v_license_verified": True},
#         {"u_id": user_id, "d_id_card": "id_card_url", "v_id_card_verified": False},
#         {"u_id": user_id, "d_school_certificate": "school_certificate_url", "v_school_certificate_verified": True},
#     ]

#     mock_connect.return_value = MagicMock()
#     mock_get_query.return_value = mock_document_data
#     result = document_user(user_id)
#     assert result["user_id"] == user_id
#     assert len(result["documents"]) == len(mock_document_data)

#     mock_disconnect.assert_called_once()


# def test_document_user_no_data(mock_get_query, mock_disconnect):
#     user_id = 456
#     mock_get_query.return_value = []

#     with pytest.raises(DocumentsTypeException):
#         document_user(user_id)

#     mock_disconnect.assert_called_once()


# def test_document_check(mock_connect, mock_disconnect, mock_execute_command):
#     data = {
#         "user_id": 123,
#         "document": {
#             "type": "license",
#             "status": "verified",
#         },
#     }

#     with patch("uniride_sme.connect_pg.connect", return_value=mock_connect):
#         result = document_check(data)

#     mock_connect.return_value = MagicMock()

#     expected_query = """
#         UPDATE uniride.ur_document_verification
#         SET v_license_verified = %s
#         WHERE u_id = %s
#     """
#     mock_execute_command.assert_called_once_with(mock_connect, expected_query, ("verified", 123))

#     assert result == {"message": "DOCUMENT_STATUS_UPDATED"}


# def test_document_check_invalid_document_type(mock_connect):
#     data = {
#         "user_id": 123,
#         "document": {
#             "type": "invalid_type",
#             "status": "verified",
#         },
#     }
#     with pytest.raises(DocumentsTypeException):
#         document_check(data)


# def test_document_to_verify(mock_connect, mock_get_query, mock_disconnect, mock_get_encoded_file):
#     user_id = 123
#     mock_document_data = [
#         (user_id, 456, "Doe", "John", "profile.jpg", datetime(2023, 1, 1), 1, 0, 1),
#     ]

#     mock_connect.return_value = MagicMock()
#     mock_get_query.return_value = mock_document_data

#     mock_get_encoded_file.return_value = "mocked_profile_picture_url"

#     result = document_to_verify()

#     assert len(result) == len(mock_document_data)
#     mock_disconnect.assert_called_once()
#     mock_get_encoded_file.assert_called_with("profile.jpg")
