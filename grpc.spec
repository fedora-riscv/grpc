Name:           grpc
Version:        1.26.0
Release:        11%{?dist}
Summary:        RPC library and framework

# The entire source is ASL 2.0 except the following:
#
# BSD:
#   - third_party/upb/, except third_party/upb/third_party/lunit/
#     * Potentially linked into any compiled subpackage (but not -doc,
#       pure-Python subpackages, etc.)
#   - third_party/address_sorting/
#     * Potentially linked into any compiled subpackage (but not -doc,
#       pure-Python subpackages, etc.)
#
# as well as the following which do not contribute to the base License field or
# any subpackage License field for the reasons noted:
#
# MPLv2.0:
#   - etc/roots.pem
#     * Truncated to an empty file in prep; a symlink to the shared system
#       certificates is used instead
#   - src/android/test/interop/app/src/main/assets/roots.pem
#     * Truncated to an empty file in prep
# ISC:
#   - src/boringssl/crypto_test_data.cc and src/boringssl/err_data.c
#     * Removed in prep; not used when building with system OpenSSL
# BSD:
#   - src/objective-c/*.podspec and templates/src/objective-c/*.podspec.template
#     * Unused since the Objective-C bindings are not currently built
# MIT:
#   - third_party/cares/ares_build.h
#     * Removed in prep; header from system C-Ares used instead
#   - third_party/rake-compiler-dock/
#     * Removed in prep, since we build no containers
#   - third_party/upb/third_party/lunit/
#     * Removed in prep, since there is no obvious way to run the upb tests
License:        ASL 2.0 and BSD
URL:            https://www.%{name}.io
%global forgeurl https://github.com/%{name}/%{name}/
Source0:        %{forgeurl}/archive/v%{version}/%{name}-%{version}.tar.gz

# ~~~~ C (core) and C++ (cpp) ~~~~

%global c_so_version 9
%global cpp_so_version 1

BuildRequires:  gcc-c++
BuildRequires:  pkgconfig
BuildRequires:  make
BuildRequires:  chrpath

BuildRequires:  protobuf-devel
BuildRequires:  protobuf-compiler
BuildRequires:  openssl-devel
BuildRequires:  c-ares-devel
BuildRequires:  gflags-devel
BuildRequires:  gtest-devel
BuildRequires:  zlib-devel
BuildRequires:  gperftools-devel

# ~~~~ Python ~~~~

%global set_grpc_python_environment %{expand:
export GRPC_PYTHON_BUILD_WITH_CYTHON=True
export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=True
export GRPC_PYTHON_BUILD_SYSTEM_ZLIB=True
export GRPC_PYTHON_BUILD_SYSTEM_CARES=True
export GRPC_PYTHON_DISABLE_LIBC_COMPATIBILITY=True
export GRPC_PYTHON_ENABLE_DOCUMENTATION_BUILD=True}

BuildRequires:  python3-devel
BuildRequires:  python3dist(setuptools)
BuildRequires:  pyproject-rpm-macros
# Not automatically generated even when we set GRPC_PYTHON_BUILD_WITH_CYTHON:
BuildRequires:  python3dist(cython)
# Otherwise, we use generated BR’s.

# ~~~~ Miscellaneous ~~~~

# https://bugzilla.redhat.com/show_bug.cgi?id=1893533
%global _lto_cflags %{nil}

BuildRequires:  ca-certificates
# For converting absolute symlinks in the buildroot to relative ones
BuildRequires:  symlinks

BuildRequires:  dos2unix

# https://docs.fedoraproject.org/en-US/packaging-guidelines/CryptoPolicies/#_cc_applications
Patch0:         %{name}-0001-enforce-system-crypto-policies.patch
Patch2:         %{name}-0003-use-shell-loop-instead-makefile-function.patch
Patch3:         99f8a10aec994a8957fbb6787768b444ef34d6a2.patch
Patch4:         72351f63fd650cc7acfcd2d0307e8e8e8f777283.patch
# Based on remove-gnu99.patch from
# https://src.fedoraproject.org/rpms/grpc/pull-request/3; corresponds to
# ignored upstream PR https://github.com/grpc/grpc/pull/23671. For consistency,
# we also patch a related shell script that we do not use.
# 
# Using -std=gnu99 for C++ code makes GCC warn and clang error; besides, it
# makes no sense.
Patch5:         %{name}-1.26.0-python-no-std-gnu99.patch
# Backport upstream commit 9e0b427893b65b220faf8a31a6afdc67f6f41364 “Use !=
# with literals”
Patch6:         %{name}-1.26.0-python-SyntaxWarning.patch
# Stop adding -static-libgcc when linking Python bindings
Patch7:         %{name}-1.26.0-python-no-static-libgcc.patch
# Build python3-grpcio_tools against system protobuf packages instead of
# expecting a git submodule. Must also add requisite linker flags using
# GRPC_PYTHON_LDFLAGS.
Patch8:         %{name}-1.26.0-python-grpcio_tools-use-system-protobuf.patch
# Allow us to use the setup.py in grpcio-tests (e.g. for generating BR’s)
# before we have built grpcio-tools; the build_package_protos command is simply
# not available in this case. Activated by setting environment variable
# GRPCIO_TESTS_IGNORE_MISSING_TOOLS with any value.
Patch9:         %{name}-1.26.0-grpcio-tests-setup-without-grpcio-tools.patch
# In grpcio-tests, require enum34 for install only on those ancient Pythons
# that require it; we are not using such a Python!
Patch10:        %{name}-1.26.0-grpcio-tests-conditionalize-enum34.patch

Requires:       %{name}-data = %{version}-%{release}

# Upstream https://github.com/protocolbuffers/upb does not support building
# with anything other than Bazel, and Bazel is not likely to make it into
# Fedora anytime soon due to its nightmarish collection of dependencies.
# Monitor this at https://bugzilla.redhat.com/show_bug.cgi?id=1470842.
# Therefore upb cannot be packaged for Fedora, and we must use the bundled copy.
#
# Note that upstream has never chosen a version, and it is not clear from which
# commit the bundled copy was taken or forked.
#
# Note also that libupb is installed in the system-wide linker path, which will
# be a problem if upb is ever packaged separately. We will cross that bridge if
# we get there.
Provides:       bundled(upb)

# Regarding third_party/address_sorting: this looks a bit like a bundled
# library, but it is not. From a source file comment:
#   This is an adaptation of Android's implementation of RFC 6724 (in Android’s
#   getaddrinfo.c). It has some cosmetic differences from Android’s
#   getaddrinfo.c, but Android’s getaddrinfo.c was used as a guide or example
#   of a way to implement the RFC 6724 spec when this was written.

%description
gRPC is a modern open source high performance RPC framework that can run in any
environment. It can efficiently connect services in and across data centers
with pluggable support for load balancing, tracing, health checking and
authentication. It is also applicable in last mile of distributed computing to
connect devices, mobile applications and browsers to backend services.

The main usage scenarios:

  * Efficiently connecting polyglot services in microservices style architecture
  * Connecting mobile devices, browser clients to backend services
  * Generating efficient client libraries

Core Features that make it awesome:

  * Idiomatic client libraries in 10 languages
  * Highly efficient on wire and with a simple service definition framework
  * Bi-directional streaming with http/2 based transport
  * Pluggable auth, tracing, load balancing and health checking

This package provides the shared C core library.


%generate_buildrequires
%set_grpc_python_environment
%pyproject_buildrequires -r
# Generate BRs from other Python packages; but use grep to filter out those we
# are building and installing ourselves.
(
  export GRPCIO_TESTS_IGNORE_MISSING_TOOLS=1
  pushd "tools/distrib/python/grpcio_tools/" >/dev/null
  %pyproject_buildrequires -r
  popd >/dev/null
  for suffix in channelz health_checking reflection status testing tests
  do
    pushd "src/python/grpcio_${suffix}/" >/dev/null
    %pyproject_buildrequires -r
    popd >/dev/null
  done
) | grep -vF 'grpc'


%package data
Summary:        Data for gRPC bindings
License:        ASL 2.0
BuildArch:      noarch

Requires:       ca-certificates

%description data
Common data for gRPC bindings: currently, this contains only a symbolic link to
the system shared TLS certificates.


%package doc
Summary:        Documentation and examples for gRPC
License:        ASL 2.0
BuildArch:      noarch

%description doc
Documentation and examples for gRPC.


%package cpp
Summary:        C++ language bindings for gRPC
# License:        same as base package
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description cpp
C++ language bindings for gRPC.


%package plugins
Summary:        Protocol buffers compiler plugins for gRPC
# License:        same as base package
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       protobuf-compiler

%description plugins
Plugins to the protocol buffers compiler to generate gRPC sources.


%package cli
Summary:        Command-line tool for gRPC
# License:        same as base package
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description cli
The command line tool can do the following things:

  * Send unary rpc.
  * Attach metadata and display received metadata.
  * Handle common authentication to server.
  * Infer request/response types from server reflection result.
  * Find the request/response types from a given proto file.
  * Read proto request in text form.
  * Read request in wire form (for protobuf messages, this means serialized
    binary form).
  * Display proto response in text form.
  * Write response in wire form to a file.


%package devel
Summary:        Development files for gRPC library
# License:        same as base package
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       %{name}-cpp%{?_isa} = %{version}-%{release}

%description devel
Development headers and files for gRPC libraries (both C and C++).


%package -n python3-grpcio
Summary:        Python language bindings for gRPC
# License:        same as base package

# Note that the Python package has no runtime dependency on the base C library;
# everything it needs is bundled.
Requires:       %{name}-data = %{version}-%{release}

%description -n python3-grpcio
Python language bindings for gRPC (HTTP/2-based RPC framework).


%package -n python3-grpcio-tools
Summary:       Package for gRPC Python tools
# License:        same as base package

%description -n python3-grpcio-tools
Package for gRPC Python tools.


%package -n python3-grpcio-channelz
Summary:        Channel Level Live Debug Information Service for gRPC
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-channelz
Channelz is a live debug tool in gRPC Python.


%package -n python3-grpcio-health-checking
Summary:        Standard Health Checking Service for gRPC
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-health-checking
Reference package for GRPC Python health checking.


%package -n python3-grpcio-reflection
Summary:        Standard Protobuf Reflection Service for gRPC
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-reflection
Reference package for reflection in GRPC Python.


%package -n python3-grpcio-status
Summary:        Status proto mapping for gRPC
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-status
Reference package for GRPC Python status proto mapping.


%package -n python3-grpcio-testing
Summary:        Testing utilities for gRPC Python
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-testing
Testing utilities for gRPC Python.


%package -n python-grpcio-doc
License:        ASL 2.0
Summary:        Documentation for Python language bindings for gRPC
BuildArch:      noarch

Provides:       python-grpcio-channelz-doc = %{version}-%{release}
Provides:       python-grpcio-health-checking-doc = %{version}-%{release}
Provides:       python-grpcio-reflection-doc = %{version}-%{release}
Provides:       python-grpcio-status-doc = %{version}-%{release}
Provides:       python-grpcio-testing-doc = %{version}-%{release}

%description -n python-grpcio-doc
Documentation for Python language bindings for gRPC, including the following
packages:

  * grpcio
  * grpcio_channelz
  * grpcio_health_checking
  * grpcio_reflection
  * grpcio_status
  * grpcio_testing


%prep
%autosetup -p1
sed -i \
    -e 's:^prefix ?= .*:prefix ?= %{_prefix}:' \
    -e 's:$(prefix)/lib:$(prefix)/%{_lib}:' \
    -e 's:^GTEST_LIB =.*::' Makefile

# Fix some of the weirdest accidentally-executable files
find . -type f -name '*.md' -perm /0111 -execdir chmod -v a-x '{}' '+'

# Allow building Python documentation with a newer Sphinx; the upstream version
# requirement is needlessly strict. (It is fine for upstream’s own purposes, as
# they are happy to build documentation with a pinned old version.)
sed -r -i "s/('Sphinx)~=.*'/\1'/" setup.py

# Remove unused sources that have licenses not in the License field, to ensure
# they are not accidentally used in the build. See the comment above the base
# package License field for more details.
rm -rfv \
    src/boringssl/*.c src/boringssl/*.cc \
    third_party/cares/ares_build.h \
    third_party/rake-compiler-dock \
    third_party/upb/third_party/lunit
# Since we are replacing roots.pem with a symlink to the shared system
# certificates, we do not include its license (MPLv2.0) in any License field.
# We remove its contents so that, if we make a packaging mistake, we will have
# a bug but not an incorrect License field.
echo '' > etc/roots.pem

# Remove Android sources and examples. We do not need these on Linux, and they
# have some issues that will be flagged when reviewing the package, such as:
#   - Another copy of the MPLv2.0-licensed certificate bundle from
#     etc/roots.pem, in src/android/test/interop/app/src/main/assets/roots.pem
#   - Pre-built jar files at
#     src/android/test/interop/gradle/wrapper/gradle-wrapper.jar and
#     examples/android/helloworld/gradle/wrapper/gradle-wrapper.jar
rm -rvf examples/android src/android

# Remove unwanted .gitignore files, generally in examples. One could argue that
# a sample .gitignore file is part of the example, but, well, we’re not going
# to do that.
find . -type f -name .gitignore -print -delete

# Find executables with /usr/bin/env shebangs in the examples, and fix them.
find examples -type f -perm /0111 |
  while read -r fn
  do
    if head -n 1 "${fn}" | grep -E '^#!/usr/bin/env[[:blank:]]'
    then
      sed -r -i '1{s|^(#!/usr/bin/)env[[:blank:]]+([^[:blank:]]+)|\1\2|}' \
          "${fn}"
    fi
  done

# Fix some CRNL line endings:
dos2unix \
    examples/cpp/helloworld/CMakeLists.txt \
    examples/cpp/helloworld/cmake_externalproject/CMakeLists.txt
# We leave those under examples/csharp alone.


%build
# ~~~~ C (core) and C++ (cpp) ~~~~

%set_build_flags
# Default targets are: static shared plugins
%make_build shared plugins

# ~~~~ Python ~~~~

# Since we will need all of the Python packages for the documentation build,
# and there are some other interdependencies (e.g., many have setup_requires:
# grpcio-tools), we do a temporary install of the built packages into a local
# directory, and add it to the PYTHONPATH.
PYROOT="${PWD}/%{_vpath_builddir}/pyroot"
if [ -n "${PYTHONPATH-}" ]; then PYTHONPATH="${PYTHONPATH}:"; fi
PYTHONPATH="${PYTHONPATH-}${PYROOT}%{python3_sitelib}"
PYTHONPATH="${PYTHONPATH}:${PYROOT}%{python3_sitearch}"
export PYTHONPATH

# ~~ grpcio ~~
%set_grpc_python_environment
%py3_build
%{__python3} %{py_setup} %{?py_setup_args} install \
    -O1 --skip-build --root "${PYROOT}"

# ~~ grpcio-tools ~~
pushd "tools/distrib/python/grpcio_tools/" >/dev/null
# When copying more things in here, make sure the subpackage License field
# stays correct. We need copies, not symlinks, so that the “graft” in
# MANIFEST.in works.
mkdir -p %{name}_root/src
for srcdir in compiler
do
  cp -rp "../../../../src/${srcdir}" "%{name}_root/src/"
done
cp -rp '../../../../include' '%{name}_root/'
(
  export GRPC_PYTHON_LDFLAGS='-lprotoc'
  %py3_build
)
# Remove unwanted shebang from grpc_tools.protoc source file, which will be
# installed without an executable bit:
find . -type f -name protoc.py -execdir sed -r -i '1{/^#!/d}' '{}' '+'
%{__python3} %{py_setup} %{?py_setup_args} install \
    -O1 --skip-build --root "${PYROOT}"
popd >/dev/null

# ~~ pure-python modules grpcio-* ~~
for suffix in channelz health_checking reflection status testing
do
  echo "----> grpcio_${suffix} <----" 1>&2
  pushd "src/python/grpcio_${suffix}/" >/dev/null
  %py3_build
  %{__python3} %{py_setup} %{?py_setup_args} install \
      -O1 --skip-build --root "${PYROOT}"
  popd >/dev/null
done

# ~~ grpcio-tests ~~
echo '----> grpcio_tests <----'
pushd 'src/python/grpcio_tests/' >/dev/null
%py3_build
popd >/dev/null

# ~~ documentation ~~
%{__python3} %{py_setup} %{?py_setup_args} doc


%install
# ~~~~ C (core) and C++ (cpp) ~~~~
# Do not strip debugging symbols!
export STRIP=/bin/true
make install prefix='%{buildroot}%{_prefix}'
make install-grpc-cli prefix='%{buildroot}%{_prefix}'
chrpath --delete '%{buildroot}%{_bindir}/%{name}_cli'
# Remove any static libraries that may have been installed against our wishes
find %{buildroot} -type f -name '*.a' -print -delete
# Fix wrong permissions on installed headers
find %{buildroot}%{_includedir}/%{name}* -type f -name '*.h' -perm /0111 \
    -execdir chmod -v a-x '{}' '+'

# ~~~~ Python ~~~~

# Since several packages have an install_requires: grpcio-tools, we must ensure
# the buildroot Python site-packages directories are in the PYTHONPATH.
pushd '%{buildroot}'
PYROOT="${PWD}"
popd
if [ -n "${PYTHONPATH-}" ]; then PYTHONPATH="${PYTHONPATH}:"; fi
PYTHONPATH="${PYTHONPATH-}${PYROOT}%{python3_sitelib}"
PYTHONPATH="${PYTHONPATH}:${PYROOT}%{python3_sitearch}"
export PYTHONPATH

# ~~ grpcio ~~
%py3_install

# ~~ grpcio-tools ~~
pushd "tools/distrib/python/grpcio_tools/" >/dev/null
%py3_install
popd >/dev/null

# ~~ pure-python modules grpcio-* ~~
for suffix in channelz health_checking reflection status testing
do
  pushd "src/python/grpcio_${suffix}/" >/dev/null
  %py3_install
  popd >/dev/null
done

# ~~~~ Miscellaneous ~~~~

# Replace copies of the certificate bundle with symlinks to the shared system
# certificates. This has the following benefits:
#   - Reduces duplication and save space
#   - Respects system-wide administrative trust configuration
#   - Keeps “MPLv2.0” from having to be added to a number of License fields
%global sysbundle %{_sysconfdir}/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
# We do not own this file; we temporarily install it in the buildroot so we do
# not have dangling symlinks.
install -D -t "%{buildroot}$(dirname '%{sysbundle}')" -m 0644 '%{sysbundle}'

find '%{buildroot}' -type f -name 'roots.pem' |
  while read -r fn
  do
    ln -s -f "%{buildroot}%{sysbundle}" "${fn}"
    symlinks -c -o "${fn}"
  done

# ~~ documentation and examples ~~

install -D -t '%{buildroot}%{_pkgdocdir}' -m 0644 -p AUTHORS *.md
cp -rp doc examples '%{buildroot}%{_pkgdocdir}'

%global pythondocdir %{_docdir}/python-grpcio
install -d '%{buildroot}%{pythondocdir}'
cp -rp doc/build '%{buildroot}%{pythondocdir}/html'


%check
# TODO: Run C/C++ test suite.

pushd src/python/grpcio_tests
# Currently fails with
#   ModuleNotFoundError: No module named 'grpc_channelz.v1.channelz_pb2'
# Will look into this if it continues on the latest version.

# See the implementation of the %%pytest macro, upon which our environment
# setup is based:
env \
    CFLAGS="${CFLAGS:-${RPM_OPT_FLAGS}}" \
    LDFLAGS="${LDFLAGS:-${RPM_LD_FLAGS}}" \
    PATH="%{buildroot}%{_bindir}:$PATH" \
    PYTHONPATH="${PYTHONPATH:-%{buildroot}%{python3_sitearch}:%{buildroot}%{python3_sitelib}}" \
    PYTHONDONTWRITEBYTECODE=1 \
    %{__python3} %{py_setup} %{?py_setup_args} test_lite || :
popd


%files
%license LICENSE NOTICE.txt
%{_libdir}/libaddress_sorting.so.%{c_so_version}*
%{_libdir}/libgpr.so.%{c_so_version}*
%{_libdir}/lib%{name}.so.%{c_so_version}*
%{_libdir}/lib%{name}_cronet.so.%{c_so_version}*
%{_libdir}/lib%{name}_unsecure.so.%{c_so_version}*
%{_libdir}/libupb.so.%{c_so_version}*


%files data
%license LICENSE NOTICE.txt
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/roots.pem
# Actually part of ca-certificates dependency:
%exclude %{sysbundle}


%files doc
%license LICENSE NOTICE.txt
%{_pkgdocdir}
# Built Python documentation:
%exclude %{_pkgdocdir}/doc/build
# Python documentation sources:
%exclude %{_pkgdocdir}/doc/python/sphinx


%files cpp
%{_libdir}/lib%{name}++.so.%{cpp_so_version}*
%{_libdir}/lib%{name}++_error_details.so.%{cpp_so_version}*
%{_libdir}/lib%{name}++_reflection.so.%{cpp_so_version}*
%{_libdir}/lib%{name}++_unsecure.so.%{cpp_so_version}*
%{_libdir}/lib%{name}pp_channelz.so.%{cpp_so_version}*


%files cli
%{_bindir}/%{name}_cli


%files plugins
%{_bindir}/%{name}_*_plugin


%files devel
%{_libdir}/libaddress_sorting.so
%{_libdir}/libgpr.so
%{_libdir}/lib%{name}.so
%{_libdir}/lib%{name}_cronet.so
%{_libdir}/lib%{name}_unsecure.so
%{_libdir}/libupb.so
%{_includedir}/%{name}
%{_libdir}/pkgconfig/gpr.pc
%{_libdir}/pkgconfig/%{name}.pc
%{_libdir}/pkgconfig/%{name}_unsecure.pc

%{_libdir}/lib%{name}++.so
%{_libdir}/lib%{name}++_error_details.so
%{_libdir}/lib%{name}++_reflection.so
%{_libdir}/lib%{name}++_unsecure.so
%{_includedir}/%{name}++
%{_libdir}/pkgconfig/%{name}++.pc
%{_libdir}/pkgconfig/%{name}++_unsecure.pc

%{_libdir}/lib%{name}pp_channelz.so
%{_includedir}/%{name}pp


%files -n python3-grpcio
%license LICENSE NOTICE.txt
%{python3_sitearch}/grpc
%{python3_sitearch}/grpcio-%{version}-py%{python3_version}.egg-info


%files -n python3-grpcio-tools
%{python3_sitearch}/grpc_tools
%{python3_sitearch}/grpcio_tools-%{version}-py%{python3_version}.egg-info


%files -n python3-grpcio-channelz
%{python3_sitelib}/grpc_channelz
%{python3_sitelib}/grpcio_channelz-%{version}-py%{python3_version}.egg-info


%files -n python3-grpcio-health-checking
%{python3_sitelib}/grpc_health
%{python3_sitelib}/grpcio_health_checking-%{version}-py%{python3_version}.egg-info


%files -n python3-grpcio-reflection
%{python3_sitelib}/grpc_reflection
%{python3_sitelib}/grpcio_reflection-%{version}-py%{python3_version}.egg-info


%files -n python3-grpcio-status
%{python3_sitelib}/grpc_status
%{python3_sitelib}/grpcio_status-%{version}-py%{python3_version}.egg-info


%files -n python3-grpcio-testing
%{python3_sitelib}/grpc_testing
%{python3_sitelib}/grpcio_testing-%{version}-py%{python3_version}.egg-info


%files -n python-grpcio-doc
%license LICENSE NOTICE.txt
%{pythondocdir}
%exclude %{pythondocdir}/html/.buildinfo
%exclude %{pythondocdir}/html/.doctrees


%changelog
* Tue Feb  2 2021 Benjamin A. Beasley <code@musicinmybrain.net> - 1.26.0-11
- General:
  * Update summaries and descriptions
  * Update License fields to include licenses from bundled components
  * Fix failure to respect Fedora build flags
  * Use the system shared certificate bundle instead of shipping our own
- CLI:
  * No longer set rpath $ORIGIN
- C (core) and C++ (cpp):
  * Add c_so_version/cpp_so_version macros
  * Split out C++ bindings and shared data into subpackages
  * Drop obsolete ldconfig_scriptlets macro
  * Stop stripping debugging symbols
- Python:
  * Use generated BR’s
  * Build and package Python binding documentation
  * Disable accommodations for older libc’s
  * Patch out -std=gnu99 flag, which is inappropriate for C++
  * Build additional Python packages grpcio_tools, gprcio_channelz,
    grpcio_health_checking, grpcio_reflection, grpcio_status, and
    grpcio_testing

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.26.0-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Thu Jan 14 08:46:34 CET 2021 Adrian Reber <adrian@lisas.de> - 1.26.0-9
- Rebuilt for protobuf 3.14

* Fri Nov 13 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 1.26.0-8
- build: disable LTO due to rh#1893533

* Thu Sep 24 2020 Adrian Reber <adrian@lisas.de> - 1.26.0-7
- Rebuilt for protobuf 3.13

* Mon Aug 03 2020 Gwyn Ciesla <gwync@protonmail.com> - 1.26.0-6
- Patches for https://github.com/grpc/grpc/pull/21669

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.26.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Sun Jun 14 2020 Adrian Reber <adrian@lisas.de> - 1.26.0-4
- Rebuilt for protobuf 3.12

* Tue May 26 2020 Miro Hrončok <mhroncok@redhat.com> - 1.26.0-3
- Rebuilt for Python 3.9

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.26.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Wed Jan 15 2020 Sergey Avseyev <sergey.avseyev@gmail.com> - 1.26.0-1
- Update to 1.26.0

* Thu Dec 19 2019 Orion Poplawski <orion@nwra.com> - 1.20.1-5
- Rebuild for protobuf 3.11

* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 1.20.1-4
- Rebuilt for Python 3.8.0rc1 (#1748018)

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 1.20.1-3
- Rebuilt for Python 3.8

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.20.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Fri May 17 2019 Sergey Avseyev <sergey.avseyev@gmail.com> - 1.20.1-1
- Update to 1.20.1

* Fri Feb 01 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.18.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Wed Jan 16 2019 Sergey Avseyev <sergey.avseyev@gmail.com> - 1.18.0-1
- Update to 1.18.0

* Mon Dec 17 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 1.17.1-3
- Properly store patch in SRPM

* Mon Dec 17 2018 Sergey Avseyev <sergey.avseyev@gmail.com> - 1.17.1-2
- Build without ruby plugin for Fedora < 30 (Thanks to Mathieu Bridon)

* Fri Dec 14 2018 Sergey Avseyev <sergey.avseyev@gmail.com> - 1.17.1-1
- Update to 1.17.1 and package python bindings

* Fri Dec 07 2018 Sergey Avseyev <sergey.avseyev@gmail.com> - 1.17.0-1
- Initial revision
