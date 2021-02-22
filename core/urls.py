from django.conf import settings
from django.urls import include, path
from django_registration.backends.activation.views import RegistrationView
from django.views.generic.base import TemplateView
from django.contrib.auth.views import (
	PasswordResetConfirmView,
	PasswordResetDoneView,
	PasswordChangeView,
	PasswordResetView,
	LogoutView
)

from .forms import CustomUserForm
from core import views

urlpatterns = [
	path('', views.HomePageView.as_view(), name='home'),
	path('products/', views.ProductListView.as_view(), name='products'),
	path('product/<slug:slug>/', views.ProductPageView.as_view(), name='one_product'),
	path('add_product/<slug:slug>/', views.AddProductView.as_view(), name='add_product'),
	path('add_product_list/', views.AddProductListView.as_view(), name='add_product_list'),
	path('personal_account/', views.PersonalAccountView.as_view(), name='personal_account'),
	path('product_update/<product_id>/', views.ProductUpdateView.as_view(), name='product_update'),
	path('proposals/<order_id>/', views.OrderExecutionProposalView.as_view(), name='proposals'),
	path('become_company/', views.BecomeCompanyView.as_view(), name='become_company'),
	path('update_company/', views.BecomeCompanyView.as_view(), name='update_company'),
	path('shopping_cart/', views.ShoppingCartView.as_view(), name='shopping_cart'),
	path('admin_panel/', views.AdminPanelView.as_view(), name='admin_panel'),
	path('new_orders/', views.NewOrdersView.as_view(), name='new_orders'),
	path('orders/', views.OrdersListView.as_view(), name='orders'),
	path('login/', views.LoginView.as_view(), name='login'),

	path('ordering/', views.OrderingView.as_view(), name='ordering'),
	path('product_distribution/', views.ProductDistributionView.as_view(), name='product_distribution'),
	path('order_handler/<ord_exec_id>/', views.set_order_status_view, name='order_handler'),
	path('cancel_order/<order_id>/<context>/', views.cancel_order_view, name='cancel_order'),
	path('delete_notification/', views.delete_notification_view, name='delete_notification'),
	path('choose_offer/<order_id>/<offer>/', views.choose_offer_view, name='choose_offer'),
	path('split_order/<order_id>/<offer>/', views.split_order_view, name='split_order'),
	path('repeat_order/<order_id>/', views.repeat_order_view, name='repeat_order'),
	path('payment/<order_id>/', views.PaymentView.as_view(), name='payment'),
	path('inn_search/<inn>/', views.inn_search_view, name='inn_search'),

	path('help/', TemplateView.as_view(template_name='other_pages/help.html'), name='help'),
	path('about_us/', TemplateView.as_view(template_name='other_pages/about_us.html'), name='about_us'),
	path('city_selection/', views.city_selection_view, name='city'),

	path('policy/platform', TemplateView.as_view(template_name='other_pages/policy/platform.html'), name='platform'),
	path('policy/privacy', TemplateView.as_view(template_name='other_pages/policy/privacy.html'), name='privacy'),
	path('policy/service', TemplateView.as_view(template_name='other_pages/policy/service.html'), name='service'),
	path('policy/p_data', TemplateView.as_view(template_name='other_pages/policy/p_data.html'), name='p_data'),
	path('policy/', TemplateView.as_view(template_name='other_pages/privacy_policy.html'), name='policy'),

	path('create_product/', views.create_product_view),

	path(
		'become_company_fail/',
		TemplateView.as_view(
			template_name='account_pages/become_company_fail.html'
		),
		name='become_company_fail'),

	path(
		'delete_product_in_cart/<product_id>/',
		views.delete_product_in_cart_view,
		name='delete_product_in_cart'
	),

	path(
		'password_reset/',
		PasswordResetView.as_view(
			template_name='account_pages/password_reset.html',
			email_template_name='account_pages/password_reset_body.txt',
			subject_template_name='account_pages/password_reset_subject.txt'
		),
		name='password_reset'
	),

	path(
		'password_reset_done/',
		PasswordResetDoneView.as_view(
			template_name='account_pages/password_reset_done.html',
		),
		name='password_reset_done'
	),

	path(
		'password_reset_confirm/<uidb64>/<token>/',
		PasswordResetConfirmView.as_view(
			template_name='account_pages/password_reset_confirm.html',
			success_url='/login/'
		),
		name='password_reset_confirm'
	),

	path(
		'password_change/',
		PasswordChangeView.as_view(
			template_name='account_pages/password_change.html',
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
