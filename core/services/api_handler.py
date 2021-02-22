from django.conf import settings
from django.http import HttpResponse

import requests
import yadisk


def inn_search(inn):
	try:
		search = requests.get('https://api-fns.ru/api/egr?req=' + inn + '&key=d38f57835907b8de4d481c100f79f0eb2f861f2e')
		json = search.json()
		if json.get('items', False):
			text = json['items'][0]['ЮЛ']['НаимСокрЮЛ']
			return HttpResponse(text)
		else:
			return HttpResponse('Не найдено')
	except(requests.RequestException, ValueError):
		return HttpResponse('Не найдено')


def upload_file_company(index, file):
	disk = yadisk.YaDisk(token=settings.YANDEX_API_TOKEN)
	if disk.check_token() and file is not None:
		disk.mkdir("/files_company/" + str(index))
		disk.upload(file, "/files_company/%s/document.pdf" % str(index))


def delete_file_company(index):
	disk = yadisk.YaDisk(token=settings.YANDEX_API_TOKEN)
	if disk.check_token():
		disk.remove("/files_company/" + str(index), permanently=True)
