FROM debian:stable-slim@sha256:fffe16098bcefa876d01862a61f8f30ef4292c9485940e905d41a15d8459828b

RUN apt-get update -q && \
    apt-get dist-upgrade -y && \
    apt-get install -y apt-utils wget lsb-release && \
    wget https://deb.globaleaks.org/install-globaleaks.sh && \
    chmod +x install-globaleaks.sh && \
    ./install-globaleaks.sh -y -n && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8080 8443

USER globaleaks

CMD ["/usr/bin/python3", "/usr/bin/globaleaks", "--working-path=/var/globaleaks/", "-n"]
