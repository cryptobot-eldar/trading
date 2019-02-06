#!/bin/bash

sleep 10000
ps x | awk {'{print $1}'} | awk 'NR > 1' | xargs kill