#!/bin/bash
set -x
set -e

TT=`tty`
BASE='http://localhost:8082'

printf 'Logging into service %s\n\n' $BASE

read session_id < <(curl -s -A 'test-script' \
     -X POST -H 'Content-type: application/json' \
     -d '{"password": "nn2@n.org","username":"admin"}' \
     $BASE/authentication | tee -p $TT | python -c 'import json, sys; print(json.loads(sys.stdin.read())["session_id"]);'
  )

printf '\nAcquired session_id: %s\n' $session_id

printf '\nGetting tls/config\n\n'

curl -vvv -A 'test-script' \
    -H "X-Session: $session_id" \
    "$BASE/admin/config/tls"

printf '\nIssuing a Cert Sig Request\n\n'

curl -vvv -A 'test-script' \
     -X POST -H 'Content-type: application/json' \
    -H "X-Session: $session_id" \
    -d '{"country":"stato","province":"regione","city":"citta","company":"azienda","department": "gruppo","email": "indrizzio@asdf"}' \
    "$BASE/admin/config/tls/csr"


printf '\nPosting a private key\n\n'

curl -vvv -A 'test-script' \
     -X POST -H 'Content-type: application/json' \
    -H "X-Session: $session_id" \
    --data @cert_upload.json \
    "$BASE/admin/config/tls/files"

printf 'Deleting content\n\n'

#curl -vvv -A 'test-script' -i -X DELETE -H "X-Session: $session_id" "$BASE/admin/config/tls"
