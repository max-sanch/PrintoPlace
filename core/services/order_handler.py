from core import models
from core.services import notification_handler


def set_order_status(order_id, status):
	if status == 4:
		delete_order(order_id, 1)
	else:
		for order_detail in models.OrderDetail.objects.filter(status=status):
			if order_detail.order.id == int(order_id):
				order_detail.status = status + 1
				order_detail.save()
				break

		if status in (1, 2, 3, 4):
			notification_handler.send_notification(order_id, status)


def delete_order(order_id, context):
	order = models.Order.objects.get(id=int(order_id))
	# obj = models.OldOrder(
	# 	user=order.user,
	# 	company=order_detail.company,
	# 	products=order.products,
	# 	context=int(context),
	# 	datetime=order_detail.datetime
	# )
	# obj.save()
	order.delete()


def repeat_order(request, order_id):
	if request.user.order_id != 0 and request.user.order_id is not None:
		obj = models.Order.objects.get(id=request.user.order_id)
		obj.delete()

	price = 0
	user = models.User.objects.get(id=request.user.id)
	old_order = models.OldOrder.objects.get(id=int(order_id))

	for prod in old_order.products['products']:
		product = models.Product.objects.get(id=int(prod['product']))
		price += product.price * int(prod['count'])

	obj = models.Order(
		user=request.user,
		products=old_order.products,
		price=price,
	)
	obj.save()
	user.order_id = obj.pk
	user.save()
