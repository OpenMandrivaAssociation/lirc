%define major		0
%define libname 	%mklibname %{name} %{major}
%define develname	%mklibname %{name} -d

Summary:	Linux Infrared Remote Control daemons
Name:		lirc
Version:	0.9.0
Release:	7
License:	GPLv2+
Group:		System/Kernel and hardware
URL:		http://www.lirc.org/
Source0:	http://prdownloads.sourceforge.net/lirc/%{name}-%{version}.tar.bz2
Source2:	lircd.sysconfig
Source3:	lircd.init
Source4:	lircmd.init
Source5:	http://svn.debian.org/viewsvn/pkg-lirc/lirc/trunk/debian/liblircclient0.pc
# (fc) 0.8.3-1mdv use new instead of conf as filename suffix in template mode (Fedora)
Patch0:		lirc-use-new-instead-of-conf-as-filename-suffix.patch
Patch2:		lirc-printf-format.patch
BuildRequires:	autoconf
BuildRequires:	pkgconfig(x11)
BuildRequires:	libirman-devel
BuildRequires:	pkgconfig(libusb)
BuildRequires:	pkgconfig(portaudio-2.0)
BuildRequires:	pkgconfig(alsa)
BuildRequires:	iguanair-devel
BuildRequires:	help2man
BuildRequires:	svgalib-devel
Requires(post):	rpm-helper
Requires(preun):rpm-helper
Requires:	setserial

%description
LIRC is a package that allows you to decode and send infra-red signals
of many (but not all) commonly used remote controls.

Configuration files for many remotes are locate in lirc-remotes package

%package -n	%{libname}
Summary:	LIRC libraries
Group:		System/Libraries

%description -n	%{libname}
This package provides the libraries necessary to run lirc client
programs.

%package -n	%{develname}
Summary:	Header and library files for LIRC development
Group:		Development/Other
Requires:	%{libname} = %{version}-%{release}
Provides:	lib%{name}-devel = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}
Obsoletes:	%{mklibname lirc 0 -d}

%description -n	%{develname}
This package provides the files necessary to develop LIRC-based
programs.

%package -n	dkms-%{name}
Summary:	Kernel modules for LIRC
Group:		System/Kernel and hardware
Obsoletes:	dkms-lirc-parallel < 0.8.7-1
Provides:	dkms-lirc-parallel = %{version}-%{release}
Requires(post):	dkms
Requires(preun):dkms

%description -n	dkms-%{name}
This package provides the kernel modules for LIRC.

Install this package if the LIRC driver you are using requires
them and your kernel doesn't include them.

%prep
%setup -q
%patch0 -p1 -b .new
%patch2 -p1

%build
%configure2_5x	--localstatedir=/var \
		--disable-static \
		--with-x \
		--with-port=0x3f8 \
		--with-irq=4 \
		--disable-manage-devices \
		--with-syslog=LOG_DAEMON \
		--with-driver=userspace \
		--with-transmitter \
		--with-kerneldir=$(pwd) # fixes build as of 20070827

# parallel make broken as of 2009-03
make

%install
mkdir -p %{buildroot}%{_datadir}/aclocal
mkdir -p %{buildroot}/var/log
mkdir -p %{buildroot}/var/run/lirc
touch %{buildroot}/var/run/lirc/lircd
touch %{buildroot}/var/run/lirc/lircd.pid

%makeinstall_std

install contrib/*.m4 %{buildroot}%{_datadir}/aclocal

mkdir -p %{buildroot}%{_sysconfdir}/udev/rules.d/
install -m644 contrib/lirc.rules %{buildroot}%{_sysconfdir}/udev/rules.d/

install -m644 %{SOURCE2} -D %{buildroot}%{_sysconfdir}/sysconfig/lircd
install -m755 %{SOURCE3} -D %{buildroot}%{_initrddir}/lircd
install -m755 %{SOURCE4} -D %{buildroot}%{_initrddir}/lircmd
install -m644 %{SOURCE5} -D %{buildroot}%{_libdir}/pkgconfig/liblircclient0.pc
sed -i -e "s/0.8.3/%{version}/" -e "s^/lib^/%{_lib}^" %{buildroot}%{_libdir}/pkgconfig/liblircclient0.pc

mkdir -p %{buildroot}%{_sysconfdir}/lirc
cat > %{buildroot}%{_sysconfdir}/lirc/lircd.conf<<END
#
# This is a placeholder for your configuration file.
# See %{_datadir}/%{name}-remotes for some examples.
# You might need to install %{name}-remotes package.
#
END

cp -f %{buildroot}%{_sysconfdir}/lirc/lirc{,m}d.conf

# dkms

install -d -m755 %{buildroot}/usr/src/%{name}-%{version}-%{release}
cp -a Makefile Makefile.in Makefile.am acinclude.m4 \
	configure.ac config.status config.h \
	%{buildroot}/usr/src/%{name}-%{version}-%{release}

# Makefiles call there to unnecessarily regenerate files
echo '#!/bin/true' > %{buildroot}/usr/src/%{name}-%{version}-%{release}/configure
chmod +x %{buildroot}/usr/src/%{name}-%{version}-%{release}/configure

cp -a drivers %{buildroot}/usr/src/%{name}-%{version}-%{release}

# get modulelist
pushd drivers
drivers="lirc_dev $(echo lirc_* | sed -e "s/lirc_gpio //" -e "s/lirc_dev //")"
popd

cat > %{buildroot}/usr/src/%{name}-%{version}-%{release}/dkms.conf <<EOF
PACKAGE_NAME="%{name}"
PACKAGE_VERSION="%{version}-%{release}"
MAKE[0]="droot=\\\$(pwd); for driver in $drivers; do cd \\\$droot/drivers/\\\$driver; make \
	KERNEL_LOCATION=\$kernel_source_dir AUTOMAKE=true AUTOCONF=true ACLOCAL=true; done"
CLEAN="droot=\\\$(pwd); for driver in $drivers; do cd \\\$droot/drivers/\\\$driver; make \
	clean AUTOMAKE=true AUTOCONF=true ACLOCAL=true; done"
AUTOINSTALL=yes
EOF

i=0
for module in $drivers; do
	cat >> %{buildroot}/usr/src/%{name}-%{version}-%{release}/dkms.conf <<-EOF
	BUILT_MODULE_NAME[$i]="$module"
	BUILT_MODULE_LOCATION[$i]="drivers/$module"
	DEST_MODULE_LOCATION[$i]="/kernel/drivers/input/misc"
	EOF
	i=$((i+1))
done

cat > README.0.8.6-2.upgrade.urpmi <<EOF
As of LIRC 0.8.6, the config file locations have changed to
/etc/lirc/lircd.conf, /etc/lirc/lircmd.conf, and /etc/lirc/lircrc.
Existing files have been moved to these locations automatically.
The socket location has changed to /var/run/lirc/lircd.
EOF

%pre
if [ $1 = 2 ] && ! [ -e %{_sysconfdir}/lirc ]; then
	mkdir -p %{_sysconfdir}/lirc
	touch %{_sysconfdir}/lirc/mdv-086-migration
fi

%post
%create_ghostfile /var/log/lircd root root 644
if [ $1 = 2 ] && [ -e %{_sysconfdir}/lirc/mdv-086-migration ]; then
	mv -vf %{_sysconfdir}/lircd.conf %{_sysconfdir}/lirc/lircd.conf 2>/dev/null
	mv -vf %{_sysconfdir}/lircmd.conf %{_sysconfdir}/lirc/lircmd.conf 2>/dev/null
	mv -vf %{_sysconfdir}/lircrc %{_sysconfdir}/lirc/lircrc 2>/dev/null
	rm -f %{_sysconfdir}/lirc/mdv-086-migration
fi
%_post_service lircd
%_post_service lircmd

%preun
%_preun_service lircmd
%_preun_service lircd

%post -n dkms-%{name}
dkms add     -m %{name} -v %{version}-%{release} --rpm_safe_upgrade &&
dkms build   -m %{name} -v %{version}-%{release} --rpm_safe_upgrade &&
dkms install -m %{name} -v %{version}-%{release} --rpm_safe_upgrade --force
true

%preun -n dkms-%{name}
dkms remove  -m %{name} -v %{version}-%{release} --rpm_safe_upgrade --all
true

%files
%doc README.0.8.6-2.upgrade.urpmi
%doc ANNOUNCE AUTHORS NEWS README TODO ChangeLog 
%doc contrib/{irman2lirc,lircs} doc/irxevent.keys
%doc doc/lirc.css doc/html doc/images
%{_initrddir}/*
%config(noreplace) %{_sysconfdir}/sysconfig/*
%dir %{_sysconfdir}/lirc
%config(noreplace) %{_sysconfdir}/lirc/*.conf
%config(noreplace) %{_sysconfdir}/udev/rules.d/*.rules
%{_bindir}/*
%{_sbindir}/*
%dir %{_var}/run/lirc
%ghost %{_var}/run/lirc/lircd.pid
%ghost %{_var}/run/lirc/lircd
%ghost %{_var}/run/lirc/lircm
%{_mandir}/*/*

%files -n %{libname}
%{_libdir}/*.so.%{major}*

%files -n %{develname}
%{_libdir}/pkgconfig/liblircclient0.pc
%{_includedir}/lirc
%{_datadir}/aclocal/*
%{_libdir}/*.so

%files -n dkms-%{name}
/usr/src/%{name}-%{version}-%{release}

%changelog
* Fri Oct 28 2011 Alexander Khrukin <akhrukin@mandriva.org> 0.9.0-5mdv2012.0
+ Revision: 707752
- fixed lirc-use-new-instead-of-conf-as-filename-suffix.patch for new version of lirc and version update see #64361

* Wed May 04 2011 Oden Eriksson <oeriksson@mandriva.com> 0.8.7-5
+ Revision: 666082
- mass rebuild

* Sun Feb 06 2011 Funda Wang <fwang@mandriva.org> 0.8.7-4
+ Revision: 636455
- update file list
- drop condtioned switch
- drop conditioned dirname, rpm5 does not like it

* Sun Feb 06 2011 Funda Wang <fwang@mandriva.org> 0.8.7-3
+ Revision: 636400
- rebuild

* Sat Feb 05 2011 Funda Wang <fwang@mandriva.org> 0.8.7-2
+ Revision: 636052
- tighten BR
- tighten BR

  + Anssi Hannula <anssi@mandriva.org>
    - new version
    - merge dkms-lirc-parallel back to dkms-lirc
    - disable dkms-lirc-gpio for now, it doesn't seem to be useful
      (doesn't build with recent kernels)

* Fri Dec 03 2010 Oden Eriksson <oeriksson@mandriva.com> 0.8.7-0.20100505.2mdv2011.0
+ Revision: 606411
- rebuild

* Wed May 05 2010 Anssi Hannula <anssi@mandriva.org> 0.8.7-0.20100505.1mdv2010.1
+ Revision: 542273
- new snapshot (fixes build with recent kernels)
- build lirc_dev first (fixes lirc_atiusb and lirc_bt829, bug #57871)

* Sun Apr 04 2010 Funda Wang <fwang@mandriva.org> 0.8.7-0.20100115.2mdv2010.1
+ Revision: 531218
- rebuild for new irman

* Fri Jan 15 2010 Anssi Hannula <anssi@mandriva.org> 0.8.7-0.20100115.1mdv2010.1
+ Revision: 491869
- new snapshot (fixes DKMS build with recent kernels)

* Mon Oct 26 2009 Anssi Hannula <anssi@mandriva.org> 0.8.6-2mdv2010.0
+ Revision: 459392
- adapt for moved configuration, socket, pid files (fixes #54409)

* Sun Sep 13 2009 Frederik Himpe <fhimpe@mandriva.org> 0.8.6-1mdv2010.0
+ Revision: 439033
- Update to new stable version 0.8.6
- Remove 2.6.26+ declaration patch: should not be necessary anymore

* Sun Aug 02 2009 Anssi Hannula <anssi@mandriva.org> 0.8.6-0.20090802.1mdv2010.0
+ Revision: 407544
- new snapshot (support for recent kernels)
- remove ftdi patch, fixed upstream
- fix lirc-i2c module build on 2.6.26+ by adding a forward declaration
  (i2c-2.6.26-declaration.patch)

* Tue Jul 14 2009 Anssi Hannula <anssi@mandriva.org> 0.8.5-0.20090320.4mdv2010.0
+ Revision: 395748
- build with iguanaIR support

* Mon May 11 2009 Götz Waschk <waschk@mandriva.org> 0.8.5-0.20090320.3mdv2010.0
+ Revision: 374833
- fix pkgconfig file on x86_64

* Mon May 11 2009 Götz Waschk <waschk@mandriva.org> 0.8.5-0.20090320.2mdv2010.0
+ Revision: 374798
- add pkgconfig file from Debian (needed by gxine)

* Sat Mar 21 2009 Anssi Hannula <anssi@mandriva.org> 0.8.5-0.20090320.1mdv2009.1
+ Revision: 359400
- fix printf format string (printf-format.patch)
- rediff suffix patch
- new snapshot (support for recent kernel versions)
- drop imon.patch, fixed upstream
- fix build without ftdi (fix-conditional-ftdi.patch)
- disable commandir as the directory is empty

* Tue Oct 21 2008 Adam Williamson <awilliamson@mandriva.org> 0.8.4-3mdv2009.1
+ Revision: 296258
- fix the imon patch (from upstream CVS, incorrect variable name)

* Tue Oct 14 2008 Adam Williamson <awilliamson@mandriva.org> 0.8.4-2mdv2009.1
+ Revision: 293719
- update imon.patch with subsequent upstream fixes / improvements

* Mon Oct 13 2008 Adam Williamson <awilliamson@mandriva.org> 0.8.4-1mdv2009.1
+ Revision: 293424
- add imon.patch (from upstream CVS): support two new iMon devices (44148)
- new release 0.8.4 final

* Sat Oct 11 2008 Adam Williamson <awilliamson@mandriva.org> 0.8.4-0.pre2.1mdv2009.1
+ Revision: 291715
- simplify our drivers definition a bit as upstream cleaned out obsolete ones
- drop most patches (merged upstream)
- adjust portaudio require (now builds against 19)
- new release 0.8.4-pre2
- improve svn / pre-release conditionals

* Thu Sep 11 2008 Frederic Crozat <fcrozat@mandriva.com> 0.8.3-4mdv2009.0
+ Revision: 283929
- Change default configuration so lircd is started even if not configured (Fedora), needed for gnome-lirc-properties

* Mon Sep 08 2008 Pascal Terjan <pterjan@mandriva.org> 0.8.3-3mdv2009.0
+ Revision: 282551
- Add upstream patches to build on 2.6.27

* Sun Aug 24 2008 Frederic Crozat <fcrozat@mandriva.com> 0.8.3-2mdv2009.0
+ Revision: 275459
- Patch3 (CVS): don't exit daemon even though device cannot be initialized

* Sun Aug 24 2008 Frederic Crozat <fcrozat@mandriva.com> 0.8.3-1mdv2009.0
+ Revision: 275440
- Release 0.8.3 final
- add patches from Fedora for gnome-lirc-properties support (thanks to Bastien Nocerra) :
 - Patch0 (Fedora): add include directive support for config file
 - Patch1 (upstream): validate transmit buffer
 - Patch2 (Fedora): use new instead of conf as filename suffix in template mode

  + Pixel <pixel@mandriva.com>
    - do not call ldconfig in %%post/%%postun, it is now handled by filetriggers

* Sat May 03 2008 Adam Williamson <awilliamson@mandriva.org> 0.8.3-0.20080501.2mdv2009.0
+ Revision: 200580
- make sure commandir module gets built and installed

* Thu May 01 2008 Adam Williamson <awilliamson@mandriva.org> 0.8.3-0.20080501.1mdv2009.0
+ Revision: 199889
- some spec cleaning
- new snapshot

  + Anssi Hannula <anssi@mandriva.org>
    - fix dkms-lirc-gpio description

* Tue Mar 11 2008 Adam Williamson <awilliamson@mandriva.org> 0.8.2-1.20080310.2mdv2008.1
+ Revision: 184862
- correct the initscript fix (thanks anssi)

* Tue Mar 11 2008 Adam Williamson <awilliamson@mandriva.org> 0.8.2-1.20080310.1mdv2008.1
+ Revision: 184762
- remove /dev in %%install as it's screwing up fix_eol script
- initscript should only start after dkms-lirc so the module actually exists
- new snapshot

* Mon Jan 28 2008 Adam Williamson <awilliamson@mandriva.org> 0.8.2-1.20080128.1mdv2008.1
+ Revision: 159264
- new snapshot (hopefully works better with 2.6.24 final)

* Sat Jan 05 2008 Olivier Blin <blino@mandriva.org> 0.8.2-1.20080105.1mdv2008.1
+ Revision: 145803
- update to cvs snapshot 20080105 (to fix build with 2.6.24-rc6)
- restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request
    - buildrequires X11-devel instead of XFree86-devel

* Mon Dec 03 2007 Adam Williamson <awilliamson@mandriva.org> 0.8.2-1.20071203.1mdv2008.1
+ Revision: 114643
- new snapshot 20071203 (see if it works with 2.6.24, current doesn't)

* Thu Oct 11 2007 Adam Williamson <awilliamson@mandriva.org> 0.8.2-1.20071011.1mdv2008.1
+ Revision: 97178
- update buildrequires
- new devel policy
- new license policy
- new snapshot (works with 2.6.23 kernels)

* Tue Oct 02 2007 Olivier Blin <blino@mandriva.org> 0.8.2-1.20070827.3mdv2008.0
+ Revision: 94683
- rebuild

* Tue Oct 02 2007 Olivier Blin <blino@mandriva.org> 0.8.2-1.20070827.2mdv2008.0
+ Revision: 94681
- rebuild

* Tue Aug 28 2007 Anssi Hannula <anssi@mandriva.org> 0.8.2-1.20070827.1mdv2008.0
+ Revision: 72759
- cvs snapshot (support for recent kernels)
- use dummy --with-kerneldir to fix build
- adapt dkms package for changes in makefiles
- do not run subsequent dkms commands if one fails

* Sun Jun 10 2007 Funda Wang <fwang@mandriva.org> 0.8.2-1mdv2008.0
+ Revision: 37830
- New version

* Fri Apr 20 2007 Anssi Hannula <anssi@mandriva.org> 0.8.1-1mdv
+ Revision: 16385
- 0.8.1 final
- drop patch1 (now unneeded), patch2 (fixed upstream)

