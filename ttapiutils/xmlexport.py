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
        Use or don't use https (default).

    --fix-ids
        Fix exorted event IDs with ttapiutils fixexport (default)

    --no-fix-ids
        Don't fix event IDs

    -h, --help
        Show this help message
"""
from cStringIO import StringIO
import getpass
import os
import sys
import urlparse

from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException
import docopt
import requests

from ttapiutils.merge import merge
from ttapiutils.fixexport import fix_export_ids
from ttapiutils.utils import write_c14n_pretty, parse_xml, assert_valid


class ExportException(Exception):
    pass


def build_api_export_url(domain, path, proto="https"):
    full_path = "/api/v0/xmlexport{}".format(path)
    return urlparse.urlunparse((proto, domain, full_path, None, None, None))


def read_password(envar):
    if not envar:
        return getpass.getpass()
    return os.environ.get(envar, "")


def get_credentials(args):
    user = args.get("--user")
    if user:
        return HTTPBasicAuth(user, read_password(args.get("--pass-envar")))
    return None


def xmlexport(domain, path, auth=None, proto="https", fix_ids=True):
    url = build_api_export_url(domain, path, proto=proto)
    try:
        response = requests.get(url, auth=auth)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()
    except RequestException as e:
        raise ExportException("Error requesting timetable: {}. {}"
                              .format(url, e))

    xml = parse_xml(StringIO(response.content))
    assert_valid(xml)

    if fix_ids:
        xml = fix_export_ids(xml)

    return xml


def main(argv):
    args = docopt.docopt(__doc__, argv=argv)

    credentials = get_credentials(args)
    proto = "http" if args.get("--no-https") else "https"
    domain = args["<domain>"]
    paths = args["<path>"]
    fix_ids = not args.get("--no-fix-ids")

    exports = [xmlexport(domain, path, auth=credentials, proto=proto,
                         fix_ids=fix_ids)
               for path in paths]

    write_c14n_pretty(merge(exports), sys.stdout)
