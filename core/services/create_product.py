from core import models


def create_product(product):
	obj = models.Product(
		slug=product['slug'],
		name=product['name'],
		category=product['category'],
		description=product['description'],
		price=product['price'],
	)
	obj.save()
	create_char(product['char'], obj.pk)


def create_char(char, product_id):
	obj = models.ProductCharacteristics(
		product=models.Product.objects.get(id=product_id),
		format=char['format'],
		color=char['color'],
		material=char['material'],
		rounding=char['rounding'],
		adhesive_side=char['adhesive_side'],
		sheets_count=char['sheets_count'],
		sheets_arrangement=char['sheets_arrangement'],
		protective_film=char['protective_film'],
		spiral_color=char['spiral_color'],
		finishing=char['finishing'],
		paper=char['paper']
	)
	obj.save()


def start():
	for product in PRODUCTS:
		create_product(product)


NONE = {'default': None}

PRODUCTS = [
		{
			'slug': 'square_sticker',
			'name': 'Наклейка квадратная',
			'category': 6,
			'description':
				'Цвет: 4/0, 5/0; Материал: Клейкая бумага 70 г, Пленка ПВХ 90 мкм белая/прозрачная; \
				Скругление: без, 3 мм',
			'price': 20,
			'char': {
				'format': {"default": [
					"297x297мм", "210x210мм", "148x148мм", "120x120мм",
					"105x105мм", "72x72мм", "60x60мм", "50x50мм", "40x40мм"]},
				'color': {"default": ["4/0", "5/0"]},
				'material': {"default": ["Клейкая бумага 70г", "Пленка ПВХ 90 мкм, белая", "Пленка ПВХ 90 мкм, прозрачная"]},
				'rounding': {"default": ["без", "3мм"]},
				'adhesive_side': {"default": ["задняя", "передняя"]},
				'sheets_count': NONE,
				'sheets_arrangement': NONE,
				'protective_film': NONE,
				'spiral_color': NONE,
				'finishing': NONE,
				'paper': NONE,
			}
		},
		{
			'slug': 'wall_calendar',
			'name': 'Настенный календарь',
			'category': 3,
			'description':
				'Формат: Портрет, Пейзаж, Квадрат; Цвет: 4/0, 1/0; Материал: Матовая печать 170г/250г, \
				Глянцевая фотопечать 170г/250г; Защитная плёнка: Без, С защитной плёнкой; Цвет спирали: \
				Чёрный, Серебряный, Белый;',
			'price': 240,
			'char': {
				'format': {
					"Портрет": ["А2", "A3", "A4", "130x420мм", "A5"],
					"Пейзаж": ["А2", "A3", "A4", "A5"],
					"Квадрат": ["297x297мм"]},
				'color': {"default": ["4/0", "1/0"]},
				'material': {"default": [
					"Клейкая бумага 70г", "Матовая печать 250г", "Глянцевая фотопечать 170г", "Глянцевая фотопечать 250г"]},
				'rounding': NONE,
				'adhesive_side': NONE,
				'sheets_count': {"default": ["13", "14", "15"]},
				'sheets_arrangement': {"default": ["Продолжающиеся ", "Последний повернутый после картонной обратной стороны"]},
				'protective_film': {"default": ["Без", "С защитной плёнкой"]},
				'spiral_color': {"default": ["Чёрный", "Серебряный", "Белый"]},
				'finishing': {"default": [
					"Без", "Ламинирование фольгой, матовая лицевая сторона",
					"Ламинирование фольгой, глянцевая лицевая сторона",
					"УФ-лак, глянцевая лицевая сторона", "УФ-лак, матовая лицевая сторона"]},
				'paper': NONE,
			}
		},
		{
			'slug': 'spiral_bound_notebook',
			'name': 'Блокнот со спиральным переплетом',
			'category': 1,
			'description':
				'Формат: Портрет, Пейзаж; Бумага: Офсетная бумага 90 г, Переработанная офсетная бумага \
				80 г; Цвет: 4/0, 1/0, 4/4, 1/1; Материал: Матовая печать, Глянцевая печать; Цвет спирали\
				: Чёрный, Серебряный, Белый;',
			'price': 275,
			'char': {
				'format': {
					"Портрет": ["A4", "A5"],
					"Пейзаж": ["A4", "A5"]},
				'color': {
					"Обложка": ["4/0", "1/0"],
					"Содержание": ["4/4", "4/0", "1/1", "1/0"]},
				'material': {
					"Обложка": [
						"Матовая печать 170г", "Матовая печать 250г", "Матовая печать 300г",
						"Глянцевая печать 170г", "Глянцевая печать 250г", "Глянцевая печать 300г"],
					"Задняя сторона": ["Картон серый"]},
				'rounding': NONE,
				'adhesive_side': NONE,
				'sheets_count': {"default": ["25", "50", "100"]},
				'sheets_arrangement': NONE,
				'protective_film': NONE,
				'spiral_color': {"default": ["Чёрный ", "Серебряный ", "Белый"]},
				'finishing': {"default": [
					"Глянцевая дисперсионная краска спереди", "Матовая дисперсионная краска спереди",
					"Глянцевый дисперсионный лак спереди и сзади", "Матовый дисперсионный лак спереди и сзади",
					"Ламинирование фольгой глянцевое спереди", "Ламинирование фольгой матовое спереди",
					"Ламинирование фольгой глянцевое спереди и сзади", "Ламинирование фольгой матовое спереди и сзади"]},
				'paper': {"default": ["Офсетная бумага 90г", "Переработанная офсетная бумага 80г"]},
			}
		},
		{
			'slug': 'advertising_flyer',
			'name': 'Рекламный флаер',
			'category': 5,
			'description':
				'Формат: Портрет, Пейзаж, Квадрат, Свободный формат; Цвет: 4/4, 1/1; Материал: Матовая \
				печать, Глянцевая печать, Хромокартон, Натуральная бумага, Картон офсетный, Офсетная \
				бумага, Переработанная бумага;',
			'price': 54,
			'char': {
				'format': {
					"Портрет": ["A3", "A4", "A5", "105х210мм", "100х210мм", "99х210мм", "A6", "A7", "A8"],
					"Пейзаж":["A3", "A4", "A5", "210х105мм", "210х100мм", "210х99мм", "A6", "A7", "A8"],
					"Квадрат": ["210х210мм", "148х148мм", "120х120мм", "105х105мм", "100х100мм"],
					"Свободный": ["74мм", "420мм"]},
				'color': {"default": ["4/4", "1/1"]},
				'material': {"default": [
					"Матовая печать 90г", "Матовая печать 135г", "Матовая печать 170г", "Матовая печать 250г",
					"Матовая печать 300г", "Матовая печать 400г", "Глянцевая печать 100г", "Глянцевая печать 135г",
					"Глянцевая печать 170г", "Глянцевая печать 250г", "Глянцевая печать 300г", "Глянцевая печать 400г",
					"Хромокартон 450г", "Натуральная бумага 90г", "Натуральная бумага 160г", "Натуральная бумага 250г",
					"Картон офсетный 300г", "Офсетная бумага 80г", "Офсетная бумага 90г", "Офсетная бумага 100г",
					"Офсетная бумага премиум-класса 120г", "Переработанная бумага 80г", "Переработанная бумага 170г",
					"Переработанная бумага 250г"]},
				'rounding': NONE,
				'adhesive_side': NONE,
				'sheets_count': NONE,
				'sheets_arrangement': NONE,
				'protective_film': NONE,
				'spiral_color': NONE,
				'finishing': NONE,
				'paper': NONE,
			}
		},
		{
			'slug': 'round_sticker',
			'name': 'Наклейка круглая',
			'category': 6,
			'description':
				'Цвет: 4/0, 5/0; Материал: Клейкая бумага 70 г, Пленка ПВХ 90 мкм белая/прозрачная; \
				Клейкая сторона: задняя, передняя;',
			'price': 23,
			'char': {
				'format': {"default": [
					"210x210мм", "140x140мм", "100x100мм", "90x90мм", "80x80мм", "70x70мм", "60x60мм", "50x50мм", "40x40мм"]},
				'color': {"default": ["4/0", "5/0"]},
				'material': {"default": ["Клейкая бумага 70г", "Пленка ПВХ 90 мкм, белая", "Пленка ПВХ 90 мкм, прозрачная"]},
				'rounding': NONE,
				'adhesive_side': {"default": ["задняя", "передняя"]},
				'sheets_count': NONE,
				'sheets_arrangement': NONE,
				'protective_film': NONE,
				'spiral_color': NONE,
				'finishing': NONE,
				'paper': NONE,
			}
		}
	]
