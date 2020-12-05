from django import template

from core.models import ShoppingCart, Product, OrderDetail, OrderProduct, Company

register = template.Library()


@register.simple_tag(takes_context=True)
def count_product_cart(context):
	request = context.get('request')
	if request is not None:
		count = len(ShoppingCart.objects.filter(user=request.user))
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
		company = Company.objects.get(user=request.user)
		if company.notification != '':
			return True

	return False


@register.simple_tag()
def get_address_and_data(prod_id):
	prod = OrderProduct.objects.get(id=int(prod_id))
	order = OrderDetail.objects.get(order=prod.order)
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
	order_detail = OrderDetail.objects.get(order__id=int(order_id))
	return order_detail.address_and_deadline['items'][int(address_id)][0]


@register.simple_tag()
def get_products(order_id):
	return OrderProduct.objects.filter(order__id=int(order_id))


@register.simple_tag()
def get_one_product(product_id):
	return OrderProduct.objects.get(id=int(product_id))


@register.simple_tag()
def get_status_client(status_id):
	statuses = (
		(1, 'Ожидание предложений'),
		(2, 'Ожидание оплаты'),
		(3, 'Ожидание отправки'),
		(4, 'В пути'),
		(5, 'Прибыл')
	)
	for status in statuses:
		if status[0] == status_id:
			return status[1]
	return ''


@register.simple_tag()
def get_status_company(status_id):
	for status in OrderDetail.STATUS:
		if status[0] == status_id:
			return status[1]
	return ''


@register.simple_tag()
def mult(x, y):
	return x * y


@register.simple_tag()
def int_to_str(num):
	return str(num)
