from __future__ import print_function, unicode_literals

import getpass
import os
from cStringIO import StringIO

from lxml import etree
from requests.auth import HTTPBasicAuth
import pkg_resources


class TimetableApiUtilsException(Exception):
    """
    The base exception for all exceptions raised by ttapiutils APIs.
    """


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


def read_password(envar):
    if not envar:
        return getpass.getpass()
    return os.environ.get(envar, "")


def get_credentials(args):
    user = args.get("--user")
    if user:
        return HTTPBasicAuth(user, read_password(args.get("--pass-envar")))
    return None


def get_proto(args):
    return "http" if args.get("--no-https") else "https"


def _serialise_headers(headers, file):
    headers = "\n".join("{}: {}".format(k, v)
                        for (k, v) in headers.items())
    print(headers, file=file)


def serialise_http_request(p, file=None):
    """
    Create an HTTP request like representation of a requests PreparedRequest.
    If file is provided the representation is written to file, otherwise it's
    returned as a str.
    """
    out = StringIO() if file is None else file

    # This is not a real HTTP request, but similar
    print("{} {}".format(p.method, p.url), file=out)
    _serialise_headers(p.headers, out)
    print(file=out)
    print(p.body, file=out, end="")

    if file is None:
        return out.getvalue()


def serialise_http_response(r, file=None):
    """
    Create an HTTP response like representation of a requests Response.
    If file is provided the representation is written to file, otherwise it's
    returned as a str.
    """
    out = StringIO() if file is None else file

    # This is not a real HTTP response, but similar
    print("{} {}".format(r.status_code, r.reason), file=out)
    _serialise_headers(r.headers, out)
    print(file=out)
    print(r.content, file=out, end="")

    if file is None:
        return out.getvalue()
