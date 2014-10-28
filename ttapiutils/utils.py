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
	return etree.parse(file, _parser)
_parser = etree.XMLParser(remove_blank_text=True)