#!/bin/bash

# nagios return codes
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2


warn_at=$1
critical_at=$2

# count of packet sockets
packet_sockets=$(cat /proc/net/packet | wc -l)

if [[ $packet_sockets -gt $critical_at ]]
then
    echo "PACKET SOCKETS CRITICAL: $packet_sockets open."
    exit $STATE_CRITICAL
fi

if [[ $packet_sockets -gt $warn_at ]]
then
    echo "PACKET SOCKETS WARNING: $packet_sockets open."
    exit $STATE_WARNING
fi

echo "PACKET SOCKETS OK: $packet_sockets open."
exit $STATE_OK
