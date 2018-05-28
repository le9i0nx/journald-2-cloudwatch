FROM ubuntu:xenial

VOLUME /etc/jd2cw/

# For click.
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y python3-systemd python3-pip python3-setuptools \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir /jd2cw
WORKDIR /jd2cw
COPY jd2cw /jd2cw/jd2cw
COPY setup.py /jd2cw/
RUN python3 setup.py install

ENTRYPOINT ["jd2cw"]
CMD ["--help"]
