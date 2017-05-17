import string
import random

metadata_prop_name = "meta"
etag_prop_name = "etag"


def random_etag():
    return random_string(7)


def random_string(length, source=string.ascii_letters):
    return ''.join(random.choice(source) for x in range(length))


class Metadata:
    """
    Metadata is used to accessing and modifying a resource's metadata props.
    """

    def __init__(self, data={}):
        self._data = data
        self._changes = []

    def _capture_changes(self):
        """
        Returns a dict of changes and resets the "changed" state.
        :rtype: dict
        """
        output = {}
        for key in self._changes:
            output[key] = self._data[key]
        self._changes = []
        return output

    def _apply_changes(self, change):
        """
        Applies a complete update of properties from the remote server.
        """
        for key, value in change.items():
            if key not in self._changes:
                self._data[key] = value

    def assign(self, **kwargs):
        """
        Assigns data in-bulk to the resource, returns the resource.
        :rtype: Resource
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        return self

    def has_changed(self):
        """
        Returns whether any metadata properties have changed.
        :rtype: bool
        """
        return len(self._changes) > 0

    def _mark_synced(self):
        """
        Marks the changed properties on the resource as having been saved.
        """
        self._changes = []

    def __setattr__(self, key, value):
        if key[0] == '_':
            self.__dict__[key] = value
            return

        if key not in self._data:
            self._data[key] = {etag_prop_name: random_etag(), 'value': None}

        if value == self._data[key]['value']:
            return

        self._data[key]['value'] = value
        if key not in self._changes:
            self._changes.append(key)

    def __getattr__(self, item):
        if item not in self._data:
            raise AttributeError(item)

        return self._data[item]['value']


class Resource:
    """Resource represents some taggable, metadata-attachable construct in
    Interactive. Scenes, groups, and participants are resources.
    """

    def __init__(self, id, id_property, mutable_props=[], etag=random_etag()):
        self._mutable_props = mutable_props
        self._changes = []
        self._data = {}
        self._id_property = id_property
        self._etag = etag
        self.id = id

        for key in mutable_props:
            self._data[key] = None

        self.meta = Metadata()

    def has_changed(self):
        """
        Returns whether any metadata properties have changed.
        :rtype: bool
        """
        return self.meta.has_changed() or len(self._changes) > 0

    def assign(self, **kwargs):
        """
        Assigns data in-bulk to the resource, returns the resource.
        :rtype: Resource
        """
        for key, value in kwargs.items():
            if key == 'meta':
                self.meta.assign(**value)
            else:
                setattr(self, key, value)

        return self

    def _apply_changes(self, change):
        """
        Applies a complete update of properties from the remote server.
        """
        for key, value in change.items():
            if key == metadata_prop_name:
                self.meta._apply_changes(**value)
            elif key not in self._changes:
                self._data[key] = value

    def _capture_changes(self):
        """
        Returns a dict of changes and resets the "changed" state.
        :rtype: dict
        """
        changes = {
            self._id_property: self.id,
            etag_prop_name: self._etag,
        }

        for key in self._changes:
            changes[key] = self._data[key]
        self._changes = []

        if self.meta.has_changed():
            changes[metadata_prop_name] = self.meta._capture_changes()

        return changes

    def _mark_synced(self):
        """
        Marks the changed properties on the resource as having been saved.
        """
        self._changes = []
        self.meta._mark_synced()

    def __setattr__(self, key, value):
        if key[0] == '_' or key not in self._mutable_props:
            self.__dict__[key] = value
            return

        if value != self._data[key]:
            self._data[key] = value
            if key not in self._changes:
                self._changes.append(key)

    def __getattr__(self, item):
        if item not in self._data:
            raise AttributeError(item)

        return self._data[item]
