# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

with open('requirements.txt', encoding='utf-8') as fp:
    install_requires = fp.read()

setup(
    name='DockerApp',
    version='0.1.0',
    description='DockerApp package for firstquadrants.com',
    long_description=readme,
    author='Zhichao Zhang',
    author_email='zc-zhang17@mails.tsinghua.edu.cn',
    url='https://firstquadrants.com',
    license=license,
    packages=find_packages(exclude=('test')),
    install_requires=install_requires
)
