FROM python:3.8

ADD . /reckoner
RUN pip install ./reckoner

ENTRYPOINT ["reckoner"]
CMD ["--help"]
