#!/bin/bash
# set -e
# set -o pipefail
dest=/var/www/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
mv /var/www/releases/tmp $dest
aws s3 cp s3://squacapi-config/bash/$DEPLOYMENT_GROUP_NAME.env  $dest/app/.env

# virtual env vars
WORKON_HOME=/var/.virtualenvs
VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
source $dest/app/.env
echo $DEPLOYMENT_GROUP_NAME
workon $DEPLOYMENT_GROUP_NAME
echo "I can't believe I have to debug this way"
pip3 install  -r $dest/requirements/production.txt
python $dest/app/manage.py migrate
python $dest/app/manage.py collectstatic --noinput
echo "this is crap"
deactivate



