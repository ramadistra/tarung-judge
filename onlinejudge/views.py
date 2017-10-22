from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404

from requests import ConnectionError
from json import JSONDecodeError
from django.utils.datastructures import MultiValueDictKeyError

from .models import Question, Attempt, User, Category, Contest
from .judger import judge


def home(request):
    contests = Contest.objects.all()
    context = {'contests': contests}
    return render(request, 'onlinejudge/index.html', context)

def contest(request, slug):
    contest = get_object_or_404(Contest, slug=slug)
    categories = Category.objects.filter(question__contest=contest)
    questions = Question.objects.filter(contest=contest).count()
    context = {
        'contest': contest,
        'categories': categories,
        }
    return render(request, 'onlinejudge/contest.html', context)


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
    
    template = question.template
    if user.is_authenticated:
        # Display the users latest attempt if user has already 
        # attempted the question. If not, display the template.
        attempts = Attempt.objects \
                  .filter(user=user, question=question) \
                  .order_by("-id")
        if attempts:
            template = attempts[0].source
        
        # Get the user's submissions
        submissions = question.attempt_set.filter(user=user).order_by("-id")
    else:
        # Empty submissions for unauthenticated users
        submissions = None

    context = {
        'question': question, 
        'submissions': submissions,
        'template': escape(template),
        }
    return render(request, 'onlinejudge/detail.html', context)


def escape(s):
    """Escapes string for JavaScript."""
    return s.replace("\\","\\\\").replace("\r\n", "\\n").replace("\"", "\\\"")


@login_required
def submit(request, slug):
    user = request.user
    question = get_object_or_404(Question, slug=slug)

    try:
        source = request.POST["source"]
    except MultiValueDictKeyError:
        source = ""
    attempt = Attempt(user=user, question=question)

    try:
        result = judge(source, question)
    except (ConnectionError, JSONDecodeError):
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


def leaderboard(request):
    leaderboard = {}

    # Only select users who have solved a question.
    solves = User.objects.filter(attempt__first_solve=True).values(
        "username", 
        "attempt__attempt_date", 
        "attempt__question__difficulty",
        )

    # Calculate user's scores and latest solve date
    for solve in solves:
        username = solve['username']
        points = solve['attempt__question__difficulty']
        attempt = solve['attempt__attempt_date']
        if username in leaderboard.keys():
            user_stat = leaderboard[username]
            user_stat[0] += points
            if attempt > user_stat[1]:
                user_stat[1] = attempt
        else:
            leaderboard[username] = [points, attempt]

    # Leaderboard is sorted by score, then earlist last solve.
    users_latest_solve = sorted(leaderboard.items(), key=lambda x: x[1][1])
    sorted_leaderboard = sorted(
        [(username, stat[0]) for username, stat in users_latest_solve], 
        key=lambda x: x[1], reverse=True,
        )

    context = {'leaderboard': sorted_leaderboard}
    return render(request, 'onlinejudge/leaderboard.html', context)


def judger_offline(request, slug):
    return render(request, 'onlinejudge/judger-offline.html')
   