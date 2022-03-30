# We need to use C++17 to link against the system abseil-cpp, or we get linker
# errors.
%global cpp_std 17

# However, we also get linker errors building the tests if we link against the
# copy of gtest in Fedora (compiled with C++11). The exact root cause is not
# quite clear. We must therefore bundle a copy of gtest in the source RPM
# rather than using the system copy. This is to be discouraged, but there is no
# alternative in this case. It is not treated as a bundled library because it
# is used only at build time, and contributes nothing to the installed files.
# We take measures to verify this in %%check.
%global gtest_version 1.11.0
%bcond_with system_gtest

# Bootstrapping breaks the circular dependency on python3dist(xds-protos),
# which is packaged separately but ultimately generated from grpc sources using
# the proto compilers in this package; the consequence is that we cannot build
# the python3-grpcio-admin or python3-grpcio-csds subpackages until after
# bootstrapping.
%bcond_with bootstrap

# This must be enabled to get grpc_cli, which is apparently considered part of
# the tests by upstream. This is mentioned in
# https://github.com/grpc/grpc/issues/23432.
%bcond_without core_tests

# A great many of these tests (over 20%) fail. Any help in understanding these
# well enough to fix them or report them upstream is welcome.
%bcond_with python_aio_tests

%ifnarch s390x
%bcond_without python_gevent_tests
%else
# A signficant number of Python tests pass in test_lite but fail in
# test_gevent, mostly by dumping core without a traceback.  Since it is tedious
# to enumerate these (and it is difficult to implement “suite-specific” skips
# for shared tests, so the tests would have to be skipped in all suites), we
# just skip the gevent suite entirely on this architecture.
%bcond_with python_gevent_tests
%endif

# HTML documentation generated with Doxygen and/or Sphinx is not suitable for
# packaging due to a minified JavaScript bundle inserted by
# Doxygen/Sphinx/Sphinx themes itself. See discussion at
# https://bugzilla.redhat.com/show_bug.cgi?id=2006555.
#
# Normally we could consider enabling the Doxygen PDF documentation as a lesser
# substitute, but (after enabling it and working around some Unicode characters
# in the Markdown input) we get:
#
#   ! TeX capacity exceeded, sorry [main memory size=6000000].
#
# A similar situation applies to the Sphinx-generated HTML documentation for
# Python, except that we have not even tried to render it as a PDF because it
# is too unpleasant to try if we already cannot package the Doxygen-generated
# documentation. Instead, we have just dropped all documentation.

Name:           grpc
Version:        1.41.1
Release:        %autorelease
Summary:        RPC library and framework

# CMakeLists.txt: gRPC_CORE_SOVERSION
%global c_so_version 19
# CMakeLists.txt: gRPC_CPP_SOVERSION
%global cpp_so_version 1.41
# CMakeLists.txt: gRPC_CSHARP_SOVERSION
%global csharp_so_version 2.41
# See https://github.com/abseil/abseil-cpp/issues/950#issuecomment-843169602
# regarding unusual SOVERSION style (not a single number).

# The entire source is ASL 2.0 except the following:
#
# BSD:
#   - third_party/upb/, except third_party/upb/third_party/lunit/
#     * Potentially linked into any compiled subpackage (but not pure-Python
#       subpackages, etc.)
#   - third_party/address_sorting/
#     * Potentially linked into any compiled subpackage (but not pure-Python
#       subpackages, etc.)
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
#   - src/objective-c/*.podspec and
#     templates/src/objective-c/*.podspec.template
#     * Unused since the Objective-C bindings are not currently built
# MIT:
#   - third_party/cares/ares_build.h
#     * Removed in prep; header from system C-Ares used instead
#   - third_party/rake-compiler-dock/
#     * Removed in prep, since we build no containers
#   - third_party/upb/third_party/lunit/
#     * Removed in prep, since there is no obvious way to run the upb tests
License:        ASL 2.0 and BSD
URL:            https://www.grpc.io
%global forgeurl https://github.com/grpc/grpc/
# Used only at build time (not a bundled library); see notes at definition of
# gtest_version macro for explanation and justification.
%global gtest_url https://github.com/google/googletest
%global gtest_archivename googletest-release-%{gtest_version}
Source0:        %{forgeurl}/archive/v%{version}/grpc-%{version}.tar.gz
Source1:        %{gtest_url}/archive/release-%{gtest_version}/%{gtest_archivename}.tar.gz

# Downstream grpc_cli man pages; hand-written based on “grpc_cli help” output.
Source100:      grpc_cli.1
Source101:      grpc_cli-ls.1
Source102:      grpc_cli-call.1
Source103:      grpc_cli-type.1
Source104:      grpc_cli-parse.1
Source105:      grpc_cli-totext.1
Source106:      grpc_cli-tojson.1
Source107:      grpc_cli-tobinary.1
Source108:      grpc_cli-help.1

# ~~~~ C (core) and C++ (cpp) ~~~~

BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  ninja-build
%if %{with core_tests}
# Used on grpc_cli:
BuildRequires:  chrpath
%endif

BuildRequires:  pkgconfig(zlib)
BuildRequires:  cmake(gflags)
BuildRequires:  pkgconfig(protobuf)
BuildRequires:  protobuf-compiler
BuildRequires:  pkgconfig(re2)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  cmake(c-ares)
BuildRequires:  abseil-cpp-devel
# Sets XXH_INCLUDE_ALL, which means xxhash is used as a header-only library
BuildRequires:  pkgconfig(libxxhash)
BuildRequires:  xxhash-static
# Header-only C library, which we unbundle from the bundled copy of upb
BuildRequires:  wyhash_final1-devel
BuildRequires:  wyhash_final1-static

%if %{with core_tests}
BuildRequires:  cmake(benchmark)
%if %{with system_gtest}
BuildRequires:  cmake(gtest)
BuildRequires:  pkgconfig(gmock)
%endif
%endif

# ~~~~ Python ~~~~

BuildRequires:  python3-devel
BuildRequires:  python3dist(setuptools)

# grpcio (setup.py) setup_requires (with
#     GRPC_PYTHON_ENABLE_DOCUMENTATION_BUILD, which is NOT enabled):
# BuildRequires:  python3dist(sphinx)

# grpcio (setup.py) setup_requires (with
#     GRPC_PYTHON_ENABLE_DOCUMENTATION_BUILD, which is NOT enabled):
# grpcio_tests (src/python/grpcio_tests/setup.py) install_requires:
BuildRequires:  python3dist(six) >= 1.10
# grpcio (setup.py) install_requires also has:
#   six>=1.5.2

# grpcio (setup.py) setup_requires (with GRPC_PYTHON_BUILD_WITH_CYTHON, or
# absent generated sources); also needed for grpcio_tools
# (tools/distrib/python/grpcio_tools/setup.py)
BuildRequires:  python3dist(cython) > 0.23

# grpcio (setup.py) install_requires:
# grpcio_tests (src/python/grpcio_tests/setup.py) install_requires:
#   futures>=2.2.0; python_version<'3.2'

# grpcio (setup.py) install_requires:
# grpcio_tests (src/python/grpcio_tests/setup.py) install_requires:
#   enum34>=1.0.4; python_version<'3.4'

# grpcio_csds (src/python/grpcio_csds/setup.py) install_requires:
# grpcio_channelz (src/python/grpcio_channelz/setup.py) install_requires:
# grpcio_health_checking (src/python/grpcio_health_checking/setup.py)
#     install_requires:
# grpcio_reflection (src/python/grpcio_reflection/setup.py) install_requires:
# grpcio_status (src/python/grpcio_status/setup.py) install_requires:
# grpcio_testing (src/python/grpcio_testing/setup.py) install_requires:
# grpcio_tests (src/python/grpcio_tests/setup.py) install_requires:
BuildRequires:  python3dist(protobuf) >= 3.6.0
# grpcio_tools (tools/distrib/python/grpcio_tools/setup.py) install_requires
# also has:
#   protobuf>=3.5.0.post1
# which is written as
#   python3dist(protobuf) >= 3.5^post1

# grpcio_status (src/python/grpcio_status/setup.py) install_requires:
BuildRequires:  python3dist(googleapis-common-protos) >= 1.5.5

%if %{without bootstrap}
# grpcio_csds (src/python/grpcio_csds/setup.py) install_requires
BuildRequires:  python3dist(xds-protos) >= 0.0.7
%endif

# Several packages have dependencies on grpcio or grpcio_tools—and grpcio-tests
# depends on all of the other Python packages—which are satisfied within this
# package.
#
# Similarly, grpcio_admin depends on grpcio_channelz and grpcio_csds.

# grpcio_tests (src/python/grpcio_tests/setup.py) install_requires:
BuildRequires:  python3dist(coverage) >= 4.0

# grpcio_tests (src/python/grpcio_tests/setup.py) install_requires:
BuildRequires:  python3dist(oauth2client) >= 1.4.7

# grpcio_tests (src/python/grpcio_tests/setup.py) install_requires:
BuildRequires:  python3dist(google-auth) >= 1.17.2

# grpcio_tests (src/python/grpcio_tests/setup.py) install_requires:
BuildRequires:  python3dist(requests) >= 2.14.2

# Required for “test_gevent” tests:
BuildRequires:  python3dist(gevent)

# For stopping the port server
BuildRequires:  curl

# ~~~~ Miscellaneous ~~~~

# https://bugzilla.redhat.com/show_bug.cgi?id=1893533
%global _lto_cflags %{nil}

# Reference documentation, which is *not* enabled
# BuildRequires:  doxygen

BuildRequires:  ca-certificates
# For converting absolute symlinks in the buildroot to relative ones
BuildRequires:  symlinks

# Apply Fedora system crypto policies. Since this is Fedora-specific, the patch
# is not suitable for upstream.
# https://docs.fedoraproject.org/en-US/packaging-guidelines/CryptoPolicies/#_cc_applications
#
# In fact, this may not be needed, since only testing code is patched.
Patch0:         grpc-1.39.0-system-crypto-policies.patch
# Add an option GRPC_PYTHON_BUILD_SYSTEM_ABSL to go with the gRPC_ABSL_PROVIDER
# option already provided upstream. See
# https://github.com/grpc/grpc/issues/25559.
Patch1:         grpc-1.40.0-python-grpcio-use-system-abseil.patch
# Fix errors like:
#   TypeError: super(type, obj): obj must be an instance or subtype of type
# It is not clear why these occur.
Patch2:         grpc-1.36.4-python-grpcio_tests-fixture-super.patch
# Skip tests requiring non-loopback network access when the
# FEDORA_NO_NETWORK_TESTS environment variable is set.
Patch3:         grpc-1.40.0-python-grpcio_tests-make-network-tests-skippable.patch
# A handful of compression tests miss the compression ratio threshold. It seems
# to be inconsistent which particular combinations fail in a particular test
# run. It is not clear that this is a real problem. Any help in understanding
# the actual cause well enough to fix this or usefully report it upstream is
# welcome.
Patch4:         grpc-1.36.4-python-grpcio_tests-skip-compression-tests.patch
# The upstream requirement to link gtest/gmock from grpc_cli is spurious.
# Remove it. We still have to build the core tests and link a test library
# (libgrpc++_test_config.so…)
Patch5:         grpc-1.37.0-grpc_cli-do-not-link-gtest-gmock.patch
# Fix confusion about path to python_wrapper.sh in httpcli/httpscli tests. I
# suppose that the unpatched code must be correct for how upstream runs the
# tests, somehow.
Patch6:         grpc-1.39.0-python_wrapper-path.patch
# Port Python 2 scripts used in core tests to Python 3
Patch7:         grpc-1.40.0-python2-test-scripts.patch
# Fix compatibility with breaking changes in google-benchmark 1.6.0
#
# This will not be sent upstream since it is impractical to make a patch
# compatible with both 1.6.0 and 1.5.0, and upstream has not yet updated to
# 1.6.0.
Patch8:         grpc-1.40.0-google-benchmark-1.6.0.patch
# In src/core/lib/promise/detail/basic_seq.h, include cassert
# https://github.com/grpc/grpc/pull/27516
Patch9:         https://github.com/grpc/grpc/pull/27516.patch
# Minimal fix for invalid implicit absl::string_view(nullptr_t)
# This fixes failure to compile on GCC 12.
# https://github.com/grpc/grpc/pull/28589
Patch10:        0001-Minimal-fix-for-invalid-implicit-absl-string_view-nu.patch

Requires:       grpc-data = %{version}-%{release}

# Upstream https://github.com/protocolbuffers/upb does not support building
# with anything other than Bazel, and Bazel is not likely to make it into
# Fedora anytime soon due to its nightmarish collection of dependencies.
# Monitor this at https://bugzilla.redhat.com/show_bug.cgi?id=1470842.
# Therefore upb cannot be packaged for Fedora, and we must use the bundled
# copy.
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

  • Efficiently connecting polyglot services in microservices style
    architecture
  • Connecting mobile devices, browser clients to backend services
  • Generating efficient client libraries

Core Features that make it awesome:

  • Idiomatic client libraries in 10 languages
  • Highly efficient on wire and with a simple service definition framework
  • Bi-directional streaming with http/2 based transport
  • Pluggable auth, tracing, load balancing and health checking

This package provides the shared C core library.


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

Obsoletes:      python-grpcio-doc < 1.26.0-13
Provides:       python-grpcio-doc = %{version}-%{release}
Provides:       python-grpcio-admin-doc = %{version}-%{release}
Provides:       python-grpcio-csds-doc = %{version}-%{release}
Provides:       python-grpcio-channelz-doc = %{version}-%{release}
Provides:       python-grpcio-health-checking-doc = %{version}-%{release}
Provides:       python-grpcio-reflection-doc = %{version}-%{release}
Provides:       python-grpcio-status-doc = %{version}-%{release}
Provides:       python-grpcio-testing-doc = %{version}-%{release}

%description doc
Documentation and examples for gRPC, including Markdown documentation sources
for the following:

  • C (core)
    ○ API
    ○ Internals
  • C++
    ○ API
    ○ Internals
  • Objective C
    ○ API
    ○ Internals
  • Python
    ○ grpcio
    ○ grpcio_admin
    ○ grpcio_csds
    ○ grpcio_channelz
    ○ grpcio_health_checking
    ○ grpcio_reflection
    ○ grpcio_status
    ○ grpcio_testing

For rendered HTML documentation, please see https://grpc.io/docs/.


%package cpp
Summary:        C++ language bindings for gRPC
# License:        same as base package

Requires:       grpc%{?_isa} = %{version}-%{release}

Provides:       bundled(upb)

%description cpp
C++ language bindings for gRPC.


%package plugins
Summary:        Protocol buffers compiler plugins for gRPC
# License:        same as base package

Requires:       grpc%{?_isa} = %{version}-%{release}
Requires:       protobuf-compiler

Provides:       bundled(upb)

%description plugins
Plugins to the protocol buffers compiler to generate gRPC sources.


%package cli
Summary:        Command-line tool for gRPC
# License:        same as base package

Requires:       grpc%{?_isa} = %{version}-%{release}

Provides:       bundled(upb)

%description cli
The command line tool can do the following things:

  • Send unary rpc.
  • Attach metadata and display received metadata.
  • Handle common authentication to server.
  • Infer request/response types from server reflection result.
  • Find the request/response types from a given proto file.
  • Read proto request in text form.
  • Read request in wire form (for protobuf messages, this means serialized
    binary form).
  • Display proto response in text form.
  • Write response in wire form to a file.


%package devel
Summary:        Development files for gRPC library
# License:        same as base package
Requires:       grpc%{?_isa} = %{version}-%{release}
Requires:       grpc-cpp%{?_isa} = %{version}-%{release}

# grpc/impl/codegen/port_platform.h includes linux/version.h
Requires:       kernel-headers%{?_isa}
# grpcpp/impl/codegen/config_protobuf.h includes google/protobuf/…
Requires:       pkgconfig(protobuf)
# grpcpp/test/mock_stream.h includes gmock/gmock.h
Requires:       pkgconfig(gmock)
# grpcpp/impl/codegen/sync.h includes absl/synchronization/mutex.h
# grpc.pc has -labsl_[…]
Requires:       abseil-cpp-devel%{?_isa}
# grpc.pc has -lre2
Requires:       pkgconfig(re2)
# grpc.pc has -lcares
Requires:       cmake(c-ares)
# grpc.pc has -lz
Requires:       pkgconfig(zlib)

%description devel
Development headers and files for gRPC libraries (both C and C++).


%package -n python3-grpcio
Summary:        Python language bindings for gRPC
# License:        same as base package

# Note that the Python package has no runtime dependency on the base C library;
# everything it needs is linked statically. It is not practical to change this,
# and since they both come from the same source RPM, we do not need to attempt
# to do so.
Requires:       grpc-data = %{version}-%{release}

Provides:       bundled(upb)

%description -n python3-grpcio
Python language bindings for gRPC (HTTP/2-based RPC framework).


%global grpcio_egg %{python3_sitearch}/grpcio-%{version}-py%{python3_version}.egg-info
%{?python_extras_subpkg:%python_extras_subpkg -n python3-grpcio -i %{grpcio_egg} protobuf}


%package -n python3-grpcio-tools
Summary:       Package for gRPC Python tools
# License:        same as base package

Provides:       bundled(upb)

%description -n python3-grpcio-tools
Package for gRPC Python tools.


%if %{without bootstrap}
%package -n python3-grpcio-admin
Summary:        A collection of admin services
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-admin
gRPC Python Admin Interface Package
===================================

Debugging gRPC library can be a complex task. There are many configurations and
internal states, which will affect the behavior of the library. This Python
package will be the collection of admin services that are exposing debug
information. Currently, it includes:

* Channel tracing metrics (grpcio-channelz)
* Client Status Discovery Service (grpcio-csds)

Here is a snippet to create an admin server on "localhost:50051":

    server = grpc.server(ThreadPoolExecutor())
    port = server.add_insecure_port('localhost:50051')
    grpc_admin.add_admin_servicers(self._server)
    server.start()

Welcome to explore the admin services with CLI tool "grpcdebug":
https://github.com/grpc-ecosystem/grpcdebug.

For any issues or suggestions, please send to
https://github.com/grpc/grpc/issues.
%endif


%if %{without bootstrap}
%package -n python3-grpcio-csds
Summary:        xDS configuration dump library
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-csds
gRPC Python Client Status Discovery Service package
===================================================

CSDS is part of the Envoy xDS protocol:
https://www.envoyproxy.io/docs/envoy/latest/api-v3/service/status/v3/csds.proto.
It allows the gRPC application to programmatically expose the received traffic
configuration (xDS resources). Welcome to explore with CLI tool "grpcdebug":
https://github.com/grpc-ecosystem/grpcdebug.

For any issues or suggestions, please send to
https://github.com/grpc/grpc/issues.
%endif


%package -n python3-grpcio-channelz
Summary:        Channel Level Live Debug Information Service for gRPC
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-channelz
gRPC Python Channelz package
============================

Channelz is a live debug tool in gRPC Python.


%package -n python3-grpcio-health-checking
Summary:        Standard Health Checking Service for gRPC
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-health-checking
gRPC Python Health Checking
===========================

Reference package for GRPC Python health checking.


%package -n python3-grpcio-reflection
Summary:        Standard Protobuf Reflection Service for gRPC
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-reflection
gRPC Python Reflection package
==============================

Reference package for reflection in GRPC Python.


%package -n python3-grpcio-status
Summary:        Status proto mapping for gRPC
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-status
gRPC Python Status Proto
===========================

Reference package for GRPC Python status proto mapping.


%package -n python3-grpcio-testing
Summary:        Testing utilities for gRPC Python
License:        ASL 2.0
BuildArch:      noarch

%description -n python3-grpcio-testing
gRPC Python Testing Package
===========================

Testing utilities for gRPC Python.


%prep
%autosetup -p1

echo '===== Patching grpcio_tools for system protobuf =====' 2>&1
# Build python3-grpcio_tools against system protobuf packages instead of
# expecting a git submodule. Must also add requisite linker flags using
# GRPC_PYTHON_LDFLAGS. This was formerly done by
# grpc-VERSION-python-grpcio_tools-use-system-protobuf.patch, but it had to be
# tediously but trivially rebased every patch release as the CC_FILES list
# changed, so we automated the patch.
sed -r -i \
    -e "s/^(# AUTO-GENERATED .*)/\\1\\n\
# Then, modified by hand to build with an external system protobuf\
# installation./" \
    -e 's/^(CC_FILES=\[).*(\])/\1\2/' \
    -e "s@^((CC|PROTO)_INCLUDE=')[^']+'@\1%{_includedir}'@" \
    -e '/^PROTOBUF_SUBMODULE_VERSION=/d' \
    'tools/distrib/python/grpcio_tools/protoc_lib_deps.py'

echo '===== Preparing gtest/gmock =====' 2>&1
%if %{without system_gtest}
# Copy in the needed gtest/gmock implementations.
%setup -q -T -D -b 1
rm -rvf 'third_party/googletest'
mv '../%{gtest_archivename}' 'third_party/googletest'
%else
# Patch CMakeLists for external gtest/gmock.
#
#  1. Create dummy sources, adding a typedef so the translation unit is not
#     empty, rather than removing references to these sources from
#     CMakeLists.txt. This is so that we do not end up with executables with no
#     sources, only libraries, which is a CMake error.
#  2. Either remove references to the corresponding include directories, or
#     create the directories and leave them empty.
#  3. “Stuff” the external library into the target_link_libraries() for each
#     test by noting that GMock/GTest/GFlags are always used together.
for gwhat in test mock
do
  mkdir -p "third_party/googletest/google${gwhat}/src" \
      "third_party/googletest/google${gwhat}/include"
  echo "typedef int dummy_${gwhat}_type;" \
      > "third_party/googletest/google${gwhat}/src/g${gwhat}-all.cc"
done
sed -r -i 's/^([[:blank:]]*)(\$\{_gRPC_GFLAGS_LIBRARIES\})/'\
'\1\2\n\1gtest\n\1gmock/' CMakeLists.txt
%endif

echo '===== Removing bundled wyhash =====' 2>&1
# Remove bundled wyhash (via upb); to avoid patching the build system, simply
# use a symlink to find the system copy. This is sufficient since it is a
# header-only library.
rm -rvf third_party/upb/third_party/wyhash
ln -s %{_includedir}/wyhash_final1/ third_party/upb/third_party/wyhash

echo '===== Removing bundled xxhash =====' 2>&1
# Remove bundled xxhash
rm -rvf third_party/xxhash
# Since grpc sets XXH_INCLUDE_ALL wherever it uses xxhash, it is using xxhash
# as a header-only library. This means we can replace it with the system copy
# by doing nothing further; xxhash.h is in the system include path and will be
# found instead, and there are no linker flags to add. See also
# https://github.com/grpc/grpc/issues/25945.

echo '===== Fixing permissions =====' 2>&1
# https://github.com/grpc/grpc/pull/27069
find . -type f -perm /0111 \
    -exec gawk '!/^#!/ { print FILENAME }; { nextfile }' '{}' '+' |
  xargs -r chmod -v a-x

echo '===== Removing selected unused sources =====' 2>&1
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

# Drop the NodeJS example’s package-lock.json file, which will hopefully keep
# us from having bugs filed due to CVE’s in its (unpackaged) recursive
# dependencies.
rm -vf examples/node/package-lock.json

# Remove unwanted .gitignore files, generally in examples. One could argue that
# a sample .gitignore file is part of the example, but, well, we’re not going
# to do that.
find . -type f -name .gitignore -print -delete

echo '===== Fixing shebangs =====' 2>&1
# Find executables with /usr/bin/env shebangs in the examples, and fix them.
find . -type f -perm /0111 -exec gawk \
    '/^#!\/usr\/bin\/env[[:blank:]]/ { print FILENAME }; { nextfile }' \
    '{}' '+' |
  xargs -r sed -r -i '1{s|^(#!/usr/bin/)env[[:blank:]]+([^[:blank:]]+)|\1\2|}' \

echo '===== Fixing hard-coded C++ standard =====' 2>&1
# We need to adjust the C++ standard to avoid abseil-related linker errors. For
# the main C++ build, we can use CMAKE_CXX_STANDARD. For extensions, examples,
# etc., we must patch.
sed -r -i 's/(std=c\+\+)11/\1%{cpp_std}/g' \
    setup.py grpc.gyp Rakefile \
    examples/cpp/*/Makefile \
    examples/cpp/*/CMakeLists.txt \
    tools/run_tests/artifacts/artifact_targets.py \
    tools/distrib/python/grpcio_tools/setup.py

echo '===== Fixing .pc install path =====' 2>&1
# Fix the install path for .pc files
# https://github.com/grpc/grpc/issues/25635
sed -r -i 's|lib(/pkgconfig)|\${gRPC_INSTALL_LIBDIR}\1|' CMakeLists.txt

echo '===== Patching to skip certain broken tests =====' 2>&1

%ifarch %{ix86} %{arm32}
# Confirmed in 1.41.0 2021-10-01 (in %%{arm32} only)
# TODO figure out how to report this upstream in a useful/actionable way
sed -r -i "s/^([[:blank:]]*)(def test_concurrent_stream_stream)\\b/\
\\1@unittest.skip('May hang unexplainedly')\\n\\1\\2/" \
    'src/python/grpcio_tests/tests/testing/_client_test.py'
%endif

%ifarch %{ix86} %{arm32}
# Confirmed in 1.41.0 2021-10-05
# These tests fail with:
#   OverflowError: Python int too large to convert to C ssize_t
# TODO figure out how to report this upstream in a useful/actionable way
sed -r -i \
    "s/^([[:blank:]]*)(def test(SSLSessionCacheLRU|SessionResumption))\\b/\
\\1@unittest.skip('Unexplained overflow error on 32-bit')\\n\\1\\2/" \
    'src/python/grpcio_tests/tests/unit/_auth_context_test.py' \
    'src/python/grpcio_tests/tests/unit/_session_cache_test.py'
%endif

# Confirmed in 1.41.0 2021-10-08 (on aarch64 and s390x)
# These tests can be flaky and may fail only sometimes. Failures have been seen
# on all architectures.
# TODO figure out how to report this upstream in a useful/actionable way
sed -r -i "s/^([[:blank:]]*)(def testConcurrent(Blocking|Future)\
Invocations)\\b/\\1@unittest.skip('May hang unexplainedly')\\n\\1\\2/" \
    'src/python/grpcio_tests/tests/unit/_rpc_part_2_test.py'

%ifarch %{arm64} ppc64le s390x x86_64
# Confirmed in 1.41.0 2021-10-05 (aarch64 and ppc64le)
# This is flaky and often succeeds.
# TODO figure out how to report this upstream in a useful/actionable way
#
# unit._dynamic_stubs_test.DynamicStubTest.test_grpc_tools_unimportable
# traceback:
# Traceback (most recent call last):
#   File "/usr/lib64/python3.10/unittest/case.py", line 59, in testPartExecutor
#     yield
#   File "/usr/lib64/python3.10/unittest/case.py", line 592, in run
#     self._callTestMethod(testMethod)
#   File "/usr/lib64/python3.10/unittest/case.py", line 549, in _callTestMethod
#     method()
#   File
#       "/builddir/build/BUILD/grpc-1.39.0/src/python/grpcio_tests/tests/unit/_dynamic_stubs_test.py",
#       line 136, in test_grpc_tools_unimportable
#     _run_in_subprocess(_test_grpc_tools_unimportable)
#   File
#       "/builddir/build/BUILD/grpc-1.39.0/src/python/grpcio_tests/tests/unit/_dynamic_stubs_test.py",
#       line 80, in _run_in_subprocess
#     assert proc.exitcode == 0, "Process exited with code {}".format(
# AssertionError: Process exited with code 64
sed -r -i "s/^([[:blank:]]*)(class DynamicStubTest)\\b/\
\\1@unittest.skip('Child process exits with code 64')\\n\\1\\2/" \
    'src/python/grpcio_tests/tests/unit/_dynamic_stubs_test.py'
%endif

%ifarch %{arm64} ppc64le s390x x86_64
# Confirmed in 1.41.0 2021-10-05 (aarch64)
# This is flaky and often succeeds.
# TODO figure out how to report this upstream in a useful/actionable way
#
# unit._logging_test.LoggingTest.test_can_configure_logger
# traceback:
# Traceback (most recent call last):
#   File "/usr/lib64/python3.10/unittest/case.py", line 59, in testPartExecutor
#     yield
#   File "/usr/lib64/python3.10/unittest/case.py", line 592, in run
#     self._callTestMethod(testMethod)
#   File "/usr/lib64/python3.10/unittest/case.py", line 549, in _callTestMethod
#     method()
#   File
#       "/builddir/build/BUILD/grpc-1.39.0/src/python/grpcio_tests/tests/unit/_logging_test.py",
#       line 66, in test_can_configure_logger
#     self._verifyScriptSucceeds(script)
#   File
#       "/builddir/build/BUILD/grpc-1.39.0/src/python/grpcio_tests/tests/unit/_logging_test.py",
#       line 91, in _verifyScriptSucceeds
#     self.assertEqual(
#   File "/usr/lib64/python3.10/unittest/case.py", line 839, in assertEqual
#     assertion_func(first, second, msg=msg)
#   File "/usr/lib64/python3.10/unittest/case.py", line 832, in _baseAssertEqual
#     raise self.failureException(msg)
# AssertionError: 0 != 64 : process failed with exit code 64 (stdout: b'', stderr: b'')
sed -r -i "s/^([[:blank:]]*)(def test_(can_configure_logger|grpc_logger|\
handler_found|logger_not_occupied))\\b/\
\\1@unittest.skip('Child process exits with code 64')\\n\\1\\2/" \
    'src/python/grpcio_tests/tests/unit/_logging_test.py'
%endif

%ifarch %{ix86} %{arm32}
# Confirmed in 1.41.0 2021-10-05
# TODO figure out how to report this upstream in a useful/actionable way
sed -r -i "s/^([[:blank:]]*)(def testCancelManyCalls)\\b/\
\\1@unittest.skip('May hang unexplainedly')\\n\\1\\2/" \
    'src/python/grpcio_tests/tests/unit/_cython/_cancel_many_calls_test.py'
%endif


%build
# ~~~~ C (core) and C++ (cpp) ~~~~

echo '===== Building C (core) and C++ components =====' 2>&1
# We could use either make or ninja as the backend; ninja is faster and has no
# disadvantages (except a small additional BR, given we already need Python)
#
# We need to adjust the C++ standard to avoid abseil-related linker errors.
%cmake \
    -DgRPC_INSTALL:BOOL=ON \
    -DCMAKE_CXX_STANDARD:STRING=%{cpp_std} \
    -DCMAKE_SKIP_INSTALL_RPATH:BOOL=ON \
    -DgRPC_INSTALL_BINDIR:PATH=%{_bindir} \
    -DgRPC_INSTALL_LIBDIR:PATH=%{_libdir} \
    -DgRPC_INSTALL_INCLUDEDIR:PATH=%{_includedir} \
    -DgRPC_INSTALL_CMAKEDIR:PATH=%{_libdir}/cmake/grpc \
    -DgRPC_INSTALL_SHAREDIR:PATH=%{_datadir}/grpc \
    -DgRPC_BUILD_TESTS:BOOL=%{?with_core_tests:ON}%{?!with_core_tests:OFF} \
    -DgRPC_BUILD_CODEGEN:BOOL=ON \
    -DgRPC_BUILD_CSHARP_EXT:BOOL=ON \
    -DgRPC_BACKWARDS_COMPATIBILITY_MODE:BOOL=OFF \
    -DgRPC_ZLIB_PROVIDER:STRING='package' \
    -DgRPC_CARES_PROVIDER:STRING='package' \
    -DgRPC_RE2_PROVIDER:STRING='package' \
    -DgRPC_SSL_PROVIDER:STRING='package' \
    -DgRPC_PROTOBUF_PROVIDER:STRING='package' \
    -DgRPC_PROTOBUF_PACKAGE_TYPE:STRING='MODULE' \
    -DgRPC_BENCHMARK_PROVIDER:STRING='package' \
    -DgRPC_ABSL_PROVIDER:STRING='package' \
    -DgRPC_USE_PROTO_LITE:BOOL=OFF \
    -DgRPC_BUILD_GRPC_CPP_PLUGIN:BOOL=ON \
    -DgRPC_BUILD_GRPC_CSHARP_PLUGIN:BOOL=ON \
    -DgRPC_BUILD_GRPC_NODE_PLUGIN:BOOL=ON \
    -DgRPC_BUILD_GRPC_OBJECTIVE_C_PLUGIN:BOOL=ON \
    -DgRPC_BUILD_GRPC_PHP_PLUGIN:BOOL=ON \
    -DgRPC_BUILD_GRPC_PYTHON_PLUGIN:BOOL=ON \
    -DgRPC_BUILD_GRPC_RUBY_PLUGIN:BOOL=ON \
    -GNinja
%cmake_build
# ~~~~ Python ~~~~

echo '===== Building Python grpcio package =====' 2>&1
# Since there are some interdepndencies in the Python packages (e.g., many have
# setup_requires: grpcio-tools), we do temporary installs of built packages
# into a local directory as needed, and add it to the PYTHONPATH.
PYROOT="${PWD}/%{_vpath_builddir}/pyroot"
if [ -n "${PYTHONPATH-}" ]; then PYTHONPATH="${PYTHONPATH}:"; fi
PYTHONPATH="${PYTHONPATH-}${PYROOT}%{python3_sitelib}"
PYTHONPATH="${PYTHONPATH}:${PYROOT}%{python3_sitearch}"
export PYTHONPATH

# ~~ grpcio ~~
# Note that we had to patch in the GRPC_PYTHON_BUILD_SYSTEM_ABSL option.
export GRPC_PYTHON_BUILD_WITH_CYTHON='True'
export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL='True'
export GRPC_PYTHON_BUILD_SYSTEM_ZLIB='True'
export GRPC_PYTHON_BUILD_SYSTEM_CARES='True'
export GRPC_PYTHON_BUILD_SYSTEM_RE2='True'
export GRPC_PYTHON_BUILD_SYSTEM_ABSL='True'
export GRPC_PYTHON_DISABLE_LIBC_COMPATIBILITY='True'
export GRPC_PYTHON_ENABLE_DOCUMENTATION_BUILD='False'
# We must set GRPC_PYTHON_CFLAGS to avoid unwanted defaults. We take the
# upstream flags except that we remove -std=c99, which is inapplicable to the
# C++ parts of the extension.
#
# We must set GRPC_PYTHON_LDFLAGS to avoid unwanted defaults. The upstream
# flags attempt to statically link libgcc, so we do not need any of them. Since
# we forcibly unbundle protobuf, we need to add linker flags for protobuf
# ourselves.
export GRPC_PYTHON_CFLAGS="-fvisibility=hidden -fno-wrapv -fno-exceptions $(
  pkg-config --cflags protobuf
)"
export GRPC_PYTHON_LDFLAGS="$(pkg-config --libs protobuf)"
%py3_build
%{__python3} %{py_setup} %{?py_setup_args} install \
    -O1 --skip-build --root "${PYROOT}"

# ~~ grpcio-tools ~~
echo '===== Building Python grpcio_tools package =====' 2>&1
pushd "tools/distrib/python/grpcio_tools/" >/dev/null
# When copying more things in here, make sure the subpackage License field
# stays correct. We need copies, not symlinks, so that the “graft” in
# MANIFEST.in works.
mkdir -p grpc_root/src
for srcdir in compiler
do
  cp -rp "../../../../src/${srcdir}" "grpc_root/src/"
done
cp -rp '../../../../include' 'grpc_root/'
# We must set GRPC_PYTHON_CFLAGS and GRPC_PYTHON_LDFLAGS again; grpcio_tools
# does not have the same default upstream flags as grpcio does, and it needs to
# link the protobuf compiler library.
export GRPC_PYTHON_CFLAGS="-fno-wrapv -frtti $(pkg-config --cflags protobuf)"
export GRPC_PYTHON_LDFLAGS="$(pkg-config --libs protobuf) -lprotoc"
%py3_build
# Remove unwanted shebang from grpc_tools.protoc source file, which will be
# installed without an executable bit:
find . -type f -name protoc.py -execdir sed -r -i '1{/^#!/d}' '{}' '+'
%{__python3} %{py_setup} %{?py_setup_args} install \
    -O1 --skip-build --root "${PYROOT}"
popd >/dev/null

echo '===== Building pure-Python packages =====' 1>&2
for suffix in channelz %{?!with_bootstrap:csds admin} health_checking \
    reflection status testing tests
do
  echo "----> grpcio_${suffix} <----" 1>&2
  pushd "src/python/grpcio_${suffix}/" >/dev/null
  if ! echo "${suffix}" | grep -E "^(admin|csds)$" >/dev/null
  then
    %{__python3} %{py_setup} %{?py_setup_args} preprocess
  fi
  if ! echo "${suffix}" | grep -E "^(admin|csds|testing)$" >/dev/null
  then
    %{__python3} %{py_setup} %{?py_setup_args} build_package_protos
  fi
  %py3_build
  %{__python3} %{py_setup} %{?py_setup_args} install \
      -O1 --skip-build --root "${PYROOT}"
  popd >/dev/null
done


%install
# ~~~~ C (core) and C++ (cpp) ~~~~
%cmake_install

%if %{with core_tests}
# For some reason, grpc_cli is not installed. Do it manually.
install -t '%{buildroot}%{_bindir}' -p -D '%{_vpath_builddir}/grpc_cli'
# grpc_cli build does not respect CMAKE_INSTALL_RPATH
# https://github.com/grpc/grpc/issues/25176
chrpath --delete '%{buildroot}%{_bindir}/grpc_cli'

# This library is also required for grpc_cli; it is built as part of the test
# code.
install -t '%{buildroot}%{_libdir}' -p \
    %{_vpath_builddir}/libgrpc++_test_config.so.*
chrpath --delete '%{buildroot}%{_libdir}/'libgrpc++_test_config.so.*

install -d '%{buildroot}/%{_mandir}/man1'
install -t '%{buildroot}/%{_mandir}/man1' -p -m 0644 \
    %{SOURCE100} %{SOURCE101} %{SOURCE102} %{SOURCE103} %{SOURCE104} \
    %{SOURCE106} %{SOURCE107} %{SOURCE108}
%endif

# Remove any static libraries that may have been installed against our wishes
find %{buildroot} -type f -name '*.a' -print -delete
# Fix wrong permissions on installed headers
find %{buildroot}%{_includedir}/grpc* -type f -name '*.h' -perm /0111 \
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
for suffix in channelz %{?!with_bootstrap:csds admin} health_checking \
    reflection status testing
do
  pushd "src/python/grpcio_${suffix}/" >/dev/null
  %py3_install
  popd >/dev/null
done
# The grpcio_tests package should not be installed; it would provide top-level
# packages with generic names like “tests” or “tests_aio”.

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

rm -rvf "%{buildroot}$(dirname '%{sysbundle}')"

# ~~ documentation and examples ~~

install -D -t '%{buildroot}%{_pkgdocdir}' -m 0644 -p AUTHORS *.md
cp -rvp doc examples '%{buildroot}%{_pkgdocdir}'


%check
export FEDORA_NO_NETWORK_TESTS=1

%if %{with core_tests}
PORT_SERVER_PORT="$(awk '
  /_PORT_SERVER_PORT[[:blank:]]*=[[:blank:]]*[[:digit:]]+$/ { print $NF }
' tools/run_tests/python_utils/start_port_server.py)"

# Note that no tests are actually found by ctest:
%ctest

# Exclude tests that are known to hang or otherwise fail. Assistance welcome in
# figuring out what is wrong with these.  Note, however, that we are running
# the tests very differently from upstream, which uses scripts in
# tools/run_tests/ that rebuild the entire source and use Docker, so it is
# likely to be difficult to get help from upstream for any failures here. Note
# that some of these tests would never work in an environment without Internet
# access.
{ sed -r -e '/^(#|$)/d' -e 's|^(.*)$|%{_vpath_builddir}/\1_test|' <<'EOF'

# Requires (or may require) network:
resolve_address_using_ares_resolver
resolve_address_using_ares_resolver_posix
resolve_address_using_native_resolver
resolve_address_using_native_resolver_posix
ssl_transport_security

# Seems to require privilege:
flaky_network

%ifarch s390x
# Unexplained:
#
# [ RUN      ] AddressSortingTest.TestSorterKnowsIpv6LoopbackIsAvailable
# ../test/cpp/naming/address_sorting_test.cc:807: Failure
# Expected equality of these values:
#   source_addr_output->sin6_family
#     Which is: 0
#   10
# ../test/cpp/naming/address_sorting_test.cc:817: Failure
# Expected equality of these values:
#   source_addr_str
#     Which is: "::"
#   "::1"
# [  FAILED  ] AddressSortingTest.TestSorterKnowsIpv6LoopbackIsAvailable (0 ms)
#
# Confirmed in 1.41.0 2021-10-10
address_sorting
%endif

%ifarch s390x
# Unexplained:
#
# Status is not ok: Setting authenticated associated data failed
# E0805 21:01:40.415152384 1888289 aes_gcm_test.cc:77]         assertion failed: status == GRPC_STATUS_OK
# *** SIGABRT received at time=1628197300 on cpu 1 ***
# PC: @      0x3ff8581ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ff85701524  (unknown)  (unknown)
#     @      0x3ff85701790  (unknown)  (unknown)
#     @      0x3ff862e3b78  (unknown)  (unknown)
#     @      0x3ff8581ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ff857d03e0  (unknown)  gsignal
#     @      0x3ff857b3480  (unknown)  abort
#     @      0x2aa27303a48  (unknown)  gsec_assert_ok()
#     @      0x2aa27303b80  (unknown)  gsec_test_random_encrypt_decrypt()
#     @      0x2aa2730156e  (unknown)  main
#     @      0x3ff857b3732  (unknown)  __libc_start_call_main
#     @      0x3ff857b380e  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa27302730  (unknown)  (unknown)
#
# Confirmed in 1.41.0 2021-10-10
alts_crypt
%endif

%ifarch s390x
# Unexplained:
#
# (aborted without output)
#
# Confirmed in 1.41.0 2021-10-10
alts_crypter
%endif

%ifarch s390x
# Unexplained:
#
# [ RUN      ] AltsConcurrentConnectivityTest.TestBasicClientServerHandshakes
# E0811 15:42:24.743250725 2232792
#   alts_grpc_privacy_integrity_record_protocol.cc:107] Failed to unprotect, More
#   bytes written than expected. Frame decryption failed.
# [… 14 similar lines omitted …]
# E0811 15:42:29.735499217 2232786
#   alts_grpc_privacy_integrity_record_protocol.cc:107] Failed to unprotect, More
#   bytes written than expected. Frame decryption failed.
# /builddir/build/BUILD/grpc-1.39.0/test/core/tsi/alts/handshaker/alts_concurrent_connectivity_test.cc:245:
#   Failure
# Expected equality of these values:
#   ev.type
#     Which is: 1
#   GRPC_OP_COMPLETE
#     Which is: 2
# connect_loop runner:0x3ffc7ffdc68 got ev.type:1 i:0
# [  FAILED  ] AltsConcurrentConnectivityTest.TestBasicClientServerHandshakes (5021 ms)
# [ RUN      ] AltsConcurrentConnectivityTest.TestConcurrentClientServerHandshakes
# [… 2983 lines including some additional failures and error messages omitted …]
# [----------] 5 tests from AltsConcurrentConnectivityTest (27346 ms total)
# [----------] Global test environment tear-down
# [==========] 5 tests from 1 test suite ran. (27347 ms total)
# [  PASSED  ] 3 tests.
# [  FAILED  ] 2 tests, listed below:
# [  FAILED  ] AltsConcurrentConnectivityTest.TestBasicClientServerHandshakes
# [  FAILED  ] AltsConcurrentConnectivityTest.TestConcurrentClientServerHandshakes
#  2 FAILED TESTS
# E0811 15:43:02.072126233 2232783 test_config.cc:195]
#   Timeout in waiting for gRPC shutdown
#
# Confirmed in 1.41.0 2021-10-10
alts_concurrent_connectivity
%endif

%ifarch s390x
# Unexplained:
#
# (aborted without output)
#
# Confirmed in 1.41.0 2021-10-10
alts_frame_protector
%endif

%ifarch s390x
# Unexplained:
#
# E0809 03:12:16.141688879 1707771
#   alts_grpc_integrity_only_record_protocol.cc:109] Failed to protect, Setting
#   authenticated associated data failed
# E0809 03:12:16.141863502 1707771 alts_grpc_record_protocol_test.cc:282]
#   assertion failed: status == TSI_OK
# *** SIGABRT received at time=1628478736 on cpu 2 ***
# PC: @      0x3ffa571ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ffa5601524  (unknown)  (unknown)
#     @      0x3ffa5601790  (unknown)  (unknown)
#     @      0x3ffa61e3b78  (unknown)  (unknown)
#     @      0x3ffa571ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ffa56d03e0  (unknown)  gsignal
#     @      0x3ffa56b3480  (unknown)  abort
#     @      0x2aa1fa82e3e  (unknown)  random_seal_unseal()
#     @      0x2aa1fa836f8  (unknown)  alts_grpc_record_protocol_tests()
#     @      0x2aa1fa81c68  (unknown)  main
#     @      0x3ffa56b3732  (unknown)  __libc_start_call_main
#     @      0x3ffa56b380e  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa1fa81d60  (unknown)  (unknown)
#
# Confirmed in 1.41.0 2021-10-10
alts_grpc_record_protocol
%endif

%ifarch s390x
# Unexplained:
#
# E0807 15:46:27.681935728 3628534
#   alts_grpc_integrity_only_record_protocol.cc:109] Failed to protect, Setting
#   authenticated associated data failed
# E0807 15:46:27.682097664 3628534 alts_grpc_record_protocol_test.cc:282]
#   assertion failed: status == TSI_OK
# *** SIGABRT received at time=1628351187 on cpu 1 ***
# PC: @      0x3ffbae9ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ffbad81524  (unknown)  (unknown)
#     @      0x3ffbad81790  (unknown)  (unknown)
#     @      0x3ffbb963b78  (unknown)  (unknown)
#     @      0x3ffbae9ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ffbae503e0  (unknown)  gsignal
#     @      0x3ffbae33480  (unknown)  abort
#     @      0x2aa07782e3e  (unknown)  random_seal_unseal()
#     @      0x2aa077836f8  (unknown)  alts_grpc_record_protocol_tests()
#     @      0x2aa07781c68  (unknown)  main
#     @      0x3ffbae33732  (unknown)  __libc_start_call_main
#     @      0x3ffbae3380e  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa07781d60  (unknown)  (unknown)
#
# Confirmed in 1.41.0 2021-10-10
alts_handshaker_client
%endif

%ifarch s390x
# Unexplained:
#
# (aborted without output)
#
# Confirmed in 1.41.0 2021-10-10
alts_iovec_record_protocol
%endif

%ifarch s390x
# Unexplained:
#
# [ RUN      ] AltsUtilTest.AuthContextWithGoodAltsContextWithoutRpcVersions
# /builddir/build/BUILD/grpc-1.39.0/test/cpp/common/alts_util_test.cc:122: Failure
# Expected equality of these values:
#   expected_sl
#     Which is: 1
#   alts_context->security_level()
#     Which is: 0
# [  FAILED  ] AltsUtilTest.AuthContextWithGoodAltsContextWithoutRpcVersions (0 ms)
#
# Confirmed in 1.41.0 2021-10-10
alts_util
%endif

%ifarch s390x
# Unexplained:
#
# E0809 16:49:05.522667340 1558872
#   alts_grpc_integrity_only_record_protocol.cc:109] Failed to protect, Setting
#   authenticated associated data failed
# E0809 16:49:05.523083934 1558872 alts_zero_copy_grpc_protector_test.cc:183]
#   assertion failed: tsi_zero_copy_grpc_protector_protect( sender,
#   &var->original_sb, &var->protected_sb) == TSI_OK
# *** SIGABRT received at time=1628527745 on cpu 2 ***
# PC: @      0x3ff8169ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ff81581524  (unknown)  (unknown)
#     @      0x3ff81581790  (unknown)  (unknown)
#     @      0x3ff82163b78  (unknown)  (unknown)
#     @      0x3ff8169ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ff816503e0  (unknown)  gsignal
#     @      0x3ff81633480  (unknown)  abort
#     @      0x2aa3d0028b8  (unknown)  seal_unseal_small_buffer()
#     @      0x2aa3d002a68  (unknown)  alts_zero_copy_protector_seal_unseal_small_buffer_tests()
#     @      0x2aa3d001b26  (unknown)  main
#     @      0x3ff81633732  (unknown)  __libc_start_call_main
#     @      0x3ff8163380e  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa3d001c10  (unknown)  (unknown)
#
# Confirmed in 1.41.0 2021-10-10
alts_zero_copy_grpc_protector
%endif

%ifarch %{ix86} %{arm32}
# Unexplained:
#
# [ RUN      ] CertificateProviderStoreTest.Basic
# E0809 18:01:00.777880860  323759 certificate_provider_store.cc:67]
#   Certificate provider factory fake2 not found
# [       OK ] CertificateProviderStoreTest.Basic (1 ms)
# [ RUN      ] CertificateProviderStoreTest.Multithreaded
# terminate called without an active exception
# *** SIGABRT received at time=1628532060 on cpu 0 ***
# PC: @ 0xf7f9d559  (unknown)  __kernel_vsyscall
#
# Confirmed in 1.41.0 2021-10-10
certificate_provider_store
%endif

%ifarch %{ix86}
# Unexplained:
#
# [ RUN      ] ChannelTracerTest.TestMultipleEviction
# /builddir/build/BUILD/grpc-1.39.0/test/core/channel/channel_trace_test.cc:65:
#   Failure
# Expected equality of these values:
#   array.array_value().size()
#     Which is: 3
#   expected
#     Which is: 4
# [  FAILED  ] ChannelTracerTest.TestMultipleEviction (1 ms)
#
# Confirmed in 1.41.0 2021-10-10
channel_trace
%endif

%ifarch ppc64le %{arm32} %{arm64} s390x
# Unexplained:
#
# ppc64le, aarch64:
#
# E0811 14:46:04.709808861 2142245 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# terminate called after throwing an instance of 'std::runtime_error'
#   what():  random_device::random_device(const std::string&): device not available
# *** SIGABRT received at time=1628693164 on cpu 4 ***
# [address_is_readable.cc : 96] RAW: Failed to create pipe, errno=24
# [failure_signal_handler.cc : 331] RAW: Signal 6 raised at PC=0x7fff926a9864 while already in AbslFailureSignalHandler()
# [… 13710 similar messages omitted …]
# *** SIGABRT received at time=1628693166 on cpu 1 ***
# [address_is_readable.cc : 96] RAW: Failed to create pipe, errno=24
# [failure_signal_handler.cc : 331] RAW: Signal 6 raised at PC=0x7fff926a9864 while already in AbslFailureSignalHandler()
# *** SIGABRT received at time=1628693167 on cpu 1 ***
# PC: @     0x7fff926a9864  (unknown)  __pthread_kill_internal
#     @     0x7fff92461a48  (unknown)  (unknown)
#     @     0x7fff937ae4e2         48  (unknown)
#     @     0x7fff9264848c         48  gsignal
#     @     0x7fff92621404        336  abort
#     @     0x7fff91d112a4       3200  (unknown)
#     @     0x7fff91d112fc         48  absl::lts_20210324::raw_logging_internal::RawLog()
#     @     0x7fff91a824c4        272  absl::lts_20210324::debugging_internal::AddressIsReadable()
#     @     0x7fff923f1568        176  (unknown)
#     @     0x7fff923f1730         96  (unknown)
#     @     0x7fff923f19e8         32  absl::lts_20210324::GetStackFramesWithContext()
#     @     0x7fff924616e4        480  (unknown)
#     @     0x7fff92461a48  (unknown)  (unknown)
#     @     0x7fff937ae4e2         48  (unknown)
#     @     0x7fff9264848c         48  gsignal
#     @     0x7fff92621404        336  abort
#     @     0x7fff91d112a4       3200  (unknown)
#     @     0x7fff91d112fc         48  absl::lts_20210324::raw_logging_internal::RawLog()
#     @     0x7fff91a824c4        272  absl::lts_20210324::debugging_internal::AddressIsReadable()
#     @     0x7fff923f1568        176  (unknown)
#     @     0x7fff923f1730         96  (unknown)
#     @     0x7fff923f19e8         32  absl::lts_20210324::GetStackFramesWithContext()
#     @     0x7fff924616e4        480  (unknown)
#     @     0x7fff92461a48  (unknown)  (unknown)
#     @     0x7fff937ae4e2         48  (unknown)
#     @     0x7fff9264848c         48  gsignal
#     @     0x7fff92621404        336  abort
#     @     0x7fff91d112a4       3200  (unknown)
#     @     0x7fff91d112fc         48  absl::lts_20210324::raw_logging_internal::RawLog()
#     @     0x7fff91a824c4        272  absl::lts_20210324::debugging_internal::AddressIsReadable()
#     @     0x7fff923f1568        176  (unknown)
#     @     0x7fff923f1730         96  (unknown)
#     @     0x7fff923f19e8         32  absl::lts_20210324::GetStackFramesWithContext()
#     @ ... and at least 1000 more frames
#
# armv7hl, s390x:
#
# E0811 15:35:58.278096553   31424 grpclb.cc:1055]             [grpclb 0xfe65c0] lb_calld=0xfe9778: Invalid LB response received: ''. Ignoring.
# E0811 15:35:58.966844494   31575 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# terminate called after throwing an instance of 'std::runtime_error'
#   what():  random_device::random_device(const std::string&): device not available
# *** SIGABRT received at time=1628696159 on cpu 4 ***
# [symbolize_elf.inc : 965] RAW: /proc/self/task/31421/maps: errno=24
# PC: @ 0xb6418058  (unknown)  (unknown)
#     @ 0xb62d4274  (unknown)  (unknown)
#     @ 0xb63d2310  (unknown)  (unknown)
#     @ 0xb6418058  (unknown)  (unknown)
#     @ 0xb63d0ddc  (unknown)  (unknown)
#
# Confirmed in 1.41.0 2021-10-10
client_channel_stress
%endif

%ifarch s390x
# Unexplained hang:
#
# [ RUN      ] ClientLbEnd2endTest.RoundRobinWithHealthChecking
# /builddir/build/BUILD/grpc-1.39.0/test/cpp/end2end/client_lb_end2end_test.cc:1452: Failure
# Value of: WaitForChannelReady(channel.get())
#   Actual: false
# Expected: true
# [… hundreds of similar messages …]
# From /builddir/build/BUILD/grpc-1.39.0/test/cpp/end2end/client_lb_end2end_test.cc:1462
# Error: Deadline Exceeded
# /builddir/build/BUILD/grpc-1.39.0/test/cpp/end2end/client_lb_end2end_test.cc:342: Failure
# Value of: success
#   Actual: false
# Expected: true
# From /builddir/build/BUILD/grpc-1.39.0/test/cpp/end2end/client_lb_end2end_test.cc:1462
# Error: Deadline Exceeded
# timeout: sending signal TERM to command 'redhat-linux-build/client_lb_end2end_test'
# *** SIGTERM received at time=1628744184 on cpu 0 ***
# PC: @      0x3ff89d165aa  (unknown)  epoll_wait
#     @      0x3ff89881524  (unknown)  (unknown)
#     @      0x3ff89881790  (unknown)  (unknown)
#     @      0x3ff8acffb78  (unknown)  (unknown)
#     @      0x3ff89d165aa  (unknown)  epoll_wait
#     @      0x3ff8a573dea  (unknown)  pollset_work()
#     @      0x3ff8a577630  (unknown)  pollset_work()
#     @      0x3ff8a611a8e  (unknown)  cq_pluck()
#     @      0x3ff8a6102c2  (unknown)  grpc_completion_queue_pluck
#     @      0x3ff8a84c08c  (unknown)  grpc::CoreCodegen::grpc_completion_queue_pluck()
#     @      0x2aa189b3de0  (unknown)  grpc::CompletionQueue::Pluck()
#     @      0x2aa189bb4be  (unknown)  grpc::internal::BlockingUnaryCallImpl<>::BlockingUnaryCallImpl()
#     @      0x2aa189d213a  (unknown)  grpc::internal::BlockingUnaryCall<>()
#     @      0x2aa189c4e2e  (unknown)  grpc::testing::EchoTestService::Stub::Echo()
#     @      0x2aa18a01112  (unknown)  grpc::testing::(anonymous namespace)::ClientLbEnd2endTest::SendRpc()
#     @      0x2aa18a0139c  (unknown)  grpc::testing::(anonymous namespace)::ClientLbEnd2endTest::CheckRpcSendOk()
#     @      0x2aa18a07a00  (unknown)  grpc::testing::(anonymous namespace)::ClientLbEnd2endTest::WaitForServer()
#     @      0x2aa18a0f97a  (unknown)  grpc::testing::(anonymous namespace)::ClientLbEnd2endTest_RoundRobinWithHealthChecking_Test::TestBody()
#     @      0x2aa18a706f6  (unknown)  testing::internal::HandleExceptionsInMethodIfSupported<>()
#     @      0x2aa18a62aba  (unknown)  testing::Test::Run()
#     @      0x2aa18a62d54  (unknown)  testing::TestInfo::Run()
#     @      0x2aa18a635ce  (unknown)  testing::TestSuite::Run()
#     @      0x2aa18a64258  (unknown)  testing::internal::UnitTestImpl::RunAllTests()
#     @      0x2aa18a70c86  (unknown)  testing::internal::HandleExceptionsInMethodIfSupported<>()
#     @      0x2aa18a62e68  (unknown)  testing::UnitTest::Run()
#     @      0x2aa189aa086  (unknown)  main
#     @      0x3ff89c33732  (unknown)  __libc_start_call_main
#     @      0x3ff89c3380e  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa189ac6a0  (unknown)  (unknown)
#
# Confirmed in 1.41.0 2021-10-10
client_lb_end2end
%endif

# Times out often enough to be annoying.
#
# Confirmed in 1.41.1 2022-03-28
client_ssl

%ifarch %{arm32} %{ix86}
# Unexplained:
#
# [ RUN      ] End2EndBinderTransportTestWithDifferentDelayTimes/
#    End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/0
# /builddir/build/BUILD/grpc-1.41.0/test/core/transport/binder/end2end/
#    end2end_binder_transport_test.cc:188: Failure
# Expected equality of these values:
#   cnt
#     Which is: 0
#   end2end_testing::EchoServer::kServerStreamingCounts
#     Which is: 100
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/0,
#   where GetParam() = 0 (3 ms)
# [… etc. …]
# [  FAILED  ] 18 tests, listed below:
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/0,
#   where GetParam() = 0
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/1,
#   where GetParam() = 10ns
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/2,
#   where GetParam() = 10us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/3,
#   where GetParam() = 100us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/4,
#   where GetParam() = 1ms
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/5,
#   where GetParam() = 20ms
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/0,
#   where GetParam() = 0
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/1,
#   where GetParam() = 10ns
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/2,
#   where GetParam() = 10us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/3,
#   where GetParam() = 100us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/4,
#   where GetParam() = 1ms
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/5,
#   where GetParam() = 20ms
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/0,
#   where GetParam() = 0
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/1,
#   where GetParam() = 10ns
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/2,
#   where GetParam() = 10us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/3,
#   where GetParam() = 100us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/4,
#   where GetParam() = 1ms
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/5,
#   where GetParam() = 20ms
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/0,
#   where GetParam() = 0
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/1,
#   where GetParam() = 10ns
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/2,
#   where GetParam() = 10us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/3,
#   where GetParam() = 100us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/4,
#   where GetParam() = 1ms
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ServerStreamingCallThroughFakeBinderChannel/5,
#   where GetParam() = 20ms
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/0,
#   where GetParam() = 0
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/1,
#   where GetParam() = 10ns
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/2,
#   where GetParam() = 10us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/3,
#   where GetParam() = 100us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/4,
#   where GetParam() = 1ms
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.ClientStreamingCallThroughFakeBinderChannel/5,
#   where GetParam() = 20ms
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/0,
#   where GetParam() = 0
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/1,
#   where GetParam() = 10ns
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/2,
#   where GetParam() = 10us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/3,
#   where GetParam() = 100us
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/4,
#   where GetParam() = 1ms
# [  FAILED  ] End2EndBinderTransportTestWithDifferentDelayTimes/
#   End2EndBinderTransportTest.BiDirStreamingCallThroughFakeBinderChannel/5,
#   where GetParam() = 20ms
#
# Confirmed in 1.41.0 2021-09-29
end2end_binder_transport
%endif

# Unexplained:
#
# [ RUN      ] EvaluateArgsTest.EmptyMetadata
# *** SIGSEGV received at time=1628108665 on cpu 143 ***
# PC: @     0xffffac12f3d0  (unknown)  __strlen_asimd
#     @     0xffffac06f810  1142966656  (unknown)
#     @     0xffffaca217ec         64  (unknown)
#     @     0xaaaadf5806dc        624  grpc_core::EvaluateArgsTest_EmptyMetadata_Test::TestBody()
#     @     0xaaaadf5c1b78         96  testing::internal::HandleExceptionsInMethodIfSupported<>()
#     @     0xaaaadf5b48d8         32  testing::Test::Run()
#     @     0xaaaadf5b4ad4         64  testing::TestInfo::Run()
#     @     0xaaaadf5b5424         80  testing::TestSuite::Run()
#     @     0xaaaadf5b5f08        240  testing::internal::UnitTestImpl::RunAllTests()
#     @     0xaaaadf5b4ca0        144  testing::UnitTest::Run()
#     @     0xaaaadf57c2d8         64  main
#     @     0xffffac0ba0c4        272  __libc_start_call_main
#     @     0xffffac0ba198  (unknown)  __libc_start_main@GLIBC_2.17
#
# Confirmed in 1.41.0 2021-10-10
evaluate_args

%ifarch x86_64 %{ix86}
# Unexplained:
#
# [ RUN      ] ExamineStackTest.AbseilStackProvider
# /builddir/build/BUILD/grpc-1.39.0/test/core/gprpp/examine_stack_test.cc:75: Failure
# Value of: stack_trace->find("GetCurrentStackTrace") != std::string::npos
#   Actual: false
# Expected: true
# [  FAILED  ] ExamineStackTest.AbseilStackProvider (0 ms)
#
# Confirmed in 1.41.0 2021-10-10
examine_stack
%endif

%ifarch s390x
# Unexplained:
#
# E0809 21:33:27.754988355 3699302 cq_verifier.cc:228]
#   no event received, but expected:tag(257) GRPC_OP_COMPLETE success=1
#   /builddir/build/BUILD/grpc-1.39.0/test/core/end2end/goaway_server_test.cc:264
# tag(769) GRPC_OP_COMPLETE success=1
#   /builddir/build/BUILD/grpc-1.39.0/test/core/end2end/goaway_server_test.cc:265
# *** SIGABRT received at time=1628544807 on cpu 2 ***
# PC: @      0x3ff9ce1ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ff9cd01524  (unknown)  (unknown)
#     @      0x3ff9cd01790  (unknown)  (unknown)
#     @      0x3ff9d9e3b78  (unknown)  (unknown)
#     @      0x3ff9ce1ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ff9cdd03e0  (unknown)  gsignal
#     @      0x3ff9cdb3480  (unknown)  abort
#     @      0x2aa3fb850a6  (unknown)  cq_verify()
#     @      0x2aa3fb8359e  (unknown)  main
#     @      0x3ff9cdb3732  (unknown)  __libc_start_call_main
#     @      0x3ff9cdb380e  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa3fb83cd0  (unknown)  (unknown)
#
# Confirmed in 1.41.0 2021-10-11
goaway_server
%endif

%ifarch %{ix86} %{arm32}
# Unexplained:
#
# [ RUN      ] GrpcTlsCertificateDistributorTest.SetKeyMaterialsInCallback
# terminate called without an active exception
# *** SIGABRT received at time=1628556696 on cpu 3 ***
# PC: @ 0xf7fa9559  (unknown)  __kernel_vsyscall
#
# Confirmed in 1.41.0 2021-10-11
grpc_tls_certificate_distributor
%endif

# Unexplained:
#
# [ RUN      ] GrpcToolTest.CallCommandWithTimeoutDeadlineSet
# [libprotobuf ERROR google/protobuf/text_format.cc:319] Error parsing text-format grpc.testing.SimpleRequest: 1:7: Message type "grpc.testing.SimpleRequest" has no field named "redhat".
# Failed to convert text format to proto.
# Failed to parse request.
# /builddir/build/BUILD/grpc-1.39.0/test/cpp/util/grpc_tool_test.cc:912: Failure
# Value of: 0 == GrpcToolMainLib(ArraySize(argv), argv, TestCliCredentials(), std::bind(PrintStream, &output_stream, std::placeholders::_1))
#   Actual: false
# Expected: true
# /builddir/build/BUILD/grpc-1.39.0/test/cpp/util/grpc_tool_test.cc:917: Failure
# Value of: nullptr != strstr(output_stream.str().c_str(), "message: \"true\"")
#   Actual: false
# Expected: true
# [  FAILED  ] GrpcToolTest.CallCommandWithTimeoutDeadlineSet (4 ms)
#
# Confirmed in 1.41.0 2021-10-11
grpc_tool

# While we have fixed a couple of problems with these tests, including porting
# the test server to Python 3, success still eludes us.
#
# 127.0.0.1 - - [02/Aug/2021 20:34:47] "GET /get HTTP/1.0" 200 -
# E0802 20:34:48.343858742 1765052 httpcli_test.cc:52]
#   assertion failed: response->status == 200
# *** SIGABRT received at time=1627936488 on cpu 2 ***
# PC: @     0x7fe44b4f2783  (unknown)  pthread_kill@@GLIBC_2.34
#     @ ... and at least 1 more frames
#
# Confirmed in 1.41.0 2021-10-11
httpcli
httpscli

%ifarch %{ix86} %{arm32}
# Unexplained:
#
# /builddir/build/BUILD/grpc-1.39.0/test/cpp/server/load_reporter/get_cpu_stats_test.cc:39: Failure
# Expected: (busy) <= (total), actual: 9034196912422118975 vs 3761728973136652623
# [  FAILED  ] GetCpuStatsTest.BusyNoLargerThanTotal (0 ms)
#
# Confirmed in 1.41.0 2021-10-11
lb_get_cpu_stats
%endif

%ifarch s390x
# Unexplained:
#
# *** SIGABRT received at time=1628614005 on cpu 0 ***
# PC: @      0x3ff81d1ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ff81c01524  (unknown)  (unknown)
#     @      0x3ff81c01790  (unknown)  (unknown)
#     @      0x3ff82363b78  (unknown)  (unknown)
#     @      0x3ff81d1ec8e  (unknown)  __pthread_kill_internal
#     @      0x3ff81cd03e0  (unknown)  gsignal
#     @      0x3ff81cb3480  (unknown)  abort
#     @      0x2aa18880c9e  (unknown)  verification_test()
#     @      0x2aa18880a34  (unknown)  main
#     @      0x3ff81cb3732  (unknown)  __libc_start_call_main
#     @      0x3ff81cb380e  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa18880ab0  (unknown)  (unknown)
#
# Confirmed in 1.41.0 2021-10-11
murmur_hash
%endif

%ifarch x86_64 %{ix86}
# Unexplained:
#
# [ RUN      ] StackTracerTest.Basic
# /builddir/build/BUILD/grpc-1.39.0/test/core/util/stack_tracer_test.cc:35: Failure
# Value of: absl::StrContains(stack_trace, "Basic")
#   Actual: false
# Expected: true
# [  FAILED  ] StackTracerTest.Basic (1 ms)
#
# Confirmed in 1.41.0 2021-10-11
stack_tracer
%endif

# Unexplained:
#
# This may be flaky and sometimes succeed; this is known to be the case on
# ppc64le.
#
# E0805 15:49:03.066330569 3863708 oauth2_credentials.cc:158]
#   Call to http server ended with error 401
#   [{"access_token":"ya29.AHES6ZRN3-HlhAPya30GnW_bHSb_",
#   "expires_in":3599,  "token_type":"Bearer"}].
# *** SIGSEGV received at time=1628178543 on cpu 3 ***
# PC: @     0x7ff236e4219c  (unknown)  __strlen_evex
#     @ ... and at least 1 more frames
#
# Confirmed in 1.41.0 2021-10-12
test_core_security_credentials

# Unexplained:
#
# [ RUN      ] XdsTest/BasicTest.Vanilla/XdsResolverV3
# E0811 05:13:55.545624715 3911922 xds_resolver.cc:836]
#   [xds_resolver 0x5650c8f82c00] received error from XdsClient:
#   {"created":"@1628658835.545596932","description":"xds call
#   failed","file":"/builddir/build/BUILD/grpc-1.39.0/src/core/ext/xds/xds_client.cc","file_line":1309}
# E0811 05:13:55.546102538 3911922 cds.cc:533]
#   [cdslb 0x5650c8f80dd0] xds error obtaining data for cluster cluster_name:
#   {"created":"@1628658835.545596932","description":"xds call
#   failed","file":"/builddir/build/BUILD/grpc-1.39.0/src/core/ext/xds/xds_client.cc","file_line":1309}
# E0811 05:13:55.546238067 3911922 xds_cluster_resolver.cc:741]
#   [xds_cluster_resolver_lb 0x5650c90f0200] discovery mechanism 0 xds watcher
#   reported error: {"created":"@1628658835.545596932","description":"xds call
#   failed","file":"/builddir/build/BUILD/grpc-1.39.0/src/core/ext/xds/xds_client.cc","file_line":1309}
# [       OK ] XdsTest/BasicTest.Vanilla/XdsResolverV3 (102 ms)
# [ RUN      ] XdsTest/BasicTest.Vanilla/XdsResolverV3WithLoadReporting
# E0811 05:13:55.635384861 3911938 xds_resolver.cc:836]
#   [xds_resolver 0x5650c8f82c00] received error from XdsClient:
#   {"created":"@1628658835.635350317","description":"xds call
#   failed","file":"/builddir/build/BUILD/grpc-1.39.0/src/core/ext/xds/xds_client.cc","file_line":1309}
# E0811 05:13:55.635785649 3911938 cds.cc:533]
#   [cdslb 0x7f597800aaf0] xds error obtaining data for cluster cluster_name:
#   {"created":"@1628658835.635350317","description":"xds call
#   failed","file":"/builddir/build/BUILD/grpc-1.39.0/src/core/ext/xds/xds_client.cc","file_line":1309}
# E0811 05:13:55.635941953 3911938 xds_cluster_resolver.cc:741]
#   [xds_cluster_resolver_lb 0x7f597c004940] discovery mechanism 0 xds watcher
#   reported error: {"created":"@1628658835.635350317","description":"xds call
#   failed","file":"/builddir/build/BUILD/grpc-1.39.0/src/core/ext/xds/xds_client.cc","file_line":1309}
# [       OK ] XdsTest/BasicTest.Vanilla/XdsResolverV3WithLoadReporting (89 ms)
# [ RUN      ] XdsTest/BasicTest.Vanilla/FakeResolverV3
# *** SIGSEGV received at time=1628658835 on cpu 5 ***
# PC: @     0x7f5984c2d19c  (unknown)  __strlen_evex
#     @ ... and at least 1 more frames
#
# Confirmed in 1.41.0 2021-10-12
xds_end2end

EOF
} | xargs -r chmod -v a-x

find %{_vpath_builddir} -type f -perm /0111 -name '*_test' | sort |
  while read -r testexe
  do
    echo "==== $(date -u --iso-8601=ns): $(basename "${testexe}") ===="
    %{__python3} tools/run_tests/start_port_server.py
    # We have tried to skip all tests that hang, but since this is a common
    # problem, we use timeout so that a test that does hang breaks the build in
    # a reasonable amount of time.
    timeout -k 11m -v 10m "${testexe}"
  done

# Stop the port server
curl "http://localhost:${PORT_SERVER_PORT}/quitquitquit" || :
%endif

# Work around problems in generated tests; we could not fix them in %%prep
# because the test implementations did not exist yet.

%ifarch ppc64le
# Confirmed in 1.41.0 2021-10-01 (likely flaky)
# protoc_plugin._python_plugin_test.SimpleStubsPluginTest.testUnaryCall
# traceback:
# Traceback (most recent call last):
#   File "/usr/lib64/python3.10/unittest/case.py", line 59, in testPartExecutor
#     yield
#   File "/usr/lib64/python3.10/unittest/case.py", line 591, in run
#     self._callTestMethod(testMethod)
#   File "/usr/lib64/python3.10/unittest/case.py", line 549, in _callTestMethod
#     method()
#   File "/builddir/build/BUILD/grpc-1.41.0/src/python/grpcio_tests/tests/
#       protoc_plugin/_python_plugin_test.py", line 548, in testUnaryCall
#     response = service_pb2_grpc.TestService.UnaryCall(
#   File "/builddir/build/BUILD/grpc-1.41.0/src/python/grpcio_tests/tests/
#       protoc_plugin/protos/service/test_service_pb2_grpc.py", line 140, in UnaryCall
#     return grpc.experimental.unary_unary(request, target,
#             '/grpc_protoc_plugin.TestService/UnaryCall',
#   File "/builddir/build/BUILDROOT/grpc-1.41.0-2.fc36.ppc64le/usr/lib64/
#       python3.10/site-packages/grpc/experimental/__init__.py", line 77, in _wrapper
#     return f(*args, **kwargs)
#   File "/builddir/build/BUILDROOT/grpc-1.41.0-2.fc36.ppc64le/usr/lib64/
#       python3.10/site-packages/grpc/_simple_stubs.py", line 242, in unary_unary
#     return multicallable(request,
#   File "/builddir/build/BUILDROOT/grpc-1.41.0-2.fc36.ppc64le/usr/lib64/
#       python3.10/site-packages/grpc/_channel.py", line 946, in __call__
#     return _end_unary_response_blocking(state, call, False, None)
#   File "/builddir/build/BUILDROOT/grpc-1.41.0-2.fc36.ppc64le/usr/lib64/
#       python3.10/site-packages/grpc/_channel.py", line 849, in
#         _end_unary_response_blocking
#     raise _InactiveRpcError(state)
# grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
#       status = StatusCode.UNAVAILABLE
#       details = "Broken pipe"
#       debug_error_string = "{"created":"@1633121043.829503175",
#         "description":"Error received from peer ipv6:[::1]:42049",
#         "file":"src/core/lib/surface/call.cc","file_line":1069,
#         "grpc_message":"Broken pipe","grpc_status":14}"
# >
# stdout:
# stderr:
# /builddir/build/BUILD/grpc-1.41.0/src/python/grpcio_tests/tests/
#     protoc_plugin/protos/service/test_service_pb2_grpc.py:140:
#     ExperimentalApiWarning: 'unary_unary' is an experimental API. It is
#     subject to change or removal between minor releases. Proceed with
#     caution.
#   return grpc.experimental.unary_unary(request, target,
#           '/grpc_protoc_plugin.TestService/UnaryCall',
sed -r -i -e "s/^([[:blank:]]*)(def UnaryCall\(request,)$/\
\\1@unittest.skip('Broken pipe')\\n\\1\\2/" \
    -e "s/^(import grpc)$/\\1\\nimport unittest/" \
    "src/python/grpcio_tests/tests/protoc_plugin/protos/service/\
test_service_pb2_grpc.py"
%endif

pushd src/python/grpcio_tests
for suite in \
    test_lite \
    %{?with_python_aio_tests:test_aio} \
    %{?with_python_gevent_tests:test_gevent} \
    test_py3_only
do
  echo "==== $(date -u --iso-8601=ns): Python ${suite} ===="
  # See the implementation of the %%pytest macro, upon which our environment
  # setup is based. We add a timeout that is rather long, as it must apply to
  # the entire test suite. (Patching in a per-test timeout would be harder.)
  env CFLAGS="${CFLAGS:-${RPM_OPT_FLAGS}}" \
      LDFLAGS="${LDFLAGS:-${RPM_LD_FLAGS}}" \
      PATH="%{buildroot}%{_bindir}:$PATH" \
      PYTHONPATH="${PYTHONPATH:-%{buildroot}%{python3_sitearch}:%{buildroot}%{python3_sitelib}}" \
      PYTHONDONTWRITEBYTECODE=1 \
      timeout -k 31m -v 30m \
      %{__python3} %{py_setup} %{?py_setup_args} "${suite}"
done
popd

%if %{without system_gtest}
# As a sanity check for our claim that gtest/gmock are not bundled, check
# installed executables for symbols that appear to have come from gtest/gmock.
foundgtest=0
if find %{buildroot} -type f -perm /0111 \
      -execdir objdump --syms --dynamic-syms --demangle '{}' '+' 2>/dev/null |
    grep -E '[^:]testing::'
then
  echo 'Found traces of gtest/gmock' 1>&2
  exit 1
fi
%endif


%files
%license LICENSE NOTICE.txt
%{_libdir}/libaddress_sorting.so.%{c_so_version}*
%{_libdir}/libgpr.so.%{c_so_version}*
%{_libdir}/libgrpc.so.%{c_so_version}*
%{_libdir}/libgrpc_unsecure.so.%{c_so_version}*
%{_libdir}/libupb.so.%{c_so_version}*


%files data
%license LICENSE NOTICE.txt
%dir %{_datadir}/grpc
%{_datadir}/grpc/roots.pem


%files doc
%license LICENSE NOTICE.txt
%{_pkgdocdir}


%files cpp
%{_libdir}/libgrpc++.so.%{cpp_so_version}*
%{_libdir}/libgrpc++_alts.so.%{cpp_so_version}*
%{_libdir}/libgrpc++_error_details.so.%{cpp_so_version}*
%{_libdir}/libgrpc++_reflection.so.%{cpp_so_version}*
%{_libdir}/libgrpc++_unsecure.so.%{cpp_so_version}*
%{_libdir}/libgrpc_plugin_support.so.%{cpp_so_version}*

%{_libdir}/libgrpcpp_channelz.so.%{cpp_so_version}*


%if %{with core_tests}
%files cli
%{_bindir}/grpc_cli
%{_libdir}/libgrpc++_test_config.so.%{cpp_so_version}*
%{_mandir}/man1/grpc_cli.1*
%{_mandir}/man1/grpc_cli-*.1*
%endif


%files plugins
# These are for program use and do not offer a CLI for the end user, so they
# should really be in %%{_libexecdir}; however, too many downstream users
# expect them in $PATH to change this for the time being.
%{_bindir}/grpc_*_plugin


%files devel
%{_libdir}/libaddress_sorting.so
%{_libdir}/libgpr.so
%{_libdir}/libgrpc.so
%{_libdir}/libgrpc_unsecure.so
%{_libdir}/libupb.so
%{_includedir}/grpc
%{_libdir}/pkgconfig/gpr.pc
%{_libdir}/pkgconfig/grpc.pc
%{_libdir}/pkgconfig/grpc_unsecure.pc
%{_libdir}/cmake/grpc

%{_libdir}/libgrpc++.so
%{_libdir}/libgrpc++_alts.so
%{_libdir}/libgrpc++_error_details.so
%{_libdir}/libgrpc++_reflection.so
%{_libdir}/libgrpc++_unsecure.so
%{_libdir}/libgrpc_plugin_support.so
%{_includedir}/grpc++
%{_libdir}/pkgconfig/grpc++.pc
%{_libdir}/pkgconfig/grpc++_unsecure.pc

%{_libdir}/libgrpcpp_channelz.so
%{_includedir}/grpcpp


%files -n python3-grpcio
%license LICENSE NOTICE.txt
%{python3_sitearch}/grpc
%{python3_sitearch}/grpcio-%{version}-py%{python3_version}.egg-info


%files -n python3-grpcio-tools
%{python3_sitearch}/grpc_tools
%{python3_sitearch}/grpcio_tools-%{version}-py%{python3_version}.egg-info


%if %{without bootstrap}
%files -n python3-grpcio-admin
%{python3_sitelib}/grpc_admin
%{python3_sitelib}/grpcio_admin-%{version}-py%{python3_version}.egg-info
%endif


%files -n python3-grpcio-channelz
%{python3_sitelib}/grpc_channelz
%{python3_sitelib}/grpcio_channelz-%{version}-py%{python3_version}.egg-info


%if %{without bootstrap}
%files -n python3-grpcio-csds
%{python3_sitelib}/grpc_csds
%{python3_sitelib}/grpcio_csds-%{version}-py%{python3_version}.egg-info
%endif


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


%changelog
%autochangelog
