%define major 0
%define libname %mklibname %{name}_client %{major}
%define devname %mklibname %{name}_client -d
%define __noautoreq '.*/bin/true'

%define build_dkms 0

Summary:	Linux Infrared Remote Control daemons
Name:		lirc
Version:	0.10.1
Release:	1
License:	GPLv2+
Group:		System/Kernel and hardware
Url:		http://www.lirc.org/
Source0:	http://prdownloads.sourceforge.net/lirc/%{name}-%{version}.tar.bz2
Source2:	%{name}-tmpfiles.conf
Source3:	lircd.service
Source4:	lircmd.service
Source5:	http://svn.debian.org/viewsvn/pkg-lirc/lirc/trunk/debian/liblircclient0.pc
# (fc) 0.8.3-1mdv use new instead of conf as filename suffix in template mode (Fedora)
#Patch0:		lirc-use-new-instead-of-conf-as-filename-suffix.patch
#Patch1:		lirc-printf-format.patch

BuildRequires:	help2man
BuildRequires:	iguanair-devel
BuildRequires:	libirman-devel
BuildRequires:	xsltproc
BuildRequires:	pkgconfig(x11)
BuildRequires:	pkgconfig(python)
BuildRequires:	python3egg(pyyaml)
BuildRequires:	python3egg(setuptools)
BuildRequires:	pkgconfig(systemd)
%ifarch %{ix86} x86_64
BuildRequires:	svgalib-devel
%endif
BuildRequires:	pkgconfig(alsa)
BuildRequires:	pkgconfig(libusb)
BuildRequires:	pkgconfig(portaudio-2.0)
BuildRequires:	pkgconfig(x11)
Requires(post,preun):	rpm-helper
Requires:	setserial

%description
LIRC is a package that allows you to decode and send infra-red signals
of many (but not all) commonly used remote controls.

Configuration files for many remotes are locate in lirc-remotes package.

%files
%doc README.0.8.6-2.upgrade.urpmi
%doc AUTHORS NEWS README ChangeLog 
%doc contrib/{irman2lirc,lircs} doc/irxevent.keys
%doc doc/html doc/images
%config(noreplace) %{_sysconfdir}/lirc/*.conf
#{_sysconfdir}/udev/rules.d/%{name}.rules
%{_bindir}/*
%{_sbindir}/*
%{_mandir}/*/*
%dir %{_var}/run/lirc
%ghost %{_var}/run/lirc/lircd
%ghost %{_var}/run/lirc/lircm
%{_unitdir}/lircd.service
%{_unitdir}/lircmd.service
%{_tmpfilesdir}/%{name}.conf

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

#----------------------------------------------------------------------------

%package -n %{libname}
Summary:	LIRC libraries
Group:		System/Libraries
Obsoletes:	%{_lib}lirc0 < 0.9.0-15
Conflicts:	%{_lib}lirc0 < 0.9.0-15

%description -n %{libname}
This package provides the libraries necessary to run lirc client
programs.

%files -n %{libname}
%{_libdir}/liblirc_client.so.%{major}*

#----------------------------------------------------------------------------

%package -n %{devname}
Summary:	Header and library files for LIRC development
Group:		Development/Other
Requires:	%{libname} = %{EVRD}
Provides:	%{name}-devel = %{EVRD}
Obsoletes:	%{_lib}lirc-devel < 0.9.0-15
Conflicts:	%{_lib}lirc-devel < 0.9.0-15

%description -n %{devname}
This package provides the files necessary to develop LIRC-based
programs.

%files -n %{devname}
%{_libdir}/pkgconfig/liblircclient0.pc
%{_includedir}/lirc
#{_datadir}/aclocal/*
%{_libdir}/*.so

#----------------------------------------------------------------------------
%if %build_dkms

%package -n dkms-%{name}
Summary:	Kernel modules for LIRC
Group:		System/Kernel and hardware
Requires(post,preun):	dkms

%description -n dkms-%{name}
This package provides the kernel modules for LIRC.

Install this package if the LIRC driver you are using requires
them and your kernel doesn't include them.

%files -n dkms-%{name}
/usr/src/%{name}-%{version}-%{release}

%post -n dkms-%{name}
dkms add     -m %{name} -v %{version}-%{release} --rpm_safe_upgrade &&
dkms build   -m %{name} -v %{version}-%{release} --rpm_safe_upgrade &&
dkms install -m %{name} -v %{version}-%{release} --rpm_safe_upgrade --force
true

%preun -n dkms-%{name}
dkms remove  -m %{name} -v %{version}-%{release} --rpm_safe_upgrade --all
true

%endif
#----------------------------------------------------------------------------

%prep
%setup -q
%autopatch -p1

%build
export CC=gcc
export CXX=g++
%configure \
	--localstatedir=/var \
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

%makeinstall_std

#install contrib/*.m4 %{buildroot}%{_datadir}/aclocal

#mkdir -p %{buildroot}%{_sysconfdir}/udev/rules.d/
#install -m644 contrib/lirc.rules %{buildroot}%{_sysconfdir}/udev/rules.d/

install -D -p -m 0644 %{SOURCE2} %{buildroot}%{_tmpfilesdir}/%{name}.conf
install -D -m 644 %{SOURCE3} %{buildroot}%{_unitdir}/lircd.service
install -D -m 644 %{SOURCE4} %{buildroot}%{_unitdir}/lircmd.service
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

%if %build_dkms

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

%endif

cat > README.0.8.6-2.upgrade.urpmi <<EOF
As of LIRC 0.8.6, the config file locations have changed to
/etc/lirc/lircd.conf, /etc/lirc/lircmd.conf, and /etc/lirc/lircrc.
Existing files have been moved to these locations automatically.
The socket location has changed to /var/run/lirc/lircd.
EOF

