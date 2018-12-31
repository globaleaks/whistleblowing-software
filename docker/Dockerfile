FROM ubuntu:18.04

RUN apt-get update -q && \
    apt-get install -y gpg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN echo "deb http://deb.globaleaks.org bionic/" > /etc/apt/sources.list.d/globaleaks.list
RUN curl -sS https://deb.globaleaks.org/globaleaks.asc | apt-key add -
RUN apt-get update -q && \
    apt-get install -y globaleaks && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

VOLUME [ "/var/globaleaks/" ]
EXPOSE 80
EXPOSE 443

CMD /usr/bin/python3 /usr/bin/globaleaks --ip=0.0.0.0 --user=globaleaks --group=globaleaks --working-path=/var/globaleaks/ -n