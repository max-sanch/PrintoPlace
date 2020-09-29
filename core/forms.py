from django_registration.forms import RegistrationForm
from django import forms

from .models import User


class CustomUserForm(RegistrationForm):
	is_company = forms.BooleanField(label="Компания", required=False)
	is_receiving_news = forms.BooleanField(label="Получать новости", required=False)

	class Meta(RegistrationForm.Meta):
		model = User
		fields = ['first_name', 'last_name', 'email', 'password1', 'password2', 'is_company', 'is_receiving_news']
