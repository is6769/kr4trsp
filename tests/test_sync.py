import pytest
from fastapi.testclient import TestClient
from app.main import app, _users_db, _id_seq


@pytest.fixture(autouse=True)
def clear_db():
    _users_db.clear()
    global _id_seq
    _id_seq = iter(range(1, 1000))
    yield
    _users_db.clear()


client = TestClient(app)


class TestUserCreation:

    def test_create_user_success(self):
        user_data = {
            "username": "john_doe",
            "age": 25,
            "email": "john@example.com",
            "password": "securepass123",
            "phone": "+1234567890"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 201
        assert response.json()["username"] == "john_doe"
        assert response.json()["age"] == 25
        assert "id" in response.json()

    def test_create_user_missing_field(self):
        user_data = {
            "username": "jane_doe",
            "age": 30,
            "email": "jane@example.com"
            # Missing password
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 422

    def test_create_user_invalid_age(self):
        user_data = {
            "username": "young_user",
            "age": 18,  # Should be > 18
            "email": "young@example.com",
            "password": "securepass123"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 422

    def test_create_user_invalid_email(self):
        user_data = {
            "username": "invalid_email",
            "age": 25,
            "email": "not-an-email",
            "password": "securepass123"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 422

    def test_create_user_short_password(self):
        user_data = {
            "username": "short_pass",
            "age": 25,
            "email": "short@example.com",
            "password": "short"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 422

    def test_create_user_long_password(self):
        user_data = {
            "username": "long_pass",
            "age": 25,
            "email": "long@example.com",
            "password": "thispasswordistoolong"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 422


class TestUserRetrieval:

    def test_get_user_success(self):
        user_data = {
            "username": "test_user",
            "age": 25,
            "email": "test@example.com",
            "password": "testpass123"
        }
        create_response = client.post("/users", json=user_data)
        user_id = create_response.json()["id"]

        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["username"] == "test_user"
        assert response.json()["id"] == user_id

    def test_get_user_not_found(self):
        response = client.get("/users/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_multiple_users(self):
        users_data = [
            {
                "username": "user1",
                "age": 25,
                "email": "user1@example.com",
                "password": "password1"
            },
            {
                "username": "user2",
                "age": 30,
                "email": "user2@example.com",
                "password": "password2"
            }
        ]

        user_ids = []
        for user_data in users_data:
            response = client.post("/users", json=user_data)
            user_ids.append(response.json()["id"])

        for i, user_id in enumerate(user_ids):
            response = client.get(f"/users/{user_id}")
            assert response.status_code == 200
            assert response.json()["username"] == f"user{i+1}"


class TestUserDeletion:

    def test_delete_user_success(self):
        user_data = {
            "username": "to_delete",
            "age": 25,
            "email": "delete@example.com",
            "password": "deletepass123"
        }
        create_response = client.post("/users", json=user_data)
        user_id = create_response.json()["id"]

        response = client.delete(f"/users/{user_id}")
        assert response.status_code == 204

    def test_delete_user_not_found(self):
        response = client.delete("/users/9999")
        assert response.status_code == 404

    def test_delete_user_twice(self):
        user_data = {
            "username": "delete_twice",
            "age": 25,
            "email": "twice@example.com",
            "password": "twicepass123"
        }
        create_response = client.post("/users", json=user_data)
        user_id = create_response.json()["id"]

        # First deletion should succeed
        response1 = client.delete(f"/users/{user_id}")
        assert response1.status_code == 204

        response2 = client.delete(f"/users/{user_id}")
        assert response2.status_code == 404


class TestCustomExceptions:

    def test_custom_exception_a(self):
        response = client.get("/test-exception-a?trigger=true")
        assert response.status_code == 400
        assert "CustomExceptionA" in response.json()["error_type"]

    def test_custom_exception_b(self):
        response = client.get("/test-exception-b?trigger=true")
        assert response.status_code == 404
        assert "CustomExceptionB" in response.json()["error_type"]

    def test_no_exception_a(self):
        response = client.get("/test-exception-a")
        assert response.status_code == 200

    def test_no_exception_b(self):
        response = client.get("/test-exception-b")
        assert response.status_code == 200


class TestHealthCheck:

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
