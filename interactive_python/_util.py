import string
import random
import json
import asyncio

from pyee import EventEmitter

metadata_prop_name = "meta"


def random_string(length, source=string.ascii_letters):
    return ''.join(random.choice(source) for x in range(length))


def until_event(emitter, name, loop=asyncio.get_event_loop()):
    fut = asyncio.Future(loop=loop)
    emitter.once(name, lambda result: fut.set_result(result))
    return fut


class OverridableJSONEncoder(json.JSONEncoder):
    """
    OverridableJSONEncoder extends the default JSON encoder to look for a method
    'to_json' on objects to be serialized, calling that when possible.
    """

    def default(self, obj):
        if callable(getattr(obj, 'to_json', None)):
            return obj.to_json()
        return super().default(obj)

json_encoder = OverridableJSONEncoder(check_circular=False, allow_nan=False,
                                      separators=(',', ':'))


class ChangeTracker:
    """
    ChangeTracker is a simple structure that keeps track of changes made to
    properties of the object.
    """

    def __init__(self, data={}, intrinsic_properties=[]):
        self._intrinsic_properties = intrinsic_properties
        self._nested_trackers = [(key, value) for key, value in data.items()
                                 if isinstance(value, ChangeTracker)]
        self._data = data
        self._changes = set()

    def assign(self, **kwargs):
        """
        Assigns data in-bulk to the resource, returns the resource.
        :rtype: Resource
        """
        for key, value in kwargs.items():
            self._set_and_track_property(key, value)

        return self

    def to_json(self):
        """
        to_json will be called when serializing the resource to JSON. It returns
        the raw data.
        :return:
        """
        return self._data

    def _capture_changes(self):
        """
        Returns a dict of changes and resets the "changed" state.
        :rtype: dict
        """
        output = {}
        for prop in self._intrinsic_properties:
            output[prop] = self._data[prop]

        for key, tracker in self._nested_trackers:
            if tracker.has_changed():
                output[key] = tracker._capture_changes()

        for key in self._changes:
            output[key] = self._data.get(key, None)

        self._changes.clear()
        return output

    def has_changed(self):
        """
        Returns whether any metadata properties have changed.
        :rtype: bool
        """
        if len(self._changes) > 0:
            return True

        if any(tracker.has_changed() for key, tracker in self._nested_trackers):
            return True

        return False

    def _mark_synced(self):
        """
        Marks the changed properties on the resource as having been saved.
        """
        self._changes.clear()

    def _set_and_track_property(self, key, value):
        previous_value = self._data.get(key, None)

        if isinstance(previous_value, ChangeTracker):
            previous_value.assign(**value)
        elif value != previous_value:
            if value is None:
                del self._data[key]
            else:
                self._data[key] = value

            self._changes.add(key)

    def __setattr__(self, key, value):
        if key[0] == '_':
            self.__dict__[key] = value
            return

        self._set_and_track_property(key, value)

    def __getattr__(self, key):
        if key not in self._data:
            raise AttributeError(key)

        return self._data[key]


class Resource(EventEmitter, ChangeTracker):
    """Resource represents some taggable, metadata-attachable construct in
    Interactive. Scenes, groups, and participants are resources.
    """

    def __init__(self, id, id_property):
        ChangeTracker.__init__(
            self,
            intrinsic_properties=[id_property],
            data={id_property: id, 'meta': ChangeTracker()}
        )
        EventEmitter.__init__(self)

        self._id_property = id_property
        self._connection = None

    @property
    def id(self):
        """
        :rtype: int
        """
        return self._data[self._id_property]

    def _attach_connection(self, connection):
        """
        Called by the State when it gets or creates a new instance of this
        resource. Used for RPC calls.
        """
        self._connection = connection

    def _apply_changes(self, change, call):
        """
        Applies a complete update of properties from the remote server.
        :type change: dict
        :type call: Call
        """
        self.assign(**change)
        self._mark_synced()
        self.emit('update', call)

    def _on_deleted(self, call):
        """
        Called when a scene is deleted.
        :type call: Call
        """
        self.emit('delete', call)
