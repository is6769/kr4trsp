import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from faker import Faker
from app.main import app, _users_db


fake = Faker()


@pytest.fixture(autouse=True)
def clear_db():
    _users_db.clear()
    yield
    _users_db.clear()


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


class TestAsyncUserCreation:

    @pytest.mark.asyncio
    async def test_create_user_success(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False),
            "phone": fake.phone_number()
        }
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 201
        assert response.json()["username"] == user_data["username"]
        assert response.json()["age"] == user_data["age"]
        assert "id" in response.json()

    @pytest.mark.asyncio
    async def test_create_multiple_users(self, async_client):
        for _ in range(3):
            user_data = {
                "username": fake.user_name(),
                "age": fake.random_int(min=19, max=80),
                "email": fake.email(),
                "password": fake.password(length=12, special_chars=False)
            }
            response = await async_client.post("/users", json=user_data)
            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_user_boundary_age_19(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": 19,
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False)
        }
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_user_boundary_password_8_chars(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": "abcdefgh"
        }
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_user_boundary_password_16_chars(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": "abcdefghijklmnop"
        }
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_user_invalid_age_18(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": 18,
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False)
        }
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_invalid_age_negative(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": -5,
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False)
        }
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_short_password(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": "short"
        }
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_long_password(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": "thisisaverylongpassword"
        }
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": "not-a-valid-email",
            "password": fake.password(length=12, special_chars=False)
        }
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 422


class TestAsyncUserRetrieval:

    @pytest.mark.asyncio
    async def test_get_user_success(self, async_client):
        """Test successful user retrieval"""
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False)
        }
        create_response = await async_client.post("/users", json=user_data)
        user_id = create_response.json()["id"]

        response = await async_client.get(f"/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["id"] == user_id
        assert response.json()["username"] == user_data["username"]

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, async_client):
        response = await async_client.get("/users/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_user_after_creation(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False)
        }
        create_response = await async_client.post("/users", json=user_data)
        assert create_response.status_code == 201

        user_id = create_response.json()["id"]
        get_response = await async_client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == user_id


class TestAsyncUserDeletion:

    @pytest.mark.asyncio
    async def test_delete_user_success(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False)
        }
        create_response = await async_client.post("/users", json=user_data)
        user_id = create_response.json()["id"]

        response = await async_client.delete(f"/users/{user_id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, async_client):
        response = await async_client.delete("/users/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_twice(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False)
        }
        create_response = await async_client.post("/users", json=user_data)
        user_id = create_response.json()["id"]

        # First deletion should succeed
        response1 = await async_client.delete(f"/users/{user_id}")
        assert response1.status_code == 204

        response2 = await async_client.delete(f"/users/{user_id}")
        assert response2.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_then_get_user(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False)
        }
        create_response = await async_client.post("/users", json=user_data)
        user_id = create_response.json()["id"]

        # Delete the user
        await async_client.delete(f"/users/{user_id}")

        response = await async_client.get(f"/users/{user_id}")
        assert response.status_code == 404


class TestAsyncConcurrentOperations:

    @pytest.mark.asyncio
    async def test_create_and_get_user(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False)
        }
        create_response = await async_client.post("/users", json=user_data)
        user_id = create_response.json()["id"]

        get_response = await async_client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == user_id

    @pytest.mark.asyncio
    async def test_create_get_delete_user(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False)
        }
        # Create
        create_response = await async_client.post("/users", json=user_data)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        # Get
        get_response = await async_client.get(f"/users/{user_id}")
        assert get_response.status_code == 200

        # Delete
        delete_response = await async_client.delete(f"/users/{user_id}")
        assert delete_response.status_code == 204

        get_response = await async_client.get(f"/users/{user_id}")
        assert get_response.status_code == 404


class TestAsyncWithFakerData:

    @pytest.mark.asyncio
    async def test_create_user_with_realistic_data(self, async_client):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=19, max=80),
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=False),
            "phone": fake.phone_number()
        }
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_multiple_with_faker(self, async_client):
        created_ids = []
        for _ in range(5):
            user_data = {
                "username": fake.user_name(),
                "age": fake.random_int(min=19, max=80),
                "email": fake.email(),
                "password": fake.password(length=12, special_chars=False)
            }
            response = await async_client.post("/users", json=user_data)
            assert response.status_code == 201
            created_ids.append(response.json()["id"])

        # Verify all were created
        assert len(created_ids) == 5
        assert len(set(created_ids)) == 5
