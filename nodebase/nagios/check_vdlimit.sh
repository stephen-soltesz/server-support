#!/bin/bash

# nagios return codes
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2

# floating functions copied from LinuxJournal
# http://www.linuxjournal.com/content/floating-point-math-bash
float_scale=2

function float_eval()
{
    local stat=0
    local result=0.0
    if [[ $# -gt 0 ]]; then
        result=$(echo "scale=$float_scale; $*" | bc -q 2>/dev/null)
        stat=$?
        if [[ $stat -eq 0  &&  -z "$result" ]]; then stat=1; fi
    fi
    echo $result
    return $stat
}

function float_cond()
{
    local cond=0
    if [[ $# -gt 0 ]]; then
        cond=$(echo "$*" | bc -q 2>/dev/null)
        if [[ -z "$cond" ]]; then cond=0; fi
        if [[ "$cond" != 0  &&  "$cond" != 1 ]]; then cond=0; fi
    fi
    local stat=$((cond == 0))
    return $stat
}

# space used by the sliver in bytes
used=$(sudo vdlimit --xid=$1 /vservers | grep "space_used" | sed -e "s/space_used=\(.*\)/\1/")
# total space allowed to the sliver in bytes
total=$(sudo vdlimit --xid=$1 /vservers | grep "space_total" | sed -e "s/space_total=\(.*\)/\1/")
# calculate the percentage of space used out of the allocated
used_pct=$(float_eval "$used.0 / $total.0 * 100")

if float_cond "$used_pct > 90.0"
then
    echo "QUOTA CRITICAL: $1 - $used out of $total bytes ($used_pct%)."
    exit $STATE_CRITICAL
fi

if float_cond "$used_pct > 80.0"
then
    echo "QUOTA WARNING: $1 - $used out of $total bytes ($used_pct%)."
    exit $STATE_WARNING
fi

echo "QUOTA OK: $1 - $used out of $total bytes ($used_pct%)."
exit $STATE_OK
