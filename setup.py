#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup for seedir.

@author: Tom Earnest
"""

from os import path
from setuptools import setup

# read the contents of the README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# read version
with open(path.join(this_directory, 'wubwub', '_version.py'), encoding='utf-8') as f:
    version = f.read().split('=')[1].strip('\'"')

requirements = ['gdown>=4.5',
                'matplotlib>=3.5',
                'numpy>=1.21',
                'pydub>=0.25',
                'sortedcontainers>=2.4']

setup(name='wubwub',
      version=version,
      description='Create sequencer-based music with Python.',
      url='https://github.com/earnestt1234/wubwub',
      author='Tom Earnest',
      author_email='earnestt1234@gmail.com',
      license='MIT',
      packages=['wubwub'],
      install_requires=requirements,
      include_package_data=True,
      zip_safe=False,
      long_description=long_description,
      long_description_content_type='text/markdown',
      )
