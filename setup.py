#!/usr/bin/env python
# http://docs.python.org/distutils/setupscript.html
# http://docs.python.org/2/distutils/examples.html
from setuptools import setup, find_packages
import re
import os
from codecs import open


name = "testdata"
kwargs = {
    "name": name,
    "description": 'Easily generate random unicode test data among other things',
    "author": 'Jay Marcyes',
    "author_email": 'jay@marcyes.com',
    "url": 'http://github.com/Jaymon/{}'.format(name),
    "package_data": {name: ['data/*']},
    "license": "MIT",
    "classifiers": [ # https://pypi.python.org/pypi?:action=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    "test_suite": "{}_test".format(name),
}

def read(path):
    if os.path.isfile(path):
        with open(path, encoding='utf-8') as f:
            return f.read()
    return ""


vpath = os.path.join(name, "__init__.py")
if os.path.isfile(vpath):
    kwargs["packages"] = find_packages()
else:
    vpath = "{}.py".format(name)
    kwargs["py_modules"] = [name]
kwargs["version"] = re.search(r"^__version__\s*=\s*[\'\"]([^\'\"]+)", read(vpath), flags=re.I | re.M).group(1)


# https://pypi.org/help/#description-content-type
kwargs["long_description"] = read('README.md')
kwargs["long_description_content_type"] = "text/markdown"


setup(**kwargs)

