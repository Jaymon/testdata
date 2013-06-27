#!/usr/bin/env python
# http://docs.python.org/distutils/setupscript.html
# http://docs.python.org/2/distutils/examples.html
import sys
from setuptools import setup
import ast

name = 'testdata'
version = ''
with open('{}.py'.format(name), 'rU') as f:
    for node in (n for n in ast.parse(f.read()).body if isinstance(n, ast.Assign)):
        name = node.targets[0]
        if isinstance(name, ast.Name) and name.id.startswith('__version__'):
            version = node.value.s
            break

if not version:
    raise RuntimeError('Unable to find version number')

setup(
    name=name,
    version=version,
    description='Easy random test data generation',
    author='Jay Marcyes',
    author_email='jay@marcyes.com',
    url='http://github.com/Jaymon/{}'.format(name),
    py_modules=[
        name,
    ],
    license="MIT",
    zip_safe=True,
    classifiers=[
        'Development Status :: {}'.format(version),
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: MIT',
        'Operating System :: OS Independent',
        'Topic :: Debug',
        ],
    test_suite = "test_{}".format(name),
)

