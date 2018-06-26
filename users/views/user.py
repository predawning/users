from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from . import errors
from .base import UnauthenticatedAPIView
from .base import AuthenticatedAPIView
from sms import send_login_code, send_register_code, send_password_change_code
from sms import verify_login_code, verify_register_code, verify_password_change_code
from sms import PHONE_REGEX
from copy import deepcopy

UserModel = get_user_model()

phone_field = serializers.RegexField(PHONE_REGEX, required=True,
                                     help_text='Chinese mobile number, like 18600001111')

pw_field = serializers.CharField(
    validators=[validate_password],
    help_text='Password must contain at least 8 characters - '
              'with at least 1 latter.')

pw_field_non_required = serializers.CharField(
    validators=[validate_password],
    required=False)


def kick_out_user(user):
    try:
        # kick out user once reset password
        token = Token.objects.get(user_id=user)
        token.delete()
    except Token.DoesNotExist:
        pass


class RegisterSerializer(serializers.Serializer):
    phone = phone_field
    code_h = 'Requried in Step2, user received the code and use it to register.'
    code = serializers.CharField(required=False, allow_blank=True,
                                 help_text=code_h)
    password = serializers.CharField(validators=[validate_password],
                                     required=False, allow_blank=True,
                                     help_text='Required in Step2.')


class RegisterStep2Serializer(serializers.Serializer):
    phone = phone_field
    code = serializers.CharField(max_length=6)
    password = pw_field


class RegisterView(UnauthenticatedAPIView):
    """
    Register with phone.

    This include 2 steps:

        1. Client submits a phone to get a verification code.
            1) if no verified user with this phone - create new user
            2) send a verification code

        2. User received the code, use phone and code to register.
            Required fields: phone, code, password
            1) verify phone & code
            2) mark user as verified
            3) return user id and token

    Possible errors:
        SerializerValidationError
        PhoneRegistered
        PhoneVerificationSendFailed
        PhoneVerificationError
    """
    serializer_class = RegisterSerializer
    model = UserModel

    def get_serializer_class(self):
        if self.request.method == 'POST':
            data = getattr(self.request, 'data', self.kwargs)
            if data.get('code'):
                return RegisterStep2Serializer
        return super(RegisterView, self).get_serializer_class()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            raise errors.SerializerValidationError(serializer.errors)

        phone = serializer.data['phone']
        if self.model.objects.filter(phone=phone, verified=True).exists():
            raise errors.PhoneRegistered()

        code = serializer.data.get('code', None)
        if not code:
            # Step1: send verify code to phone
            succeed, err_msg = send_register_code(phone)
            if not succeed:
                raise errors.PhoneVerificationSendFailed(msg=err_msg)
            return Response(status=status.HTTP_200_OK)
        else:
            # Step2: register with phone & code
            succeed, err_msg = verify_register_code(phone, code)
            if not succeed:
                raise errors.PhoneVerificationError(reason=err_msg)

            # get phone related user
            try:
                user = self.model.objects.get(phone=phone)
            except self.model.DoesNotExist:
                user = self.model.objects.create_by_phone(phone)
            # setup password
            user.set_password(serializer.data['password'])
            # Update login time - will save user in mark_verified
            user.last_login = timezone.now()
            # mark as verified - means the register success done.
            user.mark_verified()

            # create token
            token = Token.objects.create(user=user)
            return Response({'user_id': user.id, 'token': token.key},
                            status=status.HTTP_200_OK)


class BaseLogin(object):
    model = UserModel

    def get_user(self, serializer):
        if not serializer.is_valid():
            raise errors.SerializerValidationError(serializer.errors)

        phone = serializer.data['phone']
        try:
            user = self.model.objects.get(phone=phone, verified=True)
        except self.model.DoesNotExist:
            raise errors.PhoneUnregistered()
        if not user.is_active:
            raise errors.AccountInactive()
        return user

    def login_resp(self, user):
        # Update login time.
        user.last_login = timezone.now()
        token = Token.objects.get_or_create(user=user)[0].key
        return Response({'user_id': user.id,
                         'token': token},
                        status=status.HTTP_200_OK)


class PhoneCodeSerializer(serializers.Serializer):
    phone = deepcopy(phone_field)
    code = serializers.CharField(
        required=False, allow_blank=True,
        help_text="Step 2, user received the code and use it to login.")


class PhoneCodeLoginView(UnauthenticatedAPIView, BaseLogin):
    """
    Login with phone & verification_code.

    This include 2 steps:

        1. Client submits a phone to get a verification code.
        2. User received the code, use phone and code to login.

    Possible errors:
        SerializerValidationError
        PhoneUnregistered
        PhoneVerificationSendFailed
        PhoneVerificationError
    """
    serializer_class = PhoneCodeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        user = self.get_user(serializer)

        phone = serializer.data['phone']
        code = serializer.data.get('code', None)
        if not code:
            # Step1: send verify code to phone
            succeed, err_msg = send_login_code(phone)
            if not succeed:
                raise errors.PhoneVerificationSendFailed(msg=err_msg)
            return Response(status=status.HTTP_200_OK)
        else:
            # Step2: login with phone & code
            succeed, err_msg = verify_login_code(phone, code)
            if not succeed:
                raise errors.PhoneVerificationError(reason=err_msg)
            return self.login_resp(user)


class PasswordLoginSerializer(serializers.Serializer):
    """PasswordLogin serializer."""
    phone = deepcopy(phone_field)
    password = serializers.CharField()


class PasswordLoginView(UnauthenticatedAPIView, BaseLogin):
    """
    Login with phone + password.
    Return user id and token.

    Possible errors:
        SerializerValidationError
        PhoneUnregistered
        PasswordNotExist
        IncorrectPassword
    """
    serializer_class = PasswordLoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        user = self.get_user(serializer)

        # check password
        if not user.password:
            raise errors.PasswordNotExist()
        if not user.check_password(serializer.data['password']):
            raise errors.IncorrectPassword()
        return self.login_resp(user)


class LogoutSerializer(serializers.Serializer):
    pass


class SetPasswordByOldPasswordSerializer(serializers.Serializer):
    old_password = deepcopy(pw_field)
    new_password = deepcopy(pw_field)


class SetPasswordByPhoneCodeSerializer(serializers.Serializer):
    code = serializers.CharField(required=False)
    new_password = deepcopy(pw_field_non_required)


class SetPasswordByPhoneCodeSteop2Serializer(serializers.Serializer):
    """SetPassword serializer."""
    code = serializers.CharField(required=True)
    new_password = deepcopy(pw_field)


class SetPasswordByPhoneCodeUnauthSerializer(serializers.Serializer):
    phone = deepcopy(phone_field)
    code = serializers.CharField(required=False)
    new_password = deepcopy(pw_field_non_required)


class SetPasswordByPhoneCodeUnauthSteop2Serializer(serializers.Serializer):
    """SetPassword serializer."""
    phone = deepcopy(phone_field)
    code = serializers.CharField(required=True)
    new_password = deepcopy(pw_field)


class SetPasswordByPhoneCodeView(AuthenticatedAPIView):
    serializer_class = SetPasswordByPhoneCodeSerializer

    def get_serializer_class(self):
        if self.request.method == "POST":
            data = getattr(self.request, 'data', self.kwargs)
            if data.get('code'):
                return SetPasswordByPhoneCodeSteop2Serializer
        return super().get_serializer_class()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            raise errors.SerializerValidationError(serializer.errors)

        user = request.user
        if not user.is_active:
            raise errors.AccountInactive()

        v_code = serializer.data.get('code', None)

        if not v_code:
            # step 1: request code
            succeed, err_msg = send_password_change_code(user.phone)
            if not succeed:
                raise errors.PhoneVerificationSendFailed()

            return Response(status=status.HTTP_200_OK)
        else:
            # step 2: save password
            succeed, err_msg = verify_password_change_code(user.phone, v_code)
            if not succeed:
                raise errors.PhoneVerificationError()
            new_password = serializer.data['new_password']
            user.set_password(new_password)
            user.save()
            kick_out_user(user)
            token = Token.objects.get_or_create(user=user)[0].key

            return Response({'user_id': user.id,
                             'token': token
                             },
                            status=status.HTTP_200_OK)


class SetPasswordByPhoneCodeUnauthView(UnauthenticatedAPIView):
    serializer_class = SetPasswordByPhoneCodeUnauthSerializer

    def get_serializer_class(self):
        if self.request.method == "POST":
            data = getattr(self.request, 'data', self.kwargs)
            if data.get('code'):
                return SetPasswordByPhoneCodeUnauthSteop2Serializer
        return super().get_serializer_class()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            raise errors.SerializerValidationError(serializer.errors)

        phone = serializer.data.get('phone')
        user = UserModel.objects.get(phone=phone)
        if not user.is_active:
            raise errors.AccountInactive()

        v_code = serializer.data.get('code', None)

        if not v_code:
            # step 1: request code
            succeed, err_msg = send_password_change_code(user.phone)
            if not succeed:
                raise errors.PhoneVerificationSendFailed()

            return Response(status=status.HTTP_200_OK)
        else:
            # step 2: save password
            succeed, err_msg = verify_password_change_code(user.phone, v_code)
            if not succeed:
                raise errors.PhoneVerificationError()
            new_password = serializer.data['new_password']
            if user.check_password(new_password):
                raise errors.InvalidNewPasswordSameAsOldPassword()
            user.set_password(new_password)
            user.save()
            kick_out_user(user)
            token = Token.objects.get_or_create(user=user)[0].key

            return Response({'user_id': user.id,
                             'token': token
                             },
                            status=status.HTTP_200_OK)


class SetPasswordByOldPasswordView(AuthenticatedAPIView):
    serializer_class = SetPasswordByOldPasswordSerializer

    def post(self, request):
        print('request.data', request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            raise errors.SerializerValidationError(serializer.errors)

        user = request.user
        old_password = serializer.data.get('old_password', None)
        new_password = serializer.data.get('new_password', None)

        if old_password == new_password:
            raise errors.InvalidNewPasswordSameAsOldPassword()

        if not user.check_password(old_password):
            raise errors.IncorrectPassword()

        if not user.is_active:
            raise errors.AccountInactive()

        user.set_password(new_password)
        user.save()
        kick_out_user(user)
        token = Token.objects.get_or_create(user=user)[0].key

        return Response({'user_id': user.id,
                         'token': token
                         },
                        status=status.HTTP_200_OK)


class LogoutView(AuthenticatedAPIView):
    """User logout view.

    Possible errors:
        NotExistError
    """
    serializer_class = LogoutSerializer

    def post(self, request):
        if request.auth:
            auth_token = request.auth
        else:
            raise errors.NotExistError(msg='request.auth')

        auth_token.delete()
        return Response(status=status.HTTP_200_OK)


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('id', 'phone')


class UserDetailsView(AuthenticatedAPIView, RetrieveAPIView):
    """
    User Detail View.
    """
    serializer_class = UserDetailsSerializer
    action = 'retrieve'

    def get_object(self):
        return self.request.user
