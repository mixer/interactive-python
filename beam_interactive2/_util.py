metadata_prop_name = "meta"
etag_prop_name = "etag"


class DiffSettable(object):
    def __init__(self, data, immutable=[etag_prop_name]):
        """Data should be a dict of keys to *something*, passed through
        _get_data and returned from _set_data. Immutable is a list of properties
        we should not allow the caller to change.
        """
        self.__data = {}
        self.__changed = []
        self.__immutable = immutable
        self._bypass_setter = False
        self.apply_update(data)

    def _get_data(self, key, raw_value):
        """Called when looking up a key, passed the value inside of the `data`.
        It may transform and return the value as necessary.
        """
        return raw_value

    def _set_data(self, key, raw_value, previous_value):
        """Called when updating a key, passed the value being updated. It may
        transform and return the value as necessary before it's stored."""
        return raw_value

    def _create_changes(self, mapping):
        """Called when creating a change list. Mapping a dict of change keys
        to the raw objects. The dict may be mutated and returned.
        """
        return mapping

    def has_changed(self):
        """Returns whether the resource has had changes made to it."""
        return len(self.__changed) > 0

    def apply_update(self, change):
        """Updates the properties stored on the resource."""
        for key, value in change.items():
            if key not in self.__changed:
                self.__data[key] = value

    def capture_changes(self):
        """Returns an object of changed properties that can be used to patch
        the resource.
        """
        changed = {}
        for key in self.__changed:
            changed[key] = self.__data[key]
        self.__changed = []

        return self._create_changes(changed)

    def __setattr__(self, key, value):
        if (len(key) > 0 and key[0] == '_') or self._bypass_setter:
            self.__dict__[key] = value
            return

        if key in self.__immutable:
            raise AttributeError('Refusing to set immutable attribute {}'
                                 .format(key))

        previous_value = None
        if key in self.__data:
            previous_value = self.__data[key]

        if previous_value != value:
            self.__data[key] = self._set_data(key, value, previous_value)
            self.__changed.append(key)

    def __getattr__(self, key):
        if key not in self.__data:
            raise AttributeError()

        return self._get_data(key, self.__data[key])


class Metadata(DiffSettable):
    def _get_data(self, key, raw_value):
        return raw_value['value']

    def _set_data(self, key, raw_value, previous_value):
        if previous_value is not None:
            return {'value': raw_value, 'etag': previous_value['etag']}

        return {'value': raw_value}


class Resource(DiffSettable):
    """Resource represents some taggable, metadata-attachable construct in
    Interactive. Scenes, groups, and participants are resources.
    """

    def __init__(self, **kwargs):
        self._bypass_setter = True
        self.meta = Metadata({})
        self._bypass_setter = False

        super(Resource, self).__init__(kwargs)

    def has_changed(self):
        return self.meta.has_changed() or super(Resource, self).has_changed()

    def apply_update(self, change):
        if metadata_prop_name in change:
            self.meta.apply_update(change[metadata_prop_name])
            del change[metadata_prop_name]

        super(Resource, self).apply_update(change)

    def _create_changes(self, mapping):
        """Called when creating a change list. Mapping a dict of change keys
        to the raw objects. The dict may be mutated and returned.
        """
        mapping[etag_prop_name] = getattr(self, etag_prop_name)
        if self.meta.has_changed():
            mapping[metadata_prop_name] = self.meta.capture_changes()

        return mapping
