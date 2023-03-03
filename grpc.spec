# We need to use C++17 to link against the system abseil-cpp, or we get linker
# errors.
%global cpp_std 17

# However, we also get linker errors building the tests if we link against the
# copy of gtest in Fedora (compiled with C++11). The exact root cause is not
# quite clear. We must therefore bundle a copy of gtest in the source RPM
# rather than using the system copy. This is to be discouraged, but there is no
# alternative in this case. It is not treated as a bundled library because it
# is used only at build time, and contributes nothing to the installed files.
# We take measures to verify this in %%check. As long as we are using our own
# copy, we use the exact same version as upstream.
%global gtest_commit 0e402173c97aea7a00749e825b194bfede4f2e45
#global gtest_version 1.11.0
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
# A significant number of Python tests pass in test_lite but fail in
# test_gevent, mostly by dumping core without a traceback.  Since it is tedious
# to enumerate these (and it is difficult to implement “suite-specific” skips
# for shared tests, so the tests would have to be skipped in all suites), we
# just skip the gevent suite entirely on this architecture.
%bcond_with python_gevent_tests
%endif

# Running core tests under valgrind may help debug crashes. This is mostly
# ignored if the gdb build conditional is also set.
%bcond_with valgrind
# Running core tests under gdb may help debug crashes.
%bcond_with gdb

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
Version:        1.46.7
Release:        %autorelease
Summary:        RPC library and framework

%global srcversion %(echo '%{version}' | sed -r 's/~rc/-pre/')
%global pyversion %(echo '%{version}' | tr -d '~')

# CMakeLists.txt: gRPC_CORE_SOVERSION
%global c_so_version 24
# CMakeLists.txt: gRPC_CPP_SOVERSION
# See https://github.com/abseil/abseil-cpp/issues/950#issuecomment-843169602
# regarding unusual C++ SOVERSION style (not a single number).
%global cpp_so_version 1.46

# The entire source is ASL 2.0 except the following:
#
# BSD:
#   - third_party/upb/, except third_party/upb/third_party/lunit/ and
#     third_party/upb/third_party/utf8_range/
#     * Potentially linked into any compiled subpackage (but not pure-Python
#       subpackages, etc.)
#   - third_party/address_sorting/
#     * Potentially linked into any compiled subpackage (but not pure-Python
#       subpackages, etc.)
#
# MIT:
#   - third_party/upb/third_party/utf8_range
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
#   - src/boringssl/boringssl_prefix_symbols.h
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
License:        ASL 2.0 and BSD and MIT
URL:            https://www.grpc.io
%global forgeurl https://github.com/grpc/grpc/
# Used only at build time (not a bundled library); see notes at definition of
# gtest_commit/gtest_version macro for explanation and justification.
%global gtest_url https://github.com/google/googletest
%global gtest_archivename googletest-%{gtest_commit}
#global gtest_archivename googletest-release-#{gtest_version}
Source0:        %{forgeurl}/archive/v%{srcversion}/grpc-%{srcversion}.tar.gz
Source1:        %{gtest_url}/archive/%{gtest_commit}/%{gtest_archivename}.tar.gz
#Source1:        #{gtest_url}/archive/release-#{gtest_version}/#{gtest_archivename}.tar.gz

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

%if %{with core_tests}
BuildRequires:  cmake(benchmark)
%if %{with system_gtest}
BuildRequires:  cmake(gtest)
BuildRequires:  pkgconfig(gmock)
%endif
%if %{with valgrind}
BuildRequires:  valgrind
%endif
%if %{with gdb}
BuildRequires:  gdb
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
# grpcio_tools (tools/distrib/python/grpcio_tools/setup.py) install_requires:
BuildRequires:  python3dist(protobuf) >= 3.12.0

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

%if %{with python_gevent_tests}
# Required for “test_gevent” tests:
BuildRequires:  python3dist(gevent)
%endif

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
Patch:          grpc-1.39.0-system-crypto-policies.patch
# Add an option GRPC_PYTHON_BUILD_SYSTEM_ABSL to go with the gRPC_ABSL_PROVIDER
# option already provided upstream. See
# https://github.com/grpc/grpc/issues/25559.
Patch:          grpc-1.40.0-python-grpcio-use-system-abseil.patch
# Fix errors like:
#   TypeError: super(type, obj): obj must be an instance or subtype of type
# It is not clear why these occur.
Patch:          grpc-1.36.4-python-grpcio_tests-fixture-super.patch
# Skip tests requiring non-loopback network access when the
# FEDORA_NO_NETWORK_TESTS environment variable is set.
Patch:          grpc-1.40.0-python-grpcio_tests-make-network-tests-skippable.patch
# A handful of compression tests miss the compression ratio threshold. It seems
# to be inconsistent which particular combinations fail in a particular test
# run. It is not clear that this is a real problem. Any help in understanding
# the actual cause well enough to fix this or usefully report it upstream is
# welcome.
Patch:          grpc-1.36.4-python-grpcio_tests-skip-compression-tests.patch
# The upstream requirement to link gtest/gmock from grpc_cli is spurious.
# Remove it. We still have to build the core tests and link a test library
# (libgrpc++_test_config.so…)
Patch:          grpc-1.37.0-grpc_cli-do-not-link-gtest-gmock.patch
# Fix confusion about path to python_wrapper.sh in httpcli/httpscli tests. I
# suppose that the unpatched code must be correct for how upstream runs the
# tests, somehow.
Patch:          grpc-1.45.0-python_wrapper-path.patch
# Do not segfault when peer CN is absent
Patch:          %{forgeurl}/pull/29359.patch
# Fix a segfault in client_lb_end2end_test
#
# In the SubchannelStreamClient constructor, do not initialize an
# absl::string_view with a null pointer; this lead to strlen() being
# called on the null pointer. Let the absl::string_view be empty in this
# case instead.
#
# Fixes #29567.
#
# “Segfault in client_lb_end2end_test due to absl::string_view(nullptr)”
# https://github.com/grpc/grpc/issues/29567
Patch:          %{forgeurl}/pull/29568.patch
# EPEL9-specific patch to work around:
#
# ../test/cpp/end2end/rls_server.cc: In function 'grpc::lookup::v1::RouteLookupResponse grpc::testing::BuildRlsResponse(std::vector<std::__cxx11::basic_string<char> >, const char*)':
# ../test/cpp/end2end/rls_server.cc:97:34: error: no matching function for call to 'google::protobuf::RepeatedPtrField<std::__cxx11::basic_string<char> >::Add(std::vector<std::__cxx11::basic_string<char> >::iterator, std::vector<std::__cxx11::basic_string<char> >::iterator)'
#    97 |   response.mutable_targets()->Add(targets.begin(), targets.end());
#       |   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# In file included from /usr/include/google/protobuf/implicit_weak_message.h:39,
#                  from /usr/include/google/protobuf/parse_context.h:42,
#                  from /usr/include/google/protobuf/map_type_handler.h:34,
#                  from /usr/include/google/protobuf/map.h:56,
#                  from /usr/include/google/protobuf/generated_message_table_driven.h:34,
#                  from gens/src/proto/grpc/lookup/v1/rls.pb.h:26,
#                  from gens/src/proto/grpc/lookup/v1/rls.grpc.pb.h:22,
#                  from ../test/cpp/end2end/rls_server.h:20,
#                  from ../test/cpp/end2end/rls_server.cc:17:
# /usr/include/google/protobuf/repeated_field.h:941:12: note: candidate: 'Element* google::protobuf::RepeatedPtrField<T>::Add() [with Element = std::__cxx11::basic_string<char>]'
#   941 |   Element* Add();
#       |            ^~~
# /usr/include/google/protobuf/repeated_field.h:941:12: note:   candidate expects 0 arguments, 2 provided
# /usr/include/google/protobuf/repeated_field.h:942:8: note: candidate: 'void google::protobuf::RepeatedPtrField<T>::Add(Element&&) [with Element = std::__cxx11::basic_string<char>]'
#   942 |   void Add(Element&& value);
#       |        ^~~
# /usr/include/google/protobuf/repeated_field.h:942:8: note:   candidate expects 1 argument, 2 provided
#
# We have not reported this upstream because it works in Fedora with a current
# protobuf package.
Patch:          grpc-1.46.2-protobuf-3.14.0-RepeatedPtrField-Add-range.patch
# Use gRPC_INSTALL_LIBDIR for pkgconfig files
# https://github.com/grpc/grpc/pull/29826
#
# Fixes:
#
# Should install pkgconfig files under gRPC_INSTALL_LIBDIR
# https://github.com/grpc/grpc/issues/25635
Patch:          %{forgeurl}/pull/29826.patch
# Use CMake variables for paths in pkg-config files
#
# Use @gRPC_INSTALL_LIBDIR@ for libdir; this fixes an incorrect
# -L/usr/lib on multilib Linux systems where that is the 32-bit library
# path and the correct path is /usr/lib64.
#
# Use @gRPC_INSTALL_INCLUDEDIR@ for consistency.
#
# See also:
# https://lists.fedoraproject.org/archives/list/devel@lists.fedoraproject.org/
#   thread/P2N35UMQVEXPILAF47RQB53MWRV2GM3J/
#
# https://github.com/grpc/grpc/pull/31671
Patch:          %{forgeurl}/pull/31671.patch

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
# The bundled upb itself bundles https://github.com/cyb70289/utf8; we follow
# upstream in styling this as “utf8_range”. It cannot reasonably be unbundled
# because the original code is not structured for distribution as a library (it
# does not even include header files). It is not clear which upstream commit
# was used.
Provides:       bundled(utf8_range)

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
Requires:       grpc-cpp%{?_isa} = %{version}-%{release}

Provides:       bundled(upb)
Provides:       bundled(utf8_range)

%description cpp
C++ language bindings for gRPC.


%package plugins
Summary:        Protocol buffers compiler plugins for gRPC
# License:        same as base package

Requires:       grpc%{?_isa} = %{version}-%{release}
Requires:       grpc-cpp%{?_isa} = %{version}-%{release}
Requires:       protobuf-compiler

Provides:       bundled(upb)
Provides:       bundled(utf8_range)

%description plugins
Plugins to the protocol buffers compiler to generate gRPC sources.


%package cli
Summary:        Command-line tool for gRPC
# License:        same as base package

Requires:       grpc%{?_isa} = %{version}-%{release}
Requires:       grpc-cpp%{?_isa} = %{version}-%{release}

Provides:       bundled(upb)
Provides:       bundled(utf8_range)

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
Requires:       grpc-plugins%{?_isa} = %{version}-%{release}

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
Provides:       bundled(utf8_range)

%description -n python3-grpcio
Python language bindings for gRPC (HTTP/2-based RPC framework).


%global grpcio_egg %{python3_sitearch}/grpcio-%{pyversion}-py%{python3_version}.egg-info
%{?python_extras_subpkg:%python_extras_subpkg -n python3-grpcio -i %{grpcio_egg} protobuf}


%package -n python3-grpcio-tools
Summary:       Package for gRPC Python tools
# License:        same as base package

Provides:       bundled(upb)
Provides:       bundled(utf8_range)

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
%autosetup -p1 -n grpc-%{srcversion}

cp -p third_party/upb/third_party/utf8_range/LICENSE LICENSE-utf8_range

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
%setup -q -T -D -b 1 -n grpc-%{srcversion}
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
    src/boringssl/boringssl_prefix_symbols.h \
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
  xargs -r sed -r -i '1{s|^(#!/usr/bin/)env[[:blank:]]+([^[:blank:]]+)|\1\2|}'

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
# Since there are some interdependencies in the Python packages (e.g., many
# have setup_requires: grpcio-tools), we do temporary installs of built
# packages into a local directory as needed, and add it to the PYTHONPATH.
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
    '%{_vpath_builddir}/libgrpc++_test_config.so.%{cpp_so_version}'
chrpath --delete \
    '%{buildroot}%{_libdir}/libgrpc++_test_config.so.%{cpp_so_version}'

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
# /builddir/build/BUILD/grpc-1.46.0/test/cpp/naming/address_sorting_test.cc:809: Failure
# Expected equality of these values:
#   source_addr_output->sin6_family
#     Which is: 0
#   10
# /builddir/build/BUILD/grpc-1.46.0/test/cpp/naming/address_sorting_test.cc:819: Failure
# Expected equality of these values:
#   source_addr_str
#     Which is: "::"
#   "::1"
# [  FAILED  ] AddressSortingTest.TestSorterKnowsIpv6LoopbackIsAvailable (2 ms)
#
# Confirmed in 1.46.0 2022-05-06
address_sorting
%endif

%ifarch s390x
# Unexplained:
#
# Status is not ok: Setting authenticated associated data failed
# E0506 15:48:55.586625401 4020849 aes_gcm_test.cc:77]         assertion failed: status == GRPC_STATUS_OK
# *** SIGABRT received at time=1651852135 on cpu 1 ***
# PC: @      0x3ff89d98096  (unknown)  __pthread_kill_implementation
#     @      0x3ff89c82544  (unknown)  (unknown)
#     @      0x3ff89c827e0  (unknown)  (unknown)
#     @      0x3ff8a9fe490  (unknown)  (unknown)
#     @      0x3ff89d98096  (unknown)  __pthread_kill_implementation
#     @      0x3ff89d48530  (unknown)  gsignal
#     @      0x3ff89d2b5c0  (unknown)  abort
#     @      0x2aa28f84818  (unknown)  gsec_assert_ok()
#     @      0x2aa28f84944  (unknown)  gsec_test_random_encrypt_decrypt()
#     @      0x2aa28f82536  (unknown)  main
#     @      0x3ff89d2b872  (unknown)  __libc_start_call_main
#     @      0x3ff89d2b950  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa28f836f0  (unknown)  (unknown)
#
# Confirmed in 1.46.0 2022-05-06
alts_crypt
%endif

%ifarch s390x
# Unexplained:
#
# (aborted without output)
#
# Confirmed in 1.46.0 2022-05-06
alts_crypter
%endif

%ifarch s390x
# Unexplained:
#
# [ RUN      ] AltsConcurrentConnectivityTest.TestBasicClientServerHandshakes
# E0506 20:38:59.376480159 4049276 alts_grpc_privacy_integrity_record_protocol.cc:107] Failed to unprotect, More bytes written than expected. Frame decryption failed.
# [… 11 similar lines omitted …]
# /builddir/build/BUILD/grpc-1.46.0/test/core/tsi/alts/handshaker/alts_concurrent_connectivity_test.cc:244: Failure
# Expected equality of these values:
#   ev.type
#     Which is: 1
#   GRPC_OP_COMPLETE
#     Which is: 2
# connect_loop runner:0x3fffa47d718 got ev.type:1 i:0
# [  FAILED  ] AltsConcurrentConnectivityTest.TestBasicClientServerHandshakes (5004 ms)
# [ RUN      ] AltsConcurrentConnectivityTest.TestConcurrentClientServerHandshakes
# E0506 20:39:04.393443259 4049343 alts_grpc_privacy_integrity_record_protocol.cc:107] Failed to unprotect, More bytes written than expected. Frame decryption failed.
# [… 1033 similar lines omitted …]
# /builddir/build/BUILD/grpc-1.46.0/test/core/tsi/alts/handshaker/alts_concurrent_connectivity_test.cc:244: Failure
# Expected equality of these values:
#   ev.type
#     Which is: 1
#   GRPC_OP_COMPLETE
#     Which is: 2
# connect_loop runner:0x2aa06421b00 got ev.type:1 i:0
# [ … 343 lines with 49 similar errors omitted …]
# [  FAILED  ] AltsConcurrentConnectivityTest.TestConcurrentClientServerHandshakes (15017 ms)
# [ RUN      ] AltsConcurrentConnectivityTest.TestHandshakeFailsFastWhenPeerEndpointClosesConnectionAfterAccepting
# [       OK ] AltsConcurrentConnectivityTest.TestHandshakeFailsFastWhenPeerEndpointClosesConnectionAfterAccepting (4519 ms)
# [ RUN      ] AltsConcurrentConnectivityTest.TestHandshakeFailsFastWhenHandshakeServerClosesConnectionAfterAccepting
# E0506 20:39:23.930152511 4049976 alts_handshaker_client.cc:223] recv_buffer is nullptr in alts_tsi_handshaker_handle_response()
# [… 193 similar lines omitted …]
# [       OK ] AltsConcurrentConnectivityTest.TestHandshakeFailsFastWhenHandshakeServerClosesConnectionAfterAccepting (2237 ms)
# [ RUN      ] AltsConcurrentConnectivityTest.TestHandshakeFailsFastWhenHandshakeServerHangsAfterAccepting
# [       OK ] AltsConcurrentConnectivityTest.TestHandshakeFailsFastWhenHandshakeServerHangsAfterAccepting (244 ms)
# [----------] 5 tests from AltsConcurrentConnectivityTest (27024 ms total)
# [----------] Global test environment tear-down
# [==========] 5 tests from 1 test suite ran. (27024 ms total)
# [  PASSED  ] 3 tests.
# [  FAILED  ] 2 tests, listed below:
# [  FAILED  ] AltsConcurrentConnectivityTest.TestBasicClientServerHandshakes
# [  FAILED  ] AltsConcurrentConnectivityTest.TestConcurrentClientServerHandshakes
#  2 FAILED TESTS
# E0506 20:39:36.394518375 4049271 test_config.cc:175]         Timeout in waiting for gRPC shutdown
#
# Confirmed in 1.46.0 2022-05-06
alts_concurrent_connectivity
%endif

%ifarch s390x ppc64le
# Unexplained:
#
# (aborted without output)
#
# Confirmed in 1.46.0 2022-05-06
# Confirmed in 1.46.4 2022-08-26 in COPR on centos-stream+epel-next-9-ppc64le
# but NOT epel-9-ppc64le… what‽
alts_frame_protector
%endif

%ifarch s390x
# Unexplained:
#
# E0506 21:49:20.855933553 1468251 alts_grpc_integrity_only_record_protocol.cc:109] Failed to protect, Setting authenticated associated data failed
# E0506 21:49:20.856134615 1468251 alts_grpc_record_protocol_test.cc:283] assertion failed: status == TSI_OK
# *** SIGABRT received at time=1651873760 on cpu 0 ***
# PC: @      0x3ff85598096  (unknown)  __pthread_kill_implementation
#     @      0x3ff85482544  (unknown)  (unknown)
#     @      0x3ff854827e0  (unknown)  (unknown)
#     @      0x3ff861fe490  (unknown)  (unknown)
#     @      0x3ff85598096  (unknown)  __pthread_kill_implementation
#     @      0x3ff85548530  (unknown)  gsignal
#     @      0x3ff8552b5c0  (unknown)  abort
#     @      0x2aa1888375e  (unknown)  random_seal_unseal()
#     @      0x2aa18884008  (unknown)  alts_grpc_record_protocol_tests()
#     @      0x2aa1888258c  (unknown)  main
#     @      0x3ff8552b872  (unknown)  __libc_start_call_main
#     @      0x3ff8552b950  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa18882680  (unknown)  (unknown)
#
# Confirmed in 1.46.0 2022-05-06
alts_grpc_record_protocol
%endif

%ifarch s390x
# Unexplained:
#
# (aborted without output)
#
# Confirmed in 1.46.0 2022-05-06
alts_iovec_record_protocol
%endif

%ifarch s390x
# Unexplained:
#
# E0507 14:19:47.146439950 2465022 alts_grpc_integrity_only_record_protocol.cc:109] Failed to protect, Setting authenticated associated data failed
# E0507 14:19:47.146597694 2465022 alts_zero_copy_grpc_protector_test.cc:184] assertion failed: tsi_zero_copy_grpc_protector_protect( sender, &var->original_sb, &var->protected_sb) == TSI_OK
# *** SIGABRT received at time=1651933187 on cpu 0 ***
# PC: @      0x3ff89498096  (unknown)  __pthread_kill_implementation
#     @      0x3ff89382544  (unknown)  (unknown)
#     @      0x3ff893827e0  (unknown)  (unknown)
#     @      0x3ff8a0fe490  (unknown)  (unknown)
#     @      0x3ff89498096  (unknown)  __pthread_kill_implementation
#     @      0x3ff89448530  (unknown)  gsignal
#     @      0x3ff8942b5c0  (unknown)  abort
#     @      0x2aa1a0032d0  (unknown)  seal_unseal_small_buffer()
#     @      0x2aa1a003478  (unknown)  alts_zero_copy_protector_seal_unseal_small_buffer_tests()
#     @      0x2aa1a00254a  (unknown)  main
#     @      0x3ff8942b872  (unknown)  __libc_start_call_main
#     @      0x3ff8942b950  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa1a002630  (unknown)  (unknown)
#
# Confirmed in 1.46.0 2022-05-06
alts_zero_copy_grpc_protector
%endif

%ifarch aarch64 ppc64le s390x
# Unexplained (EPEL9 only):
#
# aarch64:
#
# E0520 13:28:14.548926683 2647909 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:28:14.548926833 2647779 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:28:14.595077604 2647782 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:28:14.648119479 2647908 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:28:14.749502403 2647905 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:28:14.902166294 2647773 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:28:14.952953893 2647782 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:28:15.547804374 2647791 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# terminate called after throwing an instance of 'std::runtime_error'
#   what():  random_device::random_device(const std::string&): device not available
# *** SIGABRT received at time=1653053295 on cpu 28 ***
# [address_is_readable.cc : 96] RAW: Failed to create pipe, errno=24
# [failure_signal_handler.cc : 331] RAW: Signal 6 raised at PC=0xffffa3fd9080 while already in AbslFailureSignalHandler()
# [… 17827 similar three-line blocks omitted …]
# *** SIGABRT received at time=1653053301 on cpu 28 ***
# PC: @     0xffffa3fd9080  (unknown)  __pthread_kill_implementation
#     @     0xffffa3df9750       4800  (unknown)
#     @     0xffffa4efc7ec        208  (unknown)
#     @     0xffffa3f944ec         32  gsignal
#     @     0xffffa3f7bd30        336  abort
#     @     0xffffa36ef1cc       3216  (unknown)
#     @     0xffffa36ef248        256  absl::lts_20211102::raw_logging_internal::RawLog()
# [symbolize_elf.inc : 1280] RAW: /usr/lib64/libabsl_debugging_internal.so.2111.0.0: open failed: errno=24
#     @     0xffffa351e1f0        160  (unknown)
# [symbolize_elf.inc : 1280] RAW: /usr/lib64/libabsl_stacktrace.so.2111.0.0: open failed: errno=24
#     @     0xffffa3da7358         48  (unknown)
# [symbolize_elf.inc : 1280] RAW: /usr/lib64/libabsl_stacktrace.so.2111.0.0: open failed: errno=24
#     @     0xffffa3da73dc         96  (unknown)
# [symbolize_elf.inc : 1280] RAW: /usr/lib64/libabsl_stacktrace.so.2111.0.0: open failed: errno=24
#     @     0xffffa3da750c         16  (unknown)
# [symbolize_elf.inc : 1280] RAW: /usr/lib64/libabsl_failure_signal_handler.so.2111.0.0: open failed: errno=24
#     @     0xffffa3df94c8        464  (unknown)
# [symbolize_elf.inc : 1280] RAW: /usr/lib64/libabsl_failure_signal_handler.so.2111.0.0: open failed: errno=24
#     @     0xffffa3df9750  (unknown)  (unknown)
#     @     0xffffa4efc7ec        208  (unknown)
#     @     0xffffa3f944ec         32  gsignal
#     @     0xffffa3f7bd30        336  abort
#     @     0xffffa36ef1cc       3216  (unknown)
#     @     0xffffa36ef248        256  absl::lts_20211102::raw_logging_internal::RawLog()
#     @     0xffffa351e1f0        160  absl::lts_20211102::debugging_internal::AddressIsReadable()
# [symbolize_elf.inc : 1280] RAW: /usr/lib64/libabsl_stacktrace.so.2111.0.0: open failed: errno=24
#     @     0xffffa3da7358         48  (unknown)
# [symbolize_elf.inc : 1280] RAW: /usr/lib64/libabsl_stacktrace.so.2111.0.0: open failed: errno=24
#     @     0xffffa3da73dc         96  (unknown)
# [symbolize_elf.inc : 1280] RAW: /usr/lib64/libabsl_stacktrace.so.2111.0.0: open failed: errno=24
#     @     0xffffa3da750c         16  (unknown)
# [symbolize_elf.inc : 1280] RAW: /usr/lib64/libabsl_failure_signal_handler.so.2111.0.0: open failed: errno=24
#     @     0xffffa3df94c8        464  (unknown)
# [symbolize_elf.inc : 1280] RAW: /usr/lib64/libabsl_failure_signal_handler.so.2111.0.0: open failed: errno=24
#     @     0xffffa3df9750  (unknown)  (unknown)
#     @     0xffffa4efc7ec        208  (unknown)
#     @     0xffffa3f944ec         32  gsignal
#     @     0xffffa3f7bd30        336  abort
#     @     0xffffa36ef1cc       3216  (unknown)
#     @     0xffffa36ef248        256  absl::lts_20211102::raw_logging_internal::RawLog()
#     @     0xffffa351e1f0        160  absl::lts_20211102::debugging_internal::AddressIsReadable()
#     @     0xffffa3da7358         48  (unknown)
#     @     0xffffa3da73dc         96  (unknown)
#     @     0xffffa3da750c         16  absl::lts_20211102::GetStackFramesWithContext()
#     @ ... and at least 200 more frames
#
# ppc64le:
#
# E0520 13:41:56.823280455  670749 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:56.823946978  670881 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:56.824023028  670880 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:56.824232961  670776 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:56.824360062  670773 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:56.824929562  670886 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:56.824992583  670749 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:56.829475610  670881 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:56.875571582  670752 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:56.980284646  670755 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:57.082101996  670879 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:57.133542671  670887 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:57.292037605  670884 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 13:41:57.840202100  670755 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# terminate called after throwing an instance of 'std::runtime_error'
#   what():  random_device::random_device(const std::string&): device not available
# *** SIGABRT received at time=1653054117 on cpu 2 ***
# [address_is_readable.cc : 96] RAW: Failed to create pipe, errno=24
# [failure_signal_handler.cc : 331] RAW: Signal 6 raised at PC=0x7fff91f66efc while already in AbslFailureSignalHandler()
# [… 34232 similar three-line blocks omitted …]
# *** SIGABRT received at time=1653054123 on cpu 3 ***
# PC: @     0x7fff91f66efc  (unknown)  __pthread_kill_implementation
#     @     0x7fff91cc1a3c       4384  (unknown)
#     @     0x7fff91f66f7c        224  __pthread_kill_implementation
#     @     0x7fff91f0633c         48  gsignal
#     @     0x7fff91ee076c        336  abort
#     @     0x7fff913a12b8       3200  (unknown)
#     @     0x7fff913a1310         48  absl::lts_20211102::raw_logging_internal::RawLog()
#     @     0x7fff910e24c4        272  absl::lts_20211102::debugging_internal::AddressIsReadable()
#     @     0x7fff91c51558        176  (unknown)
#     @     0x7fff91c51720        112  (unknown)
#     @     0x7fff91c51a18         32  absl::lts_20211102::GetStackFramesWithContext()
#     @     0x7fff91cc16e4        480  (unknown)
#     @     0x7fff91cc1a3c  (unknown)  (unknown)
#     @     0x7fff91f66f7c        224  __pthread_kill_implementation
#     @     0x7fff91f0633c         48  gsignal
#     @     0x7fff91ee076c        336  abort
#     @     0x7fff913a12b8       3200  (unknown)
#     @     0x7fff913a1310         48  absl::lts_20211102::raw_logging_internal::RawLog()
#     @     0x7fff910e24c4        272  absl::lts_20211102::debugging_internal::AddressIsReadable()
#     @     0x7fff91c51558        176  (unknown)
#     @     0x7fff91c51720        112  (unknown)
#     @     0x7fff91c51a18         32  absl::lts_20211102::GetStackFramesWithContext()
#     @     0x7fff91cc16e4        480  (unknown)
#     @     0x7fff91cc1a3c  (unknown)  (unknown)
#     @     0x7fff91f66f7c        224  __pthread_kill_implementation
#     @     0x7fff91f0633c         48  gsignal
#     @     0x7fff91ee076c        336  abort
#     @     0x7fff913a12b8       3200  (unknown)
#     @     0x7fff913a1310         48  absl::lts_20211102::raw_logging_internal::RawLog()
#     @     0x7fff910e24c4        272  absl::lts_20211102::debugging_internal::AddressIsReadable()
#     @     0x7fff91c51558        176  (unknown)
#     @     0x7fff91c51720        112  (unknown)
#     @     0x7fff91c51a18         32  absl::lts_20211102::GetStackFramesWithContext()
#     @ ... and at least 1000 more frames
#
# s390x
#
# E0520 14:55:38.075589878 2008339 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 14:55:38.115523588 2008365 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 14:55:38.220459390 2008198 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 14:55:38.273140893 2008354 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 14:55:38.541933196 2008349 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 14:55:38.705084891 2008349 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# E0520 14:55:39.071924831 2008349 tcp_server_posix.cc:216]    Failed accept4: Too many open files
# terminate called after throwing an instance of 'std::runtime_error'
#   what():  random_device::random_device(const std::string&): device not available
# *** SIGABRT received at time=1653058539 on cpu 0 ***
# [symbolize_elf.inc : 979] RAW: /proc/self/task/2008153/maps: errno=24
# PC: @      0x3ff914a8356  (unknown)  (unknown)
#     @      0x3ff90f81574  (unknown)  (unknown)
#     @      0x3ff90f817e0  (unknown)  (unknown)
#     @      0x3ff928fe490  (unknown)  (unknown)
#     @      0x3ff914a8356  (unknown)  (unknown)
#     @      0x3ff91458c90  (unknown)  (unknown)
#     @      0x3ff914326d0  (unknown)  (unknown)
#     @      0x3ff9173f0d8  (unknown)  (unknown)
#     @      0x3ff9173c90e  (unknown)  (unknown)
#     @      0x3ff9173c998  (unknown)  (unknown)
#     @      0x3ff9173ccc6  (unknown)  (unknown)
#     @      0x3ff9172d534  (unknown)  (unknown)
#     @      0x3ff917718c8  (unknown)  (unknown)
#     @      0x2aa39973244  (unknown)  (unknown)
#     @      0x2aa399223ca  (unknown)  (unknown)
#     @      0x3ff91438c42  (unknown)  (unknown)
#     @      0x3ff91438d1e  (unknown)  (unknown)
#     @      0x2aa39922b10  (unknown)  (unknown)
#
# Confirmed in 1.46.2 2022-05-20 (EPEL9)
client_channel_stress
%endif

# Unexplained, flaky:
#
# (hangs indefinitely, timeout triggered)
#
# Confirmed in 1.46.1 2022-05-14 (on at least ppc64le)
client_ssl

%ifarch x86_64
# Unexplained:
#
# [ RUN      ] ExamineStackTest.AbseilStackProvider
# /builddir/build/BUILD/grpc-1.46.0/test/core/gprpp/examine_stack_test.cc:75: Failure
# Value of: stack_trace->find("GetCurrentStackTrace") != std::string::npos
#   Actual: false
# Expected: true
# [  FAILED  ] ExamineStackTest.AbseilStackProvider (0 ms)
#
# Confirmed in 1.46.0 2022-05-09
examine_stack
%endif

%ifarch s390x
# Unexplained:
#
# E0509 15:02:47.269422552 2434394 cq_verifier.cc:228]         no event received, but expected:tag(257) GRPC_OP_COMPLETE success=1 /builddir/build/BUILD/grpc-1.46.0/test/core/end2end/goaway_server_test.cc:279
# tag(769) GRPC_OP_COMPLETE success=1 /builddir/build/BUILD/grpc-1.46.0/test/core/end2end/goaway_server_test.cc:280
# *** SIGABRT received at time=1652108567 on cpu 1 ***
# PC: @      0x3ffb6e98096  (unknown)  __pthread_kill_implementation
#     @      0x3ffb6d82544  (unknown)  (unknown)
#     @      0x3ffb6d827e0  (unknown)  (unknown)
#     @      0x3ffb7cfe490  (unknown)  (unknown)
#     @      0x3ffb6e98096  (unknown)  __pthread_kill_implementation
#     @      0x3ffb6e48530  (unknown)  gsignal
#     @      0x3ffb6e2b5c0  (unknown)  abort
#     @      0x2aa1b406a72  (unknown)  cq_verify()
#     @      0x2aa1b404f9a  (unknown)  main
#     @      0x3ffb6e2b872  (unknown)  __libc_start_call_main
#     @      0x3ffb6e2b950  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa1b405720  (unknown)  (unknown)
#
# Confirmed in 1.46.0 2022-05-09
goaway_server
%endif

# Unexplained:
#
# [ RUN      ] GrpcToolTest.CallCommandWithTimeoutDeadlineSet
# [libprotobuf ERROR google/protobuf/text_format.cc:335] Error parsing text-format grpc.testing.SimpleRequest: 1:7: Message type "grpc.testing.SimpleRequest" has no field named "redhat".
# Failed to convert text format to proto.
# Failed to parse request.
# /builddir/build/BUILD/grpc-1.46.0/test/cpp/util/grpc_tool_test.cc:915: Failure
# Value of: 0 == GrpcToolMainLib(ArraySize(argv), argv, TestCliCredentials(), std::bind(PrintStream, &output_stream, std::placeholders::_1))
#   Actual: false
# Expected: true
# /builddir/build/BUILD/grpc-1.46.0/test/cpp/util/grpc_tool_test.cc:920: Failure
# Value of: nullptr != strstr(output_stream.str().c_str(), "message: \"true\"")
#   Actual: false
# Expected: true
# [  FAILED  ] GrpcToolTest.CallCommandWithTimeoutDeadlineSet (4 ms)
#
# Confirmed in 1.46.0 2022-05-09
grpc_tool

%ifarch s390x
# Unexplained:
#
# *** SIGABRT received at time=1652104042 on cpu 1 ***
# PC: @      0x3ffa5398096  (unknown)  __pthread_kill_implementation
#     @      0x3ffa5282544  (unknown)  (unknown)
#     @      0x3ffa52827e0  (unknown)  (unknown)
#     @      0x3ffa59fe490  (unknown)  (unknown)
#     @      0x3ffa5398096  (unknown)  __pthread_kill_implementation
#     @      0x3ffa5348530  (unknown)  gsignal
#     @      0x3ffa532b5c0  (unknown)  abort
#     @      0x2aa2b40145e  (unknown)  verification_test()
#     @      0x2aa2b4011e8  (unknown)  main
#     @      0x3ffa532b872  (unknown)  __libc_start_call_main
#     @      0x3ffa532b950  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa2b401270  (unknown)  (unknown)
#
# Confirmed in 1.46.0 2022-05-09
murmur_hash
%endif

%ifarch x86_64
# Unexplained:
#
# [ RUN      ] StackTracerTest.Basic
# /builddir/build/BUILD/grpc-1.46.0/test/core/util/stack_tracer_test.cc:36: Failure
# Value of: absl::StrContains(stack_trace, "Basic")
#   Actual: false
# Expected: true
# [  FAILED  ] StackTracerTest.Basic (0 ms)
#
# Confirmed in 1.46.0 2022-05-09
stack_tracer
%endif

%ifarch aarch64 x86_64 ppc64le s390x
# Unexplained:
#
# This may be flaky and sometimes succeed; this was known to be the case on
# ppc64le in older versions.
#
# aarch64, x86_64, ppc64le:
#
# [ RUN      ] CredentialsTest.TestOauth2TokenFetcherCredsParsingEmptyHttpBody
# E0509 16:23:59.122730405 3124460 oauth2_credentials.cc:165]  Call to http server ended with error 401 [{"access_token":"ya29.AHES6ZRN3-HlhAPya30GnW_bHSb_", "expires_in":3599,  "token_type":"Bearer"}].
# *** SIGSEGV received at time=1652113439 on cpu 3 ***
# PC: @     0x7f13bf51165c  (unknown)  __strlen_evex
#     @               0x33  (unknown)  (unknown)
#
# s390x (EPEL9 only):
#
# [ RUN      ] CredentialsTest.TestOauth2TokenFetcherCredsParsingEmptyHttpBody
# E0520 19:39:29.709945032 2075725 oauth2_credentials.cc:165]  Call to http server ended with error 401 [{"access_token":"ya29.AHES6ZRN3-HlhAPya30GnW_bHSb_", "expires_in":3599,  "token_type":"Bearer"}].
# *** SIGSEGV received at time=1653075569 on cpu 1 ***
# PC: @      0x3ff98feff4c  (unknown)  grpc_oauth2_token_fetcher_credentials_parse_server_response()
#     @      0x3ff97e01574  (unknown)  (unknown)
#     @      0x3ff97e017e0  (unknown)  (unknown)
#     @      0x3ff992fe490  (unknown)  (unknown)
#     @      0x3ff98feff4c  (unknown)  grpc_oauth2_token_fetcher_credentials_parse_server_response()
#     @      0x2aa3b4abb90  (unknown)  grpc_core::(anonymous namespace)::CredentialsTest_TestOauth2TokenFetcherCredsParsingEmptyHttpBody_Test::TestBody()
#     @      0x2aa3b50f766  (unknown)  testing::internal::HandleExceptionsInMethodIfSupported<>()
#     @      0x2aa3b4fcbfa  (unknown)  testing::Test::Run()
#     @      0x2aa3b4fcea0  (unknown)  testing::TestInfo::Run()
#     @      0x2aa3b4fd794  (unknown)  testing::TestSuite::Run()
#     @      0x2aa3b503898  (unknown)  testing::internal::UnitTestImpl::RunAllTests()
#     @      0x2aa3b50fcf6  (unknown)  testing::internal::HandleExceptionsInMethodIfSupported<>()
#     @      0x2aa3b4fcfe2  (unknown)  testing::UnitTest::Run()
#     @      0x2aa3b49ea1e  (unknown)  main
#     @      0x3ff97eb8c42  (unknown)  __libc_start_call_main
#     @      0x3ff97eb8d1e  (unknown)  __libc_start_main@GLIBC_2.2
#     @      0x2aa3b4a3d00  (unknown)  (unknown)
#
# Confirmed in 1.46.0 2022-05-09
test_core_security_credentials
%endif

# It looks like server_key_log has the right lines, but in an unexpected order.
# It is not immediately obvious if this a real problem, or an implementation
# quirk. Opinions about whether, or how, to report this upstream are welcome!
#
# [ RUN      ] TlsKeyLogging/TlsKeyLoggingEnd2EndTest.KeyLogging/TestScenario__num_listening_ports_5__share_tls_key_log_file_false__enable_tls_key_logging_true
# /builddir/build/BUILD/grpc-1.45.2/test/cpp/end2end/tls_key_export_test.cc:277: Failure
# Value of: server_key_log
# Expected: is equal to "SERVER_HANDSHAKE_TRAFFIC_SECRET cbe6c0edbc9729ca0ac78c15a707661c13efbf9c88d702f9746771e38e478b97 e2d3f9cb30e7eef95f95e3bca6f5e4258e42cc7903c424529730f2397ea6444b8c5e6e8c40b6f8d2060141a045ef814c\rEXPORTER_SECRET cbe6c0edbc9729ca0ac78c15a707661c13efbf9c88d702f9746771e38e478b97 820a4529b3e9614df378adb43a712ebc472b7fc91b6a92ff3421fb5870dd18782e7fb47e261eca093d9b8285e4ff17e0\rSERVER_TRAFFIC_SECRET_0 cbe6c0edbc9729ca0ac78c15a707661c13efbf9c88d702f9746771e38e478b97 dfac76dd16ed221785dc5e41fb1243430bddd70d78fe33344c8cc899d1e1b3f56d6865a2506044674063e9d32902588e\rCLIENT_HANDSHAKE_TRAFFIC_SECRET cbe6c0edbc9729ca0ac78c15a707661c13efbf9c88d702f9746771e38e478b97 f2f276c097044d63448a3413109702cd6413e6bbd75b3a40208c3fb5a9a0c8ca86d4a0460e1a04dcc025571e1edbb927\rCLIENT_TRAFFIC_SECRET_0 cbe6c0edbc9729ca0ac78c15a707661c13efbf9c88d702f9746771e38e478b97 8abeb453616823875792497d98bc6032f772a6f4cd75716209c49c4abc4ef470e6fd4ab274b7019162a6c584ff94ec4b\r"
#   Actual: "SERVER_HANDSHAKE_TRAFFIC_SECRET cbe6c0edbc9729ca0ac78c15a707661c13efbf9c88d702f9746771e38e478b97 e2d3f9cb30e7eef95f95e3bca6f5e4258e42cc7903c424529730f2397ea6444b8c5e6e8c40b6f8d2060141a045ef814c\rCLIENT_HANDSHAKE_TRAFFIC_SECRET cbe6c0edbc9729ca0ac78c15a707661c13efbf9c88d702f9746771e38e478b97 f2f276c097044d63448a3413109702cd6413e6bbd75b3a40208c3fb5a9a0c8ca86d4a0460e1a04dcc025571e1edbb927\rEXPORTER_SECRET cbe6c0edbc9729ca0ac78c15a707661c13efbf9c88d702f9746771e38e478b97 820a4529b3e9614df378adb43a712ebc472b7fc91b6a92ff3421fb5870dd18782e7fb47e261eca093d9b8285e4ff17e0\rSERVER_TRAFFIC_SECRET_0 cbe6c0edbc9729ca0ac78c15a707661c13efbf9c88d702f9746771e38e478b97 dfac76dd16ed221785dc5e41fb1243430bddd70d78fe33344c8cc899d1e1b3f56d6865a2506044674063e9d32902588e\rCLIENT_TRAFFIC_SECRET_0 cbe6c0edbc9729ca0ac78c15a707661c13efbf9c88d702f9746771e38e478b97 8abeb453616823875792497d98bc6032f772a6f4cd75716209c49c4abc4ef470e6fd4ab274b7019162a6c584ff94ec4b\r"
# /builddir/build/BUILD/grpc-1.45.2/test/cpp/end2end/tls_key_export_test.cc:277: Failure
# Value of: server_key_log
# Expected: is equal to "SERVER_HANDSHAKE_TRAFFIC_SECRET f3f5bb032b5283139d8e69c5e7d408b0e58b32b857b790c28bb81083c1f08751 aaa28bd7a945c3fccb1248bd024a604e2825891009af24bf44376d0ba36983dc243c7cb272e8f403db8762d6f44f1c3c\rEXPORTER_SECRET f3f5bb032b5283139d8e69c5e7d408b0e58b32b857b790c28bb81083c1f08751 c4a36ba53829243df5fccf0bf416c889e9c8813353a4487615e33dd443e5f196267c0fb7bacb8ee5b23f9c8c38c46b2e\rSERVER_TRAFFIC_SECRET_0 f3f5bb032b5283139d8e69c5e7d408b0e58b32b857b790c28bb81083c1f08751 89765e5e4cbd62a3be738f4c2ceb4be2e3fe204245f9765cab0f026ea1ec2e686d0df06291a1ae44b744a50e9493f944\rCLIENT_HANDSHAKE_TRAFFIC_SECRET f3f5bb032b5283139d8e69c5e7d408b0e58b32b857b790c28bb81083c1f08751 6ce17c81bb29ef1660e4404ac61755ba438a4c26bb93e812602e86329c03c6d63b6db282d9e6d0827025a43e2a6db507\rCLIENT_TRAFFIC_SECRET_0 f3f5bb032b5283139d8e69c5e7d408b0e58b32b857b790c28bb81083c1f08751 6a816d2d67967d1d455b69894ee731e41794b3fe299220bae615e66727d112f58d8982675a5d533d49dc0378bf9fb103\r"
#   Actual: "SERVER_HANDSHAKE_TRAFFIC_SECRET f3f5bb032b5283139d8e69c5e7d408b0e58b32b857b790c28bb81083c1f08751 aaa28bd7a945c3fccb1248bd024a604e2825891009af24bf44376d0ba36983dc243c7cb272e8f403db8762d6f44f1c3c\rCLIENT_HANDSHAKE_TRAFFIC_SECRET f3f5bb032b5283139d8e69c5e7d408b0e58b32b857b790c28bb81083c1f08751 6ce17c81bb29ef1660e4404ac61755ba438a4c26bb93e812602e86329c03c6d63b6db282d9e6d0827025a43e2a6db507\rEXPORTER_SECRET f3f5bb032b5283139d8e69c5e7d408b0e58b32b857b790c28bb81083c1f08751 c4a36ba53829243df5fccf0bf416c889e9c8813353a4487615e33dd443e5f196267c0fb7bacb8ee5b23f9c8c38c46b2e\rSERVER_TRAFFIC_SECRET_0 f3f5bb032b5283139d8e69c5e7d408b0e58b32b857b790c28bb81083c1f08751 89765e5e4cbd62a3be738f4c2ceb4be2e3fe204245f9765cab0f026ea1ec2e686d0df06291a1ae44b744a50e9493f944\rCLIENT_TRAFFIC_SECRET_0 f3f5bb032b5283139d8e69c5e7d408b0e58b32b857b790c28bb81083c1f08751 6a816d2d67967d1d455b69894ee731e41794b3fe299220bae615e66727d112f58d8982675a5d533d49dc0378bf9fb103\r"
# /builddir/build/BUILD/grpc-1.45.2/test/cpp/end2end/tls_key_export_test.cc:277: Failure
# Value of: server_key_log
# Expected: is equal to "SERVER_HANDSHAKE_TRAFFIC_SECRET 7c9ff52917c484e1296e07db3ebe639b0451d53e4e96ba49b6e2f730b08dbecc 4faa820090880462e1b2e9a3bb83e2f09744986e72e26e57d6c9ac7bb72058b57adac41c123de64e4b3b72719bc8eea4\rEXPORTER_SECRET 7c9ff52917c484e1296e07db3ebe639b0451d53e4e96ba49b6e2f730b08dbecc e43c4527fbe9b5a552604b7cc92f47ab79cdf6f58804b06f0e02a634eb252f95b78b202634d084c46b24b132187e603d\rSERVER_TRAFFIC_SECRET_0 7c9ff52917c484e1296e07db3ebe639b0451d53e4e96ba49b6e2f730b08dbecc 2da0bcf4584dd9cb1795f2d8adc4e766c0d6c2d0295cdd5f6ec0e9eed057613d81ab386e96bf1a4d2364d66a677acc3c\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 7c9ff52917c484e1296e07db3ebe639b0451d53e4e96ba49b6e2f730b08dbecc 95beadcad1b17f86e504b4bf525406c6a29a2251867567aa93ce23b531b62f9b0c2c7e82d061c2a741edd96d84874ad5\rCLIENT_TRAFFIC_SECRET_0 7c9ff52917c484e1296e07db3ebe639b0451d53e4e96ba49b6e2f730b08dbecc 0f047139f6c4dfafb590f3a62ee812cefc8550aaa2f15edca843f0365d5a17b4507ad5f63a369974e83cd1ec0fdb5049\r"
#   Actual: "SERVER_HANDSHAKE_TRAFFIC_SECRET 7c9ff52917c484e1296e07db3ebe639b0451d53e4e96ba49b6e2f730b08dbecc 4faa820090880462e1b2e9a3bb83e2f09744986e72e26e57d6c9ac7bb72058b57adac41c123de64e4b3b72719bc8eea4\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 7c9ff52917c484e1296e07db3ebe639b0451d53e4e96ba49b6e2f730b08dbecc 95beadcad1b17f86e504b4bf525406c6a29a2251867567aa93ce23b531b62f9b0c2c7e82d061c2a741edd96d84874ad5\rEXPORTER_SECRET 7c9ff52917c484e1296e07db3ebe639b0451d53e4e96ba49b6e2f730b08dbecc e43c4527fbe9b5a552604b7cc92f47ab79cdf6f58804b06f0e02a634eb252f95b78b202634d084c46b24b132187e603d\rSERVER_TRAFFIC_SECRET_0 7c9ff52917c484e1296e07db3ebe639b0451d53e4e96ba49b6e2f730b08dbecc 2da0bcf4584dd9cb1795f2d8adc4e766c0d6c2d0295cdd5f6ec0e9eed057613d81ab386e96bf1a4d2364d66a677acc3c\rCLIENT_TRAFFIC_SECRET_0 7c9ff52917c484e1296e07db3ebe639b0451d53e4e96ba49b6e2f730b08dbecc 0f047139f6c4dfafb590f3a62ee812cefc8550aaa2f15edca843f0365d5a17b4507ad5f63a369974e83cd1ec0fdb5049\r"
# /builddir/build/BUILD/grpc-1.45.2/test/cpp/end2end/tls_key_export_test.cc:277: Failure
# Value of: server_key_log
# Expected: is equal to "SERVER_HANDSHAKE_TRAFFIC_SECRET 59fd362f394bf867a5bcf4c6dd600790bd784424bdea837a47698c85082eebff d09d807afd55f9c1582e6879d97a262fa26f19db06cb57a14ce53f6be372dbb70ed036f8bf7d5f6a3168771eb2e4de30\rEXPORTER_SECRET 59fd362f394bf867a5bcf4c6dd600790bd784424bdea837a47698c85082eebff 5e76f891f0bbf4fa51a6fc5cc52aadf150995804a3ab81a185efb3ff02a6847ba7945cdd9a3a4c99ab3a657d150e1ca6\rSERVER_TRAFFIC_SECRET_0 59fd362f394bf867a5bcf4c6dd600790bd784424bdea837a47698c85082eebff 4c2839a7d98111e43bccabc839fd76ca6fc35b6bf294d93e800d8d0c8536b5b71eb11b6b2e5233227f42f2e4ba04645e\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 59fd362f394bf867a5bcf4c6dd600790bd784424bdea837a47698c85082eebff 920fc5885c48f5aa5d79fc6749e29f9bc8841f73a87a949888e7bbfbabaff970bf54ed668e86c591b5d11c2ff59720e4\rCLIENT_TRAFFIC_SECRET_0 59fd362f394bf867a5bcf4c6dd600790bd784424bdea837a47698c85082eebff a1691a7847eb12b18d58152bb2b849ae588abf54b6f9ff019abebedb3e749e13bbe039526137d6b5ae2d6e630bb4589c\r"
#   Actual: "SERVER_HANDSHAKE_TRAFFIC_SECRET 59fd362f394bf867a5bcf4c6dd600790bd784424bdea837a47698c85082eebff d09d807afd55f9c1582e6879d97a262fa26f19db06cb57a14ce53f6be372dbb70ed036f8bf7d5f6a3168771eb2e4de30\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 59fd362f394bf867a5bcf4c6dd600790bd784424bdea837a47698c85082eebff 920fc5885c48f5aa5d79fc6749e29f9bc8841f73a87a949888e7bbfbabaff970bf54ed668e86c591b5d11c2ff59720e4\rEXPORTER_SECRET 59fd362f394bf867a5bcf4c6dd600790bd784424bdea837a47698c85082eebff 5e76f891f0bbf4fa51a6fc5cc52aadf150995804a3ab81a185efb3ff02a6847ba7945cdd9a3a4c99ab3a657d150e1ca6\rSERVER_TRAFFIC_SECRET_0 59fd362f394bf867a5bcf4c6dd600790bd784424bdea837a47698c85082eebff 4c2839a7d98111e43bccabc839fd76ca6fc35b6bf294d93e800d8d0c8536b5b71eb11b6b2e5233227f42f2e4ba04645e\rCLIENT_TRAFFIC_SECRET_0 59fd362f394bf867a5bcf4c6dd600790bd784424bdea837a47698c85082eebff a1691a7847eb12b18d58152bb2b849ae588abf54b6f9ff019abebedb3e749e13bbe039526137d6b5ae2d6e630bb4589c\r"
# /builddir/build/BUILD/grpc-1.45.2/test/cpp/end2end/tls_key_export_test.cc:277: Failure
# Value of: server_key_log
# Expected: is equal to "SERVER_HANDSHAKE_TRAFFIC_SECRET 770d00f300fc4e6175da566d6d6b8d0fc247a27e7f1ec329b69d575e2a1f7bac e6fedd13291bdc2820ecbe310ffd3c778f4a74ddee894d617fb94bce1ac8ae89c2ea71b34e0036c48e8b7cb410a3ccad\rEXPORTER_SECRET 770d00f300fc4e6175da566d6d6b8d0fc247a27e7f1ec329b69d575e2a1f7bac 50cce74e4c6ac319c384cd9de9b68e0bc299f26a0ed2142d710b0cf361fd188eabb2c7f3bd8113cae2fcb4f3eca66c22\rSERVER_TRAFFIC_SECRET_0 770d00f300fc4e6175da566d6d6b8d0fc247a27e7f1ec329b69d575e2a1f7bac 90d2e703ad1079114b224f53a5f8225fe0305987d6a219527d28903ccae552f27b5ca7089d7790d66da0cccbdfd26645\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 770d00f300fc4e6175da566d6d6b8d0fc247a27e7f1ec329b69d575e2a1f7bac 6b0dcc8075ee0b2188b6cf781662be3c8b3e43476ac48f2ab1257adb8c9e9c74b5824347e18c4f969c6cbb30d5c7207f\rCLIENT_TRAFFIC_SECRET_0 770d00f300fc4e6175da566d6d6b8d0fc247a27e7f1ec329b69d575e2a1f7bac 1acef388db865ac638051ee13f5b6ef7a9ca79822e0436a11aaf64a1af2cb07a72cf26a115cb35556637a0a7c2fd27a2\r"
#   Actual: "SERVER_HANDSHAKE_TRAFFIC_SECRET 770d00f300fc4e6175da566d6d6b8d0fc247a27e7f1ec329b69d575e2a1f7bac e6fedd13291bdc2820ecbe310ffd3c778f4a74ddee894d617fb94bce1ac8ae89c2ea71b34e0036c48e8b7cb410a3ccad\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 770d00f300fc4e6175da566d6d6b8d0fc247a27e7f1ec329b69d575e2a1f7bac 6b0dcc8075ee0b2188b6cf781662be3c8b3e43476ac48f2ab1257adb8c9e9c74b5824347e18c4f969c6cbb30d5c7207f\rEXPORTER_SECRET 770d00f300fc4e6175da566d6d6b8d0fc247a27e7f1ec329b69d575e2a1f7bac 50cce74e4c6ac319c384cd9de9b68e0bc299f26a0ed2142d710b0cf361fd188eabb2c7f3bd8113cae2fcb4f3eca66c22\rSERVER_TRAFFIC_SECRET_0 770d00f300fc4e6175da566d6d6b8d0fc247a27e7f1ec329b69d575e2a1f7bac 90d2e703ad1079114b224f53a5f8225fe0305987d6a219527d28903ccae552f27b5ca7089d7790d66da0cccbdfd26645\rCLIENT_TRAFFIC_SECRET_0 770d00f300fc4e6175da566d6d6b8d0fc247a27e7f1ec329b69d575e2a1f7bac 1acef388db865ac638051ee13f5b6ef7a9ca79822e0436a11aaf64a1af2cb07a72cf26a115cb35556637a0a7c2fd27a2\r"
# [  FAILED  ] TlsKeyLogging/TlsKeyLoggingEnd2EndTest.KeyLogging/TestScenario__num_listening_ports_5__share_tls_key_log_file_false__enable_tls_key_logging_true, where GetParam() = 8-byte object <05-00 00-00 00-01 00-00> (66 ms)
# [ RUN      ] TlsKeyLogging/TlsKeyLoggingEnd2EndTest.KeyLogging/TestScenario__num_listening_ports_5__share_tls_key_log_file_true__enable_tls_key_logging_true
# /builddir/build/BUILD/grpc-1.45.2/test/cpp/end2end/tls_key_export_test.cc:277: Failure
# Value of: server_key_log
# Expected: is equal to "SERVER_HANDSHAKE_TRAFFIC_SECRET 4a8ed2a8c89cd95df5f9d01850058410323c6af346b963681db84235dfa2ec4d 73d93193674a9695da3a647bba6c3f73fbfc97c4aa8ec7c6c5c4fb3bd5c6820ce08c0a1820180e3ce43aab2f75b72aac\rEXPORTER_SECRET 4a8ed2a8c89cd95df5f9d01850058410323c6af346b963681db84235dfa2ec4d 763fa5cb1c97c94afc21ebc009e892dc383e201a6e9e96edc23c17b5cd97f524ba52644a1df4a75615df043de4fbcb39\rSERVER_TRAFFIC_SECRET_0 4a8ed2a8c89cd95df5f9d01850058410323c6af346b963681db84235dfa2ec4d e5f7b8ab7a46968f2ad0dcaf6af74ad22a9da21fb832b5d4bbf307cc791fa5354ba6ba8fc43397b3895b5fc83c8f65f4\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 4a8ed2a8c89cd95df5f9d01850058410323c6af346b963681db84235dfa2ec4d f5f336b8428667b13bf8a67bb0dcb9c21ba2fe8cfe1281d2a41c55b170b49ae79b4a5d1eac5742d9658af5ef547f344d\rCLIENT_TRAFFIC_SECRET_0 4a8ed2a8c89cd95df5f9d01850058410323c6af346b963681db84235dfa2ec4d 6c16bd5f35371de56139a027f06004bc264725922a09bfef8cdf7a33e7b4b8c69f0bf6293e2cb3523c7f22e84410176d\rSERVER_HANDSHAKE_TRAFFIC_SECRET 22d345d7c46834996e8db60793f8dbfe71ea9adc4124ac72934a56418b923736 ea5bed615069634fe81ec1a9f6096e5ee1c74fe321743a65898eecfbfab9956e73d7de35a9eba0fc55b957ba6cdf34ee\rEXPORTER_SECRET 22d345d7c46834996e8db60793f8dbfe71ea9adc4124ac72934a56418b923736 113d480846d1db2326c46f52559f173d5a390220618ea81afd5a63165a64cc911ff011dbf915de20699251a25036655a\rSERVER_TRAFFIC_SECRET_0 22d345d7c46834996e8db60793f8dbfe71ea9adc4124ac72934a56418b923736 443c7cfb34709b1ce2e80592e2192786ee6e1ad86f145a32e1ec9fc076b682b5cdcc7def181fbc51f835cf4888f0f85b\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 22d345d7c46834996e8db60793f8dbfe71ea9adc4124ac72934a56418b923736 8fd27dfdb917133ba4a9dc594821ca3df81fecd60da72dd8f5b779a96cbd3a41ce9e93b435eac4850d29faddb7500dc8\rCLIENT_TRAFFIC_SECRET_0 22d345d7c46834996e8db60793f8dbfe71ea9adc4124ac72934a56418b923736 691969bbf02c386f2758cc5dfd197fc7272430902b0c90a4b365ab3a1cc5066a616bc50ad29ceecba6f23dc85bd277e5\rSERVER_HANDSHAKE_TRAFFIC_SECRET f274f840c4d297c3fdefa0dd5695c4573c9037075b9d79432e88faa4a187385a 3c17149401c2b3878cbe3105164d362bba2e098e0d1de09bf69939568a2c69133c0ddc1c8fa76903e5e293b1197a01fb\rEXPORTER_SECRET f274f840c4d297c3fdefa0dd5695c4573c9037075b9d79432e88faa4a187385a e668b4888a058ce00a93da55ac690365336ee6cf331ad2ae97e0b8c837cf0b449aed4940ee2a3ab56c045056c1d5574d\rSERVER_TRAFFIC_SECRET_0 f274f840c4d297c3fdefa0dd5695c4573c9037075b9d79432e88faa4a187385a 7bd47384a53931188daab512bb59cedfd2f309ed189f80ad737f4465cd00fb472cc11992204c2252d534ffc9b48bc097\rCLIENT_HANDSHAKE_TRAFFIC_SECRET f274f840c4d297c3fdefa0dd5695c4573c9037075b9d79432e88faa4a187385a 6ae0594f0c38c3abf6a65b428f00347c6aee8b60a54fd702458ab439c6f718c58bdf55b92c42b3d968663e385922294b\rCLIENT_TRAFFIC_SECRET_0 f274f840c4d297c3fdefa0dd5695c4573c9037075b9d79432e88faa4a187385a cd9ed62e171e71d65580455e7ce374a2a91e15f3f889441144c23b2a54e6c4b2daf98e09525c317d871686872a5f2d81\rSERVER_HANDSHAKE_TRAFFIC_SECRET 3021d89743e0308f3bfe589aa16ed52d82bafe35506b5bfcdc31863f3fa9aaff 330b459fed7217708e8163baf5eabe6a34a45bbf3d4c1bde32f7bcce29016bec85539ee7724c73d23cbaaa5f8e100a34\rEXPORTER_SECRET 3021d89743e0308f3bfe589aa16ed52d82bafe35506b5bfcdc31863f3fa9aaff cc32ae2d7a1bd46bc38569ebf0987e36b4ef1037f5280099a80e3ee5cf83a0be1d8283f5d925e12c78b27660de63cc9f\rSERVER_TRAFFIC_SECRET_0 3021d89743e0308f3bfe589aa16ed52d82bafe35506b5bfcdc31863f3fa9aaff 2be00b20bdf6157af69c6bac8806d5dfb6c13a3cfa9d314c73d46ead360f3a9c1562eb2eb1a073c86fab2ceda4da2a56\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 3021d89743e0308f3bfe589aa16ed52d82bafe35506b5bfcdc31863f3fa9aaff e106db0914f10fc6612d4b1cbdeb92bffc3ec4c21ab906a17a3a060b7a5d91e805a41b98822f9a6482e8eb510fb37ba4\rCLIENT_TRAFFIC_SECRET_0 3021d89743e0308f3bfe589aa16ed52d82bafe35506b5bfcdc31863f3fa9aaff 7505e76f6398b39352003bbc3268a36a137ef4ecb2a795a8f53e9a77fdf57b5b1e2793f2ed6cb721e991920d87607aa7\rSERVER_HANDSHAKE_TRAFFIC_SECRET 14e07d555479cf6be60e056105482571a0b06a92c686246a0dfecf2c5ef7eb18 c96ade516607c05ac9b5016caf4d554ba26c8b540c37eb5d4c6a4f1849b4e50da20614cf55909d0998e744a4b0e9e276\rEXPORTER_SECRET 14e07d555479cf6be60e056105482571a0b06a92c686246a0dfecf2c5ef7eb18 4e5196a9c611ae860f8b8b7d16f8130fcfdacdf899831997e7a410e18d2d9b19f5eaa2aa79b868b5b6bad29a84e97fff\rSERVER_TRAFFIC_SECRET_0 14e07d555479cf6be60e056105482571a0b06a92c686246a0dfecf2c5ef7eb18 aac75064ad90e8b08818e4c6d0b895639f78f89d5ea9e3bc780b9fc295f2430fd4edb30eef91202bcc61b19774bcbdd9\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 14e07d555479cf6be60e056105482571a0b06a92c686246a0dfecf2c5ef7eb18 658902e283b741d5057db588d38b0d565fe3479bb242a7b93ec614f94d142b86608c9b6e6e93794c28e06ab7a12e3382\rCLIENT_TRAFFIC_SECRET_0 14e07d555479cf6be60e056105482571a0b06a92c686246a0dfecf2c5ef7eb18 062684c5b1bcb1ba7b1997c88694d06f81a250f7bb90b9c0214989753eca11c2308a0e5431d6c80607ad5cd7f83ad98d\r"
#   Actual: "SERVER_HANDSHAKE_TRAFFIC_SECRET 4a8ed2a8c89cd95df5f9d01850058410323c6af346b963681db84235dfa2ec4d 73d93193674a9695da3a647bba6c3f73fbfc97c4aa8ec7c6c5c4fb3bd5c6820ce08c0a1820180e3ce43aab2f75b72aac\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 4a8ed2a8c89cd95df5f9d01850058410323c6af346b963681db84235dfa2ec4d f5f336b8428667b13bf8a67bb0dcb9c21ba2fe8cfe1281d2a41c55b170b49ae79b4a5d1eac5742d9658af5ef547f344d\rEXPORTER_SECRET 4a8ed2a8c89cd95df5f9d01850058410323c6af346b963681db84235dfa2ec4d 763fa5cb1c97c94afc21ebc009e892dc383e201a6e9e96edc23c17b5cd97f524ba52644a1df4a75615df043de4fbcb39\rSERVER_TRAFFIC_SECRET_0 4a8ed2a8c89cd95df5f9d01850058410323c6af346b963681db84235dfa2ec4d e5f7b8ab7a46968f2ad0dcaf6af74ad22a9da21fb832b5d4bbf307cc791fa5354ba6ba8fc43397b3895b5fc83c8f65f4\rCLIENT_TRAFFIC_SECRET_0 4a8ed2a8c89cd95df5f9d01850058410323c6af346b963681db84235dfa2ec4d 6c16bd5f35371de56139a027f06004bc264725922a09bfef8cdf7a33e7b4b8c69f0bf6293e2cb3523c7f22e84410176d\rSERVER_HANDSHAKE_TRAFFIC_SECRET 22d345d7c46834996e8db60793f8dbfe71ea9adc4124ac72934a56418b923736 ea5bed615069634fe81ec1a9f6096e5ee1c74fe321743a65898eecfbfab9956e73d7de35a9eba0fc55b957ba6cdf34ee\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 22d345d7c46834996e8db60793f8dbfe71ea9adc4124ac72934a56418b923736 8fd27dfdb917133ba4a9dc594821ca3df81fecd60da72dd8f5b779a96cbd3a41ce9e93b435eac4850d29faddb7500dc8\rEXPORTER_SECRET 22d345d7c46834996e8db60793f8dbfe71ea9adc4124ac72934a56418b923736 113d480846d1db2326c46f52559f173d5a390220618ea81afd5a63165a64cc911ff011dbf915de20699251a25036655a\rSERVER_TRAFFIC_SECRET_0 22d345d7c46834996e8db60793f8dbfe71ea9adc4124ac72934a56418b923736 443c7cfb34709b1ce2e80592e2192786ee6e1ad86f145a32e1ec9fc076b682b5cdcc7def181fbc51f835cf4888f0f85b\rCLIENT_TRAFFIC_SECRET_0 22d345d7c46834996e8db60793f8dbfe71ea9adc4124ac72934a56418b923736 691969bbf02c386f2758cc5dfd197fc7272430902b0c90a4b365ab3a1cc5066a616bc50ad29ceecba6f23dc85bd277e5\rSERVER_HANDSHAKE_TRAFFIC_SECRET f274f840c4d297c3fdefa0dd5695c4573c9037075b9d79432e88faa4a187385a 3c17149401c2b3878cbe3105164d362bba2e098e0d1de09bf69939568a2c69133c0ddc1c8fa76903e5e293b1197a01fb\rCLIENT_HANDSHAKE_TRAFFIC_SECRET f274f840c4d297c3fdefa0dd5695c4573c9037075b9d79432e88faa4a187385a 6ae0594f0c38c3abf6a65b428f00347c6aee8b60a54fd702458ab439c6f718c58bdf55b92c42b3d968663e385922294b\rEXPORTER_SECRET f274f840c4d297c3fdefa0dd5695c4573c9037075b9d79432e88faa4a187385a e668b4888a058ce00a93da55ac690365336ee6cf331ad2ae97e0b8c837cf0b449aed4940ee2a3ab56c045056c1d5574d\rSERVER_TRAFFIC_SECRET_0 f274f840c4d297c3fdefa0dd5695c4573c9037075b9d79432e88faa4a187385a 7bd47384a53931188daab512bb59cedfd2f309ed189f80ad737f4465cd00fb472cc11992204c2252d534ffc9b48bc097\rCLIENT_TRAFFIC_SECRET_0 f274f840c4d297c3fdefa0dd5695c4573c9037075b9d79432e88faa4a187385a cd9ed62e171e71d65580455e7ce374a2a91e15f3f889441144c23b2a54e6c4b2daf98e09525c317d871686872a5f2d81\rSERVER_HANDSHAKE_TRAFFIC_SECRET 3021d89743e0308f3bfe589aa16ed52d82bafe35506b5bfcdc31863f3fa9aaff 330b459fed7217708e8163baf5eabe6a34a45bbf3d4c1bde32f7bcce29016bec85539ee7724c73d23cbaaa5f8e100a34\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 3021d89743e0308f3bfe589aa16ed52d82bafe35506b5bfcdc31863f3fa9aaff e106db0914f10fc6612d4b1cbdeb92bffc3ec4c21ab906a17a3a060b7a5d91e805a41b98822f9a6482e8eb510fb37ba4\rEXPORTER_SECRET 3021d89743e0308f3bfe589aa16ed52d82bafe35506b5bfcdc31863f3fa9aaff cc32ae2d7a1bd46bc38569ebf0987e36b4ef1037f5280099a80e3ee5cf83a0be1d8283f5d925e12c78b27660de63cc9f\rSERVER_TRAFFIC_SECRET_0 3021d89743e0308f3bfe589aa16ed52d82bafe35506b5bfcdc31863f3fa9aaff 2be00b20bdf6157af69c6bac8806d5dfb6c13a3cfa9d314c73d46ead360f3a9c1562eb2eb1a073c86fab2ceda4da2a56\rCLIENT_TRAFFIC_SECRET_0 3021d89743e0308f3bfe589aa16ed52d82bafe35506b5bfcdc31863f3fa9aaff 7505e76f6398b39352003bbc3268a36a137ef4ecb2a795a8f53e9a77fdf57b5b1e2793f2ed6cb721e991920d87607aa7\rSERVER_HANDSHAKE_TRAFFIC_SECRET 14e07d555479cf6be60e056105482571a0b06a92c686246a0dfecf2c5ef7eb18 c96ade516607c05ac9b5016caf4d554ba26c8b540c37eb5d4c6a4f1849b4e50da20614cf55909d0998e744a4b0e9e276\rCLIENT_HANDSHAKE_TRAFFIC_SECRET 14e07d555479cf6be60e056105482571a0b06a92c686246a0dfecf2c5ef7eb18 658902e283b741d5057db588d38b0d565fe3479bb242a7b93ec614f94d142b86608c9b6e6e93794c28e06ab7a12e3382\rEXPORTER_SECRET 14e07d555479cf6be60e056105482571a0b06a92c686246a0dfecf2c5ef7eb18 4e5196a9c611ae860f8b8b7d16f8130fcfdacdf899831997e7a410e18d2d9b19f5eaa2aa79b868b5b6bad29a84e97fff\rSERVER_TRAFFIC_SECRET_0 14e07d555479cf6be60e056105482571a0b06a92c686246a0dfecf2c5ef7eb18 aac75064ad90e8b08818e4c6d0b895639f78f89d5ea9e3bc780b9fc295f2430fd4edb30eef91202bcc61b19774bcbdd9\rCLIENT_TRAFFIC_SECRET_0 14e07d555479cf6be60e056105482571a0b06a92c686246a0dfecf2c5ef7eb18 062684c5b1bcb1ba7b1997c88694d06f81a250f7bb90b9c0214989753eca11c2308a0e5431d6c80607ad5cd7f83ad98d\r"
# [  FAILED  ] TlsKeyLogging/TlsKeyLoggingEnd2EndTest.KeyLogging/TestScenario__num_listening_ports_5__share_tls_key_log_file_true__enable_tls_key_logging_true, where GetParam() = 8-byte object <05-00 00-00 01-01 00-00> (80 ms)
# [ RUN      ] TlsKeyLogging/TlsKeyLoggingEnd2EndTest.KeyLogging/TestScenario__num_listening_ports_5__share_tls_key_log_file_true__enable_tls_key_logging_false
# [       OK ] TlsKeyLogging/TlsKeyLoggingEnd2EndTest.KeyLogging/TestScenario__num_listening_ports_5__share_tls_key_log_file_true__enable_tls_key_logging_false (71 ms)
# [ RUN      ] TlsKeyLogging/TlsKeyLoggingEnd2EndTest.KeyLogging/TestScenario__num_listening_ports_5__share_tls_key_log_file_false__enable_tls_key_logging_false
# [       OK ] TlsKeyLogging/TlsKeyLoggingEnd2EndTest.KeyLogging/TestScenario__num_listening_ports_5__share_tls_key_log_file_false__enable_tls_key_logging_false (70 ms)
# [----------] 4 tests from TlsKeyLogging/TlsKeyLoggingEnd2EndTest (289 ms total)
#
# [----------] Global test environment tear-down
# [==========] 4 tests from 1 test suite ran. (289 ms total)
# [  PASSED  ] 2 tests.
# [  FAILED  ] 2 tests, listed below:
# [  FAILED  ] TlsKeyLogging/TlsKeyLoggingEnd2EndTest.KeyLogging/TestScenario__num_listening_ports_5__share_tls_key_log_file_false__enable_tls_key_logging_true, where GetParam() = 8-byte object <05-00 00-00 00-01 00-00>
# [  FAILED  ] TlsKeyLogging/TlsKeyLoggingEnd2EndTest.KeyLogging/TestScenario__num_listening_ports_5__share_tls_key_log_file_true__enable_tls_key_logging_true, where GetParam() = 8-byte object <05-00 00-00 01-01 00-00>
#
# Confirmed in 1.46.0 2022-05-10
tls_key_export

# Unexplained, flaky:
#
# [ RUN      ] XdsTest/XdsSecurityTest.TestTlsConfigurationWithRootPluginUpdate/V3XdsCreds
# E0514 12:41:31.427154539 3509119 ssl_transport_security.cc:1910] No match found for server name: server.example.com.
# *** SIGSEGV received at time=1652532091 on cpu 4 ***
# PC: @     0x7f2f65694f88  (unknown)  grpc_core::CertificateProviderStore::CertificateProviderWrapper::interested_parties()
#     @               0x34  (unknown)  (unknown)
#
# Confirmed in 1.46.1 2022-05-14 (on at least x86_64 and s390x)
xds_end2end

EOF
} | xargs -r chmod -v a-x

find %{_vpath_builddir} -type f -perm /0111 -name '*_test' | sort |
  while read -r testexe
  do
    echo "==== $(date -u --iso-8601=ns): $(basename "${testexe}") ===="
    %{__python3} tools/run_tests/start_port_server.py

%if %{without gdb}
    # There is a history of some tests failing by hanging. We use “timeout” so
    # that a test that does hang breaks the build in a vagurely reasonable
    # amount of time. Some tests really can be slow, so the timeout is long!
    timeout -k 61m -v 60m \
%if %{with valgrind}
        valgrind --trace-children=yes --leak-check=full --track-origins=yes \
%endif
        "${testexe}"
%else
    # Script gdb to run the test file and record any backtrace. Note that this
    # reports an error when tests fail, because there is no stack on which to
    # report a backtrace after the test exits successfully, and that this keeps
    # going after a test fails, because we ignore the mentioned error. A
    # cleverer gdb script would be nice, but this is good enough for the
    # intended purpose.
    tee "${testexe}-script.gdb" <<EOF
set pagination off
set logging file ${testexe}-gdb.log
set logging on
file ${testexe}
run
bt -full
set logging off
quit
EOF
    gdb -q -x "${testexe}-script.gdb" --batch </dev/null || :
%endif
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
%license LICENSE NOTICE.txt LICENSE-utf8_range
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
%{_libdir}/libgrpc++_test_config.so.%{cpp_so_version}
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
%license LICENSE NOTICE.txt LICENSE-utf8_range
%{python3_sitearch}/grpc
%{python3_sitearch}/grpcio-%{pyversion}-py%{python3_version}.egg-info


%files -n python3-grpcio-tools
%license LICENSE NOTICE.txt LICENSE-utf8_range
%{python3_sitearch}/grpc_tools
%{python3_sitearch}/grpcio_tools-%{pyversion}-py%{python3_version}.egg-info


%if %{without bootstrap}
%files -n python3-grpcio-admin
%{python3_sitelib}/grpc_admin
%{python3_sitelib}/grpcio_admin-%{pyversion}-py%{python3_version}.egg-info
%endif


%files -n python3-grpcio-channelz
%{python3_sitelib}/grpc_channelz
%{python3_sitelib}/grpcio_channelz-%{pyversion}-py%{python3_version}.egg-info


%if %{without bootstrap}
%files -n python3-grpcio-csds
%{python3_sitelib}/grpc_csds
%{python3_sitelib}/grpcio_csds-%{pyversion}-py%{python3_version}.egg-info
%endif


%files -n python3-grpcio-health-checking
%{python3_sitelib}/grpc_health
%{python3_sitelib}/grpcio_health_checking-%{pyversion}-py%{python3_version}.egg-info


%files -n python3-grpcio-reflection
%{python3_sitelib}/grpc_reflection
%{python3_sitelib}/grpcio_reflection-%{pyversion}-py%{python3_version}.egg-info


%files -n python3-grpcio-status
%{python3_sitelib}/grpc_status
%{python3_sitelib}/grpcio_status-%{pyversion}-py%{python3_version}.egg-info


%files -n python3-grpcio-testing
%{python3_sitelib}/grpc_testing
%{python3_sitelib}/grpcio_testing-%{pyversion}-py%{python3_version}.egg-info


%changelog
%autochangelog
