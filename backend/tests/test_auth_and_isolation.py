import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.projects.models import Project

User = get_user_model()


@pytest.mark.django_db
def test_signup_and_login_flow():
    client = APIClient()

    # 1. Sign up
    signup_res = client.post(
        "/api/v1/auth/signup/",
        {
            "email": "alice@example.com",
            "password": "strongpassword123",
            "full_name": "Alice Wonderland",
        },
        format="json",
    )
    assert signup_res.status_code == status.HTTP_201_CREATED
    data = signup_res.json()
    assert "token" in data
    assert data["user"]["email"] == "alice@example.com"
    token = data["token"]

    # 2. Get Me
    client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    me_res = client.get("/api/v1/auth/me/")
    assert me_res.status_code == status.HTTP_200_OK
    assert me_res.json()["user"]["email"] == "alice@example.com"

    # 3. Log in with credentials
    client.credentials()  # clear auth
    login_res = client.post(
        "/api/v1/auth/login/",
        {
            "username_or_email": "alice@example.com",
            "password": "strongpassword123",
        },
        format="json",
    )
    assert login_res.status_code == status.HTTP_200_OK
    assert login_res.json()["token"] == token


@pytest.mark.django_db
def test_demo_login():
    client = APIClient()
    res = client.post("/api/v1/auth/demo/")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "token" in data
    assert data["user"]["username"] == "demo_user"


@pytest.mark.django_db
def test_unauthenticated_requests_blocked():
    client = APIClient()
    res = client.get("/api/v1/projects/")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_project_isolation():
    client1 = APIClient()
    client2 = APIClient()

    user1 = User.objects.create_user(username="user1", email="u1@example.com", password="pw1")
    user2 = User.objects.create_user(username="user2", email="u2@example.com", password="pw2")

    from rest_framework.authtoken.models import Token
    token1, _ = Token.objects.get_or_create(user=user1)
    token2, _ = Token.objects.get_or_create(user=user2)

    client1.credentials(HTTP_AUTHORIZATION=f"Token {token1.key}")
    client2.credentials(HTTP_AUTHORIZATION=f"Token {token2.key}")

    # User 1 creates a project
    create_res = client1.post("/api/v1/projects/", {"name": "Secret Project User 1"}, format="json")
    assert create_res.status_code == status.HTTP_201_CREATED
    proj1_id = create_res.json()["id"]

    # User 1 can list their project
    list1 = client1.get("/api/v1/projects/").json()
    assert list1["count"] == 1
    assert list1["results"][0]["id"] == proj1_id

    # User 2 lists projects -> should see 0 projects
    list2 = client2.get("/api/v1/projects/").json()
    assert list2["count"] == 0

    # User 2 tries to directly access User 1's project -> 404
    detail2 = client2.get(f"/api/v1/projects/{proj1_id}/")
    assert detail2.status_code == status.HTTP_404_NOT_FOUND

    # User 2 tries to access User 1's graph -> 404
    graph2 = client2.get(f"/api/v1/projects/{proj1_id}/graphs/architecture/")
    assert graph2.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_project_deletion():
    client1 = APIClient()
    client2 = APIClient()

    user1 = User.objects.create_user(username="owner_user", email="owner@example.com", password="pw")
    user2 = User.objects.create_user(username="other_user", email="other@example.com", password="pw")

    from rest_framework.authtoken.models import Token
    token1, _ = Token.objects.get_or_create(user=user1)
    token2, _ = Token.objects.get_or_create(user=user2)

    client1.credentials(HTTP_AUTHORIZATION=f"Token {token1.key}")
    client2.credentials(HTTP_AUTHORIZATION=f"Token {token2.key}")

    # 1. User 1 creates a project
    create_res = client1.post("/api/v1/projects/", {"name": "Project to Delete"}, format="json")
    assert create_res.status_code == status.HTTP_201_CREATED
    proj_id = create_res.json()["id"]

    # 2. User 2 tries to delete User 1's project -> 404 Not Found
    del_res_unauthorized = client2.delete(f"/api/v1/projects/{proj_id}/")
    assert del_res_unauthorized.status_code == status.HTTP_404_NOT_FOUND
    assert Project.objects.filter(id=proj_id).exists()

    # 3. User 1 deletes their own project -> 204 No Content
    del_res = client1.delete(f"/api/v1/projects/{proj_id}/")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT
    assert not Project.objects.filter(id=proj_id).exists()

