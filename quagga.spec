%define quagga_uid  92
%define quagga_gid  92
%define vty_group   quaggavt
%define vty_gid     85

%global _hardened_build 1

Name: quagga
Version: 0.99.22.4
Release: 4%{?dist}
Summary: Routing daemon
License: GPLv2+
Group: System Environment/Daemons
URL: http://www.quagga.net
Source0: http://download.savannah.gnu.org/releases/quagga/%{name}-%{version}.tar.xz
Source1: quagga-filter-perl-requires.sh
Source2: quagga-tmpfs.conf
BuildRequires: systemd
BuildRequires: net-snmp-devel
BuildRequires: texinfo libcap-devel texi2html
BuildRequires: readline readline-devel ncurses ncurses-devel
Requires: net-snmp ncurses
Requires(post): systemd /sbin/install-info
Requires(preun): systemd /sbin/install-info
Requires(postun): systemd
Provides: routingdaemon = %{version}-%{release}
Obsoletes: quagga-sysvinit

Patch0: 0001-systemd-change-the-WantedBy-target.patch

%define __perl_requires %{SOURCE1}

%description
Quagga is free software that operates TCP/IP-based routing protocols. It takes
a multi-server and multi-threaded approach to resolving the current complexity
of the Internet.

Quagga supports Babel, BGP4, BGP4+, BGP4-, IS-IS (experimental), OSPFv2,
OSPFv3, RIPv1, RIPv2, and RIPng.

Quagga is intended to be used as a Route Server and a Route Reflector. It is
not a toolkit; it provides full routing power under a new architecture.
Quagga by design has a process for each protocol.

Quagga is a fork of GNU Zebra.

%package contrib
Summary: Contrib tools for quagga
Group: System Environment/Daemons

%description contrib
Contributed/3rd party tools which may be of use with quagga.

%package devel
Summary: Header and object files for quagga development
Group: System Environment/Daemons
Requires: %{name} = %{version}-%{release}

%description devel
The quagga-devel package contains the header and object files necessary for
developing OSPF-API and quagga applications.

%prep
%setup -q

%patch0 -p1

%build
%configure \
    --sysconfdir=%{_sysconfdir}/quagga \
    --libdir=%{_libdir}/quagga \
    --libexecdir=%{_libexecdir}/quagga \
    --localstatedir=%{_localstatedir}/run/quagga \
    --enable-ipv6=yes \
    --enable-isisd=yes \
    --enable-snmp=agentx \
    --enable-multipath=64 \
    --enable-opaque-lsa \
    --enable-ospf-te \
    --enable-vtysh=yes \
    --enable-ospfclient=no \
    --enable-ospfapi=no \
    --enable-user=quagga \
    --enable-group=quagga \
    --enable-vty-group=%vty_group \
    --enable-rtadv \
    --disable-exampledir \
    --enable-netlink

make %{?_smp_mflags} MAKEINFO="makeinfo --no-split" CFLAGS="%{optflags} -fno-strict-aliasing"

pushd doc
texi2html quagga.texi
popd

%install
mkdir -p %{buildroot}/etc/{quagga,rc.d/init.d,sysconfig,logrotate.d} \
         %{buildroot}/var/log/quagga %{buildroot}%{_infodir} \
         %{buildroot}%{_unitdir}

make DESTDIR=%{buildroot} INSTALL="install -p" CP="cp -p" install

# Remove this file, as it is uninstalled and causes errors when building on RH9
rm -rf %{buildroot}/usr/share/info/dir

install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/zebra.service %{buildroot}%{_unitdir}/zebra.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/isisd.service %{buildroot}%{_unitdir}/isisd.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/ripd.service %{buildroot}%{_unitdir}/ripd.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/ospfd.service %{buildroot}%{_unitdir}/ospfd.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/bgpd.service %{buildroot}%{_unitdir}/bgpd.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/babeld.service %{buildroot}%{_unitdir}/babeld.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/ospf6d.service %{buildroot}%{_unitdir}/ospf6d.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/ripngd.service %{buildroot}%{_unitdir}/ripngd.service

install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/quagga.sysconfig %{buildroot}/etc/sysconfig/quagga
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/quagga.logrotate %{buildroot}/etc/logrotate.d/quagga

install -d -m 770  %{buildroot}/var/run/quagga

install -d -m 755 %{buildroot}/%{_tmpfilesdir}
install -p -m 644 %{SOURCE2} %{buildroot}/%{_tmpfilesdir}/quagga.conf

rm %{buildroot}%{_libdir}/quagga/*.a
rm %{buildroot}%{_libdir}/quagga/*.la

%pre
getent group %vty_group >/dev/null 2>&1 || groupadd -r -g %vty_gid %vty_group >/dev/null 2>&1 || :
getent group quagga >/dev/null 2>&1 || groupadd -g %quagga_gid quagga >/dev/null 2>&1 || :
getent passwd quagga >/dev/null 2>&1 || useradd -u %quagga_uid -g %quagga_gid -M -r -s /sbin/nologin \
 -c "Quagga routing suite" -d %{_localstatedir}/run/quagga quagga >/dev/null 2>&1 || :

%post
%systemd_post zebra.service
%systemd_post isisd.service
%systemd_post ripd.service
%systemd_post ospfd.service
%systemd_post bgpd.service
%systemd_post babeld.service
%systemd_post ospf6d.service
%systemd_post ripngd.service

if [ -f %{_infodir}/%{name}.inf* ]; then
    install-info %{_infodir}/quagga.info %{_infodir}/dir || :
fi

# Create dummy files if they don't exist so basic functions can be used.
if [ ! -e %{_sysconfdir}/quagga/zebra.conf ]; then
    echo "hostname `hostname`" > %{_sysconfdir}/quagga/zebra.conf
    chown quagga:quagga %{_sysconfdir}/quagga/zebra.conf
    chmod 640 %{_sysconfdir}/quagga/zebra.conf
fi

if [ ! -e %{_sysconfdir}/quagga/vtysh.conf ]; then
    touch %{_sysconfdir}/quagga/vtysh.conf
    chmod 640 %{_sysconfdir}/quagga/vtysh.conf
    chown quagga:%{vty_group} %{_sysconfdir}/quagga/vtysh.conf
fi

%postun
%systemd_postun_with_restart zebra.service
%systemd_postun_with_restart isisd.service
%systemd_postun_with_restart ripd.service
%systemd_postun_with_restart ospfd.service
%systemd_postun_with_restart bgpd.service
%systemd_postun_with_restart babeld.service
%systemd_postun_with_restart ospf6d.service
%systemd_postun_with_restart ripngd.service

if [ -f %{_infodir}/%{name}.inf* ]; then
    install-info --delete %{_infodir}/quagga.info %{_infodir}/dir || :
fi

%preun
%systemd_preun zebra.service
%systemd_preun isisd.service
%systemd_preun ripd.service
%systemd_preun ospfd.service
%systemd_preun bgpd.service
%systemd_preun babeld.service
%systemd_preun ospf6d.service
%systemd_preun ripngd.service

%files
%defattr(-,root,root)
%doc AUTHORS COPYING
%doc zebra/zebra.conf.sample
%doc isisd/isisd.conf.sample
%doc ripd/ripd.conf.sample
%doc bgpd/bgpd.conf.sample*
%doc ospfd/ospfd.conf.sample
%doc babeld/babeld.conf.sample
%doc ospf6d/ospf6d.conf.sample
%doc ripngd/ripngd.conf.sample
%doc doc/quagga.html
%doc doc/mpls
%doc ChangeLog INSTALL NEWS README REPORTING-BUGS SERVICES TODO
%dir %attr(750,quagga,quagga) %{_sysconfdir}/quagga
%dir %attr(750,quagga,quagga) /var/log/quagga
%dir %attr(750,quagga,quagga) /var/run/quagga
%{_infodir}/*info*
%{_mandir}/man*/*
%exclude %{_mandir}/man*/watchquagga.*
%{_sbindir}/*
%exclude %{_sbindir}/watchquagga
%{_bindir}/*
%dir %{_libdir}/quagga
%{_libdir}/quagga/*.so.*
%config(noreplace) %attr(640,root,root) /etc/logrotate.d/quagga
%config(noreplace) /etc/sysconfig/quagga
%{_tmpfilesdir}/quagga.conf
%{_unitdir}/*.service

%files contrib
%defattr(-,root,root)
%doc AUTHORS COPYING %attr(0644,root,root) tools

%files devel
%defattr(-,root,root)
%doc AUTHORS COPYING
%dir %{_libdir}/quagga/
%{_libdir}/quagga/*.so
%dir %{_includedir}/quagga
%{_includedir}/quagga/*.h
%dir %{_includedir}/quagga/ospfd
%{_includedir}/quagga/ospfd/*.h

%changelog
* Thu Feb 13 2014 Michal Sekletar <msekleta@redhat.com> - 0.99.22.4-4
- fix link to upstream tarball (#1059219)
- reference pidfiles of quagga daemons in service files (#842309)

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 0.99.22.4-3
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 0.99.22.4-2
- Mass rebuild 2013-12-27

* Fri Sep 13 2013 Michal Sekletar <msekleta@redhat.com> - 0.99.22.4-1
- update to 0.99.22.4

* Sat Aug 03 2013 Petr Pisar <ppisar@redhat.com> - 0.99.22.3-2
- Perl 5.18 rebuild

* Tue Jul 30 2013 Michal Sekletar <msekleta@redhat.com> - 0.99.22.3-1
- update to 0.99.22.3
- disable ospfapi and ospfclient
- fix bogus dates in changelog
- resolves : #984532

* Fri Jul 12 2013 Jan Safranek <jsafrane@redhat.com> - 0.99.22.1-9
- Rebuilt for new net-snmp

* Thu Jul 11 2013 Than Ngo <than@redhat.com> - 0.99.22.1-8
- drop unused BR in tetex

* Fri Jun 21 2013 Michal Sekletar <msekleta@redhat.com> - 0.99.22.1-7
- quagga is service which might implement networking, thus it should not have
  WantedBy=network.target in its systemd configuration
- resolves: #976883

* Mon Jun 10 2013 Michal Sekletar <msekleta@redhat.com> - 0.99.22.1-6
- obsolete quagga-sysvinit subpackage
- use macro to specify location where to install tmpfiles configuration file
- fix rpm scripts handling documentation in info format

* Thu Jun 06 2013 Michal Sekletar <msekleta@redhat.com> - 0.99.22.1-5
- configure quagga using correct user

* Tue May 28 2013 Michal Sekletar <msekleta@redhat.com> - 0.99.22.1-4
- call chmod on correct path

* Mon May 27 2013 Michal Sekletar <msekleta@redhat.com> - 0.99.22.1-3
- build package with required compiler flags

* Fri May 17 2013 Michal Sekletar <msekleta@redhat.com> - 0.99.22.1-2
- claim ownership of libdir/quagga directory
- fix dependencies

* Fri Apr 19 2013 Michal Sekletar <msekleta@redhat.com> - 0.99.22.1-1
- update to 0.99.22.1
- install tmpfiles dropping configuration to proper location
- drop sysv subpackage and initscripts support

* Tue Mar 26 2013 Adam Tkac <atkac redhat com> - 0.99.22-2
- fix typo in ipv6.texi documentation

* Wed Feb 20 2013 Adam Tkac <atkac redhat com> - 0.99.22-1
- update to 0.99.22
- quagga-CVE-2012-1820.patch has been merged
- explicitly enable SMNP AgentX interface

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.99.21-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Fri Jul 27 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.99.21-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Jul 12 2012 Adam Tkac <atkac redhat com> 0.99.21-3
- build with -fno-strict-aliasing

* Thu Jun 07 2012 Adam Tkac <atkac redhat com> 0.99.21-2
- fix CVE-2012-1820

* Thu May 03 2012 Adam Tkac <atkac redhat com> 0.99.21
- update to 0.99.21
- various packaging fixes

* Thu Mar 15 2012 Jiri Skala <jskala@redhat.com> - 0.99.20.1-1
- updated to latest upstream version 0.99.20.1

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.99.20-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Nov 23 2011 Jiri Skala <jskala@redhat.com> - 0.99.20-4
- modified permissions of var dirs (fixes #755491)

* Wed Oct 26 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.99.20-3
- Rebuilt for glibc bug#747377

* Tue Oct 18 2011 Jiri Skala <jskala@redhat.com> - 0.99.20-2
- fixes #746886 - severe memory leak in quagga 0.99.{19,20}

* Fri Sep 30 2011 Jiri Skala <jskala@redhat.com> - 0.99.20-1
- updated to latest upstream version 0.99.20
- fixes #741343 - CVE-2011-3325 corrected fix

* Thu Sep 29 2011 Jiri Skala <jskala@redhat.com> - 0.99.19-1
- fixes #741343 - CVE-2011-3323 CVE-2011-3324 CVE-2011-3325 CVE-2011-3326 CVE-2011-3327
- fixes #741580 - updated to latest upstream version 0.99.19

* Thu Aug 18 2011 Jiri Skala <jskala@redhat.com> - 0.99.18-9
- rebuild for rpm

* Mon Aug 01 2011 Jiri Skala <jskala@redhat.com> - 0.99.18-8
- rebuild for libcap

* Tue Jul 19 2011 Jiri Skala <jskala@redhat.com> - 0.99.18-7
- fixes #716561 - isisd binary is not included in quagga

* Tue Jul 19 2011 Jiri Skala <jskala@redhat.com> - 0.99.18-6
- fixes #719610 - add unit files, SysV initscripts moved to subpackage

* Mon Jul 11 2011 Jiri Skala <jskala@redhat.com> - 0.99.18-5
- rebuild with new snmp

* Wed Jun 08 2011 Jiri Skala <jskala@redhat.com> - 0.99.18-4
- removed conflicts tag

* Thu Apr 28 2011 Jiri Skala <jskala@redhat.com> - 0.99.18-3
- fixes Requires /sbin/{chkconfig, install-info} (#226352 - Merge review)

* Thu Mar 31 2011 Jiri Skala <jskala@redhat.com> - 0.99.18-2
- rebuild to keep correct nvr rule F15 vers. F16

* Wed Mar 23 2011 Jiri Skala <jskala@redhat.com> - 0.99.18-1
- fixes #689852 - CVE-2010-1674 CVE-2010-1675 quagga various flaws
- fixes #690087 - ripd fails to start
- fixes #689763 - updated to latest upstream version 0.99.18

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.99.17-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Dec 08 2010 Jiri Skala <jskala@redhat.com> - 0.99.17-4
- #656681 - using tmpfiles.d

* Thu Dec 02 2010 Jiri Skala <jskala@redhat.com> - 0.99.17-3
- fixes #656681 - using %ghost on files in /var/run and /var/lock
- removed unused script from spec
- corrected installing /etc/pam.d

* Mon Nov 01 2010 Jiri Skala <jskala@redhat.com> - 0.99.17-2
- rebuild for net-snmp

* Tue Aug 31 2010 Jiri Skala <jskala@redhat.com> - 0.99.17-1
- update to latest upstream
- fixes #628981 - CVE-2010-2948 and CVE-2010-2949

* Tue Jul 20 2010 Jiri Skala <jskala@redhat.com> - 0.99.16-5
- fixes #525666 - Missing man-pages
- fixed and added initscript of watchquagga daemon

* Mon Jul 12 2010 Jiri Skala <jskala@redhat.com> - 0.99.16-4
- added license text to subpackages
- fixes #609931 - quagga : does not adhere to Static Library Packaging Guidelines

* Thu Jul 01 2010 Jiri Skala <jskala@redhat.com> - 0.99.16-3
- fixes #609616 - does not adhere to Static Library Packaging Guidelines

* Fri Jun 11 2010 Jiri Skala <jskala@redhat.com> - 0.99.16-2
- pam.d is disabled

* Wed Mar 17 2010 Jiri Skala <jskala@redhat.com> - 0.99.16-1
- latest upstream version
- merged initscript patches

* Tue Jan 26 2010 Jiri Skala <jskala@redhat.com> - 0.99.15-2
- changes in spec file and init scritps (#226352)

* Mon Oct 19 2009 Jiri Skala <jskala@redhat.com> - 0.99.15-1
- bump to latest upstream
- fixed #527734 - posix compliant init scripts

* Mon Sep 14 2009 Jiri Skala <jskala@redhat.com> - 0.99.12-3
- fixed #516005 - Errors installing quagga-0.99.11-2.fc11.i586 with --excludedocs
- fixed #522787 - quagga: build future versions without PAM

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0:0.99.12-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Jul 14 2009 Jiri Skala <jskala@redhat.com> - 0.99.12-2
- replaced Obsoletes by Conflicts

* Wed May 20 2009 Jiri Skala <jskala@redhat.com> - 0.99.12-1
- update to latest upstream version
- fix #499960 - BGPd in Quagga prior to 0.99.12 has a serious assert problem crashing with ASN4's

* Mon May 04 2009 Jiri Skala <jskala@redhat.com> - 0.99.11-3
- fix #498832 - bgpd crashes on as paths containing more 6 digit as numbers
- corrected release number

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0:0.99.11-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Jan 06 2009 Jiri Skala <jskala@redhat.com> - 0.99.11-1
- bump to latest upstream version 0.99.11

* Wed Sep  3 2008 Tom "spot" Callaway <tcallawa@redhat.com> - 0.99.10-2
- fix license tag

* Wed Jun 11 2008 Martin Nagy <mnagy@redhat.com> - 0.99.10-1
- upgrade to new upstream 0.99.10

* Wed Mar 05 2008 Martin Nagy <mnagy@redhat.com> - 0.99.9-6
- fix vtysh.conf owner and group (#416121)
- fix bpgd IPv6 advertisements, patch from upstream (#429448)

* Mon Feb 11 2008 Martin Nagy <mnagy@redhat.com> - 0.99.9-5
- rebuild for gcc-4.3

* Tue Jan 29 2008 Martin Nagy <mnagy@redhat.com> - 0.99.9-4
- check port number range when using -P or -p (#206071)

* Wed Jan 23 2008 Martin Nagy <mnagy@redhat.com> - 0.99.9-3
- rebuild

* Mon Nov 12 2007 Martin Bacovsky <mbacovsk@redhat.com> - 0.99.9-2
- resolves: #376821: ospfd init script looks for ospf6 configuration and lock file
- resolves: #376841: Usage string in ospf6d init script incorrect

* Mon Sep 17 2007 Martin Bacovsky <mbacovsk@redhat.com> - 0.99.9-1
- upgrade to new upstream 0.99.9
- Resolves: #292841: CVE-2007-4826 quagga bgpd DoS

* Fri Sep 14 2007 Martin Bacovsky <mbacovsk@redhat.com> - 0.99.8-1.1
- rebuild

* Mon Jul 30 2007 Martin Bacovsky <mbacovsk@redhat.com> - 0.99.8-1
- upgrade to new upstream version 0.99.8
- resolves: #249423: scripts in /etc/rc.d/init.d/* are marked as config files in specfile
- resolves: #247040: Initscript Review
- resolves: #249538: Inconsistencies in init scripts
- resolves: #220531: quagga: non-failsafe install-info usage, info files removed from index on update

* Tue Jul  3 2007 Martin Bacovsky <mbacovsk@redhat.com> - 0.99.7-1
- upgrade to new upstream 0.99.7
- resolves: #240488: CVE-2007-1995 Quagga bgpd DoS

* Wed Mar 28 2007 Martin Bacovsky <mbacovsk@redhat.com> - 0.99.6-1
- upgrade to new upstream 0.99.6
- Resolves: #233909: quagga: unowned directory
- removed redundant patches (#226352)

* Mon Jan 22 2007 Martin Bacovsky <mbacovsk@redhat.com> - 0.98.6-3
- Resolves: #172548 - quagga.spec defines with_vtysh 1 but vtysh is not enabled in the build

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 0:0.98.6-2.1
- rebuild

* Mon May 8 2006 Jay Fenlason <fenlason@redhat.com> 0:0.98.6-2
- Upgrade to new upstream version, closing security problems:
  bz#191081 CVE-2006-2223 Quagga RIPd information disclosure
  bz#191085 CVE-2006-2224 Quagga RIPd route injection

* Wed Mar  8 2006 Bill Nottingham <notting@redhat.com> - 0:0.98.5-4
- use an assigned gid for quaggavt

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 0:0.98.5-3.2.1
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 0:0.98.5-3.2
- rebuilt for new gcc4.1 snapshot and glibc changes

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com>
- rebuilt

* Wed Oct 19 2005 Jay Fenlason <fenlason@redhat.com> 0.98.5-3
- add the -pie patch, to make -fPIE compiling actually work on all platforms.
- Include -pam patch to close
  bz#170256 ? pam_stack is deprecated
- Change ucd-snmp to net-snmp to close
  bz#164333 ? quagga 0.98.4-2 requires now obsolete package ucd-snmp-devel
- also fix duplicate line mentioned in bz#164333

* Mon Aug 29 2005 Jay Fenlason <fenlason@redhat.com> 0.98.5-2
- New upstream version.

* Mon Jun 27 2005 Jay Fenlason <fenlason@redhat.com> 0.98.4-2
- New upstream version.

* Mon Apr 4 2005 Jay Fenlason <fenlason@redhat.com> 0.98.3-2
- new upstream verison.
- remove the -bug157 patch.

* Tue Mar 8 2005 Jay Fenlason <fenlason@redhat.com> 0.98.2-2
- New upstream version, inclues my -gcc4 patch, and a patch from
  Vladimir Ivanov <wawa@yandex-team.ru>

* Sun Jan 16 2005 Jay Fenlason <fenlason@redhat.com> 0.98.0-2
- New upstream version.  This fixes bz#143796
- --with-rtadv needs to be --enable-rtadv according to configure.
  (but it was enabled by default, so this is a cosmetic change only)
  Change /etc/logrotate.d/* to /etc/logrotate.d/quagga in this spec file.
- Modify this spec file to move the .so files to the base package
  and close bz#140894
- Modify this spec file to separate out macro <_includedir>/quagga/ospfd
  from .../*.h and macro <_includedir>/quagga/ospfapi from .../*.h
  Rpmbuild probably shouldn't allow macro <dir> of a plain file.

* Wed Jan 12 2005 Tim Waugh <twaugh@redhat.com> 0.97.3-3
- Rebuilt for new readline.
- Don't explicitly require readline.  The correct dependency is automatically
  picked up by linking against it.

* Fri Nov 26 2004 Florian La Roche <laroche@redhat.com>
- remove target buildroot again to not waste disk space

* Wed Nov 10 2004 Jay Fenlason <fenlason@redhat.com> 0.97.3-1
- New upstream version.

* Tue Oct 12 2004 Jay Fenlason <fenlason@redhat.com> 0.97.2-1
- New upstream version.

* Fri Oct 8 2004 Jay Fenlason <fenlason@redhat.com> 0.97.0-1
- New upstream version.  This obsoletes the -lib64 patch.

* Wed Oct 6 2004 Jay Fenlason <fenlason@redhat.com>
- Change the permissions of /var/run/quagga to 771 and /var/log/quagga to 770
  This closes #134793

* Thu Sep  9 2004 Bill Nottingham <notting@redhat.com> 0.96.5-2
- don't run by default

* Tue Jun 15 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Tue May 4 2004 Jay Fenlason <fenlason@redhat.com> 0.96.5-0
- New upstream version
- Change includedir
- Change the pre scriptlet to fail if the useradd command fails.
- Remove obsolete patches from this .spec file and renumber the two
  remaining ones.

* Tue Mar 02 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Fri Feb 13 2004 Jay Fenlason <fenlason@redhat.com>
- Add --enable-rtadv, to turn ipv6 router advertisement back on.  Closes
  bugzilla #114691

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Mon Nov 3 2003 Jay Fenlason <fenlason@redhat.com> 0.96.4-0
- New upstream version
- include .h files in the -devel package.

* Wed Oct 15 2003 Jay Fenlason <fenlason@redhat.com> 0.96.3-1
- Patch a remote DoS attack (#107140)
- New upstream version
- Removed the .libcap patch, which was applied upstream
- Renamed the vty group from quaggavty to quaggavt because quaggavty is
  too long for NIS.
- Patch the spec file to fix #106857: /etc/quagga/zebra.conf is created with
  the wrong owner.
- Removed the "med" part of the 0.96.1-warnings patch for . . .
- Add a new warnings patch with a fix for #106315.  This also updates
  the "med" part of the previous warnings patch.

* Mon Sep 22 2003 Jay Fenlason <fenlason@redhat.com> 0.96.2-5
- merge sysconfig patch from 3E branch.  This patch is from Kaj J. Niemi
  (kajtzu@basen.net), and puts Quagga configuration options in
  /etc/sysconfig/quagga, and defaults Quagga to listening on 127.0.0.1 only.
  This closes #104376
- Use /sbin/nologin for the shell of the quagga user.  This closes #103320
- Update the quagga-0.96.1-warnings.patch patch to kill a couple more
  warnings.

* Mon Sep 22 2003 Nalin Dahyabhai <nalin@redhat.com>
- Remove the directory part of paths for PAM modules in quagga.pam, allowing
  libpam to search its default directory (needed if a 64-bit libpam needs to
  look in /lib64/security instead of /lib/security).

* Tue Aug 26 2003 Jay Fenlason <fenlason@redhat.com> 0.96.2-1
- New upstream version

* Tue Aug 19 2003 Jay Fenlason <fenlason@redhat.com> 0.96.1-3
- Merge from quagga-3E-branch, with a fix for #102673 and a couple
  more compiler warnings quashed.

* Wed Aug 13 2003 Jay Fenlason <fenlason@redhat.com> 0.96-1
- added a patch (libwrap) to allow the generated Makefiles for zebra/
  and lib/ to work on AMD64 systems.  For some reason make there does
  not like a dependency on -lcap
- added a patch (warnings) to shut up warnings about an undefined
  structure type in some function prototypes and quiet down all the
  warnings about assert(ptr) on x86_64.
- Modified the upstream quagga-0.96/readhat/quagga.spec to work as an
  official Red Hat package (remove user and group creation and changes
  to services)
- Trimmed changelog.  See the upstream .spec file for previous
  changelog entries.
