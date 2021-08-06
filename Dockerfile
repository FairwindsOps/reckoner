FROM python:3.8

ADD . /bin/reckoner
RUN pip install ./reckoner

ENTRYPOINT ["reckoner"]
CMD ["--help"]
