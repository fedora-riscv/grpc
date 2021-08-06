# We need to use C++17 to link against the system abseil-cpp, or we get linker
# errors.
%global cpp_std 17

# Bootstrapping breaks the circular dependency on python3dist(xds-protos),
# which is packaged separately but ultimately generated from grpc sources using
# the proto compilers in this package; the consequence is that we cannot build
# the python3-grpcio-admin or python3-grpcio-csds, or the Python documentation,
# until after bootstrapping.
%bcond_with bootstrap

# However, gtest in Fedora uses the C++11 ABI, so we get linker errors building
# the tests if we use C++17. We must therefore bundle a copy of gtest in the
# source RPM rather than using the system copy. This is to be discouraged, but
# there is no alternative in this case. It is not treated as a bundled library
# because it is used only at build time, and contributes nothing to the
# installed files.
%global gtest_version 1.11.0
%bcond_with system_gtest

# This must be enabled to get grpc_cli, which is apparently considered part of
# the tests by upstream. This is mentioned in
# https://github.com/grpc/grpc/issues/23432.
%bcond_without core_tests

# A few failing Python “test_lite” tests are skipped without understanding.
# This lets us easily re-enable them to try to work toward a fix or a useful
# upstream bug report.
%bcond_with unexplained_failing_python_lite_tests

# A great many of these tests (over 20%) fail. Any help in understanding these
# well enough to fix them or report them upstream is welcome.
%bcond_with python_aio_tests

# Several of these still fail. We should try to work toward re-enabling this.
%bcond_with python_gevent_tests

Name:           grpc
Version:        1.39.0
Release:        %autorelease
Summary:        RPC library and framework

# CMakeLists.txt: gRPC_CORE_SOVERSION
%global c_so_version 18
# CMakeLists.txt: gRPC_CPP_SOVERSION
%global cpp_so_version 1.39
# CMakeLists.txt: gRPC_CSHARP_SOVERSION
%global csharp_so_version 2.39
# See https://github.com/abseil/abseil-cpp/issues/950#issuecomment-843169602
# regarding unusual SOVERSION style (not a single number).

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
URL:            https://www.%{name}.io
%global forgeurl https://github.com/%{name}/%{name}/
Source0:        %{forgeurl}/archive/v%{version}/%{name}-%{version}.tar.gz
# Used only at build time (not a bundled library); see notes at definition of
# gtest_version macro for explanation and justification.
%global gtest_url https://github.com/google/googletest
%global gtest_archivename googletest-release-%{gtest_version}
Source1:        https://github.com/google/googletest/archive/release-%{gtest_version}/%{gtest_archivename}.tar.gz

# Downstream grpc_cli man pages; hand-written based on “grpc_cli help” output.
Source100:      %{name}_cli.1
Source101:      %{name}_cli-ls.1
Source102:      %{name}_cli-call.1
Source103:      %{name}_cli-type.1
Source104:      %{name}_cli-parse.1
Source105:      %{name}_cli-totext.1
Source106:      %{name}_cli-tojson.1
Source107:      %{name}_cli-tobinary.1
Source108:      %{name}_cli-help.1

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
#     GRPC_PYTHON_ENABLE_DOCUMENTATION_BUILD):
BuildRequires:  python3dist(sphinx)

# grpcio (setup.py) setup_requires (with
#     GRPC_PYTHON_ENABLE_DOCUMENTATION_BUILD):
# grpcio_tests (src/python/grpcio_tests/setup.py) install_requires:
BuildRequires:  python3dist(six) >= 1.10
# grpcio (setup.py) install_requires also has:
#   six>=1.5.2

# grpcio (setup.py) setup_requires (with GRPC_PYTHON_BUILD_WITH_CYTHON, or
# absent generated sources); also needed for grpcio_tools
# (tools/distrib/python/grpcio_tools/setup.py)
BuildRequires:  python3dist(cython)

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
BuildRequires:  python3dist(google-auth) >= 1.0.0

# grpcio_tests (src/python/grpcio_tests/setup.py) install_requires:
BuildRequires:  python3dist(requests) >= 2.4.12

# Required for “test_gevent” tests:
BuildRequires:  python3dist(gevent)

# For stopping the port server
BuildRequires:  curl

# ~~~~ Miscellaneous ~~~~

# https://bugzilla.redhat.com/show_bug.cgi?id=1893533
%global _lto_cflags %{nil}

# Reference documentation
BuildRequires:  doxygen

BuildRequires:  ca-certificates
# For converting absolute symlinks in the buildroot to relative ones
BuildRequires:  symlinks

BuildRequires:  dos2unix

# Apply Fedora system crypto policies. Since this is Fedora-specific, the patch
# is not suitable for upstream.
# https://docs.fedoraproject.org/en-US/packaging-guidelines/CryptoPolicies/#_cc_applications
#
# In fact, this may not be needed, since only testing code is patched.
Patch0:         %{name}-1.39.0-system-crypto-policies.patch
# Build python3-grpcio_tools against system protobuf packages instead of
# expecting a git submodule. Must also add requisite linker flags using
# GRPC_PYTHON_LDFLAGS.
Patch1:         %{name}-1.39.0-python-grpcio_tools-use-system-protobuf.patch
# Add an option GRPC_PYTHON_BUILD_SYSTEM_ABSL to go with the gRPC_ABSL_PROVIDER
# option already provided upstream. See
# https://github.com/grpc/grpc/issues/25559.
Patch2:         %{name}-1.37.0-python-grpcio-use-system-abseil.patch
# Fix errors like:
#   TypeError: super(type, obj): obj must be an instance or subtype of type
# It is not clear why these occur.
Patch3:         %{name}-1.36.4-python-grpcio_tests-fixture-super.patch
# Skip tests requiring non-loopback network access when the
# FEDORA_NO_NETWORK_TESTS environment variable is set.
Patch4:         %{name}-1.36.4-python-grpcio_tests-make-network-tests-skippable.patch
# A handful of compression tests miss the compression ratio threshold. It seems
# to be inconsistent which particular combinations fail in a particular test
# run. It is not clear that this is a real problem. Any help in understanding
# the actual cause well enough to fix this or usefully report it upstream is
# welcome.
Patch5:         %{name}-1.36.4-python-grpcio_tests-skip-compression-tests.patch
# The upstream requirement to link gtest/gmock from grpc_cli is spurious.
# Remove it. We still have to build the core tests and link a test library
# (libgrpc++_test_config.so…)
Patch6:         %{name}-1.37.0-grpc_cli-do-not-link-gtest-gmock.patch
# Fix confusion about path to python_wrapper.sh in httpcli/httpscli tests. I
# suppose that the unpatched code must be correct for how upstream runs the
# tests, somehow.
Patch7:         %{name}-1.39.0-python_wrapper-path.patch
# Port Python 2 scripts used in core tests to Python 3
Patch8:         %{name}-1.39.0-python2-test-scripts.patch

Requires:       %{name}-data = %{version}-%{release}

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
%if %{without bootstrap}
Provides:       python-grpcio-admin-doc = %{version}-%{release}
Provides:       python-grpcio-csds-doc = %{version}-%{release}
Provides:       python-grpcio-channelz-doc = %{version}-%{release}
Provides:       python-grpcio-health-checking-doc = %{version}-%{release}
Provides:       python-grpcio-reflection-doc = %{version}-%{release}
Provides:       python-grpcio-status-doc = %{version}-%{release}
Provides:       python-grpcio-testing-doc = %{version}-%{release}
%endif

%description doc
Documentation and examples for gRPC, including documentation for the following:

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
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       %{name}-cpp%{?_isa} = %{version}-%{release}

Requires:       cmake-filesystem

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
# everything it needs is bundled.
Requires:       %{name}-data = %{version}-%{release}

%description -n python3-grpcio
Python language bindings for gRPC (HTTP/2-based RPC framework).


%package -n python3-grpcio-tools
Summary:       Package for gRPC Python tools
# License:        same as base package

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
# Fix some of the weirdest accidentally-executable files
find . -type f -name '*.md' -perm /0111 -execdir chmod -v a-x '{}' '+'

echo '===== Loosening version specifications =====' 2>&1
# Allow building Python documentation with a newer Sphinx; the upstream version
# requirement is needlessly strict. (It is fine for upstream’s own purposes, as
# they are happy to build documentation with a pinned old version.)
sed -r -i "s/('Sphinx)~=.*'/\1'/" setup.py

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

# Remove unwanted .gitignore files, generally in examples. One could argue that
# a sample .gitignore file is part of the example, but, well, we’re not going
# to do that.
find . -type f -name .gitignore -print -delete

echo '===== Fixing shebangs =====' 2>&1
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

echo '===== Fixing line endings =====' 2>&1
# Fix some CRNL line endings:
dos2unix \
    examples/cpp/helloworld/CMakeLists.txt \
    examples/cpp/helloworld/cmake_externalproject/CMakeLists.txt
# We leave those under examples/csharp alone.

echo '===== Fixing hard-coded C++ standard =====' 2>&1
# We need to adjust the C++ standard to avoid abseil-related linker errors. For
# the main C++ build, we can use CMAKE_CXX_STANDARD. For extensions, examples,
# etc., we must patch.
sed -r -i 's/(std=c\+\+)11/\1%{cpp_std}/g' \
    setup.py %{name}.gyp Rakefile \
    examples/cpp/*/Makefile \
    examples/cpp/*/CMakeLists.txt \
    tools/run_tests/artifacts/artifact_targets.py \
    tools/distrib/python/grpcio_tools/setup.py

echo '===== Fixing .pc install path =====' 2>&1
# Fix the install path for .pc files
# https://github.com/grpc/grpc/issues/25635
sed -r -i 's|lib(/pkgconfig)|\${gRPC_INSTALL_LIBDIR}\1|' CMakeLists.txt

echo '===== Patching to skip certain broken tests =====' 2>&1
%if %{without unexplained_failing_python_lite_tests}
# Confirmed in 1.39.0 2021-07-29
# TODO figure out how to report this upstream in a useful/actionable way
sed -r -i "s/^([[:blank:]]*)(def test_deallocated_server_stops)\\b/\
\\1@unittest.skip('May hang unexplainedly')\\n\\1\\2/" \
    'src/python/grpcio_tests/tests/unit/_server_shutdown_test.py'

%ifarch %{ix86} %{arm32}
# Confirmed in 1.39.0 2021-07-29
# TODO figure out how to report this upstream in a useful/actionable way
sed -r -i "s/^([[:blank:]]*)(def test_concurrent_stream_stream)\\b/\
\\1@unittest.skip('May hang unexplainedly')\\n\\1\\2/" \
    'src/python/grpcio_tests/tests/testing/_client_test.py'
%endif

%ifarch %{ix86} %{arm32}
# Confirmed in 1.39.0 2021-07-29
# These tests fail with:
#   OverflowError: Python int too large to convert to C ssize_t
# TODO figure out how to report this upstream in a useful/actionable way
sed -r -i \
    "s/^([[:blank:]]*)(def test(SSLSessionCacheLRU|SessionResumption))\\b/\
\\1@unittest.skip('Unexplained overflow error on 32-bit')\\n\\1\\2/" \
    'src/python/grpcio_tests/tests/unit/_auth_context_test.py' \
    'src/python/grpcio_tests/tests/unit/_session_cache_test.py'
%endif

%ifarch %{arm64}
# Confirmed in 1.39.0 2021-08-06
# TODO figure out how to report this upstream in a useful/actionable way
sed -r -i "s/^([[:blank:]]*)(def testConcurrentFutureInvocations)\\b/\
\\1@unittest.skip('May hang unexplainedly')\\n\\1\\2/" \
    'src/python/grpcio_tests/tests/unit/_rpc_part_2_test.py'
%endif

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
    -DgRPC_INSTALL_CMAKEDIR:PATH=%{_libdir}/cmake/%{name} \
    -DgRPC_INSTALL_SHAREDIR:PATH=%{_datadir}/%{name} \
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

echo '===== Building C (core) and C++ documentation =====' 2>&1
# Doxygen (reference: C/core, C++, objc)
./tools/doxygen/run_doxygen.sh

# ~~~~ Python ~~~~

echo '===== Building Python grpcio package =====' 2>&1
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
# Note that we had to patch in the GRPC_PYTHON_BUILD_SYSTEM_ABSL option.
export GRPC_PYTHON_BUILD_WITH_CYTHON='True'
export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL='True'
export GRPC_PYTHON_BUILD_SYSTEM_ZLIB='True'
export GRPC_PYTHON_BUILD_SYSTEM_CARES='True'
export GRPC_PYTHON_BUILD_SYSTEM_RE2='True'
export GRPC_PYTHON_BUILD_SYSTEM_ABSL='True'
export GRPC_PYTHON_DISABLE_LIBC_COMPATIBILITY='True'
export GRPC_PYTHON_ENABLE_DOCUMENTATION_BUILD='True'
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
mkdir -p %{name}_root/src
for srcdir in compiler
do
  cp -rp "../../../../src/${srcdir}" "%{name}_root/src/"
done
cp -rp '../../../../include' '%{name}_root/'
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

echo '===== Building pure-Python documentation =====' 1>&2
%if %{without bootstrap}
# Sphinx (Python)
%{__python3} %{py_setup} %{?py_setup_args} doc
rm -vrf doc/build/.buildinfo doc/build/.doctrees
%endif


%install
# ~~~~ C (core) and C++ (cpp) ~~~~
%cmake_install

%if %{with core_tests}
# For some reason, grpc_cli is not installed. Do it manually.
install -t '%{buildroot}%{_bindir}' -p -D '%{_vpath_builddir}/%{name}_cli'
# grpc_cli build does not respect CMAKE_INSTALL_RPATH
# https://github.com/grpc/grpc/issues/25176
chrpath --delete '%{buildroot}%{_bindir}/%{name}_cli'

# This library is also required for grpc_cli; it is built as part of the test
# code.
install -t '%{buildroot}%{_libdir}' -p \
    %{_vpath_builddir}/lib%{name}++_test_config.so.*
chrpath --delete '%{buildroot}%{_libdir}/'lib%{name}++_test_config.so.*

install -d '%{buildroot}/%{_mandir}/man1'
install -t '%{buildroot}/%{_mandir}/man1' -p -m 0644 \
    %{SOURCE100} %{SOURCE101} %{SOURCE102} %{SOURCE103} %{SOURCE104} \
    %{SOURCE106} %{SOURCE107} %{SOURCE108}
%endif

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
cp -rp doc/ref examples '%{buildroot}%{_pkgdocdir}'
%if %{without bootstrap}
install -d '%{buildroot}%{_pkgdocdir}/python'
cp -rp doc/build '%{buildroot}%{_pkgdocdir}/python/html'
%endif


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

# Bad assumption about which directory the tests are running in:
#
# E0802 01:16:33.084040928 3911182 subprocess_posix.cc:61]
#   execv 'redhat-linux-build/../../test/core/http/python_wrapper.sh'
#   failed: No such file or directory
# E0802 01:16:39.086691950 3911178 httpcli_test.cc:52]
#   assertion failed: response->status == 200
# *** SIGABRT received at time=16278 66999 on cpu 1 ***

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
# Confirmed in 1.39.0 2021-08-02
httpcli
httpscli

# Error shutting down fd, then falsely claims the port server is not running.
#
# [ RUN      ] ServerBuilderTest.CreateServerOnePort
# E0413 22:52:26.853421021   28920 ev_epollex_linux.cc:516]
#   Error shutting down fd 7. errno: 9
# E0413 22:52:30.082373319   28920 ev_epollex_linux.cc:516]
#   Error shutting down fd 7. errno: 9
# E0413 22:52:33.168560214   28923 ev_epollex_linux.cc:516]
#   Error shutting down fd 7. errno: 9
# E0413 22:52:36.905371168   28920 ev_epollex_linux.cc:516]
#   Error shutting down fd 7. errno: 9
# E0413 22:52:40.455413890   28923 ev_epollex_linux.cc:516]
#   Error shutting down fd 7. errno: 9
# E0413 22:52:44.012408974   28922 ev_epollex_linux.cc:516]
#   Error shutting down fd 7. errno: 9
# gRPC tests require a helper port server to allocate ports used
# during the test.
#
# This server is not currently running.
#
# To start it, run tools/run_tests/start_port_server.py
#
# CHECKME
admin_services_end2end
alts_concurrent_connectivity
async_end2end
channelz_service
cli_call
client_callback_end2end
client_channel_stress
client_interceptors_end2end
client_lb_end2end
context_allocator_end2end
delegating_channel
end2end
filter_end2end
generic_end2end
grpc_tool
grpclb_end2end
health_service_end2end
hybrid_end2end
mock
nonblocking
proto_server_reflection
raw_end2end
server_builder
server_builder_plugin
service_config_end2end
shutdown
streaming_throughput
thread_stress
xds_end2end

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
# Confirmed in 1.39.0 2021-08-05
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
# Confirmed in 1.39.0 2021-08-05
alts_crypt
%endif

%ifarch s390x
# Unexplained:
#
# (aborted without output)
#
# Confirmed in 1.39.0 2021-08-05
alts_crypter
%endif

%ifarch s390x
# Unexplained:
#
# (aborted without output)
#
# Confirmed in 1.39.0 2021-08-05
alts_frame_protector
%endif

%ifarch s390x
# Unexplained:
#
# E0502 15:06:40.951214061 1640707
# alts_grpc_integrity_only_record_protocol.cc:109] Failed to protect, Setting
#   authenticated associated data failed
# E0502 15:06:40.951411109 1640707 alts_grpc_record_protocol_test.cc:282]
#   assertion failed: status == TSI_OK
# *** SIGABRT received at time=1619968000 ***
# PC: @      0x3ff939c8e0c  (unknown)  raise
#     @      0x3ff938814c4  (unknown)  (unknown)
#     @      0x3ff9388168a  (unknown)  (unknown)
#     @      0x3ff944e4b78  (unknown)  (unknown)
#     @      0x3ff939c8e0c  (unknown)  raise
#     @      0x3ff939abae8  (unknown)  abort
#     @      0x2aa11482c9e  (unknown)  random_seal_unseal()
#     @      0x2aa11483558  (unknown)  alts_grpc_record_protocol_tests()
#     @      0x2aa11481b08  (unknown)  main
#     @      0x3ff939abdf4  (unknown)  __libc_start_main
#     @      0x2aa11481bc4  (unknown)  (unknown)
#
# CHECKME
alts_grpc_record_protocol
%endif

%ifarch s390x
# Unexplained:
#
# E0505 21:08:10.125639702 2153925 alts_handshaker_client.cc:863]
#   client or client->vtable has not been initialized properly
# E0505 21:08:10.125794714 2153925 alts_handshaker_client.cc:579]
#   Invalid arguments to handshaker_client_start_server()
# E0505 21:08:10.125877215 2153925 alts_handshaker_client.cc:874]
#   client or client->vtable has not been initialized properly
# E0505 21:08:10.125948887 2153925 alts_handshaker_client.cc:615]
#   Invalid arguments to handshaker_client_next()
# E0505 21:08:10.126015062 2153925 alts_handshaker_client.cc:885]
#   client or client->vtable has not been initialized properly
# E0505 21:08:10.126146291 2153925 alts_handshaker_client_test.cc:177]
#   assertion failed:
#   grpc_gcp_StartClientHandshakeReq_handshake_security_protocol( client_start)
#   == grpc_gcp_ALTS
# *** SIGABRT received at time=1620248890 ***
# PC: @      0x3ff98ac8e0c  (unknown)  raise
#     @      0x3ff989814c4  (unknown)  (unknown)
#     @      0x3ff9898168a  (unknown)  (unknown)
#     @      0x3ff99664b78  (unknown)  (unknown)
#     @      0x3ff98ac8e0c  (unknown)  raise
#     @      0x3ff98aabae8  (unknown)  abort
#     @      0x2aa3760375e  (unknown)  check_client_start_success()
#     @      0x3ff99419a72  (unknown)  continue_make_grpc_call()
#     @      0x3ff9941ac58  (unknown)  handshaker_client_start_client()
#     @      0x2aa37603c66  (unknown)  schedule_request_success_test()
#     @      0x2aa3760281e  (unknown)  main
#     @      0x3ff98aabdf4  (unknown)  __libc_start_main
#     @      0x2aa376028b4  (unknown)  (unknown)
#
# CHECKME
alts_handshaker_client
%endif

%ifarch s390x
# Unexplained:
#
# (aborted without output)
#
# CHECKME
alts_iovec_record_protocol
%endif

%ifarch s390x
# Unexplained:
#
# [ RUN      ] AltsUtilTest.AuthContextWithGoodAltsContextWithoutRpcVersions
# ../test/cpp/common/alts_util_test.cc:122: Failure
# Expected equality of these values:
#   expected_sl
#     Which is: 1
#   alts_context->security_level()
#     Which is: 0
# [  FAILED  ] AltsUtilTest.AuthContextWithGoodAltsContextWithoutRpcVersions (0 ms)
# [ RUN      ] AltsUtilTest.AuthContextWithGoodAltsContext
# [       OK ] AltsUtilTest.AuthContextWithGoodAltsContext (0 ms)
# [ RUN      ] AltsUtilTest.AltsClientAuthzCheck
# [       OK ] AltsUtilTest.AltsClientAuthzCheck (0 ms)
# [----------] 7 tests from AltsUtilTest (0 ms total)
# [----------] Global test environment tear-down
# [==========] 7 tests from 1 test suite ran. (0 ms total)
# [  PASSED  ] 6 tests.
# [  FAILED  ] 1 test, listed below:
# [  FAILED  ] AltsUtilTest.AuthContextWithGoodAltsContextWithoutRpcVersions
#  1 FAILED TEST
# E0506 13:27:12.407095885 2895549 alts_util.cc:37]
#     auth_context is nullptr.
# E0506 13:27:12.407174329 2895549 alts_util.cc:43]
#     contains zero or more than one ALTS context.
# E0506 13:27:12.407191312 2895549 alts_util.cc:43]
#     contains zero or more than one ALTS context.
# E0506 13:27:12.407210713 2895549 alts_util.cc:50]
#     fails to parse ALTS context.
# E0506 13:27:12.407261763 2895549 alts_util.cc:43]
#     contains zero or more than one ALTS context.
#
# CHECKME
alts_util
%endif

%ifarch s390x
# Unexplained:
#
# E0506 14:42:08.079363072 2916785
#     alts_grpc_integrity_only_record_protocol.cc:109] Failed to protect,
#     Setting authenticated associated data failed
# E0506 14:42:08.079807806 2916785 alts_zero_copy_grpc_protector_test.cc:183]
#     assertion failed: tsi_zero_copy_grpc_protector_protect( sender,
#     &var->original_sb, &var->protected_sb) == TSI_OK
# *** SIGABRT received at time=1620312128 ***
# PC: @      0x3ffae548e0c  (unknown)  raise
#     @      0x3ffae4014c4  (unknown)  (unknown)
#     @      0x3ffae40168a  (unknown)  (unknown)
#     @      0x3ffaf064b78  (unknown)  (unknown)
#     @      0x3ffae548e0c  (unknown)  raise
#     @      0x3ffae52bae8  (unknown)  abort
#     @      0x2aa11202728  (unknown)  seal_unseal_small_buffer()
#     @      0x2aa112028d8  (unknown)
#         alts_zero_copy_protector_seal_unseal_small_buffer_tests()
#     @      0x2aa112019d6  (unknown)  main
#     @      0x3ffae52bdf4  (unknown)  __libc_start_main
#     @      0x2aa11201a84  (unknown)  (unknown)
#
# CHECKME
alts_zero_copy_grpc_protector
%endif

%ifarch %{ix86} %{arm32}
# Unexplained:
#
# [ RUN      ] CertificateProviderStoreTest.Multithreaded
# terminate called without an active exception
# *** SIGABRT received at time=1619103150 ***
# PC: @ 0xf7fa3559  (unknown)  __kernel_vsyscall
#     @ ... and at least 1 more frames
#
# CHECKME
certificate_provider_store
%endif

%ifarch %{ix86}
# Unexplained:
#
# [ RUN      ] ChannelTracerTest.TestMultipleEviction
# ../test/core/channel/channel_trace_test.cc:65: Failure
# Expected equality of these values:
#   array.array_value().size()
#     Which is: 3
#   expected
#     Which is: 4
# [  FAILED  ] ChannelTracerTest.TestMultipleEviction (2 ms)
#
# CHECKME
channel_trace
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
# Confirmed in 1.39.0 2021-08-04
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
# Confirmed in 1.39.0 2021-08-05
examine_stack
%endif

%ifarch s390x
# Unexplained:
#
# E0506 16:24:35.085362185 2328244 cq_verifier.cc:228]
#     no event received, but expected:tag(257) GRPC_OP_COMPLETE success=1
#     ../test/core/end2end/goaway_server_test.cc:264
# tag(769) GRPC_OP_COMPLETE success=1
#     ../test/core/end2end/goaway_server_test.cc:265
# *** SIGABRT received at time=1620318275 ***
# PC: @      0x3ffa05c8e0c  (unknown)  raise
#     @      0x3ffa04814c4  (unknown)  (unknown)
#     @      0x3ffa048168a  (unknown)  (unknown)
#     @      0x3ffa11e4b78  (unknown)  (unknown)
#     @      0x3ffa05c8e0c  (unknown)  raise
#     @      0x3ffa05abae8  (unknown)  abort
#     @      0x2aa1e984e96  (unknown)  cq_verify()
#     @      0x2aa1e9833ce  (unknown)  main
#     @      0x3ffa05abdf4  (unknown)  __libc_start_main
#     @      0x2aa1e983ac4  (unknown)  (unknown)
#
# CHECKME
goaway_server
%endif

%ifarch %{ix86} %{arm32}
# Unexplained:
#
# [ RUN      ] GrpcTlsCertificateDistributorTest.SetKeyMaterialsInCallback
# terminate called without an active exception
# *** SIGABRT received at time=1619125567 ***
# PC: @ 0xb682c114  (unknown)  raise
#     @ 0xb67e817c  (unknown)  (unknown)
#     @ 0xb682d6b0  (unknown)  (unknown)
#     @ 0xb682c114  (unknown)  raise
#
# CHECKME
grpc_tls_certificate_distributor
%endif

%ifarch %{ix86} %{arm32}
# Unexplained:
#
# [ RUN      ] GetCpuStatsTest.BusyNoLargerThanTotal
# ../test/cpp/server/load_reporter/get_cpu_stats_test.cc:39: Failure
# Expected: (busy) <= (total), actual: 9025859384538762329 vs
#     3751280126112716351
# [  FAILED  ] GetCpuStatsTest.BusyNoLargerThanTotal (0 ms)
#
# CHECKME
lb_get_cpu_stats
%endif

%ifarch s390x
# Unexplained:
#
# *** SIGABRT received at time=1620336694 ***
# PC: @      0x3ffa3348e0c  (unknown)  raise
#     @      0x3ffa32014c4  (unknown)  (unknown)
#     @      0x3ffa320168a  (unknown)  (unknown)
#     @      0x3ffa39e4b78  (unknown)  (unknown)
#     @      0x3ffa3348e0c  (unknown)  raise
#     @      0x3ffa332bae8  (unknown)  abort
#     @      0x2aa27600c8e  (unknown)  verification_test()
#     @      0x2aa27600a24  (unknown)  main
#     @      0x3ffa332bdf4  (unknown)  __libc_start_main
#     @      0x2aa27600aa4  (unknown)  (unknown)
#
# CHECKME
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
# Confirmed in 1.39.0 2021-08-05
stack_tracer
%endif

%ifarch x86_64 %{ix86} %{arm64}
# Unexplained hang.
#
# This may be flaky and sometimes succeed; this is known to be the case on
# x86_64.
#
# mutex: 256 512 1024 2048 4096 8192 16384 32768 65536 131072 262144 done 1.372237159 s
# mutex try: 256 512 1024 2048 4096 8192 16384 32768 65536 131072 done 1.285748396 s
# cv: 256 512 1024 2048 done 1.134636147 s
# timedcv: 256 512 1024 done 1.925035489 s
# queue: 256timeout: sending signal TERM to command 'redhat-linux-build/sync_test'
# *** SIGTERM received at time=1627413101 on cpu 0 ***
# PC: @     0xffff8299f8a8  (unknown)  syscall
#     @     0xffff82896850  1732032480  (unknown)
#     @     0xffff82d7b7bc        112  (unknown)
#     @     0xffff8237ac44         48  AbslInternalPerThreadSemWait_lts_20210324
#     @     0xffff8237e5c8        144  absl::lts_20210324::CondVar::WaitCommon()
#     @     0xffff82ce82c4         64  gpr_cv_wait
#     @     0xaaaae0ae2118        288  test()
#     @     0xaaaae0ae1560         64  main
#     @     0xffff828e10c4        272  __libc_start_call_main
#     @     0xffff828e1198  (unknown)  __libc_start_main@GLIBC_2.17
#
# Confirmed in 1.39.0 2021-08-01
sync
%endif

%ifarch s390x
# Unexplained:
#
# E0416 16:03:14.051081049   67245 tcp_posix_test.cc:387]
#     assertion failed: error == GRPC_ERROR_NONE
# *** SIGABRT received at time=1618588994 ***
# PC: @       0x4001f5be0c  (unknown)  raise
#     @       0x40020bf4c4  (unknown)  (unknown)
#     @       0x40020bf68a  (unknown)  (unknown)
#     @       0x4002624df0  (unknown)  (unknown)
#     @       0x4001f5be0c  (unknown)  raise
#     @       0x4001f3eae8  (unknown)  abort
#     @       0x4000003f60  (unknown)  timestamps_verifier()
#     @       0x4001ac36d8  (unknown)  grpc_core::TracedBuffer::Shutdown()
#     @       0x4001ae53ea  (unknown)  tcp_shutdown_buffer_list()
#     @       0x4001ae774a  (unknown)  tcp_flush()
#     @       0x4001ae99f2  (unknown)  tcp_write()
#     @       0x4000005806  (unknown)  write_test()
#     @       0x400000622e  (unknown)  run_tests()
#     @       0x40000028c8  (unknown)  main
#     @       0x4001f3edf4  (unknown)  __libc_start_main
#     @       0x40000029f4  (unknown)  (unknown)
#
# CHECKME
tcp_posix
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
# Confirmed in 1.39.0 2021-08-05
test_core_security_credentials

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
%{_libdir}/lib%{name}.so.%{c_so_version}*
%{_libdir}/lib%{name}_unsecure.so.%{c_so_version}*
%{_libdir}/libupb.so.%{c_so_version}*


%files data
%license LICENSE NOTICE.txt
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/roots.pem


%files doc
%license LICENSE NOTICE.txt
%{_pkgdocdir}


%files cpp
%{_libdir}/lib%{name}++.so.%{cpp_so_version}*
%{_libdir}/lib%{name}++_alts.so.%{cpp_so_version}*
%{_libdir}/lib%{name}++_error_details.so.%{cpp_so_version}*
%{_libdir}/lib%{name}++_reflection.so.%{cpp_so_version}*
%{_libdir}/lib%{name}++_unsecure.so.%{cpp_so_version}*
%{_libdir}/lib%{name}_plugin_support.so.%{cpp_so_version}*

%{_libdir}/lib%{name}pp_channelz.so.%{cpp_so_version}*


%if %{with core_tests}
%files cli
%{_bindir}/%{name}_cli
%{_libdir}/lib%{name}++_test_config.so.%{cpp_so_version}*
%{_mandir}/man1/%{name}_cli.1*
%{_mandir}/man1/%{name}_cli-*.1*
%endif


%files plugins
# These are for program use and do not offer a CLI for the end user, so they
# should really be in %%{_libexecdir}; however, too many downstream users
# expect them in $PATH to change this for the time being.
%{_bindir}/%{name}_*_plugin


%files devel
%{_libdir}/libaddress_sorting.so
%{_libdir}/libgpr.so
%{_libdir}/lib%{name}.so
%{_libdir}/lib%{name}_unsecure.so
%{_libdir}/libupb.so
%{_includedir}/%{name}
%{_libdir}/pkgconfig/gpr.pc
%{_libdir}/pkgconfig/%{name}.pc
%{_libdir}/pkgconfig/%{name}_unsecure.pc
%{_libdir}/cmake/%{name}

%{_libdir}/lib%{name}++.so
%{_libdir}/lib%{name}++_alts.so
%{_libdir}/lib%{name}++_error_details.so
%{_libdir}/lib%{name}++_reflection.so
%{_libdir}/lib%{name}++_unsecure.so
%{_libdir}/lib%{name}_plugin_support.so
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
