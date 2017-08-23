FROM debian:stretch-slim

VOLUME /etc/jd2cw/

# Install Python, pip and python-systemd.
RUN BUILD_DEPS="curl python3-dev pkg-config gcc git libsystemd-dev" \
    VERSION="233"; \
    apt-get update && \
    apt-get install -y python3 $BUILD_DEPS && \
    curl --fail 'https://bootstrap.pypa.io/get-pip.py' | python3 && \
    pip3 install --no-cache-dir "git+https://github.com/systemd/python-systemd.git/@v$VERSION#egg=systemd" && \
    apt-get purge --auto-remove -y $BUILD_DEPS && \
    pip3 uninstall --yes pip && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /jd2cw
WORKDIR /jd2cw
COPY . /jd2cw/
RUN pip3 install -e "."

ENTRYPOINT ["jd2cw"]
CMD ["--help"]
