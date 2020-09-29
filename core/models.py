from django.conf import settings
from django.db import models
from django.contrib.postgres import fields
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.core.mail import send_mail
from phonenumber_field.modelfields import PhoneNumberField


class CompanyManager(models.Manager):
	def create_user_company(self, company_name, phone_number, user):
		company = self.model(
			company_name=company_name,
			phone_number=phone_number,
			user=user
		)
		company.save(using=self._db)

		return company


class UserManager(BaseUserManager):
	def create_user(
		self, email, first_name, last_name, is_receiving_news, is_company,
		company_name=None, phone_number=None, password=None):

		if not email:
			raise ValueError('У пользователя должен быть адрес электронной почты')

		if is_company and (company_name is None or phone_number is None):
			raise ValueError('Укажите название компании и номер телефона')

		user = self.model(
			email=self.normalize_email(email),
			first_name=first_name,
			last_name=last_name,
			is_receiving_news=is_receiving_news,
			is_company=is_company
		)
		user.set_password(password)
		user.save(using=self._db)

		if is_company and company_name is not None and phone_number is not None:
			Company.objects.create_user_company(company_name, phone_number, user)

		return user

	def create_superuser(self, email, password=None):
		user = self.create_user(
			email,
			first_name='Admin',
			last_name=None,
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
		unique=True,
	)
	first_name = models.CharField(
		verbose_name='Имя',
		max_length=32,
	)
	last_name = models.CharField(
		verbose_name='Фамилия',
		max_length=32,
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
	company_name = models.CharField(
		verbose_name='Название компании',
		max_length=64,
	)
	phone_number = PhoneNumberField(
		verbose_name='Номер телефона',
		unique=True
	)
	addresses = fields.ArrayField(
		models.CharField(max_length=128),
		size=None,
		verbose_name='Список адресов',
		blank=True
	)
	inn = models.CharField(
		verbose_name='ИНН',
		max_length=12,
		blank=True,
		unique=True
	)
	is_verification = models.BooleanField(default=False)

	objects = CompanyManager()
