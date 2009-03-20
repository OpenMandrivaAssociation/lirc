# cvs -d:pserver:anonymous@lirc.cvs.sourceforge.net:/cvsroot/lirc login
# cvs -z8 -d:pserver:anonymous@lirc.cvs.sourceforge.net:/cvsroot/lirc co lirc
%define snapshot	20090320
%define pre		0
%define	rel		1

%if %snapshot
%define release		%mkrel 0.%{snapshot}.%{rel}
%define distname	%{name}-%{snapshot}.tar.lzma
%define dirname		%{name}
%else
%if %pre
%define release		%mkrel 0.pre%{pre}.%{rel}
%define distname	%{name}-%{version}pre%{pre}.tar.bz2
%define dirname		%{name}-%{version}pre%{pre}
%else
%define	release		%mkrel %{rel}
%define distname	%{name}-%{version}.tar.bz2
%define dirname		%{name}-%{version}
%endif
%endif

%define	major		0
%define libname 	%mklibname %{name} %{major}
%define develname	%mklibname %{name} -d

Summary:	Linux Infrared Remote Control daemons
Name:		lirc
Version:	0.8.5
Release:	%{release}
License:	GPLv2+
Group:		System/Kernel and hardware
Source0:	http://prdownloads.sourceforge.net/lirc/%{distname}
Source2:	lircd.sysconfig
Source3:	lircd.init
Source4:	lircmd.init
# (fc) 0.8.3-1mdv use new instead of conf as filename suffix in template mode (Fedora)
Patch0:		lirc-use-new-instead-of-conf-as-filename-suffix.patch
# Build ftdi conditionally as intended
Patch1:		lirc-fix-conditional-ftdi.patch
URL:		http://www.lirc.org/
BuildRequires:	autoconf
BuildRequires:	X11-devel
BuildRequires:  libirman-static-devel
BuildRequires:	libusb-devel
BuildRequires:	portaudio-devel
BuildRequires:	libalsa-devel
BuildRequires:	help2man
Requires(post):	rpm-helper
Requires(preun):rpm-helper
Requires:	setserial
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

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
Requires(post):	dkms
Requires(preun): dkms

%description -n	dkms-%{name}
This package provides the kernel modules for LIRC.

Install this package if the LIRC driver you are using requires
them and your kernel doesn't include them.

Note that lirc_gpio and lirc_parallel are in packages of their own.

%package -n     dkms-%{name}-parallel
Summary:        Parallel port module for LIRC
Group:          System/Kernel and hardware
Requires:       dkms-%{name} = %version
Requires(post): dkms
Requires(preun): dkms

%description -n dkms-%{name}-parallel
This package provides the parallel port module for LIRC.

This module requires a non-SMP kernel.

%package -n	dkms-%{name}-gpio
Summary:	GPIO module for LIRC
Group:		System/Kernel and hardware
Requires:	dkms-%{name} = %version
Requires(post):	dkms
Requires(preun): dkms

%description -n	dkms-%{name}-gpio
This package provides the GPIO module for LIRC.

%prep
%setup -q -n %{dirname}
%patch0 -p1 -b .new
%patch1 -p1

%build
%if %snapshot
./autogen.sh
%endif

%configure2_5x	--localstatedir=/var \
		--with-x \
		--with-port=0x3f8 \
		--with-irq=4 \
		--disable-manage-devices \
		--with-syslog=LOG_DAEMON \
		--with-driver=userspace \
		--with-transmitter \
		--with-kerneldir=$(pwd) # fixes build as of 20070827

# parallel make broken as of 2009-03
make \
%if %mdkversion < 1020
DEFS="-DHAVE_CONFIG_H -DHID_MAX_USAGES"
%endif

%if %snapshot
make -C doc release
%endif

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_datadir}/aclocal
mkdir -p %{buildroot}/var/log

%makeinstall_std

install contrib/*.m4 %{buildroot}%{_datadir}/aclocal

mkdir -p %{buildroot}%{_sysconfdir}/udev/rules.d/
install -m644 contrib/lirc.rules %{buildroot}%{_sysconfdir}/udev/rules.d/

install -m644 %{SOURCE2} -D %{buildroot}%{_sysconfdir}/sysconfig/lircd
install -m755 %{SOURCE3} -D %{buildroot}%{_initrddir}/lircd
install -m755 %{SOURCE4} -D %{buildroot}%{_initrddir}/lircmd

cat > %{buildroot}%{_sysconfdir}/lircd.conf<<END
#
# This is a placeholder for your configuration file.
# See %{_datadir}/%{name}-remotes for some examples.
# You might need to install %{name}-remotes package.
#
END

cp -f %{buildroot}%{_sysconfdir}/lirc{,m}d.conf

# dkms

for lircsrcdir in %{name} %{name}-parallel %{name}-gpio; do

install -d -m755 %{buildroot}/usr/src/$lircsrcdir-%{version}-%{release}
cp -a Makefile Makefile.in Makefile.am acinclude.m4 \
	configure.ac config.status config.h \
	%{buildroot}/usr/src/$lircsrcdir-%{version}-%{release}

# Makefiles call there to unnecessarily regenerate files
echo '#!/bin/true' > %{buildroot}/usr/src/$lircsrcdir-%{version}-%{release}/configure
chmod +x %{buildroot}/usr/src/$lircsrcdir-%{version}-%{release}/configure

done

cp -a drivers %{buildroot}/usr/src/%{name}-%{version}-%{release}

for drivername in parallel gpio; do
install -d -m755 %{buildroot}/usr/src/%{name}-$drivername-%{version}-%{release}/drivers
mv %{buildroot}/usr/src/%{name}-%{version}-%{release}/drivers/lirc_$drivername \
	%{buildroot}/usr/src/%{name}-$drivername-%{version}-%{release}/drivers/
cp -a drivers/*.h drivers/Makefile* drivers/lirc_dev \
	%{buildroot}/usr/src/%{name}-$drivername-%{version}-%{release}/drivers/

done

# get modulelist
pushd drivers
drivers=$(echo lirc_* | sed "s/lirc_parallel //" | sed "s/lirc_gpio //")
popd

# Anssi 2009-03 empty directory
drivers="${drivers/lirc_cmdir /}"

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

#cat >> %{buildroot}/usr/src/%{name}-%{version}-%{release}/dkms.conf <<-EOF
#BUILT_MODULE_NAME[$i]="commandir"
#BUILT_MODULE_LOCATION[$i]="drivers/lirc_cmdir"
#DEST_MODULE_LOCATION[$i]="/kernel/drivers/input/misc"
#EOF
#i=$((i+1))

for drivername in parallel gpio; do
cat > %{buildroot}/usr/src/%{name}-$drivername-%{version}-%{release}/dkms.conf <<EOF
PACKAGE_NAME="%{name}-$drivername"
PACKAGE_VERSION="%{version}-%{release}"
MAKE[0]="cd drivers/lirc_$drivername; make \
	KERNEL_LOCATION=\$kernel_source_dir AUTOMAKE=true AUTOCONF=true ACLOCAL=true"
CLEAN="cd drivers/lirc_$drivername; make \
	clean AUTOMAKE=true AUTOCONF=true ACLOCAL=true"
AUTOINSTALL=yes
BUILT_MODULE_NAME[0]="lirc_$drivername"
BUILT_MODULE_LOCATION[0]="drivers/lirc_$drivername"
DEST_MODULE_LOCATION[0]="/kernel/drivers/input/misc"
EOF

done

rm -rf %{buildroot}/dev

%clean
rm -rf %{buildroot}

%if %mdkversion < 200900
%post	-n %{libname} -p /sbin/ldconfig
%endif
%if %mdkversion < 200900
%postun	-n %{libname} -p /sbin/ldconfig
%endif

%post
%create_ghostfile /var/log/lircd root root 644
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

%post -n dkms-%{name}-parallel
dkms add     -m %{name}-parallel -v %{version}-%{release} --rpm_safe_upgrade &&
dkms build   -m %{name}-parallel -v %{version}-%{release} --rpm_safe_upgrade &&
dkms install -m %{name}-parallel -v %{version}-%{release} --rpm_safe_upgrade --force
true

%preun -n dkms-%{name}-parallel
dkms remove  -m %{name}-parallel -v %{version}-%{release} --rpm_safe_upgrade --all
true

%post -n dkms-%{name}-gpio
dkms add     -m %{name}-gpio -v %{version}-%{release} --rpm_safe_upgrade &&
dkms build   -m %{name}-gpio -v %{version}-%{release} --rpm_safe_upgrade &&
dkms install -m %{name}-gpio -v %{version}-%{release} --rpm_safe_upgrade --force
true

%preun -n dkms-%{name}-gpio
dkms remove  -m %{name}-gpio -v %{version}-%{release} --rpm_safe_upgrade --all
true

%files
%defattr(-,root,root)
%doc ANNOUNCE AUTHORS NEWS README TODO ChangeLog 
%doc contrib/{irman2lirc,lircs} doc/irxevent.keys
%doc doc/lirc.css doc/html doc/images
%{_initrddir}/*
%config(noreplace) %{_sysconfdir}/sysconfig/*
%config(noreplace) %{_sysconfdir}/*.conf
%config(noreplace) %{_sysconfdir}/udev/rules.d/*.rules
%{_bindir}/*
%{_sbindir}/*
%{_mandir}/*/*

%files -n %{libname}
%defattr(-,root,root)
%{_libdir}/*.so.%{major}*

%files -n %{develname}
%defattr(-,root,root)
%{_includedir}/lirc
%{_datadir}/aclocal/*
%{_libdir}/*.so
%{_libdir}/*.la
%{_libdir}/*.a

%files -n dkms-%{name}
%defattr(-,root,root)
/usr/src/%{name}-%{version}-%{release}

%files -n dkms-%{name}-parallel
%defattr(-,root,root)
/usr/src/%{name}-parallel-%{version}-%{release}

%files -n dkms-%{name}-gpio
%defattr(-,root,root)
/usr/src/%{name}-gpio-%{version}-%{release}
