#!/bin/sh
printenv > /etc/crontab.env
cron -f