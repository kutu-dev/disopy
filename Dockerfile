FROM python:3.13-alpine

RUN pip install disopy
RUN mkdir -p /config

VOLUME ["/config"]

CMD ["disopy", "-c", "/config"]
