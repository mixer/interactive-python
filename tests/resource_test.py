import unittest
from beam_interactive2._util import Resource


def get_fixture():
    return Resource(groupID='red_team', etag='1234',
                    meta={'enabled': {'etag': '5678', 'value': True}})


class TestGzipEncoding(unittest.TestCase):

    def test_accesses_data(self):
        resource = get_fixture()
        self.assertEqual("red_team", resource.groupID)
        self.assertEqual(True, resource.meta.enabled)
        with self.assertRaises(AttributeError):
            resource.meta.wut
        with self.assertRaises(AttributeError):
            resource.wut

    def tests_diffs_resource(self):
        resource = get_fixture()
        resource.disabled = True  # adding a new property
        resource.groupID = 'blue_team'  # modifying an existing property
        self.assertTrue(resource.has_changed())
        self.assertEqual(
            {'etag':'1234', 'groupID': 'blue_team', 'disabled': True},
            resource.capture_changes()
        )
        self.assertFalse(resource.has_changed())

        resource.groupID = 'blue_team'  # setting but not changing the prop
        self.assertFalse(resource.has_changed())
        self.assertEqual({'etag': '1234'}, resource.capture_changes())

    def test_fails_to_set_immutable_properties(self):
        with self.assertRaises(AttributeError):
            get_fixture().etag = 'wut'

    def test_includes_changes_to_metadata(self):
        resource = get_fixture()
        resource.meta.enabled = False
        self.assertTrue(resource.has_changed())
        self.assertEqual(
            {
                'etag': '1234',
                'meta': {'enabled': {'etag': '5678', 'value': False}}
             },
            resource.capture_changes()
        )
        self.assertFalse(resource.has_changed())
