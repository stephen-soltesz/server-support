#!/usr/bin/python
#
# Copyright (c) 2003 Intel Corporation
# All rights reserved.
#
# Copyright (c) 2004-2006 The Trustees of Princeton University
# All rights reserved.


import xmlrpclib
import xml.parsers.expat
import hmac
import string
import sha
import cPickle
import os
import sys

stash = None

def create_auth_structure( ):
    # This is a bit easier with a bit of shell script; apologies for the mixed mode.
    line = os.popen(""" 
    function read_value () {
        echo `grep $1 /usr/boot/plnode.txt | sed -e 's/.*=//g' -e 's/\"//g' `
    }
    if ! ( mount | grep /mnt/boot ) ; then 
        mkdir -p /mnt/boot/
        mount /dev/cdrom /mnt/boot/
        zcat /mnt/boot/overlay.img | cpio -i --to-stdout usr/boot/plnode.txt 2> /dev/null > /usr/boot/plnode.txt
        ID=$( read_value "NODE_ID" ) 
        IP=$( read_value "IP_ADDRESS" )
        KEY=$( read_value "NODE_KEY" )
        BOOT=$( grep PLC_BOOT_HOST /etc/planetlab/plc_config | sed -e 's/.*=//g' | tr \"'\" ' ' )
        umount /mnt/boot 2> /dev/null
        echo $BOOT $IP $KEY $ID
    fi
""").read().strip()
    print line
    (bootserver,node_ip,node_key,node_id) = line.split()

    bootserver = "https://" + bootserver + "/PLCAPI/"
    print bootserver

    auth= {}
    auth['AuthMethod']= 'hmac'
    auth['node_id'] = int(node_id)
    auth['node_ip'] = node_ip
    node_hmac= hmac.new(node_key, "[]".encode('utf-8'), sha).hexdigest()
    auth['value']= node_hmac

    try:
        auth_session = {}
        api_server = xmlrpclib.Server( bootserver, verbose=0 )
        session = api_server.GetSession(auth)
        auth = auth_session
        print session

    except Exception, e:
        # NOTE: BM has failed to authenticate utterly.
        import traceback
        traceback.print_exc()

    return auth


if __name__ == "__main__":
    create_auth_structure()
