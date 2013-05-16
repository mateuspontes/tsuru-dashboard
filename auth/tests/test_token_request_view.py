from django.test import TestCase
from django.core.urlresolvers import reverse


class TokeRequestViewTest(TestCase):
    def test_get(self):
        response = self.client.get(reverse('token-request'))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed('auth/token_request.html')
