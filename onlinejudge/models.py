from django.contrib.auth.models import User
from django.db import models
from django.db.models import permalink
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Contest(models.Model):
    name = models.CharField(max_length=64, unique=True, db_index=True)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    description = models.TextField()

    def __str__(self):
        return self.name

    @permalink
    def get_absolute_url(self):
        return ('contest', None, {'slug': self.slug})


class Question(models.Model):
    EASY = 20
    MEDIUM = 40
    HARD = 70
    GANTENG = 200
    FWP = 100000
    DIFFICULTY_CHOICES = ((EASY, 'Mudah'), (MEDIUM, 'Sedang'), (HARD, 'Sulit'),
                          (GANTENG, 'Ganteng'), (FWP, 'FWP'))
    difficulty_dict = dict(DIFFICULTY_CHOICES)

    # Question Body
    title = models.CharField(max_length=64, unique=True, db_index=True)
    description = models.TextField()

    # Question Details
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, choices=None)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=True)
    published_date = models.DateTimeField(default=timezone.now)
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES)
    template = models.TextField()

    @property
    def cases(self):
        return self.case_set.filter(sample_case=False).all()

    @property
    def sample_cases(self):
        return self.case_set.filter(sample_case=True).all()

    @property
    def solves(self):
        return self.attempt_set.filter(
            status=1).values("user").distinct().count()

    @property
    def total(self):
        return self.attempt_set.values("user").distinct().count()

    @property
    def success_rate(self):
        if self.total == 0:
            return "0"
        return "{0:.2f}".format(self.solves / self.total * 100)

    @property
    def difficulty_str(self):
        return self.difficulty_dict[self.difficulty]

    @property
    def is_published(self):
        return self.published_date <= timezone.now()

    # Check whether the question has been answered by a user.
    def is_solved_by(self, user):
        return bool(self.attempt_set.filter(status=1, user=user))

    def __str__(self):
        return "Title: {}\nSuccess Rate:{}%".format(self.title,
                                                    self.success_rate)

    @permalink
    def get_absolute_url(self):
        return ('detail', None, {'slug': self.slug})


class Case(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    stdin = models.TextField()
    stdout = models.TextField()
    sample_case = models.BooleanField(default=False)


class Attempt(models.Model):
    WRONG_ANSWER = 0
    ACCEPTED = 1
    RUNTIME_ERROR = 2
    SERVER_ERROR = 3
    TIMED_OUT = 4
    TESTING = 5
    STATUS_CHOICES = (
        (WRONG_ANSWER, 'Wrong Answer'),
        (ACCEPTED, 'Accepted'),
        (RUNTIME_ERROR, 'Runtime Error'),
        (SERVER_ERROR, 'Server Error'),
        (TIMED_OUT, 'Timed Out'),
        (TESTING, 'Accepted (Testing)'),
    )
    _status_dict = dict(STATUS_CHOICES)

    # Attempt Information
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    # Attempt Details
    attempt_date = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.IntegerField(choices=STATUS_CHOICES)
    source = models.TextField(default="")
    first_solve = models.BooleanField(default=False)

    @property
    def status_str(self):
        return self._status_dict[self.status]

    @classmethod
    def latest_solves(cls, user=None):
        if not user:
            # Get latest solves for all users.
            return cls.objects.filter(
                first_solve=True).order_by('-attempt_date')
        # Get latest solves for user.
        return cls.objects.filter(
            first_solve=True, user=user).order_by('-attempt_date')

    def __str__(self):
        return "{} -> {} (status: {})".format(self.user.username,
                                              self.question.title, self.status)
