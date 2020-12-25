from core import models
from core.services import notification_handler


def set_order_status(order_id):
	order_detail = models.OrderDetail.objects.get(order__id=int(order_id))
	if order_detail.status < 5:
		order_detail.status += 1
		order_detail.save()

	if order_detail.status == 5:
		add_data_old_order(order_id, 1)

	notification_handler.send_notification(order_id, order_detail.status)


def add_data_old_order(order_id, context):
	price = sum([x.price for x in models.OrderExecution.objects.filter(order__id=int(order_id))])
	old_order = models.OldOrder(
		order=models.Order.objects.get(id=int(order_id)),
		price=price,
		context=context
	)
	old_order.save()


def set_order_execution_status(ord_exec_id):
	obj = models.OrderExecution.objects.get(id=ord_exec_id)
	order_detail = models.OrderDetail.objects.get(order=obj.order)
	if obj.status < 5:
		obj.status += 1
		obj.save() ### fix
		if is_all_order_execution_set_status(obj.order, order_detail):
			set_order_status(obj.order.id)


def is_all_order_execution_set_status(order, order_detail):
	is_set_status = True
	for order_exec in models.OrderExecution.objects.filter(order=order):
		if order_exec.status <= order_detail.status:
			is_set_status = False

	return is_set_status


def cancel_order(order_id, context):
	if int(context) == 4:
		order = models.Order.objects.get(id=int(order_id))
		order.delete()
	elif int(context) == 3:
		order_exec = models.OrderExecution.objects.get(id=int(order_id))
		order_detail = models.OrderDetail.objects.get(order=order_exec.order)
		if len(models.OrderExecution.objects.filter(order=order_exec.order)) == 1:
			order_detail.status = 6
			order_detail.save()
			order_exec.status = 6
			order_exec.save()
			add_data_old_order(order_exec.order.id, 3)
		else:
			order_exec.status = 6
			order_exec.save()
			add_data_old_order(order_exec.order.id, 3)
			is_set_status = True
			for order_exec in models.OrderExecution.objects.filter(order=order_exec.order):
				if order_exec.status != 6:
					is_set_status = False

			if is_set_status:
				order_detail.status = 6
				order_detail.save()
		user = order_detail.order.user
		user.notification = 'Компания '+order_exec.company.user.company_name+' отменила выполнение заказа №'+str(order_id)
		user.save()


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
	set_order_status(order_id)


def split_order(order_id, offer):
	proposal = models.OrderProposalTemp.objects.get(order__id=order_id).proposal[offer]
	products_list = dict()

	for company in proposal[0].items():
		for product in company[1].items():
			count = 0
			for item in product[1]:
				count += item[0]
			products_list.update({product[0]: count + products_list.get(product[0], 0)})

	for order_product in models.OrderProduct.objects.filter(order__id=order_id):
		count = products_list.get(str(order_product.id))
		
		if count is not None:
			count = 0

		if order_product.total_count - count > 0:
			obj = models.ShoppingCart(
				user=order_product.order.user,
				product=order_product.product,
				characteristics=order_product.characteristics,
				design=order_product.design_url[6:],
				other_design=[],
				count=order_product.total_count - count,
			)
			obj.save()

	choose_offer(order_id, offer)


def _delete_orders_execution_proposal_and_temp(order_id):
	order_id = int(order_id)
	for order in models.OrderExecutionProposal.objects.filter(order__id=order_id):
		order.delete()
	models.OrderProposalTemp.objects.get(order__id=order_id).delete()
