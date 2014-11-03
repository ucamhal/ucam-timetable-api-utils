# coding=utf-8
import unittest

from lxml import etree

from ttapiutils.utils import write_c14n_pretty


class UtilsTest(unittest.TestCase):
    def test_write_c14n_pretty_maintains_unicode(self):
        elem = etree.Element("foo")
        elem_text = u"ƒ˙¬˚ßå∆ƒ∆ß¬å"
        elem.text = elem_text

        serialised = write_c14n_pretty(elem)
        self.assertEqual(
            u"<foo>{}</foo>".format(elem_text).encode("utf-8"), serialised)
