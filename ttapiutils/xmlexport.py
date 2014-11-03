"""
Export Timetable XML from a Timetable site.

usage: ttapiutils xmlexport [options] <domain> <path>...

If more than one <path> is specified, the output will be run through
ttapiutils merge to produce a single XML file.

options:
    --user=<user>
        The username to authenticate with.

    --pass-envar=<envar>
        The name of the environment variable which contains the user's
        password. If none is provided the password will be prompted
        for on stdin.

    --https
    --no-https
        Use or don't use https [default: https].

    --fix-ids
        Fix exorted event IDs with ttapiutils fixexport (default)

    --no-fix-ids
        Don't fix event IDs

    -h, --help
        Show this help message
"""
from cStringIO import StringIO
import sys
import urlparse

from lxml import etree
from requests.exceptions import RequestException
import docopt
import requests

from ttapiutils.merge import merge
from ttapiutils.fixexport import fix_export_ids
from ttapiutils.utils import (
    write_c14n_pretty, parse_xml, assert_valid, read_password,
    get_credentials, get_proto)


class ExportException(Exception):
    pass


class HttpRequestExportException(ExportException):
    pass


class XMLParseExportException(ExportException):
    pass


def build_api_export_url(domain, path, proto="https"):
    full_path = "/api/v0/xmlexport{}".format(path)
    return urlparse.urlunparse((proto, domain, full_path, None, None, None))


def xmlexport(domain, path, auth=None, proto="https", fix_ids=True):
    url = build_api_export_url(domain, path, proto=proto)
    try:
        response = requests.get(url, auth=auth, allow_redirects=False)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()
            raise HttpRequestExportException(
                "Non-200 response received to request for: {}. {}".format(
                    url, response.status_code))
    except RequestException as e:
        raise HttpRequestExportException("Error requesting timetable: {}. {}"
                                         .format(url, e))

    try:
        xml = parse_xml(StringIO(response.content))
    except etree.Error as e:
        raise XMLParseExportException(
            "Unable to parse response as XML: {}".format(e), e, response)

    assert_valid(xml)

    if fix_ids:
        xml = fix_export_ids(xml)

    return xml


def main(argv):
    args = docopt.docopt(__doc__, argv=argv)

    credentials = get_credentials(args)
    proto = get_proto(args)
    domain = args["<domain>"]
    paths = args["<path>"]
    fix_ids = not args.get("--no-fix-ids")

    exports = [xmlexport(domain, path, auth=credentials, proto=proto,
                         fix_ids=fix_ids)
               for path in paths]

    write_c14n_pretty(merge(exports), sys.stdout)
