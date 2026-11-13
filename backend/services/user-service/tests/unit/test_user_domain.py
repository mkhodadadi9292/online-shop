"""Unit tests for the pure domain layer."""

from __future__ import annotations

import pytest

from user_service.domain.user import Email, InvalidEmailError, User


class TestEmail:
    def test_normalizes_email(self):
        assert Email("  Foo@Bar.COM ").value == "foo@bar.com"

    def test_rejects_email_without_at(self):
        with pytest.raises(InvalidEmailError):
            Email("not-an-email")

    def test_rejects_email_without_domain_dot(self):
        with pytest.raises(InvalidEmailError):
            Email("foo@localhost")


class TestUser:
    def test_create_generates_id_and_normalizes_email(self):
        user = User.create("Foo@Bar.com", "hashed", "Foo Bar")
        assert user.id
        assert user.email == "foo@bar.com"
        assert user.hashed_password == "hashed"
        assert user.full_name == "Foo Bar"

    def test_create_raises_on_invalid_email(self):
        with pytest.raises(InvalidEmailError):
            User.create("bad", "hashed")
