#!/bin/sh


url="node"
payload="{'fuffa': 'xxx'}"
echo "\n\nNEXT: $url"
echo $payload
read y
curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json

url="nodwRONGe"
payload="{'fuffa': 'xxx'}"
echo "\n\nNEXT: $url"
read y
curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json

url="admin/group/GR0UP1D/"
payload="{'xxx': 'yyy'}"
echo "\n\nNEXT: $url"
read y
curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json

url="admin/group/GR0UP1D/"
echo "\n\nNEXT: GET $url"
read y
curl -G http://127.0.0.1:8082/$url

url="submission/48329049032840923/status"
payload="{'xxx': 'yyy'}"
echo "\n\nNEXT: $url"
read y
curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json

url="external_test/4832"
payload="{'xxx': 'yyy'}"
echo "\n\nNEXT: $url"
read y
curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json

url="tip/4u3242309/download_material"
payload="{'xxx': 'yyy'}"
echo "\n\nNEXT: $url"
read y
curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json

url="tip/pertinence"
payload="{'xxx': 'yyy'}"
echo "\n\nNEXT: $url"
read y
curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json
