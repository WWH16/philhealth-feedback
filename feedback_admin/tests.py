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
            is_superuser=True,
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


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='password123',
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_dashboard_view_renders_successfully(self):
        from feedback.models import FeedbackEntry
        FeedbackEntry.objects.create(
            experience=FeedbackEntry.STRONGLY_AGREE,
            category='compliment',
            comment='Great service!',
        )
        FeedbackEntry.objects.create(
            experience=FeedbackEntry.AGREE,
            category='suggestion',
            comment='Smooth process.',
        )

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('filter_data', response.context)
        self.assertEqual(response.context['total'], 2)
        self.assertEqual(response.context['strongly_agree'], 1)
        self.assertEqual(response.context['agree'], 1)
        self.assertEqual(response.context['disagree'], 0)
        self.assertEqual(response.context['filter_data']['all']['total'], 2)
        self.assertContains(response, 'id="nav-dashboard"')
        self.assertContains(response, 'nav-item active')


class SentimentAnalysisViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='password123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

    def test_sentiment_analysis_view_renders_successfully(self):
        from feedback.models import FeedbackEntry
        FeedbackEntry.objects.create(
            experience=FeedbackEntry.STRONGLY_AGREE,
            sentiment=FeedbackEntry.POSITIVE,
            comment='Exemplary assistance.',
        )
        FeedbackEntry.objects.create(
            experience=FeedbackEntry.DISAGREE,
            sentiment=FeedbackEntry.NEGATIVE,
            comment='Delayed processing.',
        )

        response = self.client.get(reverse('sentiment_analysis'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 2)
        self.assertEqual(response.context['positive'], 1)
        self.assertEqual(response.context['neutral'], 0)
        self.assertEqual(response.context['negative'], 1)
        self.assertContains(response, 'nav-item active')


class ReportsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='password123',
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_reports_view_renders_successfully(self):
        from feedback.models import FeedbackEntry
        FeedbackEntry.objects.create(
            experience=FeedbackEntry.STRONGLY_AGREE,
            category='compliment',
            comment='Superb staff responsiveness.',
        )

        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('report_json', response.context)
        report_data = response.context['report_json']
        self.assertIn('daily', report_data)
        self.assertIn('weekly', report_data)
        self.assertIn('monthly', report_data)
        self.assertIn('quarterly', report_data)
        self.assertIn('annual', report_data)
        self.assertEqual(report_data['daily']['strongly_agree'], 1)
        self.assertContains(response, 'nav-item active')


class ResponsesViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='password123',
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_responses_view_renders_successfully(self):
        from feedback.models import FeedbackEntry
        FeedbackEntry.objects.create(
            experience=FeedbackEntry.STRONGLY_AGREE,
            category='compliment',
            comment='Fast transaction.',
        )

        response = self.client.get(reverse('responses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 1)
        self.assertEqual(response.context['strongly_agree'], 1)
        self.assertEqual(len(response.context['entries_data']), 1)
        self.assertContains(response, 'nav-item active')


class ActivityLogViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='password123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

    def test_activity_log_view_renders_successfully(self):
        response = self.client.get(reverse('activity_log'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('logs_data', response.context)
        self.assertContains(response, 'nav-item active')


class UsersViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='password123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

    def test_users_view_renders_successfully(self):
        response = self.client.get(reverse('users'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_users'], 1)
        self.assertEqual(response.context['active_users'], 1)
        self.assertEqual(response.context['staff_users'], 1)
        self.assertContains(response, 'nav-item active')

    def test_self_password_update_requires_current_password(self):
        response = self.client.post(
            reverse('user_edit', args=[self.user.id]),
            {
                'username': self.user.username,
                'email': self.user.email,
                'password1': 'newpassword12345',
                'password2': 'newpassword12345',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['ok'])
        self.assertIn('Current password is required', data['error'])

    def test_self_password_update_rejects_wrong_current_password(self):
        response = self.client.post(
            reverse('user_edit', args=[self.user.id]),
            {
                'username': self.user.username,
                'email': self.user.email,
                'current_password': 'wrongpassword',
                'password1': 'newpassword12345',
                'password2': 'newpassword12345',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['ok'])
        self.assertIn('Current password is incorrect', data['error'])

    def test_self_password_update_succeeds_with_correct_current_password(self):
        response = self.client.post(
            reverse('user_edit', args=[self.user.id]),
            {
                'username': self.user.username,
                'email': self.user.email,
                'current_password': 'password123',
                'password1': 'newpassword12345',
                'password2': 'newpassword12345',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword12345'))

    def test_admin_reset_other_user_password_does_not_require_current_password(self):
        other_user = User.objects.create_user(
            username='staff_member',
            password='oldpassword123',
            is_staff=True,
        )
        response = self.client.post(
            reverse('user_edit', args=[other_user.id]),
            {
                'username': other_user.username,
                'email': other_user.email,
                'password1': 'resetpassword12345',
                'password2': 'resetpassword12345',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        other_user.refresh_from_db()
        self.assertTrue(other_user.check_password('resetpassword12345'))


class RoleBasedAccessControlTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff_member',
            password='password123',
            is_active=True,
            is_staff=True,
            is_superuser=False,
        )
        self.superuser = User.objects.create_user(
            username='superuser_admin',
            password='password123',
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        self.regular_user = User.objects.create_user(
            username='regular_juan',
            password='password123',
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        self.inactive_user = User.objects.create_user(
            username='inactive_pedro',
            password='password123',
            is_active=False,
            is_staff=True,
            is_superuser=False,
        )

    def test_staff_can_access_core_operations(self):
        self.client.force_login(self.staff_user)

        # Dashboard, Responses, and Reports
        res_dash = self.client.get(reverse('dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_resp = self.client.get(reverse('responses'))
        self.assertEqual(res_resp.status_code, 200)

        res_rep = self.client.get(reverse('reports'))
        self.assertEqual(res_rep.status_code, 200)

    def test_staff_is_blocked_from_superuser_views(self):
        self.client.force_login(self.staff_user)

        for route_name in ['users', 'settings_page', 'activity_log', 'sentiment_analysis']:
            response = self.client.get(reverse(route_name), follow=True)
            self.assertRedirects(response, reverse('dashboard'))
            self.assertContains(response, 'Access restricted to administrators.')

    def test_regular_user_cannot_login(self):
        response = self.client.post(
            reverse('admin_login'),
            {'username': 'regular_juan', 'password': 'password123'},
            follow=True,
        )
        self.assertContains(response, 'Access denied. Staff privileges are required.')
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_inactive_user_login_shows_deactivated_message(self):
        response = self.client.post(
            reverse('admin_login'),
            {'username': 'inactive_pedro', 'password': 'password123'},
            follow=True,
        )
        self.assertContains(response, 'This account has been deactivated. Please contact your system administrator.')
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_invalid_password_shows_generic_error(self):
        response = self.client.post(
            reverse('admin_login'),
            {'username': 'staff_member', 'password': 'wrongpassword'},
            follow=True,
        )
        self.assertContains(response, 'Invalid username or password. Please check your credentials and try again.')
        self.assertFalse('_auth_user_id' in self.client.session)
