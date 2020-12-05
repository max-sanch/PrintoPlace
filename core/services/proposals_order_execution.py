from core.models import OrderExecutionProposal, OrderProduct


def get_proposals(order_id):
	proposals = OrderExecutionProposal.objects.filter(order__id=int(order_id))
	order_products = OrderProduct.objects.filter(order__id=int(order_id))
	execution_full_order = []
	other_proposals = []

	for proposal in proposals:
		if len(proposal.order_products) != len(order_products):
			other_proposals.append((proposal, _get_total_count_product(proposal)))
			continue

		for product in order_products:
			if product.total_count != sum([x[0] for x in proposal.order_products[str(product.id)]]):
				other_proposals.append((proposal, _get_total_count_product(proposal)))
				break
		else:
			if len(execution_full_order) != 0:
				if proposal.price <= execution_full_order[0].price:
					execution_full_order.insert(0, proposal)
				else:
					execution_full_order.append(proposal)
			else:
				execution_full_order.append(proposal)

	if len(execution_full_order) == len(proposals):
		if len(execution_full_order) > 1:
			return {'best': (execution_full_order[0], ), 'other': [(x, ) for x in execution_full_order[1:]]}
		else:
			return {'best': (execution_full_order[0], ), 'other': ()}

	complete_other_offers = _get_other_proposals(other_proposals, order_products)

	if len(execution_full_order) == 0:
		if len(complete_other_offers) > 1:
			return {'best': complete_other_offers[0], 'other': complete_other_offers[1:]}
		elif len(complete_other_offers) == 1:
			return {'best': complete_other_offers[0], 'other': ()}
		else:
			return {'best': (), 'other': ()}

	if len(execution_full_order) > 1:
		return {
			'best': (execution_full_order[0], ),
			'other': [(x, ) for x in execution_full_order[1:]] + complete_other_offers
		}
	return {'best': (execution_full_order[0], ), 'other': complete_other_offers}


def _get_total_count_product(proposal):
	result = 0
	for data in proposal.order_products.values:
		result += sum([x[0] for x in data])
	return result


def _get_other_proposals(proposals, order_products):
	result = []
	order_products_dict = _get_dict_order_products(order_products)
	missing_items = _get_list_missing_items(proposals, order_products)
	missing_items.sort(key=lambda n: n[0])
	for x in range(len(missing_items)):
		for y in range(x+1, len(missing_items)):
			if missing_items[x][0] == 1:
				for product in missing_items[x][1].items():
					if product[0] in missing_items[y][1].keys():
						break
				else:
					result.append((missing_items[x][2], missing_items[y][2]))
					continue

			print(missing_items[x][0])
			is_add = True
			for product in missing_items[x][1].items():
				if not is_add:
					break
				if product[1] is None and product[0] in missing_items[y][1].keys():
					break
				for item in product:
					if missing_items[y][2].get(item[1][0]) is None:
						is_add = False
						break
					if item[1][1]+missing_items[y][2][item[1][0]] >= order_products_dict[item[0]].total_count:
						continue
					is_add = False
					break
			else:
				result.append((missing_items[x][2], missing_items[y][2]))
	return result


def _get_list_missing_items(proposals, order_products):
	result = []
	for proposal in proposals:
		missing_items = [0, dict(), proposal]

		if len(proposal.order_products) == len(order_products):
			for product in order_products:
				if product.total_count == sum([x[0] for x in proposal.order_products[str(product.id)]]):
					continue
				_search_missing_items(proposal, product, missing_items)
		else:
			for product in order_products:
				if proposal.order_product.get(str(product.id)) is None:
					missing_items[0] = 3
					missing_items[0].update({product.id: None})
					continue
				if missing_items[0] != 3:
					_search_missing_items(proposal, product, missing_items, 2)
					continue
				_search_missing_items(proposal, product, missing_items, 3)
		result.append(missing_items)
	return result


def _search_missing_items(proposal, product, missing_items, context=1):
	for data in proposal.order_products[str(product.id)]:
		if data[0] < product.count_and_address[str(data[1])]:
			missing_items[0] = context
			if missing_items[1].get(product.id) is None:
				missing_items[1].update(
					{product.id: [(data[1], product.count_and_address[str(data[1])] - data[0])]}
				)
			missing_items[1][product].append((data[1], product.count_and_address[str(data[1])] - data[0]))


def _get_dict_order_products(order_products):
	result = dict()
	for product in order_products:
		result.update({product.id: product})
	return result
