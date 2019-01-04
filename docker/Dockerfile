FROM ubuntu:18.04

RUN apt-get update -q && \
    apt-get install -y gpg curl supervisor && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN echo "deb http://deb.globaleaks.org bionic/" > /etc/apt/sources.list.d/globaleaks.list
RUN curl -sS https://deb.globaleaks.org/globaleaks.asc | apt-key add -
RUN apt-get update -q && \
    apt-get install -y globaleaks && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV TORPIDDIR=/var/run/tor
ENV TORLOGDIR=/var/log/tor

RUN mkdir -m 02755 "$TORPIDDIR" && chown debian-tor:debian-tor "$TORPIDDIR"
RUN chmod 02750 "$TORLOGDIR" && chown debian-tor:adm "$TORLOGDIR"
ADD data/torrc /etc/tor/torrc

VOLUME [ "/var/globaleaks/" ]
EXPOSE 80
EXPOSE 443

ADD data/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord"]
