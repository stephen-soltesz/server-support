#!/usr/bin/python
# For some PL workloads (read attacks) the cache-reclaiming policy of Linux is not
# aggressive enough to avert OOMs when low-memory is running out. Examples of this
# were seen on MLAB when TCP flooding attacks would lead to a sudden burst in kernel-memory 
# utilization.
#
# This script is for scenarios of that type. We monitor our memory reserves and empty all
# caches if we find that they are critically low.

import os
import sys
import time
import re

UMASK = 0
WORKDIR = "/"
MAXFD = 1024
if (hasattr(os, "devnull")):
   REDIRECT_TO = os.devnull
else:
   REDIRECT_TO = "/dev/null"
# NOTE: early versions of M-Lab used 200000, 
#       later versions 400000
lmthreshold = 400000

def createDaemon():
   try:
      pid = os.fork()
   except OSError, e:
      raise Exception, "%s [%d]" % (e.strerror, e.errno)

   if (pid == 0):   # The first child.
      os.setsid()
      try:
         pid = os.fork()    # Fork a second child.
      except OSError, e:
         raise Exception, "%s [%d]" % (e.strerror, e.errno)
      if (pid == 0):    # The second child.
         os.chdir(WORKDIR)
         os.umask(UMASK)
      else:
         os._exit(0)    # Exit parent (the first child) of the second child.
   else:
      os._exit(0)   # Exit parent of the first child.

   # Iterate through and close all file descriptors.
   for fd in range(0, MAXFD):
      try:
         os.close(fd)
      except OSError:   # ERROR, fd wasn't open to begin with (ignored)
         pass

   os.open(REDIRECT_TO, os.O_RDWR)  # standard input (0)
   os.dup2(0, 1)            # standard output (1)
   os.dup2(0, 2)            # standard error (2)

   return(0)


def get_free_lowmem():
    meminfo=open('/proc/meminfo').read();
    m=re.search(r'LowFree:\s+(\d+)\s+kB',meminfo);
    lowfree=int(m.group(1))
    return lowfree

retCode = createDaemon()

while (1):
    lowfree1 = get_free_lowmem()

    if (lowfree1<200000):
        os.system('echo 3 > /proc/sys/vm/drop_caches')
        lowfree2 = get_free_lowmem()
            
        open("/var/log/oombailout.log", "a").write("OOMBailout: Freed up %d kB of low memory\n"%(lowfree2-lowfree1))
        
    time.sleep(60)


