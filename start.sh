#!/bin/bash
#exec &>>/var/log/work.log

./start_buy.sh&
./start_sell.sh&

