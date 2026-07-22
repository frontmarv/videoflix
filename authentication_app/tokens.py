from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Token generator for account activation links.

    Generates secure, one-time-use tokens for account activation emails.
    Tokens include user PK, timestamp, activation status, and password
    change timestamp to ensure they are unique per user state.
    """

    def _make_hash_value(self, user, timestamp):
        """Generate token hash value including user state information.

        Args:
            user: User instance
            timestamp: Token generation timestamp

        Returns:
            str: Hash value incorporating user attributes for token uniqueness
        """
        return str(user.pk) + str(timestamp) + str(user.is_activated) + str(user.password_changed_at)


account_activation_token = AccountActivationTokenGenerator()
