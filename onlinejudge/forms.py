from django.forms import Form, CharField, EmailField, PasswordInput, ValidationError
from .models import User

class SignUpForm(Form):
    first_name = CharField(label='First Name', max_length=16)
    last_name = CharField(label='Last Name', max_length=16)
    username = CharField(label='Username', max_length=24)
    email = EmailField(label='E-mail', max_length=32)
    password = CharField(label='Password', widget=PasswordInput())

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise ValidationError(u'Username "%s" is already in use.' % username)

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise ValidationError(u'Email "%s" is already in use.' % email)