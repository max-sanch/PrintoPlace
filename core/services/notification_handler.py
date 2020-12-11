from django.core.mail import send_mail
from django.conf import settings
from core import models


def delete_notification(request):
	user = models.User.objects.get(id=request.user.id)
	user.notification = ''
	user.save()

	if user.is_company:
		company = models.Company.objects.get(user=request.user)
		company.notification = ''
		company.moderator_message = ''
		company.save()


def send_notification(order_id, status):
	status = int(status)
	order_id = str(order_id)
	user_message = {
		2: 'Ожидайте подтверждение от компаний на заказ №' + order_id,
		3: 'Все компании взяли в работу ваш заказ №' + order_id,
		4: 'Компании ожидают подтверждение доставки заказа №' + order_id,
		5: 'Заказ №%s исполнен, он находить во вкладке "Завершённые"' % order_id,
	}
	company_message = {
		1: 'Новый заказ!',
		2: 'Заказ №%s ждёт подтверждения' % order_id,
		4: 'Ожидайте подтверждение доставки заказа №' + order_id,
		5: 'Клиент получил заказ №%s, он находить во вкладке "Завершённые"' % order_id,
	}

	user = models.Order.objects.get(id=int(order_id)).user
	user.notification = user_message.get(status, '')
	user.save()

	if user.notification != '':
		send_mail(
			'Уведомление о заказе',
			user.notification,
			settings.DEFAULT_FROM_EMAIL,
			[user.email]
		)

	orders_execution = models.OrderExecution.objects.filter(order__id=int(order_id))
	if len(orders_execution) != 0:
		for order in orders_execution:
			company = order.company
			company.notification = company_message.get(status, '')
			company.save()

	else:
		for company in models.Company.objects.all():
			company.notification = company_message.get(status, '')
			company.save()
