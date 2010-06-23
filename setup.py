#!/usr/bin/env python

try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import setup
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
    url = 'http://formunculous.org/',
    download_url = 'http://formunculous.org/media/downloads/formunculous-%s.tar.gz' % version,
    platforms = ('Any',),
    keywords = ('forms','django','web',),
    description = 'A Django Web application that builds database backed Web forms utilizing a nice javascript user interface to create them.',
    long_description = """
This is a Django based application for creating database backed or
email forms. It features an innovative drag and drop interface for
building forms, a workflow for reviewing forms, and infinite
customization.

The Website for this project at http://formunculous.org has
a lot of documentation, demos, and screenshots for getting you up and running
with the application.
""",
    packages = packages, 
    data_files = data_files,
    scripts = [],
    install_requires = ['django>=1.1','pil','simplejson',],
    zip_safe = False,
)
