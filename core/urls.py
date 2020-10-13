from django.conf import settings
from django.urls import include, path
from django_registration.backends.activation.views import RegistrationView
from django.contrib.auth.views import (
	PasswordResetConfirmView,
	PasswordResetDoneView,
	PasswordChangeView,
	PasswordResetView,
	LogoutView
)

from .forms import CustomUserForm
from .views import (
	PersonalAccountView,
	BecomeCompanyView,
	UpdateCompanyView,
	ProductPageView,
	ProductListView,
	AdminPanelView,
	HomePageView,
	LoginView
)

urlpatterns = [
	path('', HomePageView.as_view(), name='home'),
	path('product/', ProductPageView.as_view(), name='one_product'),
	path('products/', ProductListView.as_view(), name='products'),
	path('personal_account/', PersonalAccountView.as_view(), name='personal_account'),
	path('become_company/', BecomeCompanyView.as_view(), name='become_company'),
	path('update_company/', UpdateCompanyView.as_view(), name='update_company'),
	path('admin_panel/', AdminPanelView.as_view(), name='admin_panel'),
	path('login/', LoginView.as_view(), name='login'),

	path(
		'password_reset/',
		PasswordResetView.as_view(
			template_name='account/password_reset.html',
			email_template_name='account/password_reset_body.txt',
			subject_template_name='account/password_reset_subject.txt'
		),
		name='password_reset'
	),

	path(
		'password_reset_done/',
		PasswordResetDoneView.as_view(
			template_name='account/password_reset_done.html',
		),
		name='password_reset_done'
	),

	path(
		'password_reset_confirm/<uidb64>/<token>/',
		PasswordResetConfirmView.as_view(
			template_name='account/password_reset_confirm.html',
			success_url='/login/'
		),
		name='password_reset_confirm'
	),

	path(
		'password_change/',
		PasswordChangeView.as_view(
			template_name='account/password_change.html',
			success_url='/personal_account/'
		),
		name='password_change'
	),

	path(
		'logout/',
		LogoutView.as_view(),
		{'next_page': settings.LOGOUT_REDIRECT_URL},
		name='logout'
	),

	path(
		'account/register/',
		RegistrationView.as_view(form_class=CustomUserForm),
		name='register'
	),

	path('account/', include('django_registration.backends.activation.urls')),
]
