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
    # List of latest published Questions
    latest_solves = Attempt.latest_solves()
    categories = Category.objects.all()[:10]
    context = {
        'categories': categories,
        'latest_solves':latest_solves,
        }
    return render(request, 'onlinejudge/index.html', context)


def detail(request, slug):
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
        attempt.first_solve = status == 1 and not question.is_solved_by(user)
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


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    if not request.method == 'POST':
        form = SignUpForm()
        return render(request, 'registration/signup.html', {'form': form})

    form = SignUpForm(request.POST)
    if not form.is_valid():
        return render(request, 'registration/signup.html', {'form': form})

    email = form.cleaned_data["email"]
    username = form.cleaned_data["username"]
    password = form.cleaned_data["password"]
    first_name = form.cleaned_data["first_name"]
    last_name = form.cleaned_data["last_name"]
    User.objects.create_user(username, email, password,
                             first_name=first_name, last_name=last_name)

    return redirect('login')


def judger_offline(request, slug):
    return render(request, 'onlinejudge/judger-offline.html')
   