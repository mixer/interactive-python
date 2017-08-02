import unittest
from interactive_python._util import Resource


def get_fixture():
    resource = Resource(
        id='red_team',
        id_property='groupID'
    )

    resource.assign(
        groupID='red_team',
        color='red',
        disabled=False,
        meta={'spooky': True},
    )

    resource._mark_synced()

    return resource


class TestResources(unittest.TestCase):

    def test_accesses_data(self):
        resource = get_fixture()
        self.assertEqual('red_team', resource.id)
        self.assertEqual('red', resource.color)
        self.assertEqual(True, resource.meta.spooky)
        with self.assertRaises(AttributeError):
            resource.meta.wut
        with self.assertRaises(AttributeError):
            resource.wut

    def test_diffs_resource(self):
        resource = get_fixture()
        resource.disabled = True  # changing a property
        resource.groupID = 'red_team'  # setting without notification
        self.assertTrue(resource.has_changed())
        self.assertEqual(
            {'groupID': 'red_team', 'disabled': True},
            resource._capture_changes()
        )
        self.assertFalse(resource.has_changed())

    def test_includes_changes_to_metadata(self):
        resource = get_fixture()
        resource.meta.spooky = False

        self.assertTrue(resource.has_changed())
        self.assertEqual(
            {
                'groupID': 'red_team',
                'meta': {'spooky': False}
             },
            resource._capture_changes()
        )
        self.assertFalse(resource.has_changed())
