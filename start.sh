#!/bin/bash
#exec &>>/var/log/work.log


./restart.sh &
./start_buy.sh &
./start_sync.sh &
./start_sell.sh

