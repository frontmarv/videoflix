from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RegisterSerializer
from ..tokens import account_activation_token

User = get_user_model()


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        activation_path = reverse(
            'activate', kwargs={'uidb64': uidb64, 'token': token})
        activation_link = request.build_absolute_uri(activation_path)

        send_mail(
            subject='Activate your Videoflix account',
            message=(
                f'Hi {user.email},\n\n'
                f'Please activate your account by clicking the link below:\n\n'
                f'{activation_link}\n\n'
                f'This link expires in 24 hours.\n'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            {'detail': 'Registration successful. Please check your email to activate your account.'},
            status=status.HTTP_201_CREATED,
        )


class ActivateAccountView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Invalid activation link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not account_activation_token.check_token(user, token):
            return Response(
                {'detail': 'Activation link is invalid or has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_activated:
            return Response(
                {'detail': 'Account is already activated.'},
                status=status.HTTP_200_OK,
            )

        user.is_activated = True
        user.save()

        return Response(
            {'detail': 'Account activated successfully.'},
            status=status.HTTP_200_OK,
        )
