from core.models import OrderExecutionProposal, OrderProposalTemp, OrderDetail, OrderProduct, Order
from django.shortcuts import get_object_or_404


def start(order_id):
	"""Получить список всех возможных предложений в нужном формате"""
	result = []
	counter = 0
	total_price = 0
	order_detail = OrderDetail.objects.get(order__id=order_id)

	# Получаем список всех возможных предложений и формируем ответ в нужном формате
	for data in get_proposals(order_id):
		proposal = [dict(), 0, counter, 0]
		counter += 1
		for company in data:
			company_name = company[0].company.user.company_name
			proposal[0].update({company_name: dict()})
			if company[1] is None:
				proposal[3] = company[2]
				for product in company[0].order_products.items():
					proposal[0][company_name].update({str(product[0]): []})
					for item in product[1]:
						if item[0] != 0:
							address = order_detail.address_and_deadline['items'][item[1]][0]
							proposal[0][company_name][str(product[0])].append((
								item[0],
								(item[1], address),
								item[2]
							))
							total_price += item[2]
			else:
				for product in company[1].items():
					proposal[0][company_name].update({str(product[0]): []})
					if product[1] is None:
						order_product = OrderProduct.objects.get(id=int(product[0]))
						for item in [(x[1], x[0], x[1] * order_product.price) for x in order_product.count_and_address.items()]:
							address = order_detail.address_and_deadline['items'][item[1]][0]
							proposal[0][company_name][str(product[0])].append((
								item[0],
								(item[1], address),
								item[2]
							))
							total_price += item[2]
					else:
						for item in product[1]:
							order_product = OrderProduct.objects.get(id=int(product[0]))
							address = order_detail.address_and_deadline['items'][item[0]][0]
							proposal[0][company_name][str(product[0])].append((
								item[1],
								(item[0], address),
								item[1]*order_product.product.price
							))
							total_price += item[1]*order_product.product.price

		proposal[1] = total_price
		total_price = 0
		result.append(proposal)

	save_proposal_temp(result, order_id)

	return result


def save_proposal_temp(proposal, order_id):
	"""Сохранить в базу данных все возможные предложения в итоговом формате"""
	OrderProposalTemp.objects.update_or_create(
		order=get_object_or_404(Order, id=order_id),
		defaults={
			'proposal': proposal,
			'count': len(proposal)
		}
	)


def get_proposals(order_id):
	"""Получить список всех возможных предложений(полных, полных скомпонованных, неполных скомпонованных и остальных)"""
	proposals = OrderExecutionProposal.objects.filter(order__id=order_id)
	order_products = OrderProduct.objects.filter(order__id=order_id)
	execution_full_order = []
	other_proposals = []

	if len(proposals) == 0:
		return []

	# Разделяем полные и неполные предложения
	for proposal in proposals:
		if len(proposal.order_products) != len(order_products):
			other_proposals.append(proposal)
			continue

		for product in order_products:
			if product.total_count != _get_count_product(proposal, product.id):
				other_proposals.append(proposal)
				break
		else:
			execution_full_order.append(proposal)

	# Сортируем полные предложения по общей стоимости
	execution_full_order.sort(key=lambda n: n.price)

	if len(execution_full_order) == len(proposals):
		return [((x, None, 0),) for x in execution_full_order] + [((x, None, 1),) for x in other_proposals]

	complete_other_offers = _get_other_proposals(other_proposals, order_products)

	if len(execution_full_order) == 0:
		return complete_other_offers + [((x, None, 1),) for x in other_proposals]

	return [((x, None, 0),) for x in execution_full_order] + complete_other_offers + [((x, None, 1),) for x in other_proposals]


def _get_other_proposals(proposals, order_products):
	"""Получить список скомпонованных предложений(полных и неполных со списком недостающих продуктов) из неполных предложений"""
	result = []
	missing_items = _get_list_missing_items(proposals, order_products)
	missing_items.sort(key=lambda n: n[0])
	for x in range(len(missing_items)):
		for y in range(x+1, len(missing_items)):
			if missing_items[x][0] == 1:
				for product in missing_items[x][1].items():
					if product[0] in missing_items[y][1].keys():
						break
				else:
					result.append(((missing_items[x][2], None, 0), (missing_items[y][2], missing_items[x][1])))
					continue

			elif missing_items[x][0] != 0:
				is_add = True
				for product in missing_items[x][1].items():
					if product[1] is None and product[0] in missing_items[y][1].keys():
						break

					for item in product[1]:
						if missing_items[y][2].order_products.get(product[0]) is None:
							is_add = False
							break

						item_id = None
						product_items = missing_items[y][2].order_products[product[0]]

						for i in product_items:
							if i[1] == item[0]:
								item_id = product_items.index(i)

						if item_id is None:
							is_add = False
							break

						if item[1] - product_items[item_id][0] > 0:
							is_add = False
							break

					if not is_add:
						break
				else:
					result.append(((missing_items[x][2], None, 0), (missing_items[y][2], missing_items[x][1])))
	return result


def _get_list_missing_items(proposals, order_products):
	"""Получить список с количеством всех недостающих продуктов в предложениях"""
	result = []

	for proposal in proposals:
		missing_items = [0, dict(), proposal]

		for product in order_products:
			if proposal.order_products.get(str(product.id)) is None:
				if missing_items[0] == 0 or missing_items[0] == 1:
					missing_items[0] = 1
					missing_items[1].update({str(product.id): None})
					continue

				missing_items[0] = 3
				missing_items[1].update({str(product.id): None})
				continue

			if _get_count_product(proposal, product.id) < product.total_count:
				if missing_items[0] == 0 or missing_items[0] == 2:
					missing_items[0] = 2
					missing_items[1].update({str(product.id): _search_missing_items(proposal, product)})
					continue

				missing_items[0] = 3
				missing_items[1].update({str(product.id): _search_missing_items(proposal, product)})
		result.append(missing_items)
	return result


def _search_missing_items(proposal, product):
	"""Получить количество всех недостающих продуктов в конкретном предложении если они есть"""
	result = []
	for data in proposal.order_products[str(product.id)]:
		if data[0] < product.count_and_address[str(data[1])]:
			result.append((data[1], product.count_and_address[str(data[1])] - data[0]))
	return result


def _get_count_product(proposal, product_id):
	"""Получить общее количество одного продукта в конкретном предложении"""
	return sum([x[0] for x in proposal.order_products[str(product_id)]])