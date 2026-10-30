from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Client, CustomUser


class SignupTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.payload = {
            'user_type': 'client',
            'user': {
                'username': 'driver',
                'email': 'driver@example.com',
                'password': 'S3cure-pass!',
                'first_name': 'Ali',
                'last_name': 'B',
                'phone_number': '0550000000',
            },
        }

    def test_signup_creates_client(self):
        response = self.client.post('/user/signup', self.payload, format='json')

        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username='driver')
        self.assertTrue(user.check_password('S3cure-pass!'))
        self.assertTrue(Client.objects.filter(user=user).exists())

    def test_signup_rejects_invalid_user_type(self):
        self.payload['user_type'] = 'nobody'
        response = self.client.post('/user/signup', self.payload, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(CustomUser.objects.exists())

    def test_signup_rejects_duplicate_email(self):
        self.client.post('/user/signup', self.payload, format='json')
        self.payload['user']['username'] = 'other'
        response = self.client.post('/user/signup', self.payload, format='json')

        self.assertEqual(response.status_code, 400)


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            username='driver', email='driver@example.com', password='S3cure-pass!'
        )

    def login(self, password='S3cure-pass!'):
        return self.client.post('/user/login', {'username': 'driver', 'password': password}, format='json')

    def test_login_returns_token(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['token'], Token.objects.get(user=self.user).key)
        self.assertEqual(response.data['user']['email'], 'driver@example.com')

    def test_login_rejects_bad_credentials(self):
        self.assertEqual(self.login('wrong').status_code, 401)
        response = self.client.post('/user/login', {'username': 'ghost', 'password': 'x'}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_token_from_login_authenticates_requests(self):
        token = self.login().data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.get('/user/get_user_info')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'driver')

    def test_get_user_info_requires_auth(self):
        self.assertIn(self.client.get('/user/get_user_info').status_code, (401, 403))

    def test_change_password(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.login().data["token"]}')

        bad = self.client.post('/user/change_password', {'old_password': 'nope', 'new_password': 'x'}, format='json')
        ok = self.client.post(
            '/user/change_password', {'old_password': 'S3cure-pass!', 'new_password': 'N3w-pass!'}, format='json'
        )

        self.assertEqual(bad.status_code, 400)
        self.assertEqual(ok.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('N3w-pass!'))

    def test_logout_revokes_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.login().data["token"]}')

        self.assertEqual(self.client.post('/user/logout').status_code, 200)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_get_user_by_id(self):
        response = self.client.get(f'/user/getUser/{self.user.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'driver')
        self.assertEqual(self.client.get('/user/getUser/9999/').status_code, 404)
