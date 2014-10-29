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

    --dry-run
        Generate all data, but don't actually perform the final
        xmlimport on the timetable site.

    -X=<name>=<value>...
        Extension parameters to send to the data source.

"""

# Data source: - for stdin, or name of generator, e.g. engineering
    - ttapiutils.autoimport.generators: engineering
# domain to upload to
# list of of paths to be affected

from ttapiutils.canonicalise import canonicalise
from ttapiutils.fixexport import fix_export_ids
from ttapiutils.utils import (parse_xml, read_password, get_credentials,
                              get_proto, TimetableApiUtilsException)
from ttapiutils.xmlexport import xmlexport
from ttapiutils.xmlimport import xmlimport


class NoSuchDataSourceException(TimetableApiUtilsException):
    pass


def get_defined_data_source_entrypoints():
    (ep.name, ep) for ep in
        pkg_resources.iter_entry_points(
            group="ttapiutils.autoimport.datasources"))


class StreamDataSource(object):
    def __init__(self, file):
        self.file = file

    def get_xml(self):
        return parse_xml(self.file)


def get_data_source(data_source_name, data_source_entrypoints):
    if data_source_name == "-":
        return StreamDataSource(sys.stdin)

    if not data_source_name in data_source_entrypoints:
        raise NoSuchDataSourceException("No such data source: {!r}".format(data_source_name))

    return data_source_entrypoints[data_source_name]


class AutoImporter(object):
    def __init__(self, data_source):
        self.data_source = data_source

    def get_paths(self):
        raise NotImplementedError()

    def get_proto(self):
        raise NotImplementedError()

    def get_domain(self):
        raise NotImplementedError()

    def get_auth(self):
        raise NotImplementedError()

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
        old_state = get_canonical_merged_old_state()
        new_state = self.get_canonical_new_state()
        return generate_deletes(old_state, new_state)

    def import_to_timetable(self, api_xml):
        return xmlimport(api_xml, self.get_domain(), self.get_paths(),
                  self.get_proto(), self.get_auth())

    def autoimport(self):
        api_xml = self.get_state_with_deletes()
        self.import_to_timetable(api_xml)


class AuditTrailAutoImporter(AutoImporter):
    def __init__(self, audit_base_dir, *args, **kwargs):
        super(AuditTrailAutoImporter, self).__init__(*args, **kwargs)
        self.audit_base_dir = audit_base_dir


def main(argv):
    pass
