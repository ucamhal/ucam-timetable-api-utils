import unittest
from copy import deepcopy

import pkg_resources

from ttapiutils.deletegen import generate_deletes, DuplicateKeyException
from ttapiutils.canonicalise import canonicalise
from ttapiutils.utils import parse_xml, write_c14n_pretty


class TtapiutilsTestCaseMixin(object):
    def get_xml_data(self, name):
        file = pkg_resources.resource_stream(
            "ttapiutils.tests.test_deletegen", "data/deletegen/{}".format(name))
        return parse_xml(file)

    def canonical_serialisation(self, api_xml):
        return write_c14n_pretty(canonicalise(api_xml))

    def assert_api_xml_equal(self, a, b):
        self.assertEqual(
            self.canonical_serialisation(a),
            self.canonical_serialisation(b))


class DeletegenTest(TtapiutilsTestCaseMixin, unittest.TestCase):
    def test_identical_states_are_unchanged(self):
        state_current = self.get_xml_data("small.xml")
        state_future = deepcopy(state_current)

        self.assert_api_xml_equal(state_current, state_future)

        with_deletes = generate_deletes(state_current, state_future)
        self.assert_api_xml_equal(state_current, with_deletes)

    def test_duplicate_event_ids_raise_exception(self):
        state = self.get_xml_data("duplicate_event.xml")

        with self.assertRaises(DuplicateKeyException):
            generate_deletes(state, state)

    def test_duplicate_series_raise_exception(self):
        state = self.get_xml_data("duplicate_series.xml")

        with self.assertRaises(DuplicateKeyException):
            generate_deletes(state, state)

    def test_duplicate_modules_raise_exception(self):
        state = self.get_xml_data("duplicate_module.xml")

        with self.assertRaises(DuplicateKeyException):
            generate_deletes(state, state)

    def test_modules_in_current_but_not_future_state_are_deleted(self):
        current = self.get_xml_data("deleted_module_current.xml")
        future = self.get_xml_data("deleted_module_future.xml")

        with_deletes = generate_deletes(current, future)

        self.assertTrue(with_deletes.xpath(
            "/moduleList/module["
                "name='Module not in future state' and "
                "path/tripos='foo' and "
                "path/part='I'"
            "]/delete"))

    def test_series_in_current_but_not_future_state_are_deleted(self):
        current = self.get_xml_data("deleted_series_current.xml")
        future = self.get_xml_data("deleted_series_future.xml")

        with_deletes = generate_deletes(current, future)

        self.assertTrue(with_deletes.xpath(
            "/moduleList/module["
                "name='Module Foo' and "
                "path/tripos='foo' and "
                "path/part='I'"
            "]/series["
                "name='Series not in future state'"
            "]/delete"))
