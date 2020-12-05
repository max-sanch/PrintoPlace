from core import models


def delete_notification(request):
	user = models.User.objects.get(id=request.user.id)
	user.notification = ''
	user.save()

	if user.is_company:
		company = models.Company.objects.get(user=request.user)
		company.notification = ''
		company.save()


def send_notification(order_id, status):
	user_message = {
		1: 'Компания приняла ваш заказ №' + order_id,
		3: 'Компания отправила ваш заказ №' + order_id,
	}
	company_message = {
		2: 'Заказ №' + order_id + ' оплачен'
	}

	order = models.Order.objects.get(id=int(order_id))
	user = models.User.objects.get(id=order.user.id)
	user.notification = user_message.get(status, '')
	user.save()

	order_detail = models.OrderDetail.objects.get(order=order)
	company = models.Company.objects.get(id=order_detail.company.id)
	company.notification = company_message.get(status, '')
	company.save()
