FROM python:3.10.3

ADD . /bin/reckoner
RUN pip install ./reckoner

ENTRYPOINT ["reckoner"]
CMD ["--help"]
