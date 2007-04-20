
%define	name	lirc

%define	version	0.8.1
%define snapshot 0
%define	rel	1

%if %snapshot
%define release	%mkrel 0.%snapshot.%rel
%else
%define	release	%mkrel %rel
%endif

%define	lib_major 0
%define lib_name %mklibname %{name} %{lib_major}

Summary:	Linux Infrared Remote Control daemons
Name:		%{name}
Version:	%{version}
Release:	%{release}
License:	GPL
Group:		System/Kernel and hardware
%if %snapshot
Source0:	%{name}-%{snapshot}.tar.bz2
%else
Source0:	http://prdownloads.sourceforge.net/lirc/%{name}-%{version}.tar.bz2
%endif
Source2:	lircd.sysconfig
Source3:	lircd.init
Source4:	lircmd.init
URL:		http://www.lirc.org/
BuildRequires:	autoconf2.5
BuildRequires:	automake1.9
BuildRequires:	XFree86-devel
BuildRequires:  libirman-static-devel
BuildRequires:	libusb-devel
%if %mdkversion >= 200710
BuildRequires:	portaudio0-devel
%else
BuildRequires:	portaudio-devel
%endif
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

%package -n	%{lib_name}
Summary:	LIRC libraries
Group:		System/Libraries

%description -n	%{lib_name}
This package provides the libraries necessary to run lirc client
programs.

%package -n	%{lib_name}-devel
Summary:	Header and library files for LIRC development
Group:		Development/Other
Requires:	%{lib_name} = %{version}-%{release}
Provides:	lib%{name}-devel = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}

%description -n	%{lib_name}-devel
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

This module requires the full kernel source. Stripped kernel source
is not enough.

%prep
%if %snapshot
%setup -q -n %{name}
rm -r CVS */CVS */*/CVS
%else
%setup -q
%endif

%build

%configure2_5x	--localstatedir=/var \
		--with-x \
		--with-port=0x3f8 \
		--with-irq=4 \
		--disable-manage-devices \
		--with-syslog=LOG_DAEMON \
		--with-driver=userspace \
		--with-transmitter

# parallel build doesn't work as of cvs20060722
make \
%if %mdkversion < 1020
DEFS="-DHAVE_CONFIG_H -DHID_MAX_USAGES"
%endif

cd doc
./release-html.sh

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_datadir}/aclocal
mkdir -p $RPM_BUILD_ROOT/var/log

%makeinstall_std

install contrib/*.m4 $RPM_BUILD_ROOT%{_datadir}/aclocal

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/udev/rules.d/
install -m644 contrib/lirc.rules $RPM_BUILD_ROOT%{_sysconfdir}/udev/rules.d/

install -m644 %{SOURCE2} -D $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/lircd
install -m755 %{SOURCE3} -D $RPM_BUILD_ROOT%{_initrddir}/lircd
install -m755 %{SOURCE4} -D $RPM_BUILD_ROOT%{_initrddir}/lircmd

cat > $RPM_BUILD_ROOT%{_sysconfdir}/lircd.conf<<END
#
# This is a placeholder for your configuration file.
# See %{_datadir}/%{name}-remotes for some examples.
# You might need to install %{name}-remotes package.
#
END

cp -f $RPM_BUILD_ROOT%{_sysconfdir}/lirc{,m}d.conf

# dkms

for lircsrcdir in %{name} %{name}-parallel %{name}-gpio; do

install -d -m755 %{buildroot}/usr/src/$lircsrcdir-%{version}-%{release}
cp -a Makefile Makefile.in Makefile.am acinclude.m4 \
	configure.in config.status config.h \
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

cat > %{buildroot}/usr/src/%{name}-%{version}-%{release}/dkms.conf <<EOF
PACKAGE_NAME="%{name}"
PACKAGE_VERSION="%{version}-%{release}"
MAKE[0]="for driver in $drivers; do make -C drivers/\\\$driver \
	KERNEL_LOCATION=\$kernel_source_dir AUTOMAKE=true AUTOCONF=true ACLOCAL=true; done"
CLEAN="for driver in $drivers; do make -C drivers/\\\$driver \
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

for drivername in parallel gpio; do
cat > %{buildroot}/usr/src/%{name}-$drivername-%{version}-%{release}/dkms.conf <<EOF
PACKAGE_NAME="%{name}-$drivername"
PACKAGE_VERSION="%{version}-%{release}"
MAKE[0]="make -C drivers/lirc_$drivername \
	KERNEL_LOCATION=\$kernel_source_dir AUTOMAKE=true AUTOCONF=true ACLOCAL=true"
CLEAN="make -C drivers/lirc_$drivername \
	clean AUTOMAKE=true AUTOCONF=true ACLOCAL=true"
AUTOINSTALL=yes
BUILT_MODULE_NAME[0]="lirc_$drivername"
BUILT_MODULE_LOCATION[0]="drivers/lirc_$drivername"
DEST_MODULE_LOCATION[0]="/kernel/drivers/input/misc"
EOF

done

%clean
rm -rf $RPM_BUILD_ROOT

%post	-n %{lib_name} -p /sbin/ldconfig
%postun	-n %{lib_name} -p /sbin/ldconfig

%post
%create_ghostfile /var/log/lircd root root 644
%_post_service lircd
%_post_service lircmd

%preun
%_preun_service lircmd
%_preun_service lircd

%post -n dkms-%{name}
dkms add     -m %{name} -v %{version}-%{release} --rpm_safe_upgrade
dkms build   -m %{name} -v %{version}-%{release} --rpm_safe_upgrade
dkms install -m %{name} -v %{version}-%{release} --rpm_safe_upgrade
true

%preun -n dkms-%{name}
dkms remove  -m %{name} -v %{version}-%{release} --rpm_safe_upgrade --all
true

%post -n dkms-%{name}-parallel
dkms add     -m %{name}-parallel -v %{version}-%{release} --rpm_safe_upgrade
dkms build   -m %{name}-parallel -v %{version}-%{release} --rpm_safe_upgrade
dkms install -m %{name}-parallel -v %{version}-%{release} --rpm_safe_upgrade
true

%preun -n dkms-%{name}-parallel
dkms remove  -m %{name}-parallel -v %{version}-%{release} --rpm_safe_upgrade --all
true

%post -n dkms-%{name}-gpio
dkms add     -m %{name}-gpio -v %{version}-%{release} --rpm_safe_upgrade
dkms build   -m %{name}-gpio -v %{version}-%{release} --rpm_safe_upgrade
dkms install -m %{name}-gpio -v %{version}-%{release} --rpm_safe_upgrade
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

%files -n %{lib_name}
%defattr(-,root,root)
%{_libdir}/*.so.*

%files -n %{lib_name}-devel
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



