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
    if request.user.is_staff:
        question = get_object_or_404(Question, slug=slug)
    else:
        question = get_object_or_404(Question, slug=slug,
                                     published_date__lte=timezone.now())
    context = {'question':question}
    return render(request, 'onlinejudge/detail.html', context)



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

def user_score(user):
    return sum(a.question.difficulty for a in user.attempt_set.filter(status=1, first_solve=True))

def leaderboard(request):
    users = User.objects.all()
    users_score = [(user, user_score(user)) for user in users]
    leaderboard = sorted(users_score, key=lambda x: x[1], reverse=True)
    context = {
        'leaderboard': leaderboard
    }
    return render(request, 'onlinejudge/leaderboard.html', context)


def judger_offline(request, slug):
    return render(request, 'onlinejudge/judger-offline.html')
   