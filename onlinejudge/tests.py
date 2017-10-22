from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User

from .models import Attempt, Question, Contest, Category

from . import views
from . import judger
from .templatetags import app_filters


class JudgerTestCase(TestCase):
    def test_parse_response(self):
        # Parse normal output.
        output = "1.in\nHello\nWorld\n2.in\nWorld\n"
        self.assertEqual(judger.parse_stdout(output), ["Hello\nWorld", "World"])

        # Parse malicious output.
        output = "1.in\nHello\nWorld\n2.in\nWorld\n2.in\nWorld\n"
        self.assertEqual(judger.parse_stdout(output), ["Hello\nWorld", "World\n2.in\nWorld"])

    def test_match(self):
        # Correct output.
        correct = Attempt.ACCEPTED
        expected_out = ['Hello\nWorld', 'World\nHello']
        response = {
            'stdout': '1.in\nHello\nWorld\n2.in\nWorld\nHello\n',
            'status': 'OK'
        }
        self.assertEqual(judger.match(expected_out, response), ([correct, correct], True))

        # Wrong output.
        wrong = Attempt.WRONG_ANSWER
        expected_out = ['Hello\nWorld', 'World\nHello']
        response = {
            'stdout': '1.in\nHello\nWorld\n2.in\nWorld\n2.in\nWorld\n',
            'status': 'OK'
        }
        self.assertEqual(judger.match(expected_out, response), ([correct, wrong], False))


class PublicViewsTest(TestCase):
    """
    Test views that can be accessed by both 
    anynomous and authenticated users.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='test', email='test@case.com', password='test_case')
        self.public_views = [
            ('/', views.home), 
            ('/scoreboard', views.leaderboard), 
            ('/activity', views.activity),
            ('/activity', views.activity),
        ]

    def test_anonymous_user(self):
        for url, view in self.public_views:
            request = self.factory.get(url)
            request.user = AnonymousUser()
            response = view(request)
            self.assertEqual(response.status_code, 200)

    def test_authenticated_user(self):
        for url, view in self.public_views:
            request = self.factory.get(url)
            request.user = AnonymousUser()
            response = view(request)
            self.assertEqual(response.status_code, 200)


class LoginRequiredTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='test', email='test@case.com', password='test_case')

    def test_anonymous_user(self):
        request = self.factory.get('/profile/test')
        request.user = AnonymousUser()
        response = views.profile(request, username='test')
        # Users that are not logged in should be redirected to login page.
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self):
        request = self.factory.get('/profile/test')
        request.user = self.user
        response = views.profile(request, username='test')
        self.assertEqual(response.status_code, 200)


class QuestionViewsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='test', email='test@case.com', password='test_case')
        self.question = Question(
            title = "Test Question",
            description = "This is a test.",
            slug = "test-question",
            difficulty = 20,
            template = "# Hello"
        )
        self.question.save()

    def test_question_details(self):
        # Anonymous and authenticated users should be able to view questions.
        for user in [self.user, AnonymousUser()]:
            request = self.factory.get('/question/%s' % self.question.slug)
            request.user = user
            response = views.detail(request, self.question.slug)
            self.assertEqual(response.status_code, 200)

    def test_submit_question(self):
        # Anonymous user cannot submit a question and will be redirected.
        request = self.factory.post(
            '/question/%s/submit' % self.question.slug,
            data = {'source':'print("Test!")'}
            )
        request.user = AnonymousUser()
        response = views.submit(request, self.question.slug)
        self.assertEqual(response.url, "/login?next=/question/%s/submit" % self.question.slug)

class LatestQuestionsTest(TestCase):
    def setUp(self):
        self.contest = Contest(name="Test", slug="test", description="con test")
        self.category = Category(name="Tests")

    def test_latest_questions(self):
        latest_questions = app_filters.latest_questions(self.category, self.contest)