# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in dashmesh/__init__.py
from dashmesh import __version__ as version

setup(
	name='dashmesh',
	version=version,
	description='Alcohol trading company',
	author='Roshna',
	author_email='roshna@craftinteractive.ae',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
