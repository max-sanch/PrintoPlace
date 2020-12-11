from django import template

from core import models

register = template.Library()


@register.simple_tag(takes_context=True)
def count_product_cart(context):
	request = context.get('request')
	if request is not None:
		count = len(models.ShoppingCart.objects.filter(user=request.user))
		return count
	return 0


@register.simple_tag(takes_context=True)
def get_city(context):
	request = context.get('request')
	citys = {
		'msk': 'Москва',
		'sch': 'Сочи',
		'irk': 'Иркутск',
		'nov': 'Новосибирск'
	}
	if request is not None:
		city = request.COOKIES.get('city', False)
		if city:
			return citys[city]
	return False


@register.simple_tag(takes_context=True)
def get_notifications(context):
	request = context.get('request')

	if request.user.notification != '':
		return True

	elif request.user.is_company:
		company = models.Company.objects.get(user=request.user)
		if company.notification != '' or company.moderator_message != '':
			return True

	return False


@register.simple_tag()
def get_context_order(order_id):
	old_order = models.OldOrder.objects.get(order__id=int(order_id))
	for context in models.OldOrder.CONTEXT:
		if context[0] == old_order.context:
			return context
	return None


@register.simple_tag()
def get_address_and_data(prod_id):
	prod = models.OrderProduct.objects.get(id=int(prod_id))
	order = models.OrderDetail.objects.get(order=prod.order)
	address = order.address_and_deadline['items']
	result = []
	for item in prod.count_and_address.items():
		result.append((
			item[1],
			address[int(item[0])][0],
			'.'.join(address[int(item[0])][1].split('-')[::-1]),
			address[int(item[0])][2],
			item[0]
		))
	return result


@register.simple_tag()
def get_address(address_id, order_id):
	order_detail = models.OrderDetail.objects.get(order__id=int(order_id))
	return order_detail.address_and_deadline['items'][int(address_id)][0]


@register.simple_tag()
def get_one_address_and_date(address_id, order_id):
	order_detail = models.OrderDetail.objects.get(order__id=int(order_id))
	return (
		order_detail.address_and_deadline['items'][int(address_id)][0],
		'%s %s' % (
			order_detail.address_and_deadline['items'][int(address_id)][1],
			order_detail.address_and_deadline['items'][int(address_id)][2]
		)
	)


@register.simple_tag()
def get_order_date(order_id):
	return models.OrderDetail.objects.get(order__id=order_id).datetime


@register.simple_tag()
def get_items_product(product_id):
	order_product = models.OrderProduct.objects.get(id=int(product_id))
	result = [(x[1], x[0], x[1]*order_product.product.price) for x in order_product.count_and_address.items()]
	return result


@register.simple_tag()
def get_logo(company_id):
	company = models.Company.objects.get(id=int(company_id))
	if company.logo == '':
		return None
	return company.logo


@register.simple_tag()
def get_id_address(address_list):
	result = []
	counter = 0
	for address in address_list:
		result.append((address, 'address-data-' + str(counter)))
		counter += 1
	return result


@register.simple_tag()
def get_products(order_id):
	return models.OrderProduct.objects.filter(order__id=int(order_id))


@register.simple_tag()
def get_one_product(product_id):
	return models.OrderProduct.objects.get(id=int(product_id))


@register.simple_tag()
def get_len_proposal(order_id):
	proposal_temp = models.OrderProposalTemp.objects.filter(order__id=int(order_id))

	if len(proposal_temp) > 0:
		return len(models.OrderExecutionProposal.objects.filter(order__id=int(order_id))) + len(proposal_temp[0].proposal)

	return len(models.OrderExecutionProposal.objects.filter(order__id=int(order_id)))


@register.simple_tag()
def get_status_client(status_id):
	statuses = (
		(1, 'Поиск исполнителей'),
		(2, 'Отправлен на исполнение'),
		(3, 'Взят в работу'),
		(4, 'Подтверждение получения'),
		(5, 'Исполнен')
	)
	for status in statuses:
		if status[0] == status_id:
			return status[1]
	return ''


@register.simple_tag()
def get_status_company(status_id):
	for status in models.OrderDetail.STATUS:
		if status[0] == status_id:
			return status[1]
	return ''


@register.simple_tag()
def mult(x, y):
	return x * y


@register.simple_tag()
def int_to_str(num):
	return str(num)
