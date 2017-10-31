import math

from django import template
from django.utils import timezone

register = template.Library()


@register.filter(name='is_solved')
def is_solved(question, user):
    return question.is_solved_by(user)


@register.filter(name='latest_questions')
def latest_questions(category, contest):
    return category.question_set \
           .filter(contest=contest, published_date__lte=timezone.now()) \
           .order_by('difficulty', 'published_date')


@register.filter(name='completed')
def completed(contest, user):
    questions = contest.question_set.count()
    solves = contest.question_set.filter(
        attempt__first_solve=True, attempt__user=user).count()
    return questions == solves


@register.filter(name='progress')
def progress(contest, user):
    questions = contest.question_set.count()
    max_stars = math.ceil(questions / 5)
    if not user.is_authenticated:
        return [False] * max_stars
    solves = contest.question_set.filter(
        attempt__first_solve=True, attempt__user=user).count()
    green = int((solves / questions) * max_stars)
    return [True] * green + [False] * (max_stars - green)
