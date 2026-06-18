from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from feedback.models import FeedbackConfiguration


class SentimentSettingsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='password123',
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_settings_page_uses_persisted_toggle_state(self):
        config = FeedbackConfiguration.get_solo()
        config.auto_analysis_enabled = False
        config.save()

        response = self.client.get(reverse('settings_page') + '#sentiment-analysis')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="autoAnalysisToggle"')
        self.assertNotContains(response, 'id="autoAnalysisToggle"\n                      name="auto_analysis_enabled"\n                      checked', html=False)

    def test_update_sentiment_settings_persists_toggle(self):
        response = self.client.post(
            reverse('update_sentiment_settings'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertFalse(payload['auto_analysis_enabled'])
        self.assertFalse(FeedbackConfiguration.get_solo().auto_analysis_enabled)

        response = self.client.post(
            reverse('update_sentiment_settings'),
            {'auto_analysis_enabled': 'on'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['auto_analysis_enabled'])
        self.assertTrue(FeedbackConfiguration.get_solo().auto_analysis_enabled)
