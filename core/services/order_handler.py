from core import models
from core.services import notification_handler


def set_order_status(order_id):
	order_detail = models.OrderDetail.objects.get(order__id=int(order_id))
	if order_detail.status == 4:
		delete_order(order_id, 1)
	else:
		order_detail.status += 1
		order_detail.save()
		# notification_handler.send_notification(order_id, status)


def set_order_execution_status(ord_exec_id):
	obj = models.OrderExecution.objects.get(id=ord_exec_id)
	order_detail = models.OrderDetail.objects.get(order=obj.order)
	if obj.status < 5:
		obj.status += 1
		obj.save()
		is_all_order_execution_set_status(obj.order, order_detail)


def is_all_order_execution_set_status(order, order_detail):
	is_set_order = True
	for order_exec in models.OrderExecution.objects.filter(order=order):
		if order_exec.status == order_detail.status:
			is_set_order = False

	if is_set_order:
		set_order_status(order.id)


def delete_order(order_id, context):
	order = models.Order.objects.get(id=int(order_id))
	# old_order
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


def choose_offer(order_id, offer):
	proposal = models.OrderProposalTemp.objects.get(order__id=order_id).proposal[offer]

	for company in proposal[0].items():
		company_obj = models.Company.objects.get(user__company_name=company[0])
		order_products = dict()
		price = 0

		for product in company[1].items():
			order_products.update({product[0]: []})
			for items in product[1]:
				price += items[2]
				order_products[product[0]].append((
					items[0],
					items[1][0],
					items[2]
				))

		obj = models.OrderExecution(
			order=models.Order.objects.get(id=order_id),
			company=company_obj,
			order_products=order_products,
			status=2,
			price=price
		)
		obj.save()

	_delete_orders_execution_proposal_and_temp(order_id)
	set_order_status(order_id, 1)


def _delete_orders_execution_proposal_and_temp(order_id):
	for order in models.OrderExecutionProposal.objects.get(id=order_id):
		order.delete()
	models.OrderProposalTemp.objects.get(id=order_id).delete()
