#!/usr/bin/env bash

## NOTES:
##   For some reason, the disk quota assigned to a sliver can get out of sync
##   with the actual use by the sliver.
##   This can result in disk_quota warnings in nagios b/c it appears that a
##   slice is using more space than it actually is.
##   To solve this false-positive reading, this script should be run once an
##   hour to re-sync the quota with actual-usage.

function reset_vdlimit () {
    slice=$1
    echo "Limits for $slice before update:"
    vdlimit --xid $slice /vservers/
    spaces=$(vdu --xid $slice --space /vservers | cut -d" " -f2 2> /dev/null )
    inodes=$(vdu --xid $slice --inode /vservers | cut -d" " -f2 2> /dev/null )

    # check that it parses as a number
    if [[ $spaces -ge 0 ]] ; then
        vdlimit --xid $slice -s space_used=$spaces /vservers
    else
        echo "ERROR: could not set space to '$spaces'"
    fi
    if [[ $inodes -ge 0 ]] ; then
        vdlimit --xid $slice -s inodes_used=$inodes /vservers
    else
        echo "ERROR: could not set inodes to '$inodes'"
    fi
    echo "Limits for $slice after update:"
    vdlimit --xid $slice /vservers/

}
function vdu_all_slivers () {
    cd /vservers
    slices=$( ls -d */ | tr '/' ' ' )
    for slice in $slices ; do 
        echo -n "$slice : " 
        vdu --xid $slice --space /vservers
    done
}

if [ -n "$1" ] ; then
    slicelist=$1
else
    slicelist=$( cd /vservers; ls -d */ | tr '/' ' ' | grep -v lost )
fi
for slice in $slicelist ; do
    reset_vdlimit $slice
done

