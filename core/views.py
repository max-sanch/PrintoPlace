from django.views.generic.base import TemplateView


class ProductPageView(TemplateView):
	template_name = "product_pages/one_product.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['name'] = 'Пластиковая карта'
		return context
