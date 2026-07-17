from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
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
