from django.contrib.auth.models import User

def callbackfunction(tree):
    username = tree[0][0].text
    name = tree[0][1][3].text
    first, last = name.split(" ", 1)
    user, _ = User.objects.get_or_create(username=username)
    user.first_name = first
    user.last_name = last
    user.save()
