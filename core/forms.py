from phonenumber_field.formfields import PhoneNumberField
from django_registration.forms import RegistrationForm
from django import forms

from .models import User, Company


class CustomUserForm(RegistrationForm):
	is_receiving_news = forms.BooleanField(required=False)
	phone_number = PhoneNumberField(required=False)

	class Meta(RegistrationForm.Meta):
		model = User
		fields = [
			'first_name', 'last_name', 'email', 'phone_number', 'company_name',
			'password1', 'password2', 'is_receiving_news'
		]

	def save(self, commit=True):
		user = super().save(commit=False)
		user.set_password(self.cleaned_data["password1"])
		if commit:
			user.save()
		return user


class AdminPanelForm(forms.Form):
	moderator_message = forms.CharField(label="Сообщение для пользователя", required=False)
	is_verification = forms.BooleanField(label="Верифицировать пользователя", required=False)
	company_user = forms.CharField(widget=forms.HiddenInput, required=False)

	class Meta(RegistrationForm.Meta):
		model = Company
		fields = ['moderator_message', 'is_verification', 'company_user']
