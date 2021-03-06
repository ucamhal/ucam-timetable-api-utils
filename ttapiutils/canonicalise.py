"""
Canonicalise a Timetable API v0 XML document.
stdin/stdout are used for input/output.

usage: ttapiutils canonicalise [--help]

The output will be semantically equivalent to the input, but the
XML representation will be canonical, allowing two canonicalised
Timetable API XML documents to be compared byte-for-byte for
equivalence.
"""
import sys

import docopt
import pkg_resources
from lxml import etree

from ttapiutils.utils import parse_xml, assert_valid, write_c14n_pretty

def get_canonicalise_transform():
	canonicalise_xsl = pkg_resources.resource_stream(
		"ttapiutils.canonicalise", "data/canonicalise.xsl")
	return etree.XSLT(etree.parse(canonicalise_xsl))


CANONICALISE_TRANSFORM = get_canonicalise_transform()


def canonicalise(api_xml):
	assert_valid(api_xml)
	return CANONICALISE_TRANSFORM(api_xml)


def main(args):
	docopt.docopt(__doc__, argv=args)

	api_xml = parse_xml(sys.stdin)
	canonic_xml = canonicalise(api_xml)
	write_c14n_pretty(canonic_xml, sys.stdout)
