FROM python:3.10.4

ADD . /bin/reckoner
RUN pip install ./reckoner

ENTRYPOINT ["reckoner"]
CMD ["--help"]
