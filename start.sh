#!/bin/bash
#exec &>>/var/log/work.log

while true
do

  for i in 1; do
    SERVICE0='buy.py'
    ps -ef | grep $SERVICE0 | grep -v grep
    [ $?  -eq "0" ] && echo "$SERVICE0 process is running" || echo "$SERVICE0 process is not running, starting"; python /usr/local/bin/buy.py
  done
sleep 5



  for i in 1; do
    SERVICE1='sell.py'
    ps -ef | grep $SERVICE1 | grep -v grep
    [ $?  -eq "0" ] && echo "$SERVICE1 process is running" || echo "$SERVICE1 process is not running, starting"; python /usr/local/bin/sell.py
  done

sleep 5
done
