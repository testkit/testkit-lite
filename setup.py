#!/usr/bin/python

from setuptools import setup, find_packages

setup(
    name = "testkit-lite",
    description = "Test runner for test execution",
    url = "https://github.com/testkit/testkit-lite",
    author = "Cathy Shen",
    author_email = "cathy.shen@intel.com",
    version = "2.3.22",
    include_package_data = True,
    data_files = [('/opt/testkit/lite/',
	          ('VERSION', 'doc/testkit-lite_user_guide_for_tct.pdf'))],
    scripts = ('testkit-lite',),
    packages = find_packages(),
)
