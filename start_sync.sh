#!/bin/bash


while true
do


SERVICE3='config_sync.py'

ps -ef | grep $SERVICE3 | grep -v grep
[ $?  -eq "0" ] && echo "$SERVICE3 process is running" || echo "$SERVICE3 process is not running, starting"; python /usr/local/bin/config_sync.py
sleep 1000
done
