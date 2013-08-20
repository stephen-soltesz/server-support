#!/usr/bin/env python

import sys
import os
import subprocess

TESTING=True

prefix = ( "" if not TESTING else os.getcwd() )

PACKAGEDIRS = {
    'rawdir'  : prefix+"/build", 
    'signdir' : prefix+"/etc/slicepkg.signed",
    'keydir'  : prefix+"/etc/slicepkg.keys",
    'vserverdir' : prefix+"/etc/vservers",
}

DEBUG=False
VERBOSE=True
def usage():
    return """
    slicepkg implements the commands for creating, signing,
    verifying and unpacking slice packages.

    Signing packages requires private keys. 
    Verifying requires the public key.

    COMMANDS: 

        init
            creates expected directories and performs some basic setup

        getconfig <kind>
            return configuration directory names: rawdir, signdir, keydir, basedir
 
    FOR MLC SERVER:

        createkeys
            generate a pub/priv key pair for signing and verifying

        create <slicename> <dir>
            creates a slice package.

        sign <filename>
            Signs a slice package and addes the signature to the package.

    FOR NODE ACTIONS:

        verifypackage <filename>
            verifies package signature.

        verifyinstall <dirname>
            verifies package signature.

        unpack [--slicebase] <filename> <dir>
            unpacks the package, changing permissions etc.

        is_unpacked <filename>
            checks for the <filename>.unpacked file and compares the checksum
            with the given filename's checksum.  If they match return 0,
            otherse 1.

        register <slicename> <hostname>
            registers slicename from host

        unregister <slicename> <hostname>
            unregisters slicename from host

    FOR SLICE ACTIONS:
        
        initialize <slicename>
            after 'unpack' the package content into a slice filesytem,
            'initialize' executes the 'initialize' script inside the VM.

        is_initialized <filename>
            checks for the <filename>.initialized file and returns 0 if
            present, otherwise 1.


    """

def parse_args():
    from optparse import OptionParser
    parser = OptionParser(usage=usage())
    parser.add_option("-v", "--verbose", dest="verbose", 
                       default=False, 
                       action="store_true", 
                       help="Verbose mode: print extra details.")
    parser.add_option("", "--user", dest="userauth", 
                       default="username:password",
                       metavar="username:password",
                       help="The username and password to log into nagios.")
    parser.add_option("", "--public", dest="publickey", 
                       default="public.key",
                       metavar="public.key",
                       help="The public key used for signing")
    parser.add_option("", "--private", dest="privatekey", 
                       default="private.key",
                       metavar="private.key",
                       help="The private key used for signing")
    parser.add_option("-n", "--dryrun", dest="dryrun",  action="store_true",
                       default=False,
                       help="Print shell commands as they are executed.")
    parser.add_option("", "--slicebase", dest="slicebase",  action="store_true",
                       default=False,
                       help="For 'unpack' command when unpacking slicebase.")

    (options, args) = parser.parse_args()

    return (options, args, parser)

def system(cmd):
    ## NOTE: use this rather than os.system() to catch KeyboardInterrupts correctly.
    if VERBOSE: print "+", cmd
    if DEBUG: return 0
    ret = subprocess.call(cmd, stdout=sys.stdout, 
                           stderr=sys.stderr, shell=True,
                           executable='/bin/bash')
    if ret != 0:
        print "Exception:  %s\nExitStatus: %s" % (cmd, ret)
        sys.exit(ret)
    return ret

import hashlib
def checksum(filename):
    d = hashlib.sha256()
    with open(filename,'rb') as f: 
        for chunk in iter(lambda: f.read(8192), b''): 
            d.update(chunk)
    return d.hexdigest()

def visit_and_check(prefix_path):
    global total_size
    global total_count

    for (path, dirnames, filenames) in os.walk(prefix_path):
        short_path = path.replace("/dist", "")
        for filename in filenames:
            dist_file = os.path.join(path, filename)
            other_file = os.path.join(short_path, filename)
            #if VERBOSE:
            #    print checksum(dist_file) == checksum(other_file)
            #    print checksum(other_file), other_file
            #    print checksum(dist_file), dist_file
            if not checksum(dist_file) == checksum(other_file):
                return False
    return True

import urllib
import urllib2

def register_slice_on_hostname(options, slicename, hostname, register="1"):
    URL      = "http://nagios.measurementlab.net/register"
    Realm    = 'M-Lab'
    (Username, Password) = options.userauth.split(":")

    authhandler = urllib2.HTTPDigestAuthHandler()
    authhandler.add_password(Realm, URL, Username, Password)
    opener = urllib2.build_opener(authhandler)
    query_args = { 'slicename' : slicename,
                   'hostname'  : hostname,
                   'register'  : register}
    encoded_args = urllib.urlencode(query_args)
    urllib2.install_opener(opener)
    print urllib2.urlopen(URL, encoded_args).read(),

def main():
    global DEBUG
    global VERBOSE
    (options, args, parser) = parse_args()
    VERBOSE = options.verbose
    DEBUG = options.dryrun

    if len(args) == 0: 
        parser.print_help()
        sys.exit(1)
        
    if len(args) > 0:
        command = args[0]
        filename=None
        if len(args) > 1:
            filename = args[1]
    
    if command == "getconfig":
        print PACKAGEDIRS[args[1]]

    elif command == "init":
        for dirname in PACKAGEDIRS.keys():
            system("mkdir -p %s" % PACKAGEDIRS[dirname])
        system("slicepkg.py createkeys")
        
    elif command == "createkeys":
        keydir = PACKAGEDIRS['keydir']
        system("openssl genrsa -out %s/private.pem 4096" % keydir)
        system(("openssl rsa    -out %s/public.pem -pubout "+
                "-in %s/private.pem" % (keydir, keydir)))

    elif command == "create":
        (slicename, slicedir) = args[1:]
        system("tar -C %s -cvf %s.tar ." % (slicedir, slicename))

    elif command == "signpackage":
        system(("openssl dgst -sha256 -sign %s/private.pem "+
                " -out '%s.sig' '%s'") % (PACKAGEDIRS['keydir'], 
                                         filename, filename))
        system("cp '%s' '%s/%s'" % (filename, PACKAGEDIRS['signdir'], os.path.basename(filename)))
        system("tar -rf '%s/%s' -C '%s' '%s.sig'" % (PACKAGEDIRS['signdir'], 
                                             os.path.basename(filename), 
                                             os.path.dirname(filename),
                                             os.path.basename(filename)))
        system("rm -f '%s.sig'" % filename)

    elif command == "verifypackage":
        system("cp %s /tmp/tmp.tar" % filename)
        system("tar -xf /tmp/tmp.tar '%s.sig'" % os.path.basename(filename))
        system("tar --delete -f /tmp/tmp.tar '%s.sig'" % os.path.basename(filename))
        system(("openssl dgst -sha256 -verify %s/public.pem "+
                " -signature '%s.sig' '/tmp/tmp.tar'") %
                (PACKAGEDIRS['keydir'], os.path.basename(filename)))
        system("rm -f '%s.sig'" % os.path.basename(filename))

    elif command == "unpack":
        (filename, slicename) = args[1:]
        if options.slicebase:
            slicedir = "%s/%s/etc/mlab" % (PACKAGEDIRS['vserverdir'], slicename)
        else:
            slicedir = "%s/%s/home/%s" % (PACKAGEDIRS['vserverdir'], slicename, slicename)
        system("mkdir -p %s/dist" % slicedir)
        system("tar --exclude '%s.sig' -C %s/dist -xf '%s'" % (os.path.basename(filename), 
                                                               slicedir, filename))
        system("chmod -R a-w %s/dist" % slicedir)
        system("tar --exclude '%s.sig' -C %s -xf '%s'" % (os.path.basename(filename), 
                                                          slicedir, filename))
        system("chown -R %s.slices %s" % (slicename, slicedir))
        #system("chmod u+w %s" % slicedir)
        if not options.slicebase:
            unpacked_file = "%s/%s.unpacked" % (PACKAGEDIRS['vserverdir'], os.path.basename(filename))
            with open(unpacked_file, 'w') as f:
                f.write(checksum(filename))

    elif command == "is_unpacked":
        found_checksum = ""
        if not os.path.exists("%s/%s.unpacked" % (PACKAGEDIRS['vserverdir'], os.path.basename(filename))):
            sys.exit(1)

        with open("%s/%s.unpacked" % (PACKAGEDIRS['vserverdir'], os.path.basename(filename)), 'r') as f:
            found_checksum = f.read()

        new_checksum = checksum(filename)
        if found_checksum != new_checksum:
            print "unpackaged checksum does not match current package"
            print found_checksum, new_checksum
            sys.exit(1)
        print "checksum:", new_checksum

    elif command == "checksum":
        for f in args[1:]:
            print checksum(f), f

    elif command == "verifyinstall":
        slicename = filename
        slicedir = "%s/%s/home/%s" % (PACKAGEDIRS['vserverdir'], slicename, slicename)
        #system("chmod u+w %s" % slicedir)
        dist_path = os.path.normpath(slicedir+"/dist")
        if not visit_and_check(dist_path):
            print "Verify Install: FAILED"
            sys.exit(1)
        print "Verify Install: PASSED"

    elif command == "initialize":
        slicename = args[1]
        if os.path.exists("/proc/virtual/status"):
            # vserver 
            system("vserver %s exec /etc/init.d/slicectrl initialize" % slicename)
        elif os.path.exists("/proc/lxcsu"):
            # lxc
            pass
        else:
            # neither, testing environment.
            ## todo: find a suitable local test command
            #system("cd slices/%s; init/initialize" % slicename )
            pass
        filename = "%s/%s.initialized" % (PACKAGEDIRS['vserverdir'], 
                                          os.path.basename(filename))
        # touch file
        # todo: only create on successful return status.
        open(filename, 'a').close()

    elif command == "is_initialized":
        filename = "%s/%s.initialized" % (PACKAGEDIRS['vserverdir'], 
                                          os.path.basename(filename))
        if not os.path.exists(filename):
            sys.exit(1)

    elif command == "unregister":
        (slicename, hostname) = args[1:]
        register_slice_on_hostname(options, slicename, hostname, "0")

    elif command == "register":
        (slicename, hostname) = args[1:]
        register_slice_on_hostname(options, slicename, hostname, "1")

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        sys.exit(1)
    except:
        import traceback
        traceback.print_exc()
        sys.exit(1)
