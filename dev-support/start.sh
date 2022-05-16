#!/bin/bash
/usr/local/redis/bin/redis-server /etc/redis.conf
supervisord -c /etc/supervisor/supervisord.conf
while true
do
    sleep 36000
done