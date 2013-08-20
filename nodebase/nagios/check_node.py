#!/usr/bin/env python2
""" Python template for a future nagios check_* command. """

import os
import sys
import time
import signal
import stat

# NOTE: You only have to modify custom_check for basic checks.
#       If you need to add additional arguments, modify parse_args
def get_count_from_command(cmd):
    try:
        result = int(os.popen(cmd, 'r').read().strip())
        return result
    except:
        return -2

    return -1

def custom_check(opt, args):
    """ 
        Check for internally consistent node states.
    """
    # TODO: check session size
    size = os.stat("/etc/planetlab/session")[stat.ST_SIZE]
    if size == 0:
        # NOTE: we're assuming that !=0 means ok.  Not strictly true.
        return (STATE_CRITICAL, "/etc/planetlab/session is zero size.")

    # NOTE: ignore the vlan offload settings.
    cmd = """ethtool -k eth0 | grep offload | grep -v vlan | grep -v ": off" | wc -l"""
    result = get_count_from_command(cmd)
    if result > 0:
        # NOTE: some offload feature has a state other than 'off'. this could be a problem.
        return (STATE_CRITICAL, "ethtool settings may have 'offload' enabled.")

    # NOTE: check ports
    cmd = """netstat -nltp | awk '{ if ( $4 ~ "0.0.0.0:" )  { print $0 }}' | grep -vE ":806 |:22 |:5666 " | wc -l"""
    result = get_count_from_command(cmd)
    if result > 0:
        # NOTE: some extra ports are open on public interface.
        return (STATE_CRITICAL, "Extra ports detected on public interface.")

    # NOTE: check sidestream & NPAD xids are equal.
    cmd1 = """cat /proc/sys/net/ipv4/web100_sidestream_xid"""
    cmd2 = """id -u iupui_npad"""
    r1 = get_count_from_command(cmd1)
    r2 = get_count_from_command(cmd2)
    if r1 <= 0 or r2 <= 0 or r1 != r2:
        return (STATE_CRITICAL, "Sidestream (%s) != NPAD (%s)" % (r1,r2))

    # NOTE: check OONI.
    cmd = """ooni_id=`id -u mlab_ooni`; X=`cat /proc/virtual/$ooni_id/status | grep CCaps | awk '{print $2}'` ; echo $(( 0x$X & 0x10000000 ))"""
    result = get_count_from_command(cmd)
    if result != 0:
        return (STATE_CRITICAL, "OONI has WEB100_ENABLED")

    # NOTE: check for RunlevelAgent.py & oombailout.py
    cmd = """ps ax | grep -v grep | grep -E "RunlevelAgent.py|oombailout.py" | wc -l"""
    result = get_count_from_command(cmd)
    if result != 2:
        return (STATE_CRITICAL, "RunlevelAgent or oombailout missing")

    # NOTE: check nodemanager is running. It should alwasy be up.
    cmd = """ps ax | grep -v grep | grep -E "nm.py|nodemanager.py" | wc -l"""
    result = get_count_from_command(cmd)
    if result == 0:
        # NOTE: NM is not running so this is a problem.
        return (STATE_CRITICAL, "NodeManager not running.")

    return (STATE_OK, "All checks passed: %s %s" % (size, result))


def parse_args():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", 
                       default=False, 
                       action="store_true", 
                       help="Verbose mode: print extra details.")
    parser.add_option("-t", "--timeout", dest="timeout", 
                       type="int", 
                       default=60, 
                       help="Kill this script after 'timeout' seconds.")

    if len(sys.argv) == 0: 
        # len() never == 0.  included as reference for mandatory args.
        parser.print_help()
        sys.exit(1)
        
    (options, args) = parser.parse_args()
    return (options, args)


STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3
STATE_DEPENDENT = 4

state_list = [ STATE_OK, STATE_WARNING, STATE_CRITICAL, 
               STATE_UNKNOWN, STATE_DEPENDENT, ]


class TimeoutException(Exception):
    pass

def init_alarm(timeout):
    def handler(signum, _frame):
        """Raise a TimeoutException when called"""
        raise TimeoutException("signal %d" % signum)
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)

def clear_alarm():
    signal.alarm(0)

def main():
    """ Unless there is a bug here, 
        it is preferable to modify only custom_check()
    """

    (opt, args) = parse_args()
    init_alarm(opt.timeout)

    # defaults
    ret = STATE_UNKNOWN
    timeout_error = 0
    exception_error = 0

    try:
        (ret,msg) = custom_check(opt, args)
        if ret not in state_list:
            raise Exception("Returned wrong state type from custom_check(): should be one of %s" % state_list)

    except TimeoutException:
        timeout_error = 1
    except KeyboardInterrupt:
        sys.exit(STATE_UNKNOWN)
    except Exception, err:
        exception_error = 1
        import traceback
        # this shouldn't happen, so more details won't hurt.
        traceback.print_exc()

    clear_alarm()

    if exception_error > 0 or timeout_error > 0 or ret == STATE_UNKNOWN:
        print "STATE UNKNOWN - could not complete check (%s)" % exception_error
        sys.exit(STATE_UNKNOWN)
    elif ret == STATE_CRITICAL:
        print "STATE CRITICAL - %s" % msg
    elif ret == STATE_WARNING:
        print "STATE WARNING - %s" % msg
    else:
        print "STATE OK - %s" % msg

    sys.exit(ret)

if __name__ == "__main__":
    main()

