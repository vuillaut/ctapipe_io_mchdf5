from setuptools import setup, find_packages
from os import path

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='ctapipe_io_mchdf5',
    packages=find_packages(),
    version='0.1',
    description='ctapipe plugin for reading Monte-Carlo files (contains the same informations as Simtel files)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'tables',
        'ctapipe',
    ],
    tests_require=['pytest'],
    setup_requires=['pytest_runner'],
    author='Pierre Aubert',
    author_email='pierre.aubert@lapp.in2p3.fr',
    license='Cecil-C',
)
