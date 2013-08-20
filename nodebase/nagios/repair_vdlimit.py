#!/usr/bin/env python

import os
import sys

def reset_vdlimit(slicename):
    print "Before:"
    os.system("vdlimit --xid %s /vservers | awk '{print \"   \"$0}'" % slicename)

    try:
        cmd = "vdu --xid %s --space /vservers 2> /dev/null | awk '{print $2}'"
        space=os.popen( cmd % slicename, 'r').read().strip()
        cmd = "vdu --xid %s --inode /vservers 2> /dev/null | awk '{print $2}'"
        inodes=os.popen( cmd % slicename, 'r').read().strip()
        if int(space) >= 0:
            os.system("vdlimit --xid %s -s space_used=%s /vservers" % (slicename, space))
            os.system("vdlimit --xid %s -s inodes_used=%s /vservers" % (slicename, inodes))
    except:
        print "error"
        pass

    print "After:"
    os.system("vdlimit --xid %s /vservers | awk '{print \"   \"$0}'" % slicename)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        reset_vdlimit(sys.argv[1])

