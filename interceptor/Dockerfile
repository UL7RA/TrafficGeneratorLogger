FROM python:3.9.3-buster

COPY requirements.txt /tmp/

RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN apt -y update && apt -y upgrade && apt install tcpdump -y

COPY . ./app

WORKDIR /app

CMD [ "python","./interceptor.py" ]