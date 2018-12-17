
Name:		openvas-manager
Version:	7.0.3
Release:	3%{?dist}
Summary:	Manager Module for the Open Vulnerability Assessment System (OpenVAS)

License:	GPLv2+
URL:		http://www.openvas.org
Source0:	https://github.com/greenbone/gvmd/releases/download/v7.0.3/openvas-manager-7.0.3.tar.gz
%if 0%{?rhel} >= 7 || 0%{?fedora} > 15
Source4:	https://raw.githubusercontent.com/diverops/openvas-manager/master/openvas-manager.service
%else
Source1:	https://raw.githubusercontent.com/diverops/openvas-manager/master/openvas-manager.initd
%endif
Source2:	https://raw.githubusercontent.com/diverops/openvas-manager/master/openvas-manager.logrotate
Source3:	https://raw.githubusercontent.com/diverops/openvas-manager/master/openvas-manager.sysconfig

# Put certs to /etc/pki as suggested by http://fedoraproject.org/wiki/PackagingDrafts/Certificates
# Not reported upstream as it is RedHat/Fedora specific
Patch1:		https://raw.githubusercontent.com/diverops/openvas-manager/master/openvas-manager-pki.patch
Patch2:		https://raw.githubusercontent.com/diverops/openvas-manager/master/openvas-manager-gpgerror.patch

# Replace _BSD_SOURCE and _SVID_SOURCE with _DEFAULT_SOURCE otherwise build fails with Werror
Patch3:		https://raw.githubusercontent.com/diverops/openvas-manager/master/openvas-manager-bsdsource.patch

BuildRequires:	openvas-libraries-devel >= 7.0
BuildRequires:	cmake >= 2.6.0
BuildRequires:	glib2-devel
BuildRequires:	sqlite-devel
BuildRequires:	gnutls-devel
BuildRequires:	libgcrypt-devel
BuildRequires:	libuuid-devel
BuildRequires:	libpcap-devel
BuildRequires:	libksba-devel
BuildRequires:	gpgme-devel
BuildRequires:	libgpg-error-devel
BuildRequires:	doxygen
BuildRequires:	pkgconfig
BuildRequires:	xmltoman
%if 0%{?rhel} >= 7 || 0%{?fedora} > 15
BuildRequires:	systemd
Requires(post):	systemd
Requires(preun):	systemd
Requires(postun):	systemd
%else
Requires(post):		chkconfig
Requires(preun):	chkconfig
Requires(preun):	initscripts
%endif

Requires:	logrotate
Requires:	/usr/bin/xsltproc


%description
The OpenVAS Manager is the central service that consolidates plain vulnerability
scanning into a full vulnerability management solution. The Manager controls the
Scanner via OTP and itself offers the XML-based, stateless OpenVAS Management 
Protocol (OMP). All intelligence is implemented in the Manager so that it is
possible to implement various lean clients that will behave consistently e.g. 
with regard to filtering or sorting scan results. The Manager also controls 
a SQL database (sqlite-based) where all configuration and scan result data is 
centrally stored.

%prep
%setup -q -c
#%patch0 -p1 -b .notused
%patch1 -p1 -b .pki
%patch2 -p1 -b .gpgerror

#%if 0%{?fedora} >= 21
#%patch3 -p1 -b .bsdsource
#%endif

#Fix encoding issues
iconv -f Windows-1250 -t utf-8 < CHANGES > CHANGES.utf8
mv CHANGES.utf8 CHANGES
iconv -f Windows-1250 -t utf-8 < ChangeLog > ChangeLog.utf8
mv ChangeLog.utf8 ChangeLog

%build
export CFLAGS="$RPM_OPT_FLAGS -Werror=unused-but-set-variable -lgpg-error"
%cmake -DLOCALSTATEDIR:PATH=%{_var}
make %{?_smp_mflags} VERBOSE=1

%install
make install DESTDIR=%{buildroot} INSTALL="install -p"

# Config directory
mkdir -p %{buildroot}/%{_sysconfdir}/openvas
chmod 755 %{buildroot}/%{_sysconfdir}/openvas

# Log direcotry
mkdir -p %{buildroot}/%{_var}/log/openvas
touch %{buildroot}%{_var}/log/openvas/openvasmd.log

# Runtime lib directory
mkdir -p %{buildroot}/%{_var}/lib/openvas/mgr

# gnupg directory
mkdir -p %{buildroot}/%{_var}/lib/openvas/gnupg


%if 0%{?rhel} >= 7 || 0%{?fedora} > 15
# Install systemd
install -Dp -m 644 %{SOURCE4} %{buildroot}/%{_unitdir}/%{name}.service
%else
# Install startup script
install -Dp -m 755 %{SOURCE1} %{buildroot}/%{_initddir}/%{name}
%endif

# Install log rotation stuff
install -m 644 -Dp %{SOURCE2} %{buildroot}/%{_sysconfdir}/logrotate.d/%{name}

# Install sysconfig configration
install -Dp -m 644 %{SOURCE3} %{buildroot}/%{_sysconfdir}/sysconfig/%{name}

# Fix permissions on templates
chmod -R a+r %{buildroot}%{_datadir}/openvas/openvasmd
find %{buildroot}%{_datadir}/openvas/openvasmd -name generate | xargs chmod 755

# Clean installed doc directory
rm -rf %{buildroot}%{_datadir}/doc/%{name}

%if 0%{?rhel} >= 7 || 0%{?fedora} > 15
#Post scripts for systemd
%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%else
#Post scripts for systemv initd
%post
# This adds the proper /etc/rc*.d links for the script
if [ "$1" -eq 1 ] ; then
	/sbin/chkconfig --add openvas-manager
fi

%preun
if [ "$1" -eq 0 ] ; then
	/sbin/service openvas-manager stop >/dev/null 2>&1
	/sbin/chkconfig --del openvas-manager
fi

%postun
# only for upgrades not erasure
if [ "$1" -eq 1 ] ; then
	/sbin/service openvas-manager condrestart  >/dev/null 2>&1
fi
%endif

%files
# INSTALL file contains post-installation guide for whole openvas
%doc CHANGES COPYING README ChangeLog INSTALL
%doc doc/*.png doc/*.sql doc/*.html doc/report-format-HOWTO doc/about-cert-feed.txt
%doc report_formats
%config(noreplace) %{_sysconfdir}/logrotate.d/openvas-manager
%dir %{_sysconfdir}/openvas
%dir %{_var}/lib/openvas
%dir %{_var}/lib/openvas/mgr
%dir %{_var}/log/openvas
%dir %{_datadir}/openvas
%dir %{_var}/lib/openvas/gnupg
%dir %{_datadir}/openvas/scap
%dir %{_datadir}/openvas/cert
%config(noreplace) %{_sysconfdir}/openvas/openvasmd_log.conf
%config(noreplace) %{_sysconfdir}/openvas/pwpolicy.conf
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%if 0%{?rhel} >= 7 || 0%{?fedora} > 15
%{_unitdir}/%{name}.service
%else
%{_initrddir}/%{name}
%endif
%{_bindir}/openvas-manage-certs
%{_sbindir}/database-statistics-sqlite
%{_sbindir}/openvasmd
%{_sbindir}/openvasmd-sqlite
%{_sbindir}/greenbone-scapdata-sync
%{_sbindir}/greenbone-certdata-sync
%{_sbindir}/openvas-portnames-update
%{_sbindir}/openvas-migrate-to-postgres
%{_mandir}/man1/openvas-manage-certs.1*
%{_mandir}/man8/openvasmd.8*
%{_mandir}/man8/database-statistics-sqlite.8*
%{_mandir}/man8//greenbone-certdata-sync.8*
%{_mandir}/man8/greenbone-scapdata-sync.8*
%{_mandir}/man8/openvas-migrate-to-postgres.8*
%{_mandir}/man8/openvas-portnames-update.8*
%{_datadir}/openvas/openvasmd
%{_datadir}/openvas/scap/*
%{_datadir}/openvas/cert/*
%{_datadir}/openvas/openvas-lsc-rpm-creator.sh
%ghost %{_var}/log/openvas/openvasmd.log


%changelog
* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 7.0.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 7.0.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jul 03 2017 Michal Ambroz <rebus at, seznam.cz> - 7.0.2-1
- bump to 7.0.2

* Wed Apr 19 2017 Michal Ambroz <rebus at, seznam.cz> - 7.0.1-1
- bump version to OpenVAS-9

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 6.0.9-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Sat Dec 10 2016 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 6.0.9-2
- Rebuild for gpgme 1.18

* Mon Sep 05 2016 Michal Ambroz <rebus at, seznam.cz> - 6.0.9-1
- bump version to 6.0.9

* Fri Apr 29 2016 Michal Ambroz <rebus at, seznam.cz> - 6.0.8-2
- sync spec-files across fedora versions

* Fri Apr 29 2016 Michal Ambroz <rebus at, seznam.cz> - 6.0.8-1
- bump version

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 6.0.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Dec 24 2015 josef radinger <cheese@nosuchhost.net> - 6.0.7-1
- bump version
- small cleanups in spec-file

* Tue Sep 29 2015 josef radinger <cheese@nosuchhost.net> - 6.0.6-1
- bump version

* Wed Sep 16 2015 josef radinger <cheese@nosuchhost.net> - 6.0.5-2
- add gnupg-directory

* Wed Jul 15 2015 Michal Ambroz <rebus at, seznam.cz> - 6.0.5-1
- bump to OpenVas-8 version 6.0.5
- 1254456 - fix logrotate script

* Wed Jul 15 2015 Michal Ambroz <rebus at, seznam.cz> - 6.0.4-1
- bump to OpenVas-8 version 6.0.4

* Mon Jun 29 2015 Michal Ambroz <rebus at, seznam.cz> - 6.0.3-4
- rebuild for F22

* Sat Jun 20 2015 Michal Ambroz <rebus at, seznam.cz> - 6.0.3-3
- fix the options in the /etc/sysconfig

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 6.0.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat May 23 2015 Michal Ambroz <rebus at, seznam.cz> - 6.0.3-1
- bump to OpenVas-8 version 6.0.3

* Sat Apr 04 2015 Michal Ambroz <rebus at, seznam.cz> - 5.0.9-1
- bump to OpenVas-7 version 5.0.9

* Sat Dec 06 2014 Michal Ambroz <rebus at, seznam.cz> - 5.0.7-1
- bump to OpenVas-7 version 5.0.7

* Fri Nov 07 2014 Michal Ambroz <rebus at, seznam.cz> - 5.0.5-2
- remove sysvinit subpackage as it is not needed anymore
- call setgroups before giving up rights with setuid

* Tue Nov 04 2014 Michal Ambroz <rebus at, seznam.cz> - 5.0.5-1
- bump to OpenVas-7 version 5.0.5

* Fri Sep 12 2014 Michal Ambroz <rebus at, seznam.cz> - 5.0.4-1
- bump to OpenVas-7 version 5.0.4

* Tue Sep 02 2014 Michal Ambroz <rebus at, seznam.cz> - 5.0.3-1
- bump to OpenVas-7 version 5.0.3

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 5.0.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Tue Jun 17 2014 Michal Ambroz <rebus at, seznam.cz> - 5.0.2-1
- bump to OpenVas-7 version 5.0.2

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 5.0.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed May 21 2014 Fabian Affolter <mail@fabian-affolter.ch> - 5.0.1-1
- Update spec file
- Update to latest upstream release 5.0.1

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.0-4.beta5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Mar 12 2013 Michal Ambroz <rebus at, seznam.cz> - 4.0-3.beta5
- bump to OpenVas-6 version 4.0+beta5

* Tue Mar 12 2013 Michal Ambroz <rebus at, seznam.cz> - 4.0-2.beta4
- rebuilt with new GnuTLS

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.0-1.beta4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Feb 06 2013 Michal Ambroz <rebus at, seznam.cz> - 4.0-0.beta4
- bump to OpenVas-6 version 4.0+beta4

* Mon Oct 15 2012 Michal Ambroz <rebus at, seznam.cz> - 3.0.4-1
- bump OpenVas-5 (openvas-manager 3.0.4)

* Sat Aug 25 2012 Michal Ambroz <rebus at, seznam.cz> - 2.0.5-1
- bugfix release
- changed post scriptlets to macros for Fedora 18+

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.4-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Apr 10 2012 Michal Ambroz <rebus at, seznam.cz> - 2.0.4-3
- migrate init scripts from sysvinit to systemd

* Mon Jan 23 2012 Michal Ambroz <rebus at, seznam.cz> - 2.0.4-2
- fix checking for the existence of the certificates in initscript

* Mon Jan 09 2012 Michal Ambroz <rebus at, seznam.cz> - 2.0.4-1
- new upstream version 2.0.4

* Wed Apr 06 2011 Michal Ambroz <rebus at, seznam.cz> - 2.0.2-4
- dependencies for F15

* Wed Mar 30 2011 Michal Ambroz <rebus at, seznam.cz> - 2.0.2-3
- implement changes based on package review

* Wed Mar 30 2011 Michal Ambroz <rebus at, seznam.cz> - 2.0.2-2
- implement changes based on package review

* Mon Mar 28 2011 Michal Ambroz <rebus at, seznam.cz> - 2.0.2-1
- initial spec for openvas-manager based on openvas-scanner
