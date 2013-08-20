server-support
==============

Support scripts for M-Lab servers, either on nodes or as part of the central
infrastructure support.

nodebase - Contents of an RPM package installed in the root context of node.
           This package is auto-updated by 'NodeUpdate', part of the PlanetLab
           software stack. 

central - Central server scripts and setup support. 

build - The output of Makefiles.  The structure is setup to be a yum repositoriy.  
        rsync the build directory to the destination, and running createrepo should be enough.
        rsync -ar build/* root@boot.measurementlab.net:/var/www/html/mlab-rpms/

