from django.conf import settings
from django.contrib.auth import views
from django.urls import include, path
from django.views.generic.base import TemplateView
from django_registration.backends.activation.views import RegistrationView

from .forms import CustomUserForm
from .views import ProductPageView

urlpatterns = [
	path('', TemplateView.as_view(template_name="home_page/index.html"), name='home'),
	path('product/', ProductPageView.as_view(), name='one_product'),
	path('products/', TemplateView.as_view(template_name="product_pages/products.html"), name='products'),

	path(
		'personal_account/',
		TemplateView.as_view(template_name="account/client_personal_account.html"),
		name='personal_account'
	),

	path(
		'login/',
		views.LoginView.as_view(template_name="account/login.html"),
		name='login'
	),

	path(
		'logout/',
		views.LogoutView.as_view(),
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
