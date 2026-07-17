from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    confirmed_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'confirmed_password']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirmed_password']:
            raise serializers.ValidationError(
                {'confirmed_password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirmed_password')
        return CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
        )


class LoginSerializer(serializers.Serializer):
    """Serializer for user login with email and password.

    Validates credentials and returns user object and JWT token pair.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate email and password credentials.

        Uses Django's authenticate() function to validate against the
        CustomUser model using email as USERNAME_FIELD.

        Args:
            attrs: Dictionary containing email and password

        Returns:
            dict: attrs with added 'user' key if credentials valid

        Raises:
            ValidationError: If credentials are invalid
        """
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError(
                'Invalid email or password.'
            )

        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        """Generate JWT tokens for authenticated user.

        Args:
            validated_data: Dictionary with 'user' key

        Returns:
            dict: Dictionary with 'user' and token pair
        """
        user = validated_data.get('user')
        refresh = RefreshToken.for_user(user)

        return {
            'user': user,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
