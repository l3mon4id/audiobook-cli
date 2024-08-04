from unittest import TestCase
from audiobook_cli.utils import path_from_metadata

metadata = {
    "title": "The Book of Tests",
    "author": "Some nice stranger",
    "series": "Programming for Dummies",
    "part": "42",
    "subtitle": "Programming for Dummies 42",
}


class MetadataTestCases(TestCase):
    def test_path_creation(self):
        path = path_from_metadata(metadata, series_subdir=True)
        assert (
            path
            == "Some nice stranger/Programming for Dummies/Programming for Dummies 42/The Book of Tests"
        )

    def test_path_creation_with_filename(self):
        path = path_from_metadata(metadata, series_subdir=True, include_filename=True)
        assert (
            path
            == "Some nice stranger/Programming for Dummies/Programming for Dummies 42/The Book of Tests/Some nice stranger - The Book of Tests.m4b"
        )

    def test_path_creation_with_subtitle(self):
        meta = metadata.copy()
        del meta["series"]
        path = path_from_metadata(meta, use_subtitle_as_series=True, series_subdir=True)
        assert (
            path
            == "Some nice stranger/Programming for Dummies/Programming for Dummies 42/The Book of Tests"
        )
