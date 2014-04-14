#!/bin/sh

while true; do
	(sleep 90  && x=`ps ax | grep stresser | awk {'print $1'}` && for i in $x; do kill -1 $i; done) &
	python stresser.py
done


