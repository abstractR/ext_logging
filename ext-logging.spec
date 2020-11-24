%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')

Summary: The extended logging library for Python %{python_version}
Name: %{name}
Version: %{version}
Release: 1%{?dist}
License: Internal
BuildArch: noarch
Packager: serj.pilipenko@gmailom
Requires: %{python_package}
Group: AbstractR

%description
The OpsTools logging library for Python %{python_version}

Features
1) Useful attrs like user, application name, hostname, path/lineno, pid are automatically added to the log.
2) Standard interface
3) Concurrent safety. Multiple programs can write into single file, module watches for external changes.

Logs format corresponds to the one described in RFC 5424-5428, but extended by multiline support.
Supplying url_encode=True or escape_rfc5424_special_chars=True options will make resulting logs fully
RFC 5424 compatible what, in turn, allows to use syslog-ng or logstash for further processing.


Example

log.info('here test', repr=some_struct, jsonData=some_jsonable_struct, trace=1, stack=1, oes=1)

repr stands for putting pretty formatted vim multiline repr() of some_struct
json_data stands for dumping some_jsonable_struct into pretty formatted string inside log
trace=1 makes sense when log is used inside except block, it automatically adds pretty formatted trace to the log data element and exception to the msg part.
stack=1 adds callstack


%pre -p /usr/bin/%{python_version}
# we check our expectation of python library matches available package instalation
from distutils.sysconfig import get_python_lib;
assert "%{site}" == get_python_lib(), "%s != %s" % ("%{site}", get_python_lib())

%prep
cp -rf %{_curdir}/ext_logging/ ./
#cp -rf %{_curdir}/requirements.txt .
#cp -rf %{_curdir}/version .
#cp -rf %{_curdir}/setup.py .

%install
mkdir -p %{buildroot}/%{site}/ext_logging
cp -r ./ext_logging/* %{buildroot}/%{site}/ext_logging
mkdir -p %{buildroot}/%{_bindir}
ln -sf %{site}/ext_logging/scripts/ngrep.py %{buildroot}/%{_bindir}/ngrep
sed -i 's/@PKG_VERSION/%{version}/' %{buildroot}/%{site}/ext_logging/__init__.py
sed -i 's|@PYTHON|/usr/bin/%{python_version}|' %{buildroot}/%{site}/ext_logging/scripts/ngrep.py
chmod a+x %{buildroot}/%{site}/ext_logging/scripts/ngrep.py

%files
%{site}/ext_logging
%{_bindir}/ngrep

