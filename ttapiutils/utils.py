from lxml import etree
import pkg_resources


def _get_api_xml_schema():
    schema_xsl = pkg_resources.resource_stream(
        "ttapiutils.utils", "data/schema.xsd")
    return etree.XMLSchema(etree.parse(schema_xsl))


API_SCHEMA = _get_api_xml_schema()


def assert_valid(api_xml):
	API_SCHEMA.assertValid(api_xml)


def parse_xml(file):
	xml = etree.parse(file, _parser)
	assert_valid(xml)
	return xml
_parser = etree.XMLParser(remove_blank_text=True)


def write_c14n_pretty(xml, file):
	"""
	Insert indentation into xml before writing to file using
	write_c14n().
	"""
	pretty_xml = etree.fromstring(
		etree.tostring(xml, pretty_print=True, encoding="utf-8"))
	pretty_xml.getroottree().write_c14n(file)
