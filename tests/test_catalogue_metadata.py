"""Retain the six independently identified metadata-parser challenge cases."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "research" / "catalogue_metadata"))
from parse_list_metadata import project


class CatalogueMetadataTests(unittest.TestCase):
    base = "https://de-crypt.org/decrypt-web/RecordsList"

    def unknown(self, html):
        result = project(html, self.base)
        self.assertEqual(result["status"], "HOLD_RESULT_COUNT_UNVERIFIED")
        self.assertIsNone(result["actual_result_count"])

    def test_generic_banner(self):
        self.unknown('<div class="alert alert-info">No records found</div>')

    def test_banner_and_login(self):
        self.unknown('<div class="ew-no-record">No records found</div>'
                     '<form>Sign in</form>')

    def test_invalid_link_and_unbound_marker(self):
        self.unknown('<table><th>Current Location and Name</th><tr><td>'
                     '<a href="https://example.invalid/decrypt-web/RecordsView/123">item</a>'
                     '</td></tr></table><div class="ew-no-record">No records found</div>')

    def test_two_conflicting_ids(self):
        self.unknown('<table><th>Current Location and Name</th><tr><td>'
                     '<a href="/decrypt-web/RecordsView/203">first</a>'
                     '<a href="/decrypt-web/RecordsView/2034">second</a>'
                     '</td></tr></table>')

    def test_empty_marker_with_invalid_pointer(self):
        self.unknown('<table><th>Current Location and Name</th><tr><td>'
                     '<a href="https://example.invalid/decrypt-web/RecordsView/123">item</a>'
                     '<div class="ew-no-record">No records found</div>'
                     '</td></tr></table>')

    def test_empty_marker_with_extra_data(self):
        self.unknown('<table><th>Current Location and Name</th><tr><td>'
                     'Additional data<div class="ew-no-record">No records found</div>'
                     '</td></tr></table>')
