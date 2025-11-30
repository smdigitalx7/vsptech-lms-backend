import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    """Test user creation."""
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "newuser@example.com",
            "password": "testpassword123",
            "full_name": "New User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "user_id" in data


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    """Test listing users."""
    # Create a user first
    await client.post(
        "/api/v1/users",
        json={
            "email": "list@example.com",
            "password": "testpassword123",
            "full_name": "List User"
        }
    )

    response = await client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient):
    """Test getting a user by ID."""
    # Create a user first
    create_response = await client.post(
        "/api/v1/users",
        json={
            "email": "get@example.com",
            "password": "testpassword123",
            "full_name": "Get User"
        }
    )
    user_id = create_response.json()["user_id"]

    # Get the user
    response = await client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["email"] == "get@example.com"


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient):
    """Test updating a user."""
    # Create a user first
    create_response = await client.post(
        "/api/v1/users",
        json={
            "email": "update@example.com",
            "password": "testpassword123",
            "full_name": "Update User"
        }
    )
    user_id = create_response.json()["user_id"]

    # Update the user
    response = await client.put(
        f"/api/v1/users/{user_id}",
        json={
            "full_name": "Updated Name"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient):
    """Test deleting a user."""
    # Create a user first
    create_response = await client.post(
        "/api/v1/users",
        json={
            "email": "delete@example.com",
            "password": "testpassword123",
            "full_name": "Delete User"
        }
    )
    user_id = create_response.json()["user_id"]

    # Delete the user
    response = await client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204

    # Verify user is deleted
    get_response = await client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404

