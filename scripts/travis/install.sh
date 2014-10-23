#!/bin/sh
sudo apt-get install tor tor-geoipdb
sudo apt-get install nodejs npm
sudo apt-get install python-pip


(cd GLBackend && \
    sudo pip install -r requirements.txt && \
    sudo pip install coverage coveralls
)

(cd GLClient && \
    sudo -i npm install --silent -g grunt-cli bower && \
    sudo npm install
)
