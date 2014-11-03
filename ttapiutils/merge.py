"""
Merge multiple Timetable API XML files into one.

usage: ttapiutils merge <xmlfile>...
"""
import sys

from lxml import etree
import docopt

from ttapiutils.utils import assert_valid, parse_xml


def merge(xmlfiles):
	root = etree.Element("moduleList")
	root.extend(
		module
		for xml in xmlfiles
		for module in xml.xpath("/moduleList/module")
	)
	return root


def main(args):
	args = docopt.docopt(__doc__)
	parser = etree.XMLParser(remove_blank_text=True)

	xml_files = [parse_xml(filename) for filename in args["<xmlfile>"]]
	map(assert_valid, xml_files)
	merge(xml_files).getroottree().write(sys.stdout, pretty_print=True)
