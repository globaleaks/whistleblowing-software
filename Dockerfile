FROM node:8


# install build dependencies (and vim ;-) )
RUN apt update
# todo: we probably don't need all of this.  vim is just for debugging
RUN apt install -y wget curl tzdata vim net-tools software-properties-common python-pip python-dev
RUN npm install -g grunt-cli

# add tor repo and key (we can't do this until after we installed software-properties-common above)
RUN gpg --keyserver keys.gnupg.net --recv A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89
RUN gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | apt-key add -
RUN add-apt-repository 'deb http://deb.torproject.org/torproject.org jessie main'

RUN apt update
RUN apt install -y tor deb.torproject.org-keyring

# install nodejs deps
COPY ./client/package.json /usr/src/globaleaks/client/package.json
COPY ./client/npm-shrinkwrap.json /usr/src/globaleaks/client/npm-shrinkwrap.json
WORKDIR /usr/src/globaleaks/client
RUN npm install
COPY ./client /usr/src/globaleaks/client
RUN grunt copy:sources

# install python deps
COPY ./backend /usr/src/globaleaks/backend
WORKDIR /usr/src/globaleaks/backend
# update pip to fix urllib3 issue, ref: https://stackoverflow.com/a/29081240/5750032
RUN pip install -U pip
RUN pip install -r ./requirements/requirements-jessie.txt
# update python-requests to fix urllib3 issue, ref: https://stackoverflow.com/a/29081240/5750032
RUN pip install requests==2.6.0

# globaleaks won't start unless this dir exists so it can write a pid file.
RUN mkdir /var/run/globaleaks

COPY ./debian/default /etc/default/globaleaks
COPY . /usr/src/globaleaks


# Disable AppArmor and Network Sandboxing.
RUN sed -i -n -e '/^APPARMOR_SANDBOXING=/!p' -e '$aAPPARMOR_SANDBOXING=0' /etc/default/globaleaks
RUN sed -i -n -e '/^NETWORK_SANDBOXING=/!p' -e '$aNETWORK_SANDBOXING=0' /etc/default/globaleaks

# ports exposed by GlobaLeaks
EXPOSE 80
EXPOSE 443

# ports for tor (but maybe we shouldn't expose these... this tor instance is ONLY for GlobaLeaks)
EXPOSE 8082
EXPOSE 8083

# todo: a better docker entrypoint.  Tor needs to run alongside globaleaks.  We could move tor into it's own container, but that makes this image harder to use.
COPY ./docker-entrypoint.sh /opt/docker-entrypoint.sh
RUN chmod +x /opt/docker-entrypoint.sh
ENTRYPOINT ["/opt/docker-entrypoint.sh"]
VOLUME /var/globaleaks/
VOLUME /etc/default/
