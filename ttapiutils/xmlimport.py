"""
Import raw XML into Timetable.

Consider using autoimport instead, as it handles the idiosyncrasies of the API
automatically for you.

usage: ttapiutils xmlimport (--allow-any-path | --path=<path>...) [options]
                            <domain> [<api-xml>]

options:
    <domain>
        The host name of the Timetable site to import to.

    <api-xml>
        A file containing the API XML to import. stdin is read if not
        provided.

    --path=<path>...
        The timetable path(s) you expect the import to touch. The import is
        checked to ensure it only touches the paths listed.

    --allow-any-path
        Allow the imported data is allowed to affect any timetable.
        This is potentially unsafe as you may unintentionally modify
        any timetable listed in your source data, which may not be
        under your control.

    --user=<user>
        The username to authenticate with.

    --pass-envar=<envar>
        The name of the environment variable which contains the user's
        password. If none is provided the password will be prompted
        for on stdin.

    --https
    --no-https
        Use or don't use https [default: https].

    --dry-run
        Do everything except actually send the POST with the API XML. The
        HTTP request that would be made is sent to stdout

    -v, --verbose
        Be more verbose.
"""
from __future__ import unicode_literals, print_function

import sys
import urlparse

from lxml import etree
from requests.exceptions import RequestException
import docopt
import requests

from ttapiutils.utils import (
    parse_xml, read_password, get_credentials, get_proto, assert_valid,
    TimetableApiUtilsException, serialise_http_request)


# The field name of the XML file in the multipart POST payload to /api/v0/xmlimport
FORM_FILE_FIELD = "file"


class UnexpectedPathException(TimetableApiUtilsException):
    pass


class ImportError(TimetableApiUtilsException):
    pass


def build_api_import_url(domain, proto="https"):
    return urlparse.urlunparse(
        (proto, domain, "/api/v0/xmlimport/", None, None, None))


def ensure_xml_only_affects_paths(api_xml, paths):
    path_elements = api_xml.xpath("/moduleList/module/path")
    affected_paths = set(
        "/tripos/" + "/".join(filter(bool, [
            path_elem.xpath("string(tripos)"),
            path_elem.xpath("string(part)"),
            path_elem.xpath("string(subject)")
        ]))
        for path_elem in path_elements
    )
    expected_paths = set(paths)

    if not affected_paths.issubset(expected_paths):
        bad_paths = affected_paths - expected_paths
        paths_repr = ", ".join("{!r}".format(p) for p in bad_paths)
        raise UnexpectedPathException(
            "API XML to be imported contained paths other those permitted: {}"
            .format(paths_repr))


def get_csrf_token(url, auth=None):
    response = None
    try:
        response = requests.get(url, auth=auth, allow_redirects=False)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        if "csrftoken" not in response.cookies:
            raise ImportError("No csrftoken cookie in GET for: {}".format(url), None, None)
        return response.cookies["csrftoken"]
    except RequestException as e:
        raise ImportError(
            "Error making GET request for csrftoken cookie to: {}"
            .format(url), response, e)


def xmlimport(api_xml, domain, paths=None, proto="https", auth=None,
              dry_run=False):
    """
    Make an import request to the Timetable API with the provided xml.

    Returns a tuple of (request, response). If dry_run is True response will
    be None as no request will be made.
    """
    if paths is not None:
        ensure_xml_only_affects_paths(api_xml, paths)

    url = build_api_import_url(domain, proto=proto)

    # The endpoint has CSRF protection via a CSRF token in a cookie. To avoid
    # being killed by it, we need to obtain the CSRF token by GETting the
    # page before trying to POST
    csrf_token = get_csrf_token(url, auth=auth)
    cookies = {"csrftoken": csrf_token}
    data = {"csrfmiddlewaretoken": csrf_token}
    headers = {"Referer": url}

    # POST the XML file in a multi-part form.
    files = {
        FORM_FILE_FIELD: ("timetable.xml",
                          etree.tostring(api_xml, encoding="utf-8"),
                          "application/xml")
    }

    response = None
    try:
        # Construct a request explicitly so that we can return a prepared
        # request for dry runs.
        request = requests.Request(
            b"POST", url, files=files, data=data, headers=headers,
            cookies=cookies, auth=auth)

        # Don't actually send the POST if it's a dry_run
        if dry_run:
            return (request.prepare(), None)

        response = requests.Session().send(request.prepare(), allow_redirects=False)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()
    except RequestException as e:
        if response is None:
            raise ImportError("Unable to make import request: {}".format(e), None, e)

        raise ImportError(
            "non-200 response received: {:d}".format(response.status_code),
            response, e)
    return (response.request, response)


def print_response(response):
    print("HTTP Response:", file=sys.stderr)
    print(response.content, file=sys.stdout)


def print_dry_run_prepared_request(p, file=sys.stdout):
    print("--dry-run enabled, the following would have been sent:\n", file=sys.stderr)
    serialise_http_request(p, file=file)

def main(argv):
    args = docopt.docopt(__doc__, argv=argv)

    credentials = get_credentials(args)
    proto = get_proto(args)
    domain = args["<domain>"]
    dry_run = args["--dry-run"]

    paths = None if args["--allow-any-path"] is True else args["--path"]
    assert paths is None or len(paths) > 0

    api_xml_file = args["<api-xml>"] or sys.stdin
    api_xml = parse_xml(api_xml_file)

    try:
        response = xmlimport(api_xml, domain, paths=paths, proto=proto,
                             auth=credentials, dry_run=dry_run)
        if dry_run:
            prepared_request = response
            print_dry_run_prepared_request(prepared_request)
            return
    except ImportError as e:
        if args["--verbose"] and e.args[1] is not None:
            response = e.args[1]
            print_response(response)
        raise e

    if args["--verbose"]:
        print_response(response)
