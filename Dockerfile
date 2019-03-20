FROM python:3.7

ADD . /reckoner
RUN pip install ./reckoner

ENTRYPOINT ["reckoner"]
