server-support
==============

Support scripts for M-Lab servers, either on nodes or as part of the central
infrastructure support.

nodebase - 

Contents of an RPM package installed in the root context of nodes.
The resulting rpm should be installed on the boot server's NodeGroup 
yum repo.  For M-lab this is:

    https://boot.planet-lab.org/install-rpms/MeasurementLabCentos/

This package is auto-updated by 'NodeUpdate', a part of the PlanetLab
software stack. 

central -

Central server scripts and setup support. 

build - 

The output of Makefiles.  The structure is setup to be a yum repositoriy.  
rsync the build directory to the destination, and running createrepo or 
package signing scripts should be enough.

