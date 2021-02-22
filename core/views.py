import yadisk

from django.conf import settings
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render

from core import models, forms
from core.services import (
	api_handler,
	order_handler,
	create_product,
	product_handler,
	notification_handler,
	proposals_order_execution
)


@login_required
def delete_notification_view(request):
	"""Очистить уведомления у пользователя."""
	notification_handler.delete_notification(request)
	return HttpResponseRedirect('/personal_account/')


@login_required
def set_order_status_view(request, ord_exec_id):
	"""Установить статус для конкретного заказа."""
	order_handler.set_order_execution_status(int(ord_exec_id))
	if request.user.is_company:
		return HttpResponseRedirect('/new_orders/')
	return HttpResponseRedirect('/orders/')


@login_required
def cancel_order_view(request, order_id, context):
	"""Отмена действующего заказа заказчиком/исполнителем"""
	order_handler.cancel_order(order_id, context)
	if request.user.is_company:
		return HttpResponseRedirect('/new_orders/')
	return HttpResponseRedirect('/orders/')


@permission_required('is_not_company')
def repeat_order_view(request, order_id):
	"""Повторение завершённого/отменённого заказа"""
	order_handler.repeat_order(request, order_id)
	return HttpResponseRedirect('/ordering/')


@login_required
def delete_product_in_cart_view(request, product_id):
	"""Удаление конкретного продукта из корзины пользователя"""
	obj = get_object_or_404(models.ShoppingCart, id=product_id, user=request.user)
	obj.delete()
	return HttpResponseRedirect('/shopping_cart/')


def city_selection_view(request):
	"""Выбор города пользователя"""
	if request.method == 'POST':
		city = request.POST.get('city')
		response = HttpResponseRedirect('/')
		response.set_cookie('city', city)
		return response
	else:
		return render(request, 'other_pages/city_selection.html')


@login_required
def inn_search_view(request, inn):
	"""Поиск информации о компании по ИНН"""
	return api_handler.inn_search(inn)


def create_product_view(request):
	create_product.start()
	return HttpResponseRedirect('/products/')


@permission_required('is_not_company')
def choose_offer_view(request, order_id, offer):
	"""Выбор предложения от исполнителя"""
	if request.user == get_object_or_404(models.Order, id=int(order_id)).user:
		order_handler.choose_offer(int(order_id), int(offer))
		return HttpResponseRedirect('/orders/#add_offer')
	else:
		return HttpResponseRedirect('/orders/')


@permission_required('is_not_company')
def split_order_view(request, order_id, offer):
	"""Добавление остатка продукции в корзину при выборе неполного предложения от исполнителя"""
	if request.user == get_object_or_404(models.Order, id=int(order_id)).user:
		order_handler.split_order(int(order_id), int(offer))
		return HttpResponseRedirect('/orders/#add_offer')
	else:
		return HttpResponseRedirect('/orders/')


class HomePageView(TemplateView):
	template_name = 'home_page/index.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['products'] = models.Product.objects.all()
		return context


class ProductPageView(FormView):
	template_name = 'product_pages/one_product.html'
	form_class = forms.ProductPageForm
	success_url = '/product/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.update({
			'product': get_object_or_404(models.Product, slug=self.kwargs.get('slug')),
			'products': models.Product.objects.all(),
			'characteristic_list': product_handler.get_characteristic_list(self.kwargs),
		})
		return context

	def get_success_url(self):
		self.success_url += self.kwargs.get('slug') + '/#successful'
		return super().get_success_url()

	def get_form_kwargs(self):
		kwargs = super(ProductPageView, self).get_form_kwargs()
		kwargs.update({
			'user': self.request.user,
			'slug': self.kwargs.get('slug'),
		})
		return kwargs

	def form_valid(self, form):
		form.save()
		return super().form_valid(form)


class ProductUpdateView(PermissionRequiredMixin, FormView):
	template_name = 'product_pages/product_update.html'
	permission_required = ('is_auth', 'is_not_company')
	form_class = forms.ProductPageForm
	success_url = '/shopping_cart/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.update({
			'product': self._get_product().product,
			'characteristic_list': product_handler.get_characteristic_list(self.kwargs, self._get_product().product),
			'product_data': self._get_product(),
		})
		return context

	def get_form_kwargs(self):
		kwargs = super(ProductUpdateView, self).get_form_kwargs()
		kwargs.update({
			'user': self.request.user,
			'slug': self.kwargs.get('slug'),
			'product_id': int(self.kwargs.get('product_id'))
		})
		return kwargs

	def form_valid(self, form):
		form.save()
		return super().form_valid(form)

	def _get_product(self):
		return get_object_or_404(models.ShoppingCart, id=int(self.kwargs.get('product_id')))


class BaseProductListView(TemplateView):
	template_name = None
	success_url = None

	def post(self, *args, **kwargs):
		self.set_success_url()
		return HttpResponseRedirect(self.get_success_url())

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		products = product_handler.get_sorted_products(self.request)
		context.update({
			'category_list': self.get_category_list(products),
			'products': products,
			'search': self.request.GET.get("search"),
			'sort': self.request.GET.get("sort"),
		})
		return context

	@staticmethod
	def get_category_list(products):
		category_list = []

		for category in models.Product.CATEGORY:
			category_list.append((
				category[0],
				category[1],
				list(filter(lambda x: x.category == category[0], products))
			))
		return category_list

	def get_success_url(self):
		return str(self.success_url)

	def set_success_url(self):
		sort = 'sort=' + self.request.POST.get('sort')
		self.success_url += '?' + sort

		if self.request.POST.get('search') != '':
			search = 'search=' + self.request.POST.get('search')
			self.success_url += '&' + search


class ProductListView(BaseProductListView):
	template_name = 'product_pages/products.html'
	success_url = '/products/'


class AddProductListView(PermissionRequiredMixin, BaseProductListView):
	template_name = 'product_pages/add_product_list.html'
	permission_required = ('is_auth', 'is_company')
	success_url = '/add_product_list/'


class AddProductView(PermissionRequiredMixin, FormView):
	template_name = 'product_pages/add_product.html'
	permission_required = ('is_auth', 'is_company')
	form_class = forms.AddProductForm
	success_url = '/add_product_list/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.update({
			'characteristics_list': product_handler.get_characteristic_list(self.kwargs),
			'product': get_object_or_404(models.Product, slug=self.kwargs.get('slug')),
		})
		return context

	def get_form_kwargs(self):
		kwargs = super(AddProductView, self).get_form_kwargs()
		kwargs.update({
			'user': self.request.user,
			'slug': self.kwargs.get('slug'),
		})
		return kwargs

	def form_valid(self, form):
		form.save()
		return super().form_valid(form)


class ShoppingCartView(FormView):
	template_name = 'ordering_pages/shopping_cart.html'
	form_class = forms.OrderingForm
	success_url = '/ordering/'

	def post(self, request, *args, **kwargs):
		if len(models.ShoppingCart.objects.filter(user=request.user)) == 0:
			form = self.get_form()
			form.errors['empty'] = 'Необходимо добавить хотя бы один продукт в корзину!'
			return self.form_invalid(form)
		return super().post(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['products'] = models.Product.objects.all()

		if self.request.user.is_authenticated:
			context['products_cart'] = models.ShoppingCart.objects.filter(user=self.request.user)
		return context

	def get_form_kwargs(self):
		kwargs = super(ShoppingCartView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def form_valid(self, form):
		form.save()
		return super().form_valid(form)


class OrderingView(PermissionRequiredMixin, FormView):
	template_name = 'ordering_pages/ordering.html'
	permission_required = ('is_auth', 'is_not_company')
	form_class = forms.OrderDetailForm
	success_url = '/product_distribution/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['company_list'] = models.Company.objects.all()
		return context

	def get_form_kwargs(self):
		kwargs = super(OrderingView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def form_valid(self, form):
		obj = form.save()
		if len(obj.address_and_deadline.get('items')) == 1:
			self.success_url = '/orders/#add_order'
		return super().form_valid(form)


class ProductDistributionView(PermissionRequiredMixin, FormView):
	template_name = 'ordering_pages/product_distribution.html'
	permission_required = ('is_auth', 'is_not_company')
	form_class = forms.ProductDistributionForm
	success_url = '/orders/#add_order'

	def post(self, request, *args, **kwargs):
		if not self.is_normal_count_products():
			form = self.get_form()
			form.errors['count'] = 'Неверное количество продуктов!'
			return self.form_invalid(form)
		return super().post(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.update({
			'products': models.OrderProduct.objects.filter(order__id=self.request.user.order_id),
			'address_list': self.get_address_list(),
		})
		return context

	def get_form_kwargs(self):
		kwargs = super(ProductDistributionView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def form_valid(self, form):
		form.save()
		return super().form_valid(form)

	def is_normal_count_products(self):
		for product in models.OrderProduct.objects.filter(order__id=self.request.user.order_id):
			counts = map(int, dict(self.request.POST).get('count-' + str(product.id)))
			if sum(counts) != product.total_count:
				return False
		return True

	def get_address_list(self):
		order_detail = get_object_or_404(models.OrderDetail, order__id=self.request.user.order_id)
		result = []
		item_id = 0
		for item in order_detail.address_and_deadline.get('items'):
			result.append((item_id, item[0]))
			item_id += 1
		return result


class NewOrdersView(PermissionRequiredMixin, FormView):
	template_name = 'account_pages/new_orders.html'
	permission_required = ('is_auth', 'is_company')
	form_class = forms.NewOrdersForm
	success_url = '/payment/'

	def post(self, request, *args, **kwargs):
		if self.request.POST.get('prod') is None:
			form = self.get_form()
			form.errors[self.request.POST.get('order')] = 'Не выбрано ни одного продукта!'
			return self.form_invalid(form)
		return super().post(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.update({
			'company': get_object_or_404(models.Company, user=self.request.user),
			'products': models.ProductCompany.objects.filter(company__user=self.request.user),
			'new_orders': order_handler.get_new_orders(self.request.user),
			'accepted_orders': order_handler.get_accepted_orders_for_company(self.request.user),
			'completed_orders': order_handler.get_completed_orders_for_company(self.request.user),
		})
		return context

	def get_form_kwargs(self):
		kwargs = super(NewOrdersView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def form_valid(self, form):
		self.success_url = '/payment/%s/' % self.request.POST.get('order')
		form.save()
		return super().form_valid(form)


class OrderExecutionProposalView(PermissionRequiredMixin, TemplateView):
	template_name = 'ordering_pages/offers_selection.html'
	permission_required = ('is_auth', 'is_not_company')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.update({
			'proposals': proposals_order_execution.start(int(self.kwargs.get('order_id'))),
			'order_id': self.kwargs.get('order_id'),
		})
		return context


class PaymentView(PermissionRequiredMixin, FormView):
	template_name = 'ordering_pages/payment.html'
	permission_required = ('is_auth', 'is_company')
	form_class = forms.PaymentForm
	success_url = '/new_orders/#successful'


class LoginView(BaseLoginView):
	template_name = 'account_pages/login.html'
	redirect_authenticated_user = True

	def get_success_url(self):
		if self.request.user.is_admin:
			redirect_url = '/admin_panel/'
			return redirect_url
		return super().get_success_url()


class PersonalAccountView(PermissionRequiredMixin, FormView):
	template_name = 'account_pages/client_personal_account.html'
	permission_required = 'is_auth'
	form_class = forms.PersonalAccountUserForm
	success_url = '/personal_account/'

	def post(self, request, *args, **kwargs):
		if self.request.POST.get('form_name') == 'user':
			self.form_class = forms.PersonalAccountUserForm
		elif self.request.POST.get('form_name') == 'company':
			self.form_class = forms.PersonalAccountCompanyForm
		return super().post(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['notifications'] = self._get_notification()

		if self.request.user.is_company:
			context.update({
				'company': get_object_or_404(models.Company, user=self.request.user),
				'products': models.ProductCompany.objects.filter(company__user=self.request.user),
			})
		return context

	def get_form_kwargs(self):
		kwargs = super(PersonalAccountView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def form_valid(self, form):
		form.save()
		return super().form_valid(form)

	def _get_notification(self):
		notification = []

		if self.request.user.is_company:
			company = get_object_or_404(models.Company, user=self.request.user)
			if company.moderator_message != '':
				notification.append(company.moderator_message)

			if company.notification != '':
				notification.append(company.notification)
		else:
			if self.request.user.notification != '':
				notification.append(self.request.user.notification)
		return notification


class OrdersListView(PermissionRequiredMixin, TemplateView):
	template_name = 'account_pages/orders_list.html'
	permission_required = ('is_auth', 'is_not_company')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.update({
			'new_orders': models.OrderDetail.objects.filter(order__user=self.request.user, status=1)[::-1],
			'executable_orders': order_handler.get_executable_orders_for_user(self.request.user),
			'completed_orders': order_handler.get_completed_orders_for_user(self.request.user),
		})
		return context


class BecomeCompanyView(PermissionRequiredMixin, FormView):
	template_name = 'account_pages/become_company.html'
	permission_required = 'is_auth'
	form_class = forms.BecomeCompanyForm
	success_url = '/personal_account/'

	def form_valid(self, form):
		disk = yadisk.YaDisk(token=settings.YANDEX_API_TOKEN)
		if disk.check_token():
			form.save()
		else:
			return HttpResponseRedirect('/become_company_fail/')
		return super().form_valid(form)

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs


class AdminPanelView(PermissionRequiredMixin, FormView):
	template_name = 'account_pages/admin_panel.html'
	permission_required = 'is_admin'
	form_class = forms.AdminPanelForm
	success_url = '/admin_panel/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['company_list'] = models.Company.objects.filter(is_verification=False, is_verified=False)
		return context

	def form_valid(self, form):
		form.save()
		return super().form_valid(form)
