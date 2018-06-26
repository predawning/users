from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from .utils import TestBase

UserModel = get_user_model()


class UserTests(TestBase):

    def test_register(self):
        url = reverse('user-register')
        # invalid phone
        data = {'phone': '123'}
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['error_code'], 'serializer_validation_error')
        invalid_phone = _('This value does not match the required pattern.')
        self.assertEqual(resp.data['err_fields'], {'phone': [invalid_phone]})

        # ask for a code
        data = {'phone': self.generate_phone()}
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # missing password
        data['code'] = 'invaid'
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['error_code'], 'serializer_validation_error')
        self.assertEqual(resp.data['err_fields'],
                         {'password': [_('This field is required.')]})

        # invalid verification code
        data['password'] = 'mockedpw'
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['error_code'], 'phone_verification_error')

        data['code'] = '111111'
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('user_id', resp.data)
        self.assertEqual(len(resp.data['token']), 40)

        # try register again
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(resp.data['error_code'], 'phone_registered')

    def test_password_login(self):
        url = reverse('password-login')
        # invalid phone
        data = {'phone': '123'}
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['error_code'], 'serializer_validation_error')
        invalid_phone = _('This value does not match the required pattern.')
        self.assertEqual(resp.data['err_fields'],
                         {'phone': [invalid_phone],
                          'password': [_('This field is required.')]})

        pw = 'mockedpw'
        data = {'phone': self.generate_phone(),
                'password': pw}
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['error_code'], 'phone_unregistered')

        # inactive user
        uid = self.register_user(data['phone'], password=pw)
        user = UserModel.objects.get(id=uid)
        user.is_active = False
        user.password = ''
        user.save()
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['error_code'], 'account_inactive')

        # user without no password
        user.is_active = True
        user.save()
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['error_code'], 'password_not_exist')

        # success login
        user.set_password(pw)
        user.save()
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['user_id'], uid)
        self.assertEqual(len(resp.data['token']), 40)

        # invalid password
        data['password'] = 'invalidpw'
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['error_code'], 'incorrect_password')

    def test_phone_code_login(self):
        url = reverse('user-login')
        # invalid phone
        data = {'phone': '123'}
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['error_code'], 'serializer_validation_error')
        invalid_phone = _('This value does not match the required pattern.')
        self.assertEqual(resp.data['err_fields'], {'phone': [invalid_phone]})

        # inactive user
        data = {'phone': self.generate_phone()}
        uid = self.register_user(data['phone'])
        user = UserModel.objects.get(id=uid)
        user.is_active = False
        user.password = ''
        user.save()
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['error_code'], 'account_inactive')

        # ask for code
        user.is_active = True
        user.save()
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # invalid verification code
        data['code'] = 'wrong'
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['error_code'], 'phone_verification_error')

        # success login
        data['code'] = '111111'
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['user_id'], uid)
        self.assertEqual(len(resp.data['token']), 40)

    def test_logout(self):
        url = reverse('user-logout')
        # Unauthenticated
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # login and try logout
        self.register_user()
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_user_details(self):
        url = reverse('user-details')
        # Unauthenticated
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Login and verify user details
        phone = self.generate_phone()
        self.register_user(phone=phone)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['phone'], phone)
