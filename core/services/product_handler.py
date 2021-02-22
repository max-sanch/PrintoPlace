from django.shortcuts import get_object_or_404
from core import models


def get_sorted_products(request):
	sort = request.GET.get("sort")
	search = request.GET.get("search")
	products = sorted(models.Product.objects.all(), key=lambda x: x.price)

	if search is not None and search != '':
		products = list(filter(lambda x: search.lower() in x.name.lower(), products))

	if sort is not None:
		if sort == 'price_down':
			products = sorted(products, key=lambda x: x.price)[::-1]
		elif sort == 'popularity':
			products = sorted(products, key=lambda x: x.name)
		elif sort == 'name':
			products = sorted(products, key=lambda x: x.name)
	return products


def get_characteristic_list(kwargs, product=None):
	if kwargs.get('slug') is not None:
		product = get_object_or_404(models.Product, slug=kwargs.get('slug'))

	characteristics = get_object_or_404(models.ProductCharacteristics, product=product)
	char_list = [x for x in characteristics.__dict__.items()]
	characteristic_list = []

	for char in char_list[3:]:
		if char[1].get('default', 0) is not None:
			name = models.ProductCharacteristics._meta.get_field(char[0]).verbose_name
			characteristic_list.append((name, char[1]))
	return characteristic_list
