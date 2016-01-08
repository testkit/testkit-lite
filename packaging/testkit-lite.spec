Summary: TCT-Lite
Name: testkit-lite
Version: 3.1.16
Release: 1
License: GPLv2
Group: Applications/System
Source: %{name}_%{version}.tar.gz

BuildRequires: python-distribute

%{!?python_sitelib: %define python_sitelib %(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%description
testkit-lite is a test runner with command-line interface.It has the following functions 
1. Accepts .xml test case descriptor files as input. 
2. drives automatic test execution. 
3. provide multiple options to meet various test requirements. 

%prep
%setup -q

%build

%install
python setup.py install --prefix=%{_prefix} --root=%{buildroot}
# remove tests
rm -rf %{buildroot}/%{python_sitelib}/tests

%clean
rm -rf %{buildroot}

%post
# Set permissions
chmod ugo+rwx /opt/testkit/lite

%files
%{python_sitelib}/testkitlite/*
%{python_sitelib}/testkit_lite-*.egg-info/*
/etc/dbus-1/system.d/com.intel.testkit.conf
/opt/testkit/lite/VERSION
/opt/testkit/lite/commodule/CONFIG
/opt/testkit/lite/mh.html
%{_bindir}/testkit-lite
%{_bindir}/testkit-lite-dbus
%defattr(-,root,root)

%doc
/opt/testkit/lite/testkit-lite_user_guide.pdf
/opt/testkit/lite/testkit-lite_tutorial.pdf
/opt/testkit/lite/test_definition_schema.pdf

%changelog
