#!/bin/bash

sleep 36000
ps x | awk {'{print $1}'} | awk 'NR > 1' | xargs kill