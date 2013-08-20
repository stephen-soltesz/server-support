#!/usr/bin/env python2
"""Verify that root dirs & slices have a r/w filesystem"""

import getopt
import re
import signal
import sys
import urllib
import os

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3
STATE_DEPENDENT = 4


def handler(signum, _frame):
    """Raise an IOError exception when called"""

    raise IOError("Signal handler called with signal %d" % signum)

def readonly_cmd(prefix, path):
    cmd = """python -c 'import os; f = open("%s%s/.test_readonly", "w"); f.close(); os.remove("%s%s/.test_readonly");'""" % (prefix, path, prefix, path)
    return cmd

def main(argv):
    """Main function"""

    slice_list = ['gt_partha', 'iupui_ndt', 'iupui_npad', 'mpisws_broadband']

    try:
        opts, _args = getopt.getopt(argv, "vt:g:", ["verbose", "timeout="])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(STATE_UNKNOWN)

    timeout = 60
    verbose = 0
    for opt, arg in opts:
        if opt in ("-t", "--timeout"):
            timeout = arg
        elif opt in ("-v", "--verbose"):
            verbose = 1
        else:
            usage()
            sys.exit(STATE_UNKNOWN)
    
    unknown_error = 0
    root_error_count = 0
    slice_error_count = 0

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)

    try:
        for test_dir in ['/vservers/', '/']:
            # NOTE: attempt to touch a small file.
            cmd = readonly_cmd("", test_dir)
            # NOTE: add sudo so nrpe user can execute this command.
            root_cmd = "sudo " + cmd
            if verbose: print root_cmd
            r = os.system(root_cmd)
            if r != 0:
                root_error_count += 1

        for slicename in slice_list:
            # NOTE: enter slice and attempt to touch a small file.
            cmd = readonly_cmd("/home/", slicename)
            # NOTE: add sudo so nrpe can execute this command
            #vserver_cmd = "sudo vserver " + slicename + " exec " + cmd
            vserver_cmd = "sudo su -l " + slicename + """ <<EOF
""" + cmd + """
EOF"""
            if verbose: print vserver_cmd
            r = os.system(vserver_cmd)
            if r != 0:
                slice_error_count += 1

    except KeyboardInterrupt:
        sys.exit(STATE_UNKNOWN)
    except Exception, err:
        unknown_error = 1
        print str(err)

    signal.alarm(0)

    if unknown_error > 0:
        print "STATE UNKNOWN - fetching data timed out"
        sys.exit(STATE_UNKNOWN)
    elif root_error_count > 0 or slice_error_count > 0:
        print "STATE CRITICAL - %s/%s root/slice errors" % (root_error_count, 
                                                            slice_error_count)
        sys.exit(STATE_CRITICAL)
    else:
        print "STATE OK - read/write test succeeded"
        sys.exit(STATE_OK)


def usage():
    """Print usage information"""
    print "--timeout=<seconds> --gbfree=n"


if __name__ == "__main__":
    main(sys.argv[1:])

