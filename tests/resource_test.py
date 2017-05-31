import unittest
from beam_interactive2._util import Resource


def get_fixture():
    resource = Resource(
        id='red_team',
        id_property='groupID',
        data_props=['disabled', 'color']
    )

    resource.assign(
        groupID='red_team',
        color='red',
        disabled=False,
        meta={'spooky': True},
    )

    resource._data['etag'] = '1234'
    resource._mark_synced()
    resource.meta._data['spooky']['etag'] = '5678'

    return resource


class TestGzipEncoding(unittest.TestCase):

    def test_accesses_data(self):
        resource = get_fixture()
        self.assertEqual('red_team', resource.id)
        self.assertEqual('red', resource.color)
        self.assertEqual(True, resource.meta.spooky)
        with self.assertRaises(AttributeError):
            resource.meta.wut
        with self.assertRaises(AttributeError):
            resource.wut

    def tests_diffs_resource(self):
        resource = get_fixture()
        resource.disabled = True  # changing a property
        resource.groupID = 'red_team'  # setting without notification
        self.assertTrue(resource.has_changed())
        self.assertEqual(
            {'etag': '1234', 'groupID': 'red_team', 'disabled': True},
            resource._capture_changes()
        )
        self.assertFalse(resource.has_changed())

    def test_includes_changes_to_metadata(self):
        resource = get_fixture()
        resource.meta.spooky = False

        self.assertTrue(resource.has_changed())
        self.assertEqual(
            {
                'etag': '1234',
                'groupID': 'red_team',
                'meta': {'spooky': {'etag': '5678', 'value': False}}
             },
            resource._capture_changes()
        )
        self.assertFalse(resource.has_changed())
