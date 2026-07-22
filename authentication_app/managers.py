from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """Custom user manager for CustomUser model.

    Provides methods to create regular users and superusers with email
    as the primary username field.
    """

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user.

        Args:
            email: User email address (required)
            password: User password
            **extra_fields: Additional user fields

        Returns:
            CustomUser: Created user instance

        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError('The email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_staff', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser.

        Args:
            email: Superuser email address (required)
            password: Superuser password
            **extra_fields: Additional user fields

        Returns:
            CustomUser: Created superuser instance

        Raises:
            ValueError: If is_superuser is not True
        """
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_activated', True)
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
