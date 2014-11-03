"""
Postprocess the output of /api/v0/xmlexport/<path> to allow it to
be round-tripped. stdin/stdout are used for input/output.

usage: ttapiutils fixexport [--help]

The API adds the prefix "import-" to the the uniqueid of events, so
the event IDs imported are not the same as those exported. This fixes
the event IDs so that the export IDs match the import IDs.
"""
import sys

import docopt
import pkg_resources
from lxml import etree

from ttapiutils.utils import parse_xml, assert_valid, write_c14n_pretty


def _get_id_fix_transform():
	id_fix_xsl = pkg_resources.resource_stream(
		"ttapiutils.fixexport", "data/fix_export_ids.xsl")
	return etree.XSLT(etree.parse(id_fix_xsl))

_FIX_IDS_TRANSFORM = _get_id_fix_transform()


def fix_export_ids(api_xml):
	assert_valid(api_xml)
	return _FIX_IDS_TRANSFORM(api_xml)


def main(args):
	docopt.docopt(__doc__, argv=args)

	api_xml = parse_xml(sys.stdin)
	fixed_xml = fix_export_ids(api_xml)
	write_c14n_pretty(fixed_xml, sys.stdout)
