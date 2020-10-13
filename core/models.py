from django.conf import settings
from django.db import models
from django.core.mail import send_mail
from django.contrib.postgres.fields import HStoreField, ArrayField
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from phonenumber_field.modelfields import PhoneNumberField


class UserManager(BaseUserManager):
	def create_user(
		self, email, first_name, last_name, is_receiving_news,
		is_company, phone_number, company_name, password=None
	):

		if not email:
			raise ValueError('У пользователя должен быть адрес электронной почты')

		user = self.model(
			email=self.normalize_email(email),
			first_name=first_name,
			last_name=last_name,
			phone_number=phone_number,
			company_name=company_name,
			is_receiving_news=is_receiving_news,
			is_company=is_company
		)
		user.set_password(password)
		user.save(using=self._db)

		return user

	def create_superuser(self, email, password=None):
		user = self.create_user(
			email,
			first_name='Admin',
			last_name='',
			phone_number='',
			company_name='',
			is_receiving_news=False,
			is_company=False,
			password=password
		)
		user.is_admin = True
		user.is_active = True
		user.save(using=self._db)

		return user


class User(AbstractBaseUser):
	email = models.EmailField(
		verbose_name='Email',
		max_length=255,
		unique=True
	)
	first_name = models.CharField(
		verbose_name='Имя',
		max_length=32
	)
	last_name = models.CharField(
		verbose_name='Фамилия',
		max_length=32
	)
	phone_number = PhoneNumberField(
		verbose_name='Номер телефона',
		max_length=12,
		blank=True,
	)
	company_name = models.CharField(
		verbose_name='Название компании',
		max_length=64,
		blank=True
	)
	is_receiving_news = models.BooleanField(default=False)
	is_company = models.BooleanField(default=False)
	is_active = models.BooleanField(default=False)
	is_admin = models.BooleanField(default=False)

	objects = UserManager()

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	def email_user(self, subject, message, from_email=None, **kwargs):
		"""Send an email to this user."""
		send_mail(subject, message, from_email, [self.email], **kwargs)

	def __str__(self):
		return self.first_name

	def has_perm(self, perm, obj=None):
		return True

	def has_module_perms(self, app_label):
		return True

	@property
	def is_staff(self):
		return self.is_admin


class Company(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	addresses = ArrayField(
		models.CharField(max_length=128),
		size=None,
		verbose_name='Список адресов'
	)
	inn = models.CharField(
		verbose_name='ИНН',
		max_length=12
	)
	company_files = models.FileField(
		verbose_name='Документы',
		upload_to='company_files/',
		max_length=50,
		blank=True
	)
	moderator_message = models.CharField(
		verbose_name='Сообщение для пользователя',
		max_length=256,
		blank=True
	)
	is_verification = models.BooleanField(default=False)
	is_verified = models.BooleanField(default=False)

	objects = models.Manager()


class Product(models.Model):
	slug = models.SlugField(
		max_length=32,
		unique=True
	)
	name = models.CharField(
		verbose_name='Название',
		max_length=32
	)
	CATEGORY = (
		(1, 'Продукция с переплётом'),
		(2, 'Флаеры, открытки и плакаты'),
		(3, 'Календари'),
		(4, 'Офисное'),
		(5, 'Рекламная'),
		(6, 'Для гастрономии и событий'),
	)
	category = models.IntegerField(choices=CATEGORY)
	description = models.CharField(
		verbose_name='Описание',
		max_length=256
	)
	price = models.IntegerField()

	objects = models.Manager()


class ProductCompany(models.Model):
	company = models.ForeignKey(
		'Company',
		verbose_name='Компания',
		on_delete=models.CASCADE
	)
	product = models.ForeignKey(
		'Product',
		verbose_name='Продукт',
		on_delete=models.CASCADE
	)
	characteristics = HStoreField(verbose_name='Характеристики')


class ShoppingCart(models.Model):
	user = models.ForeignKey(
		'User',
		on_delete=models.CASCADE
	)
	product_company = models.ForeignKey(
		'ProductCompany',
		on_delete=models.CASCADE
	)
	characteristics = HStoreField()
	design = models.FileField(
		upload_to='design_product/',
		max_length=50
	)
	count = models.IntegerField()


class ProductCharacteristics(models.Model):
	format = ArrayField(models.CharField(max_length=32))
	color = ArrayField(models.CharField(max_length=32))
	material = ArrayField(models.CharField(max_length=32))


class Orders(models.Model):
	user = models.ForeignKey(
		'User',
		on_delete=models.CASCADE
	)
	product_company = models.ForeignKey(
		'ProductCompany',
		on_delete=models.CASCADE
	)
	characteristics = HStoreField()
	design = models.FileField(
		upload_to='design_product/',
		max_length=50
	)
	count = models.IntegerField()
	price = models.IntegerField()
	datetime = models.DateTimeField(auto_now_add=True)
	STATUS = (
		(1, 'Новый заказ'),
		(2, 'На согласовании'),
		(3, 'Отправка'),
		(4, 'В пути'),
		(5, 'Прибыл'),
	)
	status = models.IntegerField(choices=STATUS)


class OldOrders(models.Model):
	user = models.ForeignKey(
		'User',
		on_delete=models.CASCADE
	)
	product_company = models.ForeignKey(
		'ProductCompany',
		on_delete=models.CASCADE
	)
	is_canceled = models.BooleanField()
	characteristics = HStoreField()
	design = models.FileField(
		upload_to='design_product_old/',
		max_length=50
	)
	count = models.IntegerField()
	price = models.IntegerField()
	datetime = models.DateTimeField()
	datetime_expiration = models.DateTimeField(auto_now_add=True)
