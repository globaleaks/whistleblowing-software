#!/bin/sh

rm -rf /var/lib/apt/lists/*
apt-get update
apt-get upgrade -y
sync
