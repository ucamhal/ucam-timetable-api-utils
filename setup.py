from setuptools import setup
from os import path

README = path.join(path.dirname(__file__), "README.rst")
with open(README) as f:
    LONG_DESCRIPTION = f.read()


def get_version(filename):
    """
    Parse the value of the __version__ var from a Python source file
    without running/importing the file.
    """
    import re
    version_pattern = r"^ *__version__ *= *['\"](\d+\.\d+\.\d+)['\"] *$"
    match = re.search(version_pattern, open(filename).read(), re.MULTILINE)

    assert match, ("No version found in file: {!r} matching pattern: {!r}"
                   .format(filename, version_pattern))

    return match.group(1)


setup(
    name="ucam-timetable-api-utils",
    version=get_version("ttapiutils/__init__.py"),
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
            "merge = ttapiutils.merge",
            "fixexport = ttapiutils.fixexport",
            "xmlexport = ttapiutils.xmlexport",
            "deletegen = ttapiutils.deletegen",
            "xmlimport = ttapiutils.xmlimport",
            "autoimport = ttapiutils.autoimport"
        ]
    },
    packages=['ttapiutils'],
    package_data = {
        "ttapiutils": ["data/*"],
        "ttapiutils.tests": ['data/*']
    },
    install_requires=[
        "docopt>=0.6.2",
        "lxml>=3.3.5",
        "requests>=2.4.3",
        "pytz>=2014.7"
    ],
    test_suite="ttapiutils.tests",
    tests_require=[],
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
