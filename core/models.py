from django.db import models
from django.core.mail import send_mail
from django.contrib.postgres.fields import ArrayField
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
	"""---"""
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
	addresses = models.JSONField()
	order_id = models.IntegerField(blank=True, null=True)
	notification = models.CharField(
		verbose_name='Уведомление',
		max_length=256,
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

	def full_name(self):
		return '%s %s' % (self.last_name, self.first_name)

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
	"""Пользователь-исполнитель — данные о компании предоставляемой продукт"""
	user = models.OneToOneField('User', on_delete=models.CASCADE)
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
	notification = models.CharField(
		verbose_name='Уведомление',
		max_length=256,
		blank=True
	)
	is_verification = models.BooleanField(default=False)
	is_verified = models.BooleanField(default=False)

	objects = models.Manager()


class Product(models.Model):
	"""Базовое описание продукта предоставляемого сайтом"""
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

	def __str__(self):
		return self.name


class ProductCompany(models.Model):
	"""Продукт предоставляемый пользователем-исполнителем(компанией) на основе базового продукта"""
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
	characteristics = models.JSONField(verbose_name='Характеристики')

	objects = models.Manager()


class ShoppingCart(models.Model):
	"""Продукты находящиеся в корзине конкретного пользователя"""
	user = models.ForeignKey(
		'User',
		on_delete=models.CASCADE
	)
	product = models.ForeignKey(
		'Product',
		on_delete=models.CASCADE
	)
	characteristics = models.JSONField()
	design = models.FileField(
		upload_to='design_product/',
		max_length=50
	)
	count = models.IntegerField()

	objects = models.Manager()


class ProductCharacteristics(models.Model):
	"""Список характеристик и их значений для конкретного продукта"""
	product = models.OneToOneField('Product', verbose_name='Продукт', on_delete=models.CASCADE)

	format = models.JSONField(verbose_name='Формат', null=True)
	color = models.JSONField(verbose_name='Цвет', null=True)
	material = models.JSONField(verbose_name='Материал', null=True)
	rounding = models.JSONField(verbose_name='Скругление', null=True)
	adhesive_side = models.JSONField(verbose_name='Клейкая сторона', null=True)
	sheets_count = models.JSONField(verbose_name='Количество листов', null=True)
	sheets_arrangement = models.JSONField(verbose_name='Расположение листов', null=True)
	protective_film = models.JSONField(verbose_name='Защитная плёнка', null=True)
	spiral_color = models.JSONField(verbose_name='Цвет спирали', null=True)
	finishing = models.JSONField(verbose_name='Отделка', null=True)
	paper = models.JSONField(verbose_name='Бумага', null=True)

	objects = models.Manager

	def __str__(self):
		return self.product.__str__()


class Order(models.Model):
	"""Базовая модель заказа"""
	user = models.ForeignKey('User', on_delete=models.CASCADE)
	price = models.IntegerField(verbose_name='Общая стоимость')

	objects = models.Manager


class OrderDetail(models.Model):
	"""Детальное описание заказа после его оформления"""
	order = models.OneToOneField('Order', on_delete=models.CASCADE)
	address_and_deadline = models.JSONField(verbose_name='Адреса доставки и сроки')
	comment = models.CharField(
		verbose_name='Комментарий',
		max_length=1024,
		blank=True
	)
	datetime = models.DateTimeField(auto_now_add=True)
	STATUS = (
		(1, 'Новая заявка'),
		(2, 'Ожидание ответа'),
		(3, 'Отправка'),
		(4, 'В пути'),
		(5, 'Прибыл')
	)
	status = models.IntegerField(choices=STATUS)

	objects = models.Manager


class OrderProduct(models.Model):
	"""Продукты фигурирующие в заказе"""
	order = models.ForeignKey('Order', on_delete=models.CASCADE)
	product = models.ForeignKey('Product', on_delete=models.CASCADE)
	characteristics = models.JSONField(verbose_name='Характеристики')
	design_url = models.CharField(verbose_name='Ссылка на дизайн', max_length=128)
	total_count = models.IntegerField(verbose_name='Общее количество товара')
	price = models.IntegerField(verbose_name='Стоимость')
	count_and_address = models.JSONField(verbose_name='Адреса доставки и количество товара')

	objects = models.Manager


class OrderExecutionProposal(models.Model):
	"""Предложения от компаний на выполнение заказа"""
	order = models.ForeignKey('Order', on_delete=models.CASCADE)
	company = models.ForeignKey('Company', on_delete=models.CASCADE)
	order_products = models.JSONField()
	price = models.IntegerField(verbose_name='Общая стоимость')
	is_partially = models.BooleanField(verbose_name='Частичное выполнение', default=False)

	objects = models.Manager


class OrderExecution(models.Model):
	"""Заказ на выполнение компанией каторую выбрал заказчик"""
	order = models.ForeignKey('Order', on_delete=models.CASCADE)
	company = models.ForeignKey('Company', on_delete=models.CASCADE)
	order_products = models.JSONField()
	price = models.IntegerField(verbose_name='Стоимость')

	objects = models.Manager


class OldOrder(models.Model):
	"""Информация о недействующих заказах"""
	user = models.ForeignKey('User', on_delete=models.CASCADE)
	company = models.ForeignKey('Company', on_delete=models.CASCADE)
	price = models.IntegerField()
	CONTEXT = (
		(1, 'Завершён'),
		(2, 'Окончание времени'),
		(3, 'Отмена компанией'),
		(4, 'Отмена клиентом'),
	)
	context = models.IntegerField(choices=CONTEXT)
	datetime = models.DateTimeField()
	completion_date = models.DateTimeField(auto_now_add=True)

	objects = models.Manager
