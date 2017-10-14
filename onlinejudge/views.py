from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from requests import ConnectionError

from .models import Question, Attempt, User, Category
from .forms import SignUpForm
from .judger import judge


def home(request):
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'onlinejudge/index.html', context)


def activity(request):
    # List of latest published Questions
    latest_solves = Attempt.latest_solves()[:50]
    context = {'latest_solves':latest_solves}
    return render(request, 'onlinejudge/activity.html', context)


def detail(request, slug):
    user = request.user

    # Admins can access and test unpublished questions.
    if user.is_staff:
        question = get_object_or_404(Question, slug=slug)
    else:
        question = get_object_or_404(Question, slug=slug,
                                     published_date__lte=timezone.now())
    
    # Display the users latest attempt if user has already 
    # attempted the question. If not, display the template.
    template = question.template
    if user.is_authenticated: 
        attempts = Attempt.objects \
                  .filter(user=user, question=question) \
                  .order_by("-id")
        if attempts:
            template = attempts[0].source

    context = {'question':question, 'template':escape(template)}
    return render(request, 'onlinejudge/detail.html', context)


def escape(s):
    """Escapes string for JavaScript."""
    return s.replace("\r\n", "\\n").replace("\"", "\\\"")


@login_required
def submit(request, slug):
    user = request.user
    question = get_object_or_404(Question, slug=slug)
    source = request.POST["source"]
    attempt = Attempt(user=user, question=question)
    try:
        result = judge(source, question)
    except ConnectionError:
        return redirect('judger-offline', slug=slug)
    else:
        status = result['verdict']
        attempt.status = status
        # If question is not published, replace AC with AC (Testing).
        if status == 1 and not question.is_published:
            attempt.status = 5
        attempt.first_solve = attempt.status == 1 and not question.is_solved_by(user)
        attempt.source = source
        attempt.save()
        attempt_id = attempt.id
        return redirect('result', slug=slug, attempt_id=attempt_id)


@login_required
def result(request, slug, attempt_id):
    # TODO: Handle case where user has solved question.
    question = get_object_or_404(Question, slug=slug)
    attempt = get_object_or_404(Attempt, id=attempt_id)
    if attempt.user == request.user:
        context = {"question":question, "attempt":attempt}
        return render(request, 'onlinejudge/result.html', context)
    return HttpResponse("Unauthorized Access :(", status=401)


@login_required
def profile(request, username):
    user = User.objects.get(username=username)
    latest_solves = Attempt.latest_solves(user)
    context = {'account':user, 'solves':latest_solves}
    return render(request, 'onlinejudge/profile.html', context)


def count_score(user):
    return sum(a.question.difficulty for a in user.attempt_set.filter(status=1, first_solve=True))


def get_latest_solve(tup):
    user = tup[0]
    return user.attempt_set.filter(first_solve=True).latest('attempt_date').attempt_date


def leaderboard(request):
    # Only select users who have solved a question.
    users = User.objects.filter(attempt__first_solve=True).distinct()
    users_score = [(user, count_score(user)) for user in users]
    users_latest_solve = sorted(users_score, key=get_latest_solve)
    leaderboard = sorted(users_latest_solve, key=lambda x: x[1], reverse=True)
    context = {
        'leaderboard': leaderboard
    }
    return render(request, 'onlinejudge/leaderboard.html', context)


def judger_offline(request, slug):
    return render(request, 'onlinejudge/judger-offline.html')
   