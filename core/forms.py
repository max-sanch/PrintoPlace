from phonenumber_field.formfields import PhoneNumberField
from django.core.validators import FileExtensionValidator
from django_registration.forms import RegistrationForm
from django.shortcuts import get_object_or_404
from django import forms

from core import models
from core.services import order_handler, api_handler


class CustomUserForm(RegistrationForm):
	is_receiving_news = forms.BooleanField(required=False)
	phone_number = PhoneNumberField(required=False)

	class Meta(RegistrationForm.Meta):
		model = models.User
		fields = [
			'first_name', 'last_name', 'email', 'phone_number', 'company_name',
			'password1', 'password2', 'is_receiving_news'
		]

	def save(self, commit=True):
		user = super().save(commit=False)
		user.set_password(self.cleaned_data["password1"])
		user.addresses = {'items': []}

		if commit:
			user.save()
		return user


class AdminPanelForm(forms.Form):
	moderator_message = forms.CharField(label="Сообщение для пользователя", required=False)
	is_verification = forms.BooleanField(label="Верифицировать пользователя", required=False)
	company_user = forms.CharField(widget=forms.HiddenInput, required=False)

	class Meta:
		model = models.Company
		fields = ['moderator_message', 'is_verification', 'company_user']

	def save(self, commit=True):
		company = get_object_or_404(models.Company, user__email=self.data.get('company_user'))
		company.moderator_message = 'Ошибка верификации: ' + self.data.get('moderator_message')
		company.is_verified = True

		if self.data.get('is_verification') is not None:
			company.moderator_message = 'Вы успешно прошли верификацию!'
			company.is_verification = True

		api_handler.delete_file_company(company.pk)

		if commit:
			company.save()
		return company


class ProductPageForm(forms.Form):
	class Meta:
		model = models.ShoppingCart

	def __init__(self, user, slug, product_id=None, *args, **kwargs):
		super(ProductPageForm, self).__init__(*args, **kwargs)
		self.product_id = product_id
		self.user = user
		self.slug = slug

	def save(self, commit=True):
		post = dict(self.data)
		char = {x: post[x][0] for x in post if x not in ('csrfmiddlewaretoken', 'next', 'design', 'count')}

		if self.product_id is None:
			shopping_cart = models.ShoppingCart(
				user=self.user,
				product=get_object_or_404(models.Product, slug=self.slug),
				characteristics=char,
				design=self.files.getlist('design')[0],
				other_design=[],
				count=int(self.data.get('count'))
			)
		else:
			shopping_cart = get_object_or_404(models.ShoppingCart, id=self.product_id)
			if self.files.get('design') is not None:
				shopping_cart.design = self.files.getlist('design')[0]
			shopping_cart.characteristics = char
			shopping_cart.count = int(self.data.get('count'))

		if commit:
			shopping_cart.save()
		return shopping_cart


class AddProductForm(forms.Form):
	class Meta:
		model = models.ProductCompany

	def __init__(self, user, slug, *args, **kwargs):
		super(AddProductForm, self).__init__(*args, **kwargs)
		self.user = user
		self.slug = slug

	def save(self, commit=True):
		post = dict(self.data)
		char = {x: post[x] for x in post if x not in ('csrfmiddlewaretoken', 'next')}
		product_company = models.ProductCompany(
			company=models.Company.objects.get(user=self.user),
			characteristics=char,
			product=models.Product.objects.get(slug=self.slug)
		)

		if commit:
			product_company.save()
		return product_company


class OrderingForm(forms.Form):
	class Meta:
		model = models.Order

	def __init__(self, user, *args, **kwargs):
		super(OrderingForm, self).__init__(*args, **kwargs)
		self.user = user

	def save(self, commit=True):
		if self.user.order_id != 0 and self.user.order_id is not None:
			self._delete_order()

		order = models.Order(
			user=self.user,
			price=0,
		)

		if commit:
			order.save()
			order_handler.set_active_order_id(self.user, order.pk)
			order.price = self._get_price_and_add_products(order)
			order.save()
		return order

	def _get_price_and_add_products(self, order):
		price = 0
		for prod in models.ShoppingCart.objects.filter(user=self.user):
			price += prod.product.price * prod.count
			order_product = models.OrderProduct(
				order=order,
				product=prod.product,
				characteristics=prod.characteristics,
				design_url=prod.design.url,
				other_design_url=[],
				total_count=prod.count,
				price=prod.product.price * prod.count,
				count_and_address={'items': []}
			)
			order_product.save()
		return price

	def _delete_order(self):
		order = models.Order.objects.get(id=self.user.order_id)
		order.delete()
		order_handler.set_active_order_id(self.user, 0)


class OrderDetailForm(forms.Form):
	class Meta:
		model = models.OrderDetail

	def __init__(self, user, *args, **kwargs):
		super(OrderDetailForm, self).__init__(*args, **kwargs)
		self.user = user

	def save(self, commit=True):
		post = dict(self.data)
		order_detail = models.OrderDetail(
			order=get_object_or_404(models.Order, id=self.user.order_id),
			address_and_deadline=self.get_address_and_deadline(post),
			comment=post['comment'][0],
			status=0,
		)

		if len(order_detail.address_and_deadline['items']) == 1:
			self.set_count_and_address_to_product()
			order_detail.status = 1

		if commit:
			order_detail.save()
		return order_detail

	@staticmethod
	def get_address_and_deadline(post):
		result = {'items': []}
		for x in range(len(post['address'])):
			result['items'].append((
				post['address'][x],
				post['date'][x],
				post['time'][x]
			))
		return result

	def set_count_and_address_to_product(self):
		for order_product in models.OrderProduct.objects.filter(order__id=self.user.order_id):
			order_product.count_and_address = {'0': int(order_product.total_count)}
			order_product.save()

		order_handler.set_active_order_id(self.user, 0)
		order_handler.clear_cart(self.user)


class ProductDistributionForm(forms.Form):
	class Meta:
		model = models.OrderDetail

	def __init__(self, user, *args, **kwargs):
		super(ProductDistributionForm, self).__init__(*args, **kwargs)
		self.user = user

	def save(self, commit=True):
		post = dict(self.data)

		for order_product in models.OrderProduct.objects.filter(order__id=self.user.order_id):
			addresses = dict()
			for x in range(len(post['address-' + str(order_product.id)])):
				address_id = int(post['address-' + str(order_product.id)][x])
				count = addresses.get(address_id, 0) + int(post['count-' + str(order_product.id)][x])
				addresses.update({address_id: count})
			order_product.count_and_address = addresses
			order_product.save()

		order_detail = get_object_or_404(models.OrderDetail, order__id=self.user.order_id)
		order_detail.status = 1
		order_handler.set_active_order_id(self.user, 0)
		order_handler.clear_cart(self.user)

		if commit:
			order_detail.save()

		return order_detail


class NewOrdersForm(forms.Form):
	class Meta:
		model = models.OrderExecutionProposal

	def __init__(self, user, *args, **kwargs):
		super(NewOrdersForm, self).__init__(*args, **kwargs)
		self.user = user
		self.total_price = 0

	def save(self, commit=True):
		post = dict(self.data)
		order_execution_proposal = models.OrderExecutionProposal(
			order=get_object_or_404(models.Order, id=int(post['order'][0])),
			company=get_object_or_404(models.Company, user=self.user),
			order_products=self.get_order_products(),
			price=self.total_price,
			is_partially=self.get_partially(post.get('partially')),
		)

		if commit:
			order_execution_proposal.save()
		return order_execution_proposal

	def get_order_products(self):
		post = dict(self.data)
		result = dict()
		for prod in post.get('prod'):
			if len(post.get('count-' + prod)) != post.get('count-' + prod).count('0'):
				data = []
				for x in range(len(post['count-' + prod])):
					if int(post['count-' + prod][x]) != 0:
						product_price = get_object_or_404(models.OrderProduct, id=int(prod)).product.price
						price = int(post['count-' + prod][x]) * product_price
						self.total_price += price
						data.append((
							int(post['count-' + prod][x]),
							int(post['address-' + prod][x]),
							price
						))
				result.update({prod: data})
		return result

	@staticmethod
	def get_partially(partially):
		if partially[0] == 'on':
			return True
		return False


class PaymentForm(forms.Form):
	class Meta:
		model = models.Order


class PersonalAccountUserForm(forms.Form):
	class Meta:
		model = models.User

	def __init__(self, user, *args, **kwargs):
		super(PersonalAccountUserForm, self).__init__(*args, **kwargs)
		self.user = user

	def save(self, commit=True):
		user = get_object_or_404(models.User, id=self.user.id)
		user.first_name = self.data.get('first_name')
		user.last_name = self.data.get('last_name')
		user.phone_number = self.data.get('phone_number')
		user.company_name = self.data.get('company_name')
		if commit:
			user.save()
		return user


class PersonalAccountCompanyForm(forms.Form):
	class Meta:
		model = models.Company

	def __init__(self, user, *args, **kwargs):
		super(PersonalAccountCompanyForm, self).__init__(*args, **kwargs)
		self.user = user

	def save(self, commit=True):
		company = get_object_or_404(models.Company, user=self.user)
		company.addresses = [] if self.data.get('address') is None else dict(self.data).get('address')

		if self.files.get('logo') is not None:
			company.logo = self.files.get('logo')

		if commit:
			company.save()
		return company


class BecomeCompanyForm(forms.Form):
	company_files = forms.FileField(max_length=50, validators=[FileExtensionValidator(['pdf'])])

	class Meta:
		model = models.Company

	def __init__(self, user, *args, **kwargs):
		super(BecomeCompanyForm, self).__init__(*args, **kwargs)
		self.user = user

	def save(self, commit=True):
		company, is_created = models.Company.objects.get_or_create(
			user=self.user,
			defaults={
				'inn': self.data.get('inn'),
				'moderator_message': 'Ваша заявка отправлена на рассмотрение!',
				'addresses': [],
			},
		)
		if not is_created:
			company.inn = self.data.get('inn')
			company.moderator_message = 'Ваша заявка отправлена на рассмотрение!'
			company.is_verified = False

		api_handler.upload_file_company(company.pk, self.files.get('company_files'))
		user = get_object_or_404(models.User, id=self.user.id)
		user.company_name = self.data.get('company_name')
		user.phone_number = self.data.get('phone_number')
		user.is_company = True

		if commit:
			user.save()
			company.save()
		return company

	def save_file(self):
		pass
