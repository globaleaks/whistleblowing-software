#!/bin/bash

openssl req \
       -x509 -nodes -days 365 -sha512 \
       -newkey rsa:1024 -keyout priv_key.pem -out cert.pem
