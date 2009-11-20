#!/usr/bin/env python
from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup
from distutils.command.install import INSTALL_SCHEMES
import os

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
application_dir = 'formunculous'
  
for dirpath, dirnames, filenames in os.walk(application_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

# Get the version from formunculous.VERSION
version = __import__('formunculous').get_version()

setup(
    name = "formunculous",
    version = version.replace(' ', '-'),
    author = 'Carson Gee',
    author_email = 'x@carsongee.com',
    url = 'http://carsongee.com',
    download_url = 'http://formunculous.com/downloads/formunculous-%s.tar.gz' % version,
    platforms = ('Any',),
    keywords = ('forms','generic ',),
    description = 'A Django Web application that builds database backed Web forms utilizing a nice javascript user interface',
    packages = packages, 
    data_files = data_files,
    scripts = [],
    requires = ('django (>=1.1)',),
    zip_safe = False,
)
