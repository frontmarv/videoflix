import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email as primary authentication field.

    Extends Django's AbstractBaseUser to provide email-based authentication
    instead of the default username. Tracks account activation status and
    password change timestamps for security purposes.

    Attributes:
        id: Unique identifier (UUID).
        email: User email address, used as USERNAME_FIELD.
        username: Optional username, defaults to email if not provided.
        is_activated: Whether the user's email has been activated.
        is_active: Whether the user account is active.
        is_staff: Whether the user has staff permissions.
        date_joined: Timestamp when user account was created.
        password_changed_at: Timestamp of last password change.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255, blank=True)
    is_activated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    password_changed_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    class Meta:
        """Model metadata for CustomUser."""
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']

    def __str__(self):
        return self.email
