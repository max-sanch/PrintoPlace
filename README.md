# PrintoPlace - маркетплейс полиграфических услуг

![PrintoPlace](https://max-sanch.github.io/PrintoPlace-front/image/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA.PNG "PrintoPlace")

PrintoPlace - это маркетплейс полиграфических услуг, который позволит
заказать любую продукцию в нужные сроки, необходимого качества и объема,
за счет распределения заказа между несколькими полиграфическими компаниями.

Маркетплейс - будет связующим звеном между заказчиками полиграфической
продукции и ее производителями.

Физлица и компании получат широкий ассортимент продукции, возможность
выполнения заказа в необходимые сроки, независимо от его объема,
выбор из множества исполнителей, а также возможность оперативного
исполнения своего заказа.

## Оглавление

* [Архитектура](#аrchitecture)
* [Инструкции](#guides)
    * [Запуск приложения](#launch-app)
        * [1: Переменные окружения](#environment-variables)
        * [2: Запуск docker-compose](#docker-compose)
    * [Дополнительно](#additionally)
        * [1: Добавить товар](#add-product)

## <a name="аrchitecture"></a> Архитектура
  
![Архитектура](https://storage.googleapis.com/zenn-user-upload/qwazyqc1ie3k2d4e7clgltckw7zx "Архитектура")

## <a name="guides"></a> Инструкции

### <a name="launch-app"></a>Запуск приложения

#### <a name="environment-variables"></a>1: Переменные окружения

Добавте файл `.env` в папку `printoplace` где находится `settings.py`

Далее в `.env` добавте переменные окружения:

```dotenv
SECRET_KEY= #Секретный ключ Django проекта
YANDEX_API_TOKEN= #Токен Яндекс приложения https://oauth.yandex.ru/
DATABASE=postgres

DB_ENGINE=django.db.backends.postgresql
DB_NAME=printoplace
DB_USER=admin
DB_PASSWORD=admin
DB_HOST=db
DB_PORT=5432

EMAIL_HOST= #smtp хост
EMAIL_PORT=25
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
```

#### <a name="docker-compose"></a>2: Запуск docker-compose

Находясь в папке с файлом `docker-compose.yml` выполнить в терминале:

	docker-compose up --build

### <a name="additionally"></a>Дополнительно
	
#### <a name="add-product"></a>1: Добавить товар

Для теста можно добавить товар перейдя по ссылке: `localhost:8000/create_product/`

