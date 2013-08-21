#
# $Id:$
#
%define url $URL:$

%define name nodebase
%define version 0.3
%define taglevel 9

# Turn off the brp-python-bytecompile script
# NOTE: at run-time this directive rewrites the __os_install_post 
#       macro from /usr/lib/rpm/redhat/macros by stripping the python bytecompile
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')


Vendor: Measurement Lab
Packager: Measurement Lab <support@measurementlab.net>
Distribution: PlanetLab %{plrelease}
URL: %(echo %{url} | cut -d ' ' -f 2)

Summary: Tools for use within a root context of an M-Lab server to install slice packages.
Name: %{name}
Version: %{version}
Release: %{taglevel}

# this is for centos6 only, package names change for future distros.
Requires: cronie
Requires: crontabs
Requires: openssl
Requires: nrpe 
Requires: nagios-plugins-nrpe 
Requires: nagios-plugins-disk
Requires: nagios-plugins-ping
Requires: net-snmp
#Requires: openvpn
#Requires: salt-minion
Requires: yum-cron

License: Apache License
Group: System Environment/Base
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch

Source0: %{name}-%{version}.tar.bz2

%description

The nodebase package provides cron scripts, a command line tool, and vserver post
scripts that all work collectively to automate the installation of slice
packages in slice filesystems. 

%prep
%setup

%build

%install
mkdir -p $RPM_BUILD_ROOT/opt/slice/

# VSYS support scripts
install -D -m 0755 vsys/slice_yum         $RPM_BUILD_ROOT/vsys/slice_yum
install -D -m 0755 vsys/slice_update      $RPM_BUILD_ROOT/vsys/slice_update
install -D -m 0755 vsys/slice_restart     $RPM_BUILD_ROOT/vsys/slice_restart
install -D -m 0755 vsys/web100_proc_write $RPM_BUILD_ROOT/vsys/web100_proc_write

# Nagios check and repair commands
install -D -m 0755 nagios/check_node.py        $RPM_BUILD_ROOT/usr/lib/nagios/plugins/check_node.py
install -D -m 0755 nagios/check_packet_sock.sh $RPM_BUILD_ROOT/usr/lib/nagios/plugins/check_packet_sock.sh
install -D -m 0755 nagios/check_readonly.py    $RPM_BUILD_ROOT/usr/lib/nagios/plugins/check_readonly.py
install -D -m 0755 nagios/check_vdlimit.sh     $RPM_BUILD_ROOT/usr/lib/nagios/plugins/check_vdlimit.sh
install -D -m 0755 nagios/repair_node_session.py $RPM_BUILD_ROOT/usr/lib/nagios/plugins/repair_node_session.py
install -D -m 0755 nagios/repair_service.sh    $RPM_BUILD_ROOT/usr/lib/nagios/plugins/repair_service.sh
install -D -m 0755 nagios/repair_vdlimit.py    $RPM_BUILD_ROOT/usr/lib/nagios/plugins/repair_vdlimit.sh

#'dest': u'/root/oombailout-0.1-0.planetlab.2009.03.03.i386.rpm',
#install -D -m 0755 slicepkg.cron  	$RPM_BUILD_ROOT/etc/cron.hourly/slicepkg.cron

install -D -m 0755 support/slicepkg.py    	  $RPM_BUILD_ROOT/usr/bin/slicepkg.py
install -D -m 0755 support/setup_ethtool      $RPM_BUILD_ROOT/usr/sbin/setup_ethtool
install -D -m 0755 support/setup-openvpn-client.sh $RPM_BUILD_ROOT/usr/sbin/setup-openvpn-client.sh
install -D -m 0755 support/xidmask-post-start $RPM_BUILD_ROOT/etc/vservers/.defaults/scripts/post-start
install -D -m 0755 support/delete_logs_safely.py $RPM_BUILD_ROOT/etc/cron.daily/delete_logs_safely.py
install -D -m 0755 support/slice_data_backup.py $RPM_BUILD_ROOT/usr/sbin/slice_data_backup.py

# Supplemental configuration
install -D -m 0644 config/vprocunhide.web100 $RPM_BUILD_ROOT/etc/vservers/.defaults/apps/vprocunhide/files

install -D -m 0644 config/nrpe.cfg           $RPM_BUILD_ROOT/etc/mlab/config/nagios/nrpe.cfg
install -D -m 0644 config/snmpd.conf         $RPM_BUILD_ROOT/etc/mlab/config/snmp/snmpd.conf
install -D -m 0644 config/nodebase.repo      $RPM_BUILD_ROOT/etc/mlab/config/yum.myplc.d/node.repo
install -D -m 0755 config/rc.local           $RPM_BUILD_ROOT/etc/mlab/config/rc.d/rc.local
mkdir -p $RPM_BUILD_ROOT/etc/mlab/config.backup

# NOTE: managed by PLC conffiles to overwrite the PLC defaults.
# NOTE: after migrating to MLC, we should pull these files back into this rpm.
# NOTE: see: server-config/central/boot/PlanetLabConf/mlab-centos6/
#install -D -m 0644 config/sshd_config        $RPM_BUILD_ROOT/etc/mlab/config/ssh/sshd_config
#install -D -m 0644 config/sysctl.conf        $RPM_BUILD_ROOT/etc/mlab/config/sysctl.conf
#install -D -m 0644 config/iptables           $RPM_BUILD_ROOT/etc/mlab/config/sysconfig/iptables
#install -D -m 0644 config/sudoers            $RPM_BUILD_ROOT/etc/mlab/config/sudoers

# oombailout -- looks for lowmem in kernel and flushes some caches proactively
#               to prevent OOM crashes.
install -D -m 755 oombailout/oombailout.py          $RPM_BUILD_ROOT/usr/bin/oombailout.py
install -D -m 755 oombailout/oombailout-initscript  $RPM_BUILD_ROOT/%{_sysconfdir}/init.d/oombailout
install -D -m 644 oombailout/oombailout.logrotate   $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/oombailout

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)

%attr(0755,root,root) /usr/bin/slicepkg.py
%attr(0755,root,root) /vsys/slice_yum
%attr(0755,root,root) /vsys/slice_update
%attr(0755,root,root) /vsys/slice_restart
%attr(0755,root,root) /vsys/web100_proc_write
%attr(0755,root,root) /usr/sbin/setup_ethtool
%attr(0755,root,root) /usr/sbin/setup-openvpn-client.sh

# NAGIOS
%attr(0755,root,root) /usr/lib/nagios/plugins/check_node.py
%attr(0755,root,root) /usr/lib/nagios/plugins/check_packet_sock.sh
%attr(0755,root,root) /usr/lib/nagios/plugins/check_readonly.py
%attr(0755,root,root) /usr/lib/nagios/plugins/check_vdlimit.sh
%attr(0755,root,root) /usr/lib/nagios/plugins/repair_node_session.py
%attr(0755,root,root) /usr/lib/nagios/plugins/repair_service.sh
%attr(0755,root,root) /usr/lib/nagios/plugins/repair_vdlimit.sh

# LOGS 
%attr(0755,root,root) /etc/cron.daily/delete_logs_safely.py
%attr(0755,root,root) /usr/sbin/slice_data_backup.py

# UNHIDE /proc/web100
%attr(0644,root,root) /etc/vservers/.defaults/apps/vprocunhide/files
# SET XIDMASK 
%attr(0755,root,root) /etc/vservers/.defaults/scripts/post-start

# CONFIG (all files under this directory)
/etc/mlab/config/
/etc/mlab/config.backup/

# oombailout
/usr/bin/oombailout.py
%{_sysconfdir}/init.d/oombailout
%{_sysconfdir}/logrotate.d/oombailout

%pre

%post

# NOTE: these files are handled by conffiles() to override defaults for PlanetLab.
#       sysctl.conf 
#       sysconfig/iptables 
#       sudoers 
#       ssh/sshd_config 
# TODO: after migration to MLC, those files should be pulled back into this rpm.
echo "Installing config files:"
for file in yum.myplc.d/node.repo nagios/nrpe.cfg \
            snmp/snmpd.conf rc.d/rc.local ; do 
    echo -e "\t$file"
    test -f /etc/$file && cp /etc/$file /etc/mlab/config.backup/
    install -D /etc/mlab/config/$file /etc/$file
done

# install in /etc/rc.d/ (important) /etc/rc.local is a symlink.
#install -D -m 0755 /etc/mlab/config/rc.local /etc/rc.d/rc.local

# NOTE: BEWARE. virtual interfaces are deprecated, but PL still using them.
#       This patch prevents ipv6 shutdown on physical interface when running 
#       'ifdown' on a virtual interface
sed -i '/^REALDEVICE=*/ s/^/#/' /etc/sysconfig/network-scripts/ifdown-ipv6 || :
sed -i '/^DEVICE=*/ s/^/#/'     /etc/sysconfig/network-scripts/ifdown-ipv6 || :

# NOTE: The mlab node images don't include 'planetlab' or 'f8' reference images.
#       By creating links, the create scripts will use the available versions.
ln -s /vservers/.vref/mlab-centos6-i386 /vservers/.vref/planetflow-f8-i386
ln -s /vservers/.vref/mlab-centos6-i386 /vservers/.vref/planetlab-f8-i386
if ! test -d  /vservers/.backup/ ; then
    mkdir -p /vservers/.backup/
fi

chkconfig --level 2345 nrpe on
chkconfig --level 345  snmpd  on
chkconfig --level 345  monitor-runlevelagent on
chkconfig --level 345  snmptrapd  off
chkconfig --level 345  yum-cron on
chkconfig --level 345 oombailout on
chkconfig rpcbind off
chkconfig nfslock off

#chkconfig --levels 345 salt-minion on

if [ "$PL_BOOTCD" != "1" ] ; then
    service oombailout restart
    service monitor-runlevelagent restart
fi

# NOTE: handled by conffiles() for now. 
# load sysctl values
#/sbin/sysctl -p /etc/sysctl.conf

# TODO: make this more robust
#/usr/sbin/setup-openvpn-client.sh

# NOTE: these services should NOT be started here
#service nrpe start
#service snmpd start
#service snmptrapd stop
#service yum-cron start
#service salt-minion start

%preun

%postun

%changelog
* Wed May 09 2013 Stephen Soltesz <soltesz@opentechinstitute.org> nodebase-0.3-7
- update check_node.py to include many more checks (ports, web100_enable, etc)
