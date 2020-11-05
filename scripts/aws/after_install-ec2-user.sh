#!/bin/bash
set -e
set -o pipefail
dest=/var/www/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
mv /var/www/releases/tmp $dest
aws s3 cp s3://squacapi-config/bash/$DEPLOYMENT_GROUP_NAME.env  $dest/app/.env



VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
workon $DEPLOYMENT_GROUP_NAME
source $dest/app/.env
pip3 install  -r $dest/requirements/production.txt
python $dest/app/manage.py migrate
python $dest/app/manage.py collectstatic --noinput
deactivate



