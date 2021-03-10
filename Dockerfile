FROM python:3.8
WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn

RUN apt-get update && apt-get install netcat -y

COPY . /usr/src/app

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]