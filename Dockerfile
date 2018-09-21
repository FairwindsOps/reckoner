FROM python:2.7-alpine3.7

ADD . /autohelm
RUN pip install ./autohelm

ENTRYPOINT ["autohelm"]
