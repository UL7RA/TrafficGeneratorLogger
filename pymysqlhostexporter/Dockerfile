FROM python:3.9.3-buster

COPY requirements.txt /tmp/

RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . ./app

WORKDIR /app

CMD [ "python","./pymysqlhostexporter.py" ]