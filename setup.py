#!/usr/bin/python

from setuptools import setup, find_packages

setup(
    name = "testkit-lite",
    description = "Test runner for test execution",
    url = "https://github.com/testkit/testkit-lite",
    author = "Cathy Shen",
    author_email = "cathy.shen@intel.com",
    version = "2.3.4",
    include_package_data = True,
    data_files = [('/opt/testkit/lite/',
	          ('VERSION', 'doc/Testkit-Lite_User_Guide.pdf'))],
    scripts = ('testkit-lite',),
    packages = find_packages(),
)
