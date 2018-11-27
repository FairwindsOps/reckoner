FROM python:2.7-alpine3.7

ADD . /reckoner
RUN pip install ./reckoner

ENTRYPOINT ["reckoner"]
