from django.urls import reverse
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.test import APITestCase


class TestBase(APITestCase):

    DATE_FORMAT='%Y-%m-%d'

    def generate_phone(self):
        return'189%s' % get_random_string(8, allowed_chars='1234567890')

    def register_user(self, phone=None, password=None):
        register_url = reverse('user-register')
        data = {'phone': phone or self.generate_phone(),
                'code': '111111',
                'password': password or 'mockedpw'}
        resp = self.client.post(register_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        token = resp.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        return resp.data['user_id']

    def _date_to_str(self, date_v):
        return date_v.strftime(self.DATE_FORMAT)

