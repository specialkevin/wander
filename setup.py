import os
from setuptools import setup

setup(
    name = "wander",
    version = "0.0.1",
    author = "Kevin Harriss",
    author_email = "special.kevin@gmail.com",
    description = ("Zimbra migration tool for moving to Google Apps."),
    license = "BSD",
    keywords = "zimbra googleapps migration",
    url = "http://packages.python.org/wander",
    packages=['wander',],
    scripts=['bin/wander'],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    install_requires = ['requests'],
)
