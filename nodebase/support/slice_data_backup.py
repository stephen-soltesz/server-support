#!/usr/bin/python
"""
slice_data_backup performs two simple operations.

backup:

    During slice package updates, it's preferable to re-install the slice
rather than update it in place.  To prevent data loss or long-waits for the
collection pipeline to pull current data (and prevent new data from being
collected), this script performs a fast backup of known data locations within
slices.

    After backup, the slice may be deleted safely, since no sensitive
information remains.

restore:
    
    After the slice is created again, the directories that contain preserved
data can be returned to their original locations, and the slice can continue
normal operation.

"""

import os
import sys
import time
from syslog import syslog


DEBUG=True
command = sys.argv[1]
slicename = sys.argv[2]
backupdir = "/vservers/.backup/"
vserversdir = "/vservers/"

slicename_to_rsyncpath = {
    'gt_partha'   : ['/home/gt_partha/shaperprobe/dropbox'],
    'iupui_ndt'     : ['/usr/local/ndt/serverdata'],
    'iupui_npad'      : ['/home/iupui_npad/VAR/www/NPAD.v1', 
                         'home/iupui_npad/VAR/www/SideStream'],
    'mlab_neubot'       : ['/var/lib/neubot'],
    'mpisws_broadband'     : ['/home/mpisws_broadband/glasnost', 
                              '/home/mpisws_broadband/logs'],
}

def log(msg):
    if DEBUG: print msg
    syslog("SDB: " + msg)

def get_paths_for_slice(slicename):
    """ get_paths_for_slice -- returns a list of all possible paths that a 
        slice is known to save logs.
        Args: 
            slicename, name of slice
        Returns: 
            list of paths, relative to VM root, of data logging dirs
    """
    ret_list = []
    if slicename in slicename_to_rsyncpath:
        ret_list += slicename_to_rsyncpath[slicename]
    ret_list += [ '/var/spool/'+slicename ]
    return ret_list 

def handle_backup(slicename):

    if not os.path.exists(backupdir):
        # NOTE: make the backupdir if it does not yet exist
        log("makedirs: %s"%backupdir)
        os.makedirs(backupdir)

    path_list = get_paths_for_slice(slicename)

    for vm_path in path_list:
        # NOTE: expects the basename of every dir to be different
        slicedir = vserversdir+slicename+vm_path
        basename = os.path.basename(slicedir)
        slicebackup = backupdir+basename

        if not os.path.exists(slicedir):
            # NOTE: source directory does not exist, so we cannot back it up
            log("slicedir: %s does not exist; continuing" % slicedir )
            continue

        if os.path.exists(slicebackup):
            # NOTE: this is a problem
            log("slicebackup: destination directory already exists!")
            log("slicebackup: should have been removed by restore")
            log("slicebackup: backing up backup")
            cmd = "mv %s %s.extra-backup.%s" % (slicebackup, slicebackup, 
                                                time.time())
            log(cmd)
            os.system(cmd)

        # NOTE: at this point we know slicedir exists, and slicebackup doesn't.
        # NOTE: So, move slice data dir to slice backup dir
        cmd = "mv %s %s" % (slicedir, slicebackup)
        log(cmd)
        os.system(cmd)

def handle_restore(slicename):

    if not os.path.exists(backupdir):
        log("Error: %s does not exist, no backups possible" % backupdir)
        sys.exit(1)

    path_list = get_paths_for_slice(slicename)
    for vm_path in path_list:
        # NOTE: expects the basename of every dir to be different
        slicedir = vserversdir+slicename+vm_path
        basename = os.path.basename(slicedir)
        slicebackup = backupdir+basename

        if not os.path.exists(slicebackup):
            # NOTE: there is no directory in backup to restore, no big deal
            log("slicebackup: %s does not exist; continuing" % slicebackup)
            continue

        # NOTE: make sure slicedir (the target of restore) is empty if present
        if os.path.exists(slicedir):
            if len(os.listdir(slicedir))==0:
                # NOTE: it's empty so remove it first
                log("slicedir: removing empty dir %s" % slicedir)
                os.rmdir(slicedir)
            else:
                log("Error: destination directory is empty")
                log("Error: %s" % slicedir)
                sys.exit(1)
        else:
            # NOTE: if slicedir does not exist, no problem, 
            # NOTE: we're about to create it.
            pass

        dirname = os.path.dirname(slicedir)
        if not os.path.exists(dirname):
            # NOTE: the full path of slicedir may not exist yet in a new 
            log("making dirname: %s" % dirname)
            os.makedirs(dirname)

        # NOTE: at this point we know slicebackup exists, and slicedir does not.
        # NOTE: So, move slice backup directory to data directory
        log("mv %s  %s"% (slicebackup, slicedir))
        os.system("mv %s  %s"% (slicebackup, slicedir) )

def main():
    if len(sys.argv) != 3:
        print "usage: %s <backup|restore> <slicename>" % sys.argv[0]
        sys.exit(1)

    if command == "backup":
        handle_backup(slicename)
    elif command == "restore":
        handle_restore(slicename)
    else:
        print "Error: unknown command: %s" % command
        sys.exit(1)

if __name__ == "__main__":
    main()
