#!/usr/bin/env python2
""" Python template for a future nagios check_* command. """

import os
import sys
import time
import signal

# NOTE: You only have to modify custom_check for basic checks.
#       If you need to add additional arguments, modify parse_args

def custom_check(opt, args):
    """
        custom_check:
            opt is an OptParse return value containing all commandline and
            default values for arguments defined in parse_args().

            Values are referenced via opt.<valuename>  without "<>"
        args:
            a list of extra positional arguments on the command line that were
            not switched (prefixed with "-" or  "--")

        RETURN VALUE:
            A tuple with (return_state, "message")

            return_state should be one of:
                STATE_OK = 0
                STATE_WARNING = 1
                STATE_CRITICAL = 2
                STATE_UNKNOWN = 3
            Message is any string.
    """
    try: 
        check_error = 0
        #raise Exception("OMG!")
        return (STATE_WARNING, "I'm warning you")
    except:
        check_error = 1
        return (STATE_CRITICAL, "FAIL.")

    return (STATE_OK, "ok, all ready.")


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

