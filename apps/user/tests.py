from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from rest_framework_simplejwt.tokens import AccessToken

from apps.user.models import UserProfile


class UserProfileAPITest(TestCase):
    def test_create_profile_with_post(self):
        token = "test-token"
        response = self.client.post(
            reverse("user-profile"),
            data={
                "employee_id": "27",
                "email": "test@example.com",
                "company": "Join Venture AI",
                "user_id": "1001",
                "login": "test@example.com",
                "user_type": "employee",
                "company_id": "27",
                "raw_data": {"foo": "bar"},
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 200)
        profile = UserProfile.objects.get(employee_id="27")
        self.assertEqual(profile.email, "test@example.com")
        self.assertEqual(profile.company, "Join Venture AI")
        self.assertEqual(profile.access_token, token)
        self.assertEqual(profile.user_id, "1001")

    def test_update_profile_with_post(self):
        UserProfile.objects.create(
            uid="user-27",
            employee_id="27",
            email="old@example.com",
            company="Old Company",
            access_token="old-token",
        )

        token = AccessToken()
        token["uid"] = "user-27"
        token["email"] = "old@example.com"
        response = self.client.post(
            reverse("user-profile"),
            data={
                "employee_id": "27",
                "email": "updated@example.com",
                "company": "Join Venture AI",
                "user_id": "1001",
                "login": "test@example.com",
                "user_type": "employee",
                "company_id": "27",
                "raw_data": {"foo": "bar"},
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 200)
        profile = UserProfile.objects.get(employee_id="27")
        self.assertEqual(profile.email, "updated@example.com")
        self.assertEqual(profile.company, "Join Venture AI")
        self.assertEqual(profile.access_token, "old-token")

    def test_update_profile_with_multipart_avatar(self):
        profile = UserProfile.objects.create(
            uid="user-27",
            employee_id="27",
            email="old@example.com",
            company="Old Company",
            access_token="old-token",
        )

        token = AccessToken()
        token["uid"] = profile.uid
        token["email"] = profile.email

        avatar_file = SimpleUploadedFile(
            "avatar.jpg",
            b"fake-image-content",
            content_type="image/jpeg",
        )

        response = self.client.post(
            reverse("user-profile"),
            data={
                "employee_id": "27",
                "email": "old@example.com",
                "company": "Old Company",
                "avatar": avatar_file,
            },
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertTrue(profile.avatar.name)
        self.assertIn("avatar", profile.avatar.name)
        self.assertTrue(profile.avatar.name.endswith(".jpg"))

    def test_update_profile_with_profile_avatar_alias(self):
        profile = UserProfile.objects.create(
            uid="user-27",
            employee_id="27",
            email="old@example.com",
            company="Old Company",
            access_token="old-token",
        )

        token = AccessToken()
        token["uid"] = profile.uid
        token["email"] = profile.email

        avatar_file = SimpleUploadedFile(
            "avatar.jpg",
            b"fake-image-content",
            content_type="image/jpeg",
        )

        response = self.client.post(
            reverse("user-profile"),
            data={
                "employee_id": "27",
                "email": "old@example.com",
                "company": "Old Company",
                "profile_avatar": avatar_file,
            },
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertTrue(profile.avatar.name)
        self.assertIn("avatar", profile.avatar.name)
        self.assertTrue(profile.avatar.name.endswith(".jpg"))

    def test_update_profile_with_same_filename_avatar_does_not_rewrite(self):
        profile = UserProfile.objects.create(
            uid="user-27",
            employee_id="27",
            email="old@example.com",
            company="Old Company",
            access_token="old-token",
        )

        profile.avatar.name = "users/avatars/avatar.jpg"
        profile.save(update_fields=["avatar"])

        token = AccessToken()
        token["uid"] = profile.uid
        token["email"] = profile.email

        avatar_file = SimpleUploadedFile(
            "avatar.jpg",
            b"fake-image-content",
            content_type="image/jpeg",
        )

        response = self.client.post(
            reverse("user-profile"),
            data={
                "employee_id": "27",
                "email": "old@example.com",
                "company": "Old Company",
                "profile_avatar": avatar_file,
            },
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json().get("message"),
            "No changes detected. Profile remains unchanged.",
        )
        profile.refresh_from_db()
        self.assertEqual(profile.avatar.name, "users/avatars/avatar.jpg")

    def test_get_profile_by_access_token(self):
        token = "test-token"
        UserProfile.objects.create(
            employee_id="27",
            email="test@example.com",
            company="Join Venture AI",
            access_token=token,
        )

        response = self.client.get(
            reverse("user-profile"),
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("data", {}).get("access_token"), token)
        self.assertEqual(response.json().get("data", {}).get("employee_id"), "27")

    def test_profile_requires_access_token(self):
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json().get("message"),
            "Unauthenticated. Access token is required.",
        )

    @patch("apps.user.views.fetch_graph_profile")
    @patch("apps.user.views.verify_microsoft_token")
    def test_sso_login_allows_public_post(self, mock_verify, mock_fetch_graph):
        mock_verify.return_value = {
            "oid": "user-27",
            "preferred_username": "test@example.com",
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_fetch_graph.return_value = {"displayName": "Test User"}

        response = self.client.post(
            reverse("sso-login"),
            data={"access_token": "fake-token"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json().get("data", {}))
        self.assertIn("refresh_token", response.json().get("data", {}))
