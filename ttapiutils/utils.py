from __future__ import print_function, unicode_literals

from cStringIO import StringIO
import datetime
import getpass
import json
import os

from lxml import etree
from requests.auth import HTTPBasicAuth
import pkg_resources
import pytz


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



def write_c14n_pretty(xml, file=None):
    """
    Insert indentation into xml before writing to file using
    write_c14n().
    """
    out = StringIO() if file is None else file

    pretty_xml = etree.fromstring(
        etree.tostring(xml, pretty_print=True, encoding="utf-8"))
    pretty_xml.getroottree().write_c14n(out)

    if file is None:
        return out.getvalue()


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


class DirectoryAuditLogger(object):
    def __init__(self, audit_base_dir, now=None):
        if now is not None and now.tzinfo is None:
            raise ValueError("now must have a timezone: {}".format(now))

        self._audit_base_dir = audit_base_dir
        self._now = self._get_now() if now is None else now

        self._create_audit_dir()

    def _get_now(self):
        """Get the current time in the UTC timezone."""
        return pytz.utc.localize(datetime.datetime.utcnow())

    def get_time(self):
        return self._now

    def get_timestamp(self):
        return self.get_time().strftime("%Y-%m-%dT%H%M%S.%f%z")

    def get_audit_dir(self):
        return os.path.join(self._audit_base_dir, self.get_timestamp())

    def _create_audit_dir(self):
        os.mkdir(self.get_audit_dir())

    def open_audit_file(self, filename, mode="w"):
        return open(os.path.join(self.get_audit_dir(), filename), mode)

    def log_xml(self, name, xml):
        with self.open_audit_file("{}.xml".format(name)) as f:
            write_c14n_pretty(xml, f)
        return xml

    def log_json(self, name, obj):
        with self.open_audit_file("{}.json".format(name)) as f:
            json.dump(obj, f, indent=4)
        return obj
