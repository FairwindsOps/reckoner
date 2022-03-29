FROM scratch

USER nobody
COPY reckoner /
WORKDIR /
ENTRYPOINT ["/reckoner"]
