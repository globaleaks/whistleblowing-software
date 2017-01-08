#!/bin/bash

TT=`tty`
BASE='http://localhost:8082'

printf 'Logging into service %s\n\n' $BASE

read session_id < <(curl -s -A 'test-script' \
     -X POST -H 'Content-type: application/json' \
     -d '{"password": "nn2@n.org","username":"admin"}' \
     $BASE/authentication | tee -p $TT | python -c 'import json, sys; print(json.loads(sys.stdin.read())["session_id"]);'
  )

printf '\nAcquired session_id: %s\n' $session_id

printf '\nPosting a private key\n\n'

curl -vvv -A 'test-script' \
    -H "X-Session: $session_id" \
    -H "Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryQSeSIiYKGwMGTB5r" \
    --data @priv_key_form.txt "$BASE/admin/files/ssl/priv_key" 

printf 'Deleting the file\n\n'

curl -A 'test-script' -i -X DELETE -H "X-Session: $session_id" $BASE/admin/files/ssl/priv_key


