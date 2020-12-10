from django.views.generic.edit import FormView, UpdateView
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.contrib.auth.views import LoginView as BaseLoginView
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render
from django.http import HttpResponse

import requests

from core import models, forms
from core.services import (
	order_handler,
	create_product,
	notification_handler,
	proposals_order_execution
)


class HomePageView(TemplateView):
	template_name = 'home_page/index.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['products'] = models.Product.objects.all()
		return context


class ProductPageView(FormView):
	template_name = 'product_pages/one_product.html'
	form_class = forms.ShoppingCartForm
	success_url = '/product/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['product'] = models.Product.objects.get(slug=self.kwargs.get('slug'))
		context['characteristic_list'] = get_characteristic_list(self.kwargs)
		return context

	def form_valid(self, form):
		self.save()
		return super().form_valid(form)

	def save(self):
		self.success_url = '/product/' + self.kwargs.get('slug') + '/#successful'
		post = dict(self.request.POST)
		char = {x: post[x][0] for x in post if x not in ('csrfmiddlewaretoken', 'next', 'design', 'count')}
		obj = models.ShoppingCart(
			user=models.User.objects.get(id=self.request.user.id),
			product=models.Product.objects.get(slug=self.kwargs.get('slug')),
			characteristics=char,
			design=self.request.FILES.get('design'),
			count=int(post.get('count')[0])
		)
		obj.save()


class ProductUpdateView(FormView):
	template_name = 'product_pages/product_update.html'
	form_class = forms.ShoppingCartForm
	success_url = '/shopping_cart/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		product = get_object_or_404(models.ShoppingCart, id=int(self.kwargs.get('product_id')))
		context['product'] = product.product
		context['characteristic_list'] = get_characteristic_list(self.kwargs, product.product)
		context['product_data'] = product
		return context

	def form_valid(self, form):
		self.save()
		return super().form_valid(form)

	def save(self):
		post = dict(self.request.POST)
		char = {x: post[x][0] for x in post if x not in ('csrfmiddlewaretoken', 'next', 'design', 'count')}
		obj = get_object_or_404(models.ShoppingCart, id=int(self.kwargs.get('product_id')))

		if self.request.FILES.get('design') is not None:
			obj.design = self.request.FILES.get('design')

		obj.characteristics = char
		obj.count = int(post.get('count')[0])
		obj.save()


class ProductListView(FormView):
	template_name = 'product_pages/products.html'
	form_class = forms.OrderingForm
	success_url = '/products/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		sort = self.request.GET.get("sort")
		search = self.request.GET.get("search")
		products = sorted(models.Product.objects.all(), key=lambda x: x.price)
		category_list = []

		if search is not None and search != '':
			products = list(filter(lambda x: search.lower() in x.name.lower(), products))

		if sort is not None:
			if sort == 'price_down':
				products = sorted(products, key=lambda x: x.price)[::-1]
			elif sort == 'popularity':
				products = sorted(products, key=lambda x: x.name)
			elif sort == 'name':
				products = sorted(products, key=lambda x: x.name)

		for category in models.Product.CATEGORY:
			category_list.append((
				category[0],
				category[1],
				list(filter(lambda x: x.category == category[0], products))
			))

		context['category_list'] = category_list
		context['products'] = products
		context['search'] = self.request.GET.get("search")
		context['sort'] = self.request.GET.get("sort")

		return context

	def form_valid(self, form):
		sort = 'sort=' + self.request.POST.get('sort')
		self.success_url += '?' + sort

		if self.request.POST.get('search') != '':
			search = 'search=' + self.request.POST.get('search')
			self.success_url += '&' + search

		return super().form_valid(form)


class AddProductListView(ListView):
	template_name = 'product_pages/add_product_list.html'
	model = models.Product
	paginate_by = 150

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		category_list = []

		for category in models.Product.CATEGORY:
			category_list.append((
				category[0],
				category[1],
				models.Product.objects.filter(category=category[0])
			))

		context['category_list'] = category_list

		return context


class AddProductView(FormView):
	template_name = 'product_pages/add_product.html'
	form_class = forms.AddProductForm
	success_url = '/add_product_list/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['characteristics_list'] = get_characteristic_list(self.kwargs)
		context['product'] = get_object_or_404(models.Product, slug=self.kwargs.get('slug'))
		return context

	def form_valid(self, form):
		self.save()
		return super().form_valid(form)

	def save(self):
		post = dict(self.request.POST)
		char = {x: post[x] for x in post if x not in ('csrfmiddlewaretoken', 'next')}
		obj = models.ProductCompany(
			company=models.Company.objects.get(user=self.request.user),
			characteristics=char,
			product=models.Product.objects.get(slug=self.kwargs.get('slug'))
		)
		obj.save()


class ShoppingCartView(FormView):
	template_name = 'ordering_pages/shopping_cart.html'
	form_class = forms.OrderingForm
	success_url = '/ordering/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		if self.request.user.is_authenticated:
			context['products_cart'] = models.ShoppingCart.objects.filter(user=self.request.user)

		context['products'] = models.Product.objects.all()
		return context

	def form_valid(self, form):
		if self.request.user.order_id != 0 and self.request.user.order_id is not None:
			obj = models.Order.objects.get(id=self.request.user.order_id)
			obj.delete()
			self.set_order_id_user(0)

		is_save = self.save()
		if is_save:
			return super().form_valid(form)

		form.errors['empty'] = 'Необходимо добавить хотя бы один продукт в корзину!'
		return self.form_invalid(form)

	def save(self):
		products = models.ShoppingCart.objects.filter(user=self.request.user)
		price = 0

		if len(products) == 0:
			return False

		new_order = models.Order(
			user=self.request.user,
			price=price,
		)
		new_order.save()
		self.set_order_id_user(new_order.pk)

		for prod in products:
			price += prod.product.price * prod.count
			new_order_product = models.OrderProduct(
				order=new_order,
				product=prod.product,
				characteristics=prod.characteristics,
				design_url=prod.design.url,
				total_count=prod.count,
				price=prod.product.price * prod.count,
				count_and_address={'items': []}
			)
			new_order_product.save()

		new_order.price = price
		new_order.save()

		return True

	def set_order_id_user(self, order_id):
		user = models.User.objects.get(id=self.request.user.id)
		user.order_id = order_id
		user.save()


class OrderingView(FormView):
	template_name = 'ordering_pages/ordering.html'
	form_class = forms.OrderDetailForm
	success_url = '/product_distribution/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['company_list'] = models.Company.objects.all()
		return context

	def form_valid(self, form):
		self.save()
		return super().form_valid(form)

	def save(self):
		post = dict(self.request.POST)
		obj = models.OrderDetail(
			order=get_object_or_404(models.Order, id=self.request.user.order_id),
			address_and_deadline=self.get_address_and_deadline(post),
			comment=post['comment'][0],
			status=1,
		)
		obj.save()

	def get_address_and_deadline(self, post):
		result = {'items': []}
		for x in range(len(post['address'])):
			result['items'].append((post['address'][x], post['date'][x], post['time'][x]))

		if len(result['items']) == 1:
			self.set_count_and_address_to_product()

		return result

	def set_count_and_address_to_product(self):
		products = models.OrderProduct.objects.filter(order__id=self.request.user.order_id)
		for product in products:
			product.count_and_address = {'0': int(product.total_count)}
			product.save()
		user = get_object_or_404(models.User, id=self.request.user.id)
		user.order_id = 0
		user.save()
		clear_cart(user)
		self.success_url = '/orders/#add_order'


class ProductDistributionView(FormView):
	template_name = 'ordering_pages/product_distribution.html'
	form_class = forms.OrderDetailForm
	success_url = '/orders/#add_order'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['products'] = models.OrderProduct.objects.filter(order__id=self.request.user.order_id)
		context['address_list'] = self.get_address_list()
		return context

	def get_address_list(self):
		order_detail = models.OrderDetail.objects.get(order__id=self.request.user.order_id)
		result = []
		item_id = 0
		for item in order_detail.address_and_deadline['items']:
			result.append((item_id, item[0]))
			item_id += 1
		return result

	def form_valid(self, form):
		self.save()
		return super().form_valid(form)

	def save(self):
		post = dict(self.request.POST)
		order_products = models.OrderProduct.objects.filter(order__id=self.request.user.order_id)

		for order_product in order_products:
			addresses = dict()
			for x in range(len(post['address-'+str(order_product.id)])):
				address_id = int(post['address-'+str(order_product.id)][x])
				count = addresses.get(address_id, 0) + int(post['count-'+str(order_product.id)][x])
				addresses.update({address_id: count})
			order_product.count_and_address = addresses
			order_product.save()

		user = get_object_or_404(models.User, id=self.request.user.id)
		user.order_id = 0
		user.save()
		clear_cart(user)


class NewOrdersView(FormView):
	template_name = 'account_pages/new_orders.html'
	form_class = forms.OrderDetailForm
	success_url = '/payment/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		context['company'] = models.Company.objects.get(user=self.request.user)
		context['products'] = models.ProductCompany.objects.filter(company__user=self.request.user)
		context['new_orders'] = self.get_new_orders()
		context['accepted_orders'] = self.get_accepted_orders()

		return context

	def get_accepted_orders(self):
		orders_execution = models.OrderExecution.objects.filter(company__user=self.request.user)
		result = []
		for order in orders_execution:
			order_detail = models.OrderDetail.objects.get(order__id=order.order.id)
			order_data = [order.order.id, order_detail.datetime.date, order.status, 0, order.order.user, [], order.id]
			for product in order.order_products.items():
				order_prod = models.OrderProduct.objects.get(id=int(product[0]))
				price = 0
				items = []

				for item in product[1]:
					price += item[2]
					address = order_detail.address_and_deadline['items'][item[1]][0]
					data = '%s %s' % (
						order_detail.address_and_deadline['items'][item[1]][1],
						order_detail.address_and_deadline['items'][item[1]][2]
					)
					items.append((item[0], address, data))

				order_data[3] += price
				order_data[5].append((
					order_prod.design_url, order_prod.product.name, price, order_prod.characteristics, items
				))
			result.append(order_data)
		return result

	def get_new_orders(self):
		orders = models.OrderDetail.objects.filter(status=1)[::-1]
		my_proposals = []
		result = []

		for proposal in models.OrderExecutionProposal.objects.filter(company__user=self.request.user):
			my_proposals.append(proposal.order.id)

		for order in orders:
			if order.order.id in my_proposals:
				result.append((models.OrderExecutionProposal.objects.get(order__id=order.order.id), 0))
				continue
			result.append((order, 1))

		return result

	def form_valid(self, form):
		post = dict(self.request.POST)
		if post.get('prod') is None:
			form.errors[post['order'][0]] = 'Не выбрано ни одного продукта!'
			return self.form_invalid(form)

		result = dict()
		total_price = 0
		for prod in post.get('prod'):
			if len(post.get('count-'+prod)) - post.get('count-'+prod).count('0') == 0:
				form.errors[post['order'][0]] = 'Указанно 0 шт на все адресса!'
				return self.form_invalid(form)
			else:
				data = []
				for x in range(len(post['count-'+prod])):
					product_price = get_object_or_404(models.OrderProduct, id=int(prod)).product.price
					price = int(post['count-'+prod][x]) * product_price
					total_price += price
					data.append((
						int(post['count-'+prod][x]),
						int(post['address-'+prod][x]),
						price
					))
				result.update({prod: data})
		self.save(post, result, total_price)
		return super().form_valid(form)

	def save(self, post, order_products, total_price):
		self.success_url = '/payment/%s/' % post['order'][0]
		obj = models.OrderExecutionProposal(
			order=get_object_or_404(models.Order, id=int(post['order'][0])),
			company=get_object_or_404(models.Company, user=self.request.user),
			order_products=order_products,
			price=total_price,
			is_partially=self.get_partially(post.get('partially')),
		)
		obj.save()

	@staticmethod
	def get_partially(partially):
		if partially[0] == 'on':
			return True
		return False


class OrderExecutionProposalView(TemplateView):
	template_name = 'ordering_pages/offers_selection.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['proposals'] = proposals_order_execution.start(int(self.kwargs.get('order_id')))
		context['order_id'] = self.kwargs.get('order_id')

		return context


class PaymentView(FormView):
	template_name = 'ordering_pages/payment.html'
	form_class = forms.OrderDetailForm
	success_url = '/new_orders/#successful'

	def form_valid(self, form):
		return super().form_valid(form)


class LoginView(BaseLoginView):
	template_name = 'account_pages/login.html'
	redirect_authenticated_user = True

	def get_success_url(self):
		if self.request.user.is_admin:
			redirect_url = '/admin_panel/'
			return redirect_url
		return super().get_success_url()


class PersonalAccountView(FormView):
	template_name = 'account_pages/client_personal_account.html'
	form_class = forms.BecomeCompanyForm
	success_url = '/personal_account/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		if self.request.user.is_company:
			context['company'] = models.Company.objects.get(user=self.request.user)
			context['products'] = models.ProductCompany.objects.filter(company__user=self.request.user)
		context['notifications'] = self.get_notification()

		return context

	def get_notification(self):
		user = self.request.user
		notification = []

		if user.is_company:
			company = models.Company.objects.get(user=user)
			if company.notification != '':
				notification.append(company.notification)

			if company.moderator_message != '':
				notification.append(company.moderator_message)

		else:
			if user.notification != '':
				notification.append(user.notification)

		return notification

	def form_valid(self, form):
		self.save()
		return super().form_valid(form)

	def save(self):
		if self.request.POST.get('form_name') == 'user':
			user = get_object_or_404(models.User, id=self.request.user.id)
			user.first_name = self.request.POST.get('first_name')
			user.last_name = self.request.POST.get('last_name')
			user.phone_number = self.request.POST.get('phone_number')
			user.company_name = self.request.POST.get('company_name')
			user.save()

		elif self.request.POST.get('form_name') == 'company':
			company = get_object_or_404(models.Company, user_id=self.request.user.id)

			if self.request.FILES.get('logo') is not None:
				company.logo = self.request.FILES.get('logo')

			if self.request.POST.get('address') is not None:
				company.addresses = dict(self.request.POST).get('address')
			else:
				company.addresses = []

			company.save()


class OrdersListView(TemplateView):
	template_name = 'account_pages/orders_list.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		context['new_orders'] = models.OrderDetail.objects.filter(order__user=self.request.user, status=1)[::-1]
		context['executable_orders'] = self.get_executable_orders()
		context['completed_orders'] = models.OldOrder.objects.filter(user=self.request.user)

		return context

	def get_executable_orders(self):
		result = []
		order_detail_list = models.OrderDetail.objects.filter(
			order__user=self.request.user
		).exclude(status=1).exclude(status=5)

		for order_detail in order_detail_list[::-1]:
			order_data = [order_detail.order.id, order_detail.datetime.date, order_detail.status, 0, []]
			executor_list = models.OrderExecution.objects.filter(order__id=order_detail.order.id)

			for executor in executor_list:
				if executor.company.logo == '':
					logo = '/static/image/none_img.png'
				else:
					logo = executor.company.logo.url

				company_data = [
					logo,
					executor.company.user.company_name,
					executor.company.user.phone_number,
					executor.company.user.email,
					executor.company.addresses,
					executor.status,
					dict(),
					executor.id
				]

				for prod in executor.order_products.items():
					items = []
					price = 0

					for item in prod[1]:
						price += item[2]
						items.append((
							item[0],
							order_detail.address_and_deadline['items'][int(item[1])][0],
							'%s %s' % (
								order_detail.address_and_deadline['items'][int(item[1])][1],
								order_detail.address_and_deadline['items'][int(item[1])][2]
							)
						))

					order_data[3] += price
					company_data[6].update({prod[0]: (price, items)})
				order_data[4].append(company_data)
			result.append(order_data)
		return result


class BecomeCompanyView(FormView):
	template_name = 'account_pages/become_company.html'
	form_class = forms.BecomeCompanyForm
	success_url = '/personal_account/'

	def form_valid(self, form):
		self.save()
		return super().form_valid(form)

	def save(self):
		user = models.User.objects.get(id=self.request.user.id)
		company = models.Company(
			user=user,
			inn=self.request.POST.get('inn'),
			addresses=[]
		)
		company.save()
		user.company_name = self.request.POST.get('company_name')
		user.phone_number = self.request.POST.get('phone_number')
		user.is_company = True
		user.save()


class UpdateCompanyView(UpdateView):
	template_name = 'account_pages/become_company.html'
	model = models.Company
	fields = ['addresses', 'inn', 'company_files']
	success_url = '/personal_account/'
	object = None

	def get_object(self, queryset=None):
		return get_object_or_404(models.Company, user=self.request.user)

	def form_valid(self, form):
		self.object = form.save()
		self.object.is_verified = False
		self.object.moderator_message = ''
		self.object.save()
		return HttpResponseRedirect(self.get_success_url())


class AdminPanelView(FormView):
	template_name = 'account_pages/admin_panel.html'
	form_class = forms.AdminPanelForm
	success_url = '/admin_panel/'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['company_list'] = models.Company.objects.filter(is_verification=False, is_verified=False)
		return context

	def form_valid(self, form):
		self.save()
		return super().form_valid(form)

	def save(self):
		user = models.User.objects.get(email=self.request.POST.get('company_user'))
		company = models.Company.objects.get(user=user)
		company.moderator_message = self.request.POST.get('moderator_message')
		company.is_verified = True

		if self.request.POST.get('is_verification') is not None:
			company.is_verification = True

		company.save()


def delete_notification_view(request):
	notification_handler.delete_notification(request)
	return HttpResponseRedirect('/personal_account/')


def set_order_status_view(request, ord_exec_id):
	order_handler.set_order_execution_status(int(ord_exec_id))
	if request.user.is_company:
		return HttpResponseRedirect('/new_orders/')
	return HttpResponseRedirect('/orders/')


def delete_order_view(request, order_id, context):
	order_handler.delete_order(order_id, context)
	if request.user.is_company:
		return HttpResponseRedirect('/new_orders/')
	return HttpResponseRedirect('/orders/')


def repeat_order_view(request, order_id):
	order_handler.repeat_order(request, order_id)
	return HttpResponseRedirect('/ordering/')


def delete_product_in_cart_view(request, product_id):
	obj = get_object_or_404(models.ShoppingCart, id=product_id, user=request.user)
	obj.delete()
	return HttpResponseRedirect('/shopping_cart/')


def city_selection_view(request):
	if request.method == 'POST':
		city = request.POST.get('city')
		response = HttpResponseRedirect('/')
		response.set_cookie('city', city)
		return response
	else:
		return render(request, 'other_pages/city_selection.html')


def inn_search_view(request, inn):
	try:
		search = requests.get('https://api-fns.ru/api/egr?req=' + inn + '&key=d38f57835907b8de4d481c100f79f0eb2f861f2e')
		json = search.json()
		if json.get('items', False):
			text = json['items'][0]['ЮЛ']['НаимСокрЮЛ']
			return HttpResponse(text)
		else:
			return HttpResponse('Не найдено')
	except(requests.RequestException, ValueError):
		return HttpResponse('Не найдено')


def create_product_view(request):
	create_product.start()
	return HttpResponseRedirect('/products/')


def choose_offer_view(request, order_id, offer):
	if request.user == get_object_or_404(models.Order, id=int(order_id)).user:
		order_handler.choose_offer(int(order_id), int(offer))
		return HttpResponseRedirect('/orders/#add_offer')
	else:
		return HttpResponseRedirect('/orders/')


def clear_cart(user):
	products = models.ShoppingCart.objects.filter(user=user)
	for product in products:
		product.delete()


def get_characteristic_list(kwargs, product=None):
	slug = kwargs.get('slug')

	if slug is not None:
		product = models.Product.objects.get(slug=slug)

	characteristics = models.ProductCharacteristics.objects.get(product=product)
	char_list = [x for x in characteristics.__dict__.items()]
	characteristic_list = []

	for char in char_list[3:]:
		if char[1].get('default', 0) is not None:
			name = models.ProductCharacteristics._meta.get_field(char[0]).verbose_name
			characteristic_list.append((name, char[1]))

	return characteristic_list
