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
