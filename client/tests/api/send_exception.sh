#!/bin/bash

curl -A 'test-script' -i \
     -X POST -H 'Content-type: application/json' \
     -d '{"errorUrl": "this.is.not.a.domain","agent":"curl","errorMessage":"1:<a onclick=alert(0)>hi!</a> 2:<img src=http://nskelsey.com/contact.png />","stackTrace":[1,2,3,"parseme"]}' \
     http://localhost:8082/exception

