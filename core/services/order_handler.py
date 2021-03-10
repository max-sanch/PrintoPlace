from django.shortcuts import get_object_or_404

from core import models
from core.services import notification_handler


def set_order_status(order_id):
	order_detail = get_object_or_404(models.OrderDetail, order__id=int(order_id))
	if order_detail.status < 5:
		order_detail.status += 1
		order_detail.save()

	if order_detail.status == 5:
		add_data_old_order(order_id, 1)

	notification_handler.send_notification(order_id, order_detail.status)


def add_data_old_order(order_id, context):
	price = sum([x.price for x in models.OrderExecution.objects.filter(order__id=int(order_id))])
	old_order = models.OldOrder(
		order=get_object_or_404(models.Order, id=int(order_id)),
		price=price,
		context=context
	)
	old_order.save()


def set_order_execution_status(ord_exec_id):
	obj = get_object_or_404(models.OrderExecution, id=ord_exec_id)
	order_detail = get_object_or_404(models.OrderDetail, order=obj.order)
	if obj.status < 5:
		obj.status += 1
		obj.save()
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
		order = get_object_or_404(models.Order, id=int(order_id))
		order.delete()
	elif int(context) == 3:
		order_exec = get_object_or_404(models.OrderExecution, id=int(order_id))
		order_detail = get_object_or_404(models.OrderDetail, order=order_exec.order)
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
		obj = get_object_or_404(models.Order, id=request.user.order_id)
		obj.delete()

	price = 0
	user = get_object_or_404(models.User, id=request.user.id)
	old_order = get_object_or_404(models.OldOrder, id=int(order_id))

	for prod in old_order.products['products']:
		product = get_object_or_404(models.Product, id=int(prod['product']))
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
	proposal = get_object_or_404(models.OrderProposalTemp, order__id=order_id).proposal[offer]

	for company in proposal[0].items():
		company_obj = get_object_or_404(models.Company, user__company_name=company[0]) # fix
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
			order=get_object_or_404(models.Order, id=order_id),
			company=company_obj,
			order_products=order_products,
			status=2,
			price=price
		)
		obj.save()

	_delete_orders_execution_proposal_and_temp(order_id)
	set_order_status(order_id)


def split_order(order_id, offer):
	proposal = get_object_or_404(models.OrderProposalTemp, order__id=order_id).proposal[offer]
	products_list = dict()

	for company in proposal[0].items():
		for product in company[1].items():
			count = 0
			for item in product[1]:
				count += item[0]
			products_list.update({product[0]: count + products_list.get(product[0], 0)})

	for order_product in models.OrderProduct.objects.filter(order__id=order_id):
		count = products_list.get(str(order_product.id))
		
		if count is None:
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


def clear_cart(user):
	products = models.ShoppingCart.objects.filter(user=user)
	for product in products:
		product.delete()


def get_new_orders(user):
	orders = models.OrderDetail.objects.filter(status=1)[::-1]
	my_proposals = []
	result = []

	for proposal in models.OrderExecutionProposal.objects.filter(company__user=user):
		my_proposals.append(proposal.order.id)

	for order in orders:
		if order.order.id in my_proposals:
			result.append((
				get_object_or_404(models.OrderExecutionProposal, order__id=order.order.id, company__user=user),
				0
			))
			continue
		result.append((order, 1))

	return result


def set_active_order_id(user, order_id):
	user = get_object_or_404(models.User, id=user.id)
	user.order_id = order_id
	user.save()


def get_accepted_orders_for_company(user):
	orders_execution = models.OrderExecution.objects.filter(
		company__user=user
	).exclude(status=5).exclude(status=6)
	return _get_orders_for_company(orders_execution)


def get_completed_orders_for_company(user):
	orders_execution = list(models.OrderExecution.objects.filter(company__user=user, status=5)) + \
						list(models.OrderExecution.objects.filter(company__user=user, status=6))
	orders_execution.sort(key=lambda x: x.order.id)
	return _get_orders_for_company(orders_execution)


def get_executable_orders_for_user(user):
	order_detail_list = models.OrderDetail.objects.filter(
		order__user=user
	).exclude(status=0).exclude(status=1).exclude(status=5).exclude(status=6)
	return _get_orders_for_user(order_detail_list)


def get_completed_orders_for_user(user):
	order_detail_list = list(models.OrderDetail.objects.filter(order__user=user, status=5))

	for order_detail in models.OrderDetail.objects.filter(order__user=user, status=6):
		if models.OldOrder.objects.get(order=order_detail.order).context == 3:
			order_detail_list.append(order_detail)
	order_detail_list.sort(key=lambda x: x.order.id)
	return _get_orders_for_user(order_detail_list)


def _get_orders_for_user(order_detail_list):
	result = []
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


def _get_orders_for_company(orders_execution):
	result = []
	for order in orders_execution[::-1]:
		order_detail = get_object_or_404(models.OrderDetail, order__id=order.order.id)
		order_data = [
			order.order.id, order_detail.datetime.date,
			order.status, 0, order.order.user, [],
			order.id, order_detail.comment
		]
		for product in order.order_products.items():
			order_prod = get_object_or_404(models.OrderProduct, id=int(product[0]))
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


def _delete_orders_execution_proposal_and_temp(order_id):
	order_id = int(order_id)
	for order in models.OrderExecutionProposal.objects.filter(order__id=order_id):
		order.delete()
	get_object_or_404(models.OrderProposalTemp, order__id=order_id).delete()
