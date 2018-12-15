FROM postgres:9.6.9

RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip \
  && rm -r /var/lib/apt/lists/*
RUN pip3 install --quiet psycopg2-binary sqlalchemy
