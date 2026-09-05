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
            'experience': FeedbackEntry.STRONGLY_AGREE,
            'comment': 'Excellent service.',
        })

        self.assertEqual(response.status_code, 201)
        entry = FeedbackEntry.objects.get()
        self.assertEqual(entry.sentiment, FeedbackEntry.POSITIVE)
        mocked_analyze.assert_called_once_with('Excellent service.', FeedbackEntry.STRONGLY_AGREE)

    @patch('feedback.views.analyze_comment_sentiment', return_value=FeedbackEntry.POSITIVE)
    def test_submit_feedback_skips_analysis_when_disabled(self, mocked_analyze):
        config = FeedbackConfiguration.get_solo()
        config.auto_analysis_enabled = False
        config.save()

        response = self._submit({
            'experience': FeedbackEntry.AGREE,
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

        entry = FeedbackEntry.objects.latest('id')
        self.assertEqual(entry.contact_no, '09171234567')
        self.assertEqual(entry.email_address, 'juan@example.com')
        self.assertEqual(entry.age, 35)
        self.assertEqual(entry.client_type, 'Citizen')
        self.assertEqual(entry.name_of_client, 'Juan Dela Cruz')
        self.assertEqual(entry.services_availed, ['KonSulTa Registration (5)', 'Claims Filing (8)'])
        self.assertEqual(entry.sqd0, 5)
        self.assertEqual(entry.experience, FeedbackEntry.STRONGLY_AGREE)
        self.assertIn('Comments: Keep up the good work!', entry.comment)
        self.assertIn('Commendation: Kudos to Frontdesk Staff Maria!', entry.comment)


class SentimentServiceTests(TestCase):
    def test_analyze_comment_with_form_headers(self):
        from .services import analyze_comment_sentiment
        res = analyze_comment_sentiment('Comments: The staff was very helpful and accommodating.')
        self.assertIn(res, [FeedbackEntry.POSITIVE, FeedbackEntry.NEUTRAL])


class DailySummaryEmailTests(TestCase):
    def setUp(self):
        from django.utils import timezone
        self.today = timezone.localtime().date()
        self.config = FeedbackConfiguration.get_solo()
        self.config.daily_summary_enabled = True
        self.config.notification_email = 'supervisor@philhealth.gov.ph'
        self.config.save()

    def test_metrics_calculation(self):
        from .email_service import get_daily_summary_metrics
        # Create test feedback entries
        FeedbackEntry.objects.create(
            experience=FeedbackEntry.STRONGLY_AGREE,
            sqd0=5,
            sentiment=FeedbackEntry.POSITIVE,
            category=FeedbackEntry.COMPLIMENT,
            comment='Great service at Window 2.'
        )
        FeedbackEntry.objects.create(
            experience=FeedbackEntry.AGREE,
            sqd0=4,
            sentiment=FeedbackEntry.POSITIVE,
            category=FeedbackEntry.SUGGESTION,
            comment='Smooth transaction.'
        )
        FeedbackEntry.objects.create(
            experience=FeedbackEntry.DISAGREE,
            sqd0=2,
            sentiment=FeedbackEntry.NEGATIVE,
            category=FeedbackEntry.COMPLAINT,
            comment='Long waiting queue.'
        )

        metrics = get_daily_summary_metrics(self.today)
        self.assertEqual(metrics['total_count'], 3)
        # (2 positive SQD0 out of 3) = 67%
        self.assertEqual(metrics['satisfaction_rate'], 67)
        self.assertEqual(metrics['pos_count'], 2)
        self.assertEqual(metrics['neg_count'], 1)
        self.assertEqual(metrics['categories']['complaints'], 1)
        self.assertEqual(len(metrics['flagged_items']), 1)
        self.assertIn('Long waiting queue', metrics['flagged_items'][0]['comment'])

    def test_zero_count_allowed(self):
        from .email_service import send_daily_summary_email
        from django.core import mail
        # When count is 0, dispatch proceeds and sends the summary of 0 submissions
        result = send_daily_summary_email(
            target_date=self.today,
            recipient_email='admin@philhealth.gov.ph',
            force=True,
            is_test=False
        )
        self.assertTrue(result['ok'])
        self.assertEqual(result['metrics']['total_count'], 0)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_test_email(self):
        from .email_service import send_daily_summary_email
        from django.core import mail
        # Force dispatch in test mode
        result = send_daily_summary_email(
            target_date=self.today,
            recipient_email='testadmin@philhealth.gov.ph',
            force=True,
            is_test=True
        )
        self.assertTrue(result['ok'])
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn('[TEST]', sent_email.subject)
        self.assertIn('testadmin@philhealth.gov.ph', sent_email.to)

    def test_dynamic_base_url_vercel(self):
        import os
        from .email_service import send_daily_summary_email
        from django.core import mail

        os.environ['VERCEL_URL'] = 'city-feedback.vercel.app'
        try:
            result = send_daily_summary_email(
                target_date=self.today,
                recipient_email='admin@philhealth.gov.ph',
                force=True
            )
            self.assertTrue(result['ok'])
            self.assertEqual(len(mail.outbox), 1)
            sent_email = mail.outbox[0]
            # Check html content has vercel https url
            html_content = sent_email.alternatives[0][0]
            self.assertIn('https://city-feedback.vercel.app/dashboard/', html_content)
        finally:
            os.environ.pop('VERCEL_URL', None)

    def test_cron_daily_summary_view(self):
        from django.test import Client
        client = Client()
        # Test endpoint
        response = client.get('/api/cron/daily-summary/?force=true')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('recipient'), 'supervisor@philhealth.gov.ph')

    def test_cron_daily_summary_with_secret(self):
        from django.test import Client, override_settings
        client = Client()
        with override_settings(CRON_SECRET='my-secret-token'):
            # Without secret -> 401
            res_fail = client.get('/api/cron/daily-summary/')
            self.assertEqual(res_fail.status_code, 401)

            # With query param secret -> 200
            res_param = client.get('/api/cron/daily-summary/?secret=my-secret-token&force=true')
            self.assertEqual(res_param.status_code, 200)
            self.assertTrue(res_param.json().get('ok'))

            # With Bearer header secret -> 200
            res_header = client.get(
                '/api/cron/daily-summary/?force=true',
                HTTP_AUTHORIZATION='Bearer my-secret-token'
            )
            self.assertEqual(res_header.status_code, 200)
            self.assertTrue(res_header.json().get('ok'))


