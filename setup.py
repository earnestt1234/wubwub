#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup for seedir.

@author: Tom Earnest
"""

from os import path

from setuptools import setup

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

requirements = []

setup(name='wubwub',
      version='0.1.0',
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
