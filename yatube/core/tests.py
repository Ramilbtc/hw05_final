from django.test import TestCase, Client


class ViewTestClass(TestCase):
    def setUp(self):
        self.client = Client()

    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)

    def test_error_template(self):
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')
