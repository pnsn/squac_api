#!/bin/bash
set -e
set -o pipefail

#should get 401 (unauthenticate user)
url=https://$DEPLOYMENT_GROUP_NAME.pnsn.org
resp=`curl -sL -w "%{http_code}\\n" "$url" -o /dev/null`
if [ $resp == 401 ];then
    echo "Success"
else
    echo "Not success - $resp"
    exit 1
fi

