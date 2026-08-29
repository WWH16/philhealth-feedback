import json
from unittest.mock import patch

from django.test import TestCase

from .models import FeedbackConfiguration, FeedbackEntry


class SubmitFeedbackAutoAnalysisTests(TestCase):
    def _submit(self, payload):
        return self.client.post(
            '/submit/',
            data=json.dumps(payload),
            content_type='application/json',
        )

    @patch('feedback.views.analyze_comment_sentiment', return_value=FeedbackEntry.POSITIVE)
    def test_submit_feedback_runs_analysis_when_enabled(self, mocked_analyze):
        config = FeedbackConfiguration.get_solo()
        config.auto_analysis_enabled = True
        config.save()

        response = self._submit({
            'experience': FeedbackEntry.VERY_SATISFACTORY,
            'comment': 'Excellent service.',
        })

        self.assertEqual(response.status_code, 201)
        entry = FeedbackEntry.objects.get()
        self.assertEqual(entry.sentiment, FeedbackEntry.POSITIVE)
        mocked_analyze.assert_called_once_with('Excellent service.')

    @patch('feedback.views.analyze_comment_sentiment', return_value=FeedbackEntry.POSITIVE)
    def test_submit_feedback_skips_analysis_when_disabled(self, mocked_analyze):
        config = FeedbackConfiguration.get_solo()
        config.auto_analysis_enabled = False
        config.save()

        response = self._submit({
            'experience': FeedbackEntry.SATISFACTORY,
            'comment': 'Please improve wait times.',
        })

        self.assertEqual(response.status_code, 201)
        entry = FeedbackEntry.objects.get()
        self.assertEqual(entry.sentiment, FeedbackEntry.PENDING)
        mocked_analyze.assert_not_called()

    def test_submit_full_csm_form_saves_all_fields(self):
        payload = {
            'date_time': '2026-08-29T10:30',
            'contact_no': '09171234567',
            'email_address': 'juan@example.com',
            'age': 35,
            'client_type': 'Citizen',
            'sex': 'Male',
            'name_of_client': 'Juan Dela Cruz',
            'services_availed': ['KonSulTa Registration (5)', 'Claims Filing (8)'],
            'cc1': '1',
            'cc2': '1',
            'cc3': '1',
            'sqd0': 5,
            'sqd1': 5,
            'sqd2': 4,
            'sqd3': 5,
            'sqd4': 5,
            'sqd5': 5,
            'sqd6': 5,
            'sqd7': 5,
            'sqd8': 5,
            'comments_suggestions': 'Keep up the good work!',
            'commendation': 'Kudos to Frontdesk Staff Maria!'
        }

        response = self._submit(payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertTrue(data['tracking_code'].startswith('CF-'))

        entry = FeedbackEntry.objects.get(tracking_code=data['tracking_code'])
        self.assertEqual(entry.contact_no, '09171234567')
        self.assertEqual(entry.email_address, 'juan@example.com')
        self.assertEqual(entry.age, 35)
        self.assertEqual(entry.client_type, 'Citizen')
        self.assertEqual(entry.name_of_client, 'Juan Dela Cruz')
        self.assertEqual(entry.services_availed, ['KonSulTa Registration (5)', 'Claims Filing (8)'])
        self.assertEqual(entry.sqd0, 5)
        self.assertEqual(entry.experience, FeedbackEntry.VERY_SATISFACTORY)
        self.assertIn('Comments: Keep up the good work!', entry.comment)
        self.assertIn('Commendation: Kudos to Frontdesk Staff Maria!', entry.comment)
