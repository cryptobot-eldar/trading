#!/bin/bash
#exec &>>/var/log/work.log

while true
do
SERVICE0='buy.py'

if ps ax | grep -v grep | grep $SERVICE0 > /dev/null
then
    echo "$SERVICE0 service running "
else
    echo there is no such "$SERVICE0 service, starting"
    python /usr/local/bin/buy.py
fi



SERVICE1='sell.py'

if ps ax | grep -v grep | grep $SERVICE1 > /dev/null
then
    echo "$SERVICE1 service running "
else
    echo there is no such "$SERVICE1 service, starting"
    python /usr/local/bin/sell.py
fi

sleep 10
done
