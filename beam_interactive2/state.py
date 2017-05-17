from pyee import EventEmitter

from .connection import Call, Connection
from .discovery import Discovery
from .scene import Scene


class State(EventEmitter):
    """State is the state container for a single interactive session.
    It should usually be created via the static ``connect`` method::

        connection = State.connect(
            project_version_id=my_version_id,
            authorization="Bearer " + oauth_token)

    :param connection: The websocket connection to interactive.
    :type connection: Connection
    """

    def __init__(self, connection):
        super(State, self).__init__()
        self._scenes = {}
        self._connection = connection

        self.on('onSceneCreate', self._on_scene_create_or_update)
        self.on('onSceneUpdate', self._on_scene_create_or_update)
        self.on('onSceneDelete', self._on_scene_delete)

    def pump(self):
        """
        pump causes the state to read any updates it has queued up. This
        should usually be called at the start of any game loop where you're
        going to be doing processing of Interactive events.
        
        Any events that have not been read when pump() is called are discarded.
        """
        self._event_queue.clear()
        while True:
            call = self._connection.get_packet()
            if call is None:
                return

            self.emit(call.name, call)

    def create_scene(self, scene):
        """
        Can be called with a Scene to add it to Interactive.
        :param scene: 
        :type scene: Scene
        """
        self._scenes[scene]

    def _on_scene_delete(self, call):
        if call.data['sceneID'] not in self._scenes:
            return

        self._scenes[call.data['sceneID']].delete()
        del self._scenes[call.data['sceneID']]

    def _on_scene_create_or_update(self, call):
        for scene in call.data.scenes:
            if scene['sceneID'] in self._scenes:
                self._scenes[scene['sceneID']].update(scene)
            else:
                self._scenes[scene['sceneID']] = Scene(self, scene)

    @staticmethod
    def connect(discovery=Discovery(), **kwargs):
        """
        Creates a new interactive connection. Most arguments will be passed
        through into the Connection constructor.
        
        :param discovery: 
        :param kwargs: 
        :return: 
        """

        if 'address' not in kwargs:
            kwargs['address'] = discovery.find()

        connection = Connection(address=discovery.find(), **kwargs)

        return State(connection)
