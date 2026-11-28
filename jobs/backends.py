from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class UsernameOrEmailBackend(ModelBackend):
    """Authenticate a user with either their username or email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or password is None:
            return None

        identifier = username.strip()
        if not identifier:
            return None

        user = User.objects.filter(username=identifier).first()
        if user is None:
            user = User.objects.filter(email__iexact=identifier).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
