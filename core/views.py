from django.views.generic.edit import FormView, UpdateView, CreateView
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.contrib.auth.views import LoginView as BaseLoginView
from django.shortcuts import HttpResponseRedirect, get_object_or_404

from .models import User, Company, Product
from .forms import AdminPanelForm


class HomePageView(TemplateView):
	template_name = 'home_page/index.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['products'] = Product.objects.all()
		return context


class ProductPageView(TemplateView):
	template_name = 'product_pages/one_product.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['name'] = 'Пластиковая карта'
		return context


class ProductListView(ListView):
	template_name = 'product_pages/products.html'
	model = Product
	paginate_by = 150

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		category_list = []

		for category in Product.CATEGORY:
			category_list.append((
				category[0],
				category[1],
				Product.objects.filter(category=category[0])
			))

		context['category_list'] = category_list
		return context


class LoginView(BaseLoginView):
	template_name = 'account/login.html'
	redirect_authenticated_user = True

	def get_success_url(self):
		if self.request.user.is_admin:
			redirect_url = '/admin_panel/'
			return redirect_url
		return super().get_success_url()


class PersonalAccountView(UpdateView):
	template_name = 'account/client_personal_account.html'
	model = User
	fields = ['first_name', 'last_name', 'phone_number', 'company_name']
	success_url = '/personal_account/'

	def get_object(self, queryset=None):
		return get_object_or_404(User, pk=self.request.user.id)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		if self.request.user.is_company:
			context['company'] = Company.objects.get(user=self.request.user)
		return context


class BecomeCompanyView(CreateView):
	template_name = 'account/become_company.html'
	model = Company
	fields = ['user', 'addresses', 'inn', 'company_files']
	success_url = '/personal_account/'

	def form_valid(self, form):
		user = User.objects.get(id=self.request.user.id)
		user.is_company = True
		user.save()
		return super().form_valid(form)


class UpdateCompanyView(UpdateView):
	template_name = 'account/become_company.html'
	model = Company
	fields = ['addresses', 'inn', 'company_files']
	success_url = '/personal_account/'
	object = None

	def get_object(self, queryset=None):
		return get_object_or_404(Company, user=self.request.user)

	def form_valid(self, form):
		self.object = form.save()
		self.object.is_verified = False
		self.object.moderator_message = ''
		self.object.save()
		return HttpResponseRedirect(self.get_success_url())


class AdminPanelView(FormView):
	template_name = 'account/admin_panel.html'
	form_class = AdminPanelForm
	success_url = '/admin_panel/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['company_list'] = Company.objects.filter(is_verification=False, is_verified=False)
		return context

	def form_valid(self, form):
		self.save()
		return super().form_valid(form)

	def save(self):
		user = User.objects.get(email=self.request.POST.get('company_user'))
		company = Company.objects.get(user=user)
		company.moderator_message = self.request.POST.get('moderator_message')
		company.is_verified = True

		if self.request.POST.get('is_verification') is not None:
			company.is_verification = True

		company.save()
