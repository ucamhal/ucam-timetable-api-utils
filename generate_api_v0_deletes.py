"""
This program is a workaround to automatically generate <delete/> operations
required by the Timetable 3 v0 API's XML import feature.

One might assume that submitting an XML file (<moduleList>) to
/api/v0/xmlimport would result in the API updating the state to match the
given representation. Unfortunately, the submitted XML file is not so much
interpreted as a representation, but as a series of actions to apply. As
such, omitting a module/series/event does not result in it being removed.
Instead, the module/series/event must be explicitly marked for deletion
using a <delete/> tag.

This significantly complicates producers of Timetable XML, as they cannot
simply generate a representation of their data in the Timetable format,
they need to know a) what's in Timetable, b) what's in their data set and
c) then work out how to modify a) to get to b).

This program basically performs step c), given a) and b) as inputs.

It pains me that this program needs to exist. The need for it should be
removed at the earliest opportunity.

usage: generate_api_v0_deletes.py [options] <current_state> <future_state>

options:
    --unmerged    Output pruned current and future states unmerged
                  (for debugging only).
"""
from __future__ import unicode_literals, print_function

from copy import deepcopy
from os import path
import sys

import docopt
from lxml import etree


SCHEMA_FILE = path.join(path.dirname(__file__), "schema.xsd")
SCHEMA = etree.XMLSchema(file=SCHEMA_FILE)
GENERATE_DELETES_FILE = path.join(path.dirname(__file__),
                                  "generate_deletes.xsl")
GENERATE_DELETES = etree.XSLT(etree.parse(GENERATE_DELETES_FILE))


def wrap(name, elements):
    parent = etree.Element(name)
    parent.extend(elements)
    return parent


def module_key(module):
    return (module.xpath("string(path/tripos)"),
            module.xpath("string(path/part)"),
            module.xpath("string(path/subject)"),
            module.xpath("string(name)"))


def series_key(series):
    module = series.xpath("..")[0]
    return module_key(module) + (series.xpath("string(uniqueid)"),)


def event_key(event):
    series = event.xpath("..")[0]
    return series_key(series) + (event.xpath("string(uniqueid)"),)


def index(items, key):
    return dict((key(i), i) for i in items)


def merge_module_lists(deletes, newstate):
    root = etree.Element("moduleList")

    merge_pairs = dictzip_longest(
        index(deletes, module_key),
        index(newstate, module_key))

    merged_modules = (merge_modules(a, b) for (_, a, b) in merge_pairs)

    root.extend(merged_modules)
    return root


def merge_modules(deletes, newstate):
    if not (deletes is not None and newstate is not None):
        return deepcopy(deletes or newstate)

    merge_pairs = dictzip_longest(
        index(deletes.xpath("series"), series_key),
        index(newstate.xpath("series"), series_key))

    merged_series = (merge_series(a, b) for (_, a, b) in merge_pairs)

    module = etree.Element("module")
    module.append(deepcopy(newstate.xpath("path")[0]))
    module.append(deepcopy(newstate.xpath("name")[0]))
    module.extend(merged_series)
    return module


def merge_series(deletes, newstate):
    if not (deletes is not None and newstate is not None):
        return deepcopy(deletes or newstate)

    merge_pairs = dictzip_longest(
        index(deletes.xpath("event"), event_key),
        index(newstate.xpath("event"), event_key))

    merged_events = (merge_events(a, b) for (_, a, b) in merge_pairs)

    series = etree.Element("series")
    series.append(deepcopy(newstate.xpath("uniqueid")[0]))
    series.append(deepcopy(newstate.xpath("name")[0]))
    series.extend(merged_events)
    return series


def merge_events(deletes, newstate):
    assert (deletes is not None) ^ (newstate is not None), (
        "either an event is updated or deleted, never both")
    return deepcopy(deletes if newstate is None else newstate)


def generate_deletes(current, future, merge=True):
    """
    Given a current representation and future (desired) representation,
    work out which parts of current are not needed in future, and mark
    them for deletion in future.
    """

    # Situation: We have 2 trees, the current state (A) and the target
    # state (B). We want to generate a third state (C) with the necessary
    # (delete) commands to have the Timetable v0 API produce the future
    # when C is imported.
    # Strategy:
    # Merge A with B:
    #  - When something exists in A but not B, mark it for deletion
    #  - When something exists in B but not A, keep it unchanged
    #  - When something exists in A and B, use the version from B

    input_tree = wrap("states", [
        wrap("current", [current.getroot()]),
        wrap("future", [future.getroot()])
    ])

    # Go through the current state, removing anything which exists in the
    # future state and marking anything which doesn't exist for deletion
    output_tree = GENERATE_DELETES(input_tree)

    if merge is False:
        return output_tree.getroot()

    # Merge the deletions from the current state into the future state.
    # This merged result would result in the future state when applied to
    # the current state via the Timetable v0 API...
    return merge_module_lists(
        output_tree.xpath("/states/current/moduleList")[0],
        output_tree.xpath("/states/future/moduleList")[0])


def parse(filename):
    parser = etree.XMLParser(remove_blank_text=True)
    xml = etree.parse(filename, parser=parser)
    SCHEMA.assertValid(xml)
    return xml


def main():
    args = docopt.docopt(__doc__)

    current_state = parse(args["<current_state>"])
    future_state = parse(args["<future_state>"])

    with_deletes = generate_deletes(current_state, future_state,
                                    merge=not args["--unmerged"])

    with_deletes.getroottree().write(sys.stdout, pretty_print=True)


# From github.com/ucamhal/jsonmerge
def dictzip_longest(*dicts, **kwargs):
    """
    Like itertools.izip_longest but for dictionaries.

    For each key occuring in any of the dicts a tuple is returned containing
    (key, dict1-val, dict2-val, ... dictn-val)

    The fillvalue kwarg is substituted as the value for any dict not containing
    the key. fillvalue defaults to None.

    The order of the dict keys in the returned list is not defined.

    For example:
    >>> dictzip_longest(dict(a=1, b=2), dict(a=11, b=12), dict(x=100),
                        fillvalue=-1)
        [('a', 1, 11, -1), ('x', -1, -1, 100), ('b', 2, 12, -1)]
    """
    fillvalue = kwargs.get("fillvalue", None)
    keys = reduce(set.union, [set(d.keys()) for d in dicts], set())
    return [tuple([k] + [d.get(k, fillvalue) for d in dicts]) for k in keys]


if __name__ == "__main__":
    main()
