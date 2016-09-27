from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.test.client import Client


class TestLoginView(TestCase):
    def create_user(self):
        user = User.objects.create_user(username='Superuser')
        user.set_password('Password')
        user.is_superuser = True
        user.save()
        EmailAddress.objects.create(user=user,
                                    email='superuser@super.com',
                                    primary=True,
                                    verified=True)
        # self.client.login(username='Superuser', password='Password')
        return user

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.user = self.create_user()

    def test_login_mapping_works(self):
        response = self.client.get('/accounts/login/')
        self.assertEquals(response.status_code, 200)

    def test_login_shows_template(self):
        response = self.client.get('/accounts/login/')
        self.assertTemplateUsed(response=response,
                                template_name='account/login.html')

    def test_login(self):
        response = self.client.post(
            '/accounts/login/',
            {'login': 'Superuser', 'password': 'Password'}, follow=True)
        self.assertRedirects(response, '/home/')

    def test_failed_login_with_wrong_password(self):
        response = self.client.post(
            '/accounts/login/',
            {'login': 'Superuser', 'password': 'a'},
            follow=True)

        self.assertContains(
            response=response,
            text="The login and/or password you specified are not correct.",
            status_code=200)

    def test_failed_login_with_wrong_username(self):
        response = self.client.post(
            '/accounts/login/',
            {'login': 'Super', 'password': 'Password'},
            follow=True)
        self.assertContains(
            response=response,
            text="The login and/or password you specified are not correct.",
            status_code=200)

    # @dmkif
    def test_login_if_user_logged_in_with_next(self):
        response = self.client.post(
            '/accounts/login/?next=/useradmin/',
            {'login': 'Superuser', 'password': 'Password'}, follow=True)
        self.assertEquals(response.status_code, 200)

    # @dmkif
    def test_login_if_user_logged_in_without_next(self):
        response = self.client.post(
            '/accounts/login/',
            {'login': 'Superuser', 'password': 'Password'}, follow=True)
        response = self.client.get('/accounts/login/')
        self.assertEquals(response.status_code, 302)

    def test_index_shows_template(self):
        response = self.client.get('/home/')
        self.assertTemplateUsed(response=response,
                                template_name='home/index.html')

    def test_impressum_shows_template(self):
        response = self.client.get('/home/impressum')
        self.assertTemplateUsed(response=response,
                                template_name='home/impressum.html')

    def test_privacypolicy_shows_template(self):
        response = self.client.get('/home/privacy_policy')
        self.assertTemplateUsed(response=response,
                                template_name='home/privacy_policy.html')


"""
class RegisterViewTest(TestCase):

    def create_user(self):
        user = User.objects.create_user('User', 'user@example.com', 'hunter2')
        user.save()
        return user

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.user = self.create_user()

class LogoutViewTest(TestCase):
    pass
"""
