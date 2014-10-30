"""
usage: ttapiutils autoimport [options] <data-source> <domain> <path>...
       ttapiutils autoimport --complete-dry-run=<audit-dir>

In the first form, <data-source> provides new timetable XML data
to be imported into <path>s on <domain>, replacing existing data.

Data produced by <data-source> is taken to be the desired state
of <path>s on <domain> after the import, so details such as
using ttapiutils deletegen to calculate deletes needed to achieve
the new state are taken care of automatically.

In the second form, the yet-unimported data from a dir created
by --audit-trail with --dry-run can be imported. This is useful
for completing an import after manually verifying behaviour.

options:
    <data-source>
        The name of the data source to use to generate the import data,
        or "-" to read Timetable XML data on stdin.

    <domain>
        The domain name of the Timetable site to perform the XML import
        on.

    <path>...
        List of timetable paths to be targeted by the import. The data
        source MUST produce data for every path listed. Pre-existing
        event data in Timetable at <domain> will be replaced by the
        data generated by the <data-source>.

    --audit-trail=<base-dir>
        Create a timestamped subdirectory of <dir> containing a record
        of the data received, generated and sent by an invocation of
        this program.

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
        Generate all data, but don't actually perform the final
        xmlimport on the timetable site.

    -X=<name>=<value>...
        Extension parameters to send to the data source.
"""

# Data source: - for stdin, or name of generator, e.g. engineering
#    - ttapiutils.autoimport.generators: engineering
# domain to upload to
# list of of paths to be affected
import datetime
import json
import os
import os.path
import re
import sys

import docopt
import pytz


from ttapiutils.canonicalise import canonicalise
from ttapiutils.fixexport import fix_export_ids
from ttapiutils.merge import merge
from ttapiutils.deletegen import generate_deletes
from ttapiutils.utils import (
    parse_xml, read_password, get_credentials, get_proto,
    TimetableApiUtilsException, serialise_http_request,
    serialise_http_response, write_c14n_pretty)
from ttapiutils.xmlexport import xmlexport
from ttapiutils.xmlimport import xmlimport


class NoSuchDataSourceException(TimetableApiUtilsException):
    pass


def get_defined_data_source_entrypoints():
    return [(ep.name, ep)
            for ep in pkg_resources.iter_entry_points(
            group="ttapiutils.autoimport.datasources")]


class StreamDataSource(object):
    def __init__(self, file):
        self.file = file

    def get_xml(self):
        return parse_xml(self.file)


def get_data_source(data_source_name, data_source_entrypoints=None):
    if data_source_name == "-":
        return StreamDataSource(sys.stdin)

    if data_source_entrypoints is None:
        data_source_entrypoints = get_defined_data_source_entrypoints()

    if not data_source_name in data_source_entrypoints:
        raise NoSuchDataSourceException("No such data source: {!r}".format(data_source_name))

    return data_source_entrypoints[data_source_name]


class AutoImporter(object):
    def __init__(self, data_source, domain, is_dry_run=False, permitted_paths=None,
                 http_protocol="https", auth=None):
        self.data_source = data_source
        self._is_dry_run = bool(is_dry_run)
        self._permitted_paths = permitted_paths
        self._http_protocol = http_protocol
        self._domain = domain
        self._auth = auth

    def get_paths(self):
        return self._permitted_paths

    def get_proto(self):
        return self._http_protocol

    def get_domain(self):
        return self._domain

    def get_auth(self):
        return self._auth

    def is_dry_run(self):
        return self._is_dry_run

    def get_raw_new_state(self):
        return self.data_source.get_xml()

    def get_canonical_new_state(self):
        return canonicalise(self.get_raw_new_state())

    def get_raw_old_state(self, path):
        return xmlexport(self.get_domain(), path, auth=self.get_auth(),
                         proto=self.get_proto(), fix_ids=False)

    def get_fixed_old_state(self, path):
        """
        As get_raw_old_state() but with event IDs fixed.
        """
        return fix_export_ids(self.get_raw_old_state(path))

    def get_merged_old_state(self):
        return merge(
            self.get_fixed_old_state(path) for path in self.get_paths())

    def get_canonical_merged_old_state(self):
        return canonicalise(self.get_merged_old_state())

    def get_state_with_deletes(self):
        old_state = self.get_canonical_merged_old_state()
        new_state = self.get_canonical_new_state()
        return generate_deletes(old_state, new_state)

    def import_to_timetable(self, api_xml):
        return xmlimport(api_xml, self.get_domain(), paths=self.get_paths(),
                  proto=self.get_proto(), auth=self.get_auth(),
                  dry_run=self.is_dry_run())

    def auto_import(self):
        api_xml = self.get_state_with_deletes()
        self.import_to_timetable(api_xml)


def path_filename_representation(path):
    """
    Get a representation of a timetable path such as /tripos/engineering/IA
    which is sutable for use in a filename.
    """
    # Strip leading / and replace / with .
    return re.sub(r"^/(.*)$", r"\1", path).replace("/", ".")


class AuditTrailAutoImporter(AutoImporter):
    def __init__(self, audit_base_dir, *args, **kwargs):
        now = kwargs.pop("now", None)
        if now is not None and now.tzinfo is None:
            raise ValueError("now must have a timezone: {}".format(now))

        super(AuditTrailAutoImporter, self).__init__(*args, **kwargs)
        self._audit_base_dir = audit_base_dir
        self._now = self._get_now() if now is None else now

        self._create_audit_dir()
        self.log_manifest()

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

    def log_manifest(self):
        """Log a JSON file containing the options"""
        with self.open_audit_file("manifest.json") as f:
            json.dump(self.get_manifest_json(), f, indent=4)

    def get_manifest_json(self):
        return {
            "pid": os.getpid(),
            "audit_base_dir": self._audit_base_dir,
            "time": self.get_timestamp(),
            "permitted_paths": self.get_paths(),
            "http_proto": self.get_proto(),
            "domain": self.get_domain(),
            "is_dry_run": self.is_dry_run()
        }

    def log_xml(self, name, xml):
        with self.open_audit_file("{}.xml".format(name)) as f:
            write_c14n_pretty(xml, f)
        return xml

    # Override XML producing methods to log output to audit dir
    def get_raw_new_state(self):
        return self.log_xml("raw_new_state",
            super(AuditTrailAutoImporter, self).get_raw_new_state())

    def get_canonical_new_state(self):
        return self.log_xml("canonical_new_state",
            super(AuditTrailAutoImporter, self).get_canonical_new_state())

    def get_raw_old_state(self, path):
        return self.log_xml(
            "raw_old_state_{}".format(path_filename_representation(path)),
            super(AuditTrailAutoImporter, self).get_raw_old_state(path))

    def get_fixed_old_state(self, path):
        return self.log_xml(
            "fixed_old_state_{}".format(path_filename_representation(path)),
            super(AuditTrailAutoImporter, self).get_fixed_old_state(path))

    def get_merged_old_state(self):
        return self.log_xml("merged_old_state",
            super(AuditTrailAutoImporter, self).get_merged_old_state())

    def get_canonical_merged_old_state(self):
        return self.log_xml("canonical_merged_old_state",
            super(AuditTrailAutoImporter, self)
            .get_canonical_merged_old_state())

    def get_state_with_deletes(self):
        return self.log_xml("state_with_deletes",
            super(AuditTrailAutoImporter, self).get_state_with_deletes())

    def import_to_timetable(self, api_xml):
        request, response = (super(AuditTrailAutoImporter, self)
            .import_to_timetable(api_xml))

        with self.open_audit_file("http_request.txt") as f:
            serialise_http_request(request, f)

        # There's only an HTTP response if it's not a dry run
        if not self.is_dry_run():
            assert response is not None
            with self.open_audit_file("http_response.txt") as f:
                serialise_http_response(response, f)


def main(argv):
    args = docopt.docopt(__doc__, argv=argv)

    # TODO: -X args for data source
    data_source = get_data_source(args["<data-source>"])
    credentials = get_credentials(args)
    proto = get_proto(args)
    domain = args["<domain>"]
    paths = args["<path>"]
    audit_trail_base_dir = args["--audit-trail"]
    dry_run = args["--dry-run"]

    # Construct an auto importer from our params
    args = [data_source, domain]
    kwargs = dict(
        is_dry_run=dry_run, permitted_paths=paths, http_protocol=proto,
        auth=credentials)
    if audit_trail_base_dir is None:
        importer_class = AutoImporter
    else:
        importer_class = AuditTrailAutoImporter
        args = [audit_trail_base_dir] + args
    auto_importer = importer_class(*args, **kwargs)

    # Perform the import
    auto_importer.auto_import()
