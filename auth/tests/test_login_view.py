from django.conf import settings
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.test.client import RequestFactory
from mock import Mock, patch

from auth.forms import LoginForm
from auth.views import Login


class LoginViewTest(TestCase):
    def test_root_should_show_login_template(self):
        request = RequestFactory().get('/')
        response = Login().get(request)
        self.assertEqual('auth/login.html', response.template_name)

    def test_login_should_show_template(self):
        request = RequestFactory().get('/login')
        response = Login().get(request)
        self.assertEqual('auth/login.html', response.template_name)

    def test_login_form_should_be_in_the_view_context(self):
        request = RequestFactory().get('/')
        response = Login().get(request)
        form = response.context_data['login_form']
        self.assertIsInstance(form, LoginForm)

    def test_should_validate_data_from_post(self):
        data = {'username': 'invalid name', 'password': ''}
        request = RequestFactory().post('/', data)
        response = Login().post(request)
        form = response.context_data['login_form']
        self.assertEqual('auth/login.html', response.template_name)
        self.assertIsInstance(form, LoginForm)
        self.assertEqual('invalid name', form.data['username'])

    @patch('requests.post')
    def test_should_return_200_when_user_does_not_exist(self, post):
        data = {'username': 'invalid@email.com', 'password': '123456'}
        request = RequestFactory().post('/', data)
        post.return_value = Mock(status_code=500)
        response = Login().post(request)
        self.assertEqual(200, response.status_code)
        self.assertEqual('auth/login.html', response.template_name)
        error_msg = response.context_data['msg']
        self.assertEqual('User not found', error_msg)

    @patch('requests.post')
    def test_should_send_request_post_to_tsuru_with_args_expected(self, post):
        data = {'username': 'valid@email.com', 'password': '123456'}
        request = RequestFactory().post('/', data)
        expected_url = '%s/users/valid@email.com/tokens' % settings.TSURU_HOST
        Login().post(request)
        self.assertEqual(1, post.call_count)
        post.assert_called_with(expected_url,
                                data='{"password": "123456"}')

    @patch('requests.post')
    def test_should_set_token_in_the_session(self, post):
        data = {'username': 'valid@email.com', 'password': '123456'}
        request = RequestFactory().post('/', data)
        request.session = {}
        text = '{"token": "my beautiful token"}'
        post.return_value = Mock(status_code=200, text=text)
        Login().post(request)
        self.assertEqual('type my beautiful token',
                         request.session["tsuru_token"])

    @patch('requests.post')
    def test_should_set_username_in_the_session(self, post):
        post.return_value = Mock(status_code=200,
                                 text='{"token": "t"}')
        data = {'username': 'valid@email.com', 'password': '123456'}
        request = RequestFactory().post('/', data)
        request.session = {}
        Login.as_view()(request)
        self.assertEqual(data["username"], request.session["username"])

    @patch('requests.post')
    def test_redirect_to_team_creation_when_login_is_successful(self, post):
        data = {'username': 'valid@email.com', 'password': '123456'}
        request = RequestFactory().post('/', data)
        request.session = {}
        text = '{"token": "my beautiful token"}'
        post.return_value = Mock(status_code=200, text=text)
        response = Login().post(request)
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual('/apps', response['Location'])
