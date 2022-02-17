FROM python:3.10.2

ADD . /bin/reckoner
RUN pip install ./reckoner

ENTRYPOINT ["reckoner"]
CMD ["--help"]
