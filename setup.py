from setuptools import setup
from os import path

README = path.join(path.dirname(__file__), "README.rst")
with open(README) as f:
    LONG_DESCRIPTION = f.read()

setup(
    name="ucam-timetable-api-utils",
    version="0.1.0",
    description=(
        "Utilities for working with the timetable.cam.ac.uk API/import "
        "functionality."),
    author="Hal Blackburn",
    author_email="hwtb2@cam.ac.uk",
    url="https://github.com/ucamhal/ucam-timetable-api-utils",
    entry_points = {
        "console_scripts": [
            "ttapiutils = ttapiutils:main"
        ],
        "ttapiutils_subcommands": [
            "canonicalise = ttapiutils.canonicalise",
            "merge = ttapiutils.merge"
        ]
    },
    packages=['ttapiutils'],
    include_package_data=True,
    requires=[
        "docopt (>=0.6.2)",
        "lxml (>=3.3.5)"
    ],
    license="BSD",
    classifiers=[
        "Intended Audience :: Developers",
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Internet :: WWW/HTTP",
    ],
    long_description=LONG_DESCRIPTION,
)
