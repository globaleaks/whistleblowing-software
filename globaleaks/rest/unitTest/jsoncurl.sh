#!/bin/sh


url="node"
payload="{'fuffa': 'xxx', 'antani': 1, 'tapioco': '1'}"
echo "\n\nNEXT: $url"
echo $payload
read y
#curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json

url="nodwRONGe"
echo "\n\nNEXT: $url"
read y
#curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json

url="admin/group/GR0UP1D/"
echo "\n\nNEXT: $url"
read y
curl -i -H "Accept: application/json" -X POST -d "$payload" http://127.0.0.1:8082/$url 

url="admin/group/GR0UP1D/"
echo "\n\nNEXT: PUT $url"
read y
curl -i -H "Accept: application/json" -X PUT -d "$payload" http://127.0.0.1:8082/$url 

url="admin/group/GR0UP1D/"
echo "\n\nNEXT: GET $url"
read y
curl -i -H "Accept: application/json" http://127.0.0.1:8082/$url 

url="submission/48329049032840923/status"
echo "\n\nNEXT: $url"
read y
curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json

url="external_test/4832"
echo "\n\nNEXT: $url"
read y
curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json

url="tip/4u3242309/download_material"
echo "\n\nNEXT: $url"
read y
curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json

url="tip/pertinence"
echo "\n\nNEXT: $url"
read y
curl http://127.0.0.1:8082/$url --data-urlencode $payload@my.json
