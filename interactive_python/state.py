import collections
import asyncio
from pyee import EventEmitter

from .connection import Connection
from .discovery import Discovery
from .scene import Scene


class State(EventEmitter):
    """State is the state container for a single interactive session.
    It should usually be created via the static
    :func:`~interactive_python.State.connect` method::

        connection = State.connect(
            project_version_id=my_version_id,
            authorization="Bearer " + oauth_token)

    The Scene is a pyee.EventEmitter. When calls come down, they're always
    emitted on the State by their method name. So, for instance, you can
    listen to "onSceneCreate" or "onParticipantJoin" on the scene::

        def greet(call):
            for participant in call.data['participants']:
                print('Welcome {}!', participant['username'])

        scene.on('onParticipantJoin', greet)

    The state can work in two modes for handling delivery of events and updates.
    You can use `pump()` calls synchronously within your game loop to apply
    updates that have been queued. Alternately, you can call ``pump_async()`` to
    signal to that state that you want updates delivered asynchronously, as soon
    as they come in. For example::

        # Async delivery. `giveInput` is emitted as soon as any input comes in.
        state.on('giveInput', lambda call: do_the_thing(call))
        state.pump_async()

        # Sync delivery. `giveInput` is emitted only during calls to pump()
        state.on('giveInput', lambda call: do_the_thing(call))
        while True:
            my_game_loop.tick()
            state.pump()

            # You can also read queues of changes from pump(), if you prefer
            # to dispatch changes manually:
            # for call in pump(): ...

    In both modes, all incoming call are emitted as events on the State
    instance.

    :param connection: The websocket connection to interactive.
    :type connection: Connection
    """

    def __init__(self, connection):
        super(State, self).__init__()
        self._scenes = {'default': Scene('default')}
        self.connection = connection
        self._enable_event_queue = True
        self._event_queue = collections.deque()
        self._scenes['default']._attach_connection(self.connection)

        self.on('onSceneCreate', self._on_scene_create_or_update)
        self.on('onSceneUpdate', self._on_scene_create_or_update)
        self.on('onSceneDelete', self._on_scene_delete)
        self.on('onControlCreate', self._on_control_update_or_create)
        self.on('onControlUpdate', self._on_control_update_or_create)
        self.on('onControlDelete', self._on_control_delete)
        self.on('giveInput', self._give_input)

    def scene(self, name):
        """
        Looks up an existing scene by ID. It returns None if the scene does
        not exist.

        :param name: The name of the scene to look up
        :type name: str
        :return:
        :rtype: Scene
        """
        return self._scenes.get(name, None)

    def pump_async(self, loop=asyncio.get_event_loop()):
        """
        Starts a pump() process working in the background. Events will be
        dispatched asynchronously.

        Returns a future that can be used for cancelling the pump, if desired.
        Otherwise the pump will automatically stop once
        the connection is closed.

        :rtype: asyncio.Future
        """
        self._enable_event_queue = False

        async def run():
            try:
                while await self.connection.has_packet():
                    self.pump()
            except asyncio.CancelledError:
                self._enable_event_queue = True
            except Exception as e:
                self.emit('error', e)

        return asyncio.ensure_future(run(), loop=loop)

    def pump(self):
        """
        pump causes the state to read any updates it has queued up. This
        should usually be called at the start of any game loop where you're
        going to be doing processing of Interactive events.

        Any events that have not been read when pump() is called are discarded.

        Alternately, you can call pump_async() to have delivery handled for you
        without manual input.

        :rtype: Iterator of Calls
        """
        self._event_queue.clear()
        while True:
            call = self.connection.get_packet()
            if call is None:
                return

            self.emit(call.name, call)

            if self._enable_event_queue:
                self._event_queue.append(call)

        return self._event_queue

    async def create_scenes(self, *scenes):
        """
        Can be called with one or more Scenes to add them to Interactive.
        :param scenes: list of scenes to create
        :type scenes: Scene
        """
        for scene in scenes:
            self._scenes[scene.id] = scene
            scene._attach_connection(self)

        return await self.connection.call(
            'createScenes', [s._resolve_all() for s in scenes])

    async def set_ready(self, is_ready=True):
        """
        Marks the interactive integration as being ready-to-go. Must be called
        before controls will appear.

        :param is_ready: True or False to allow input
        :rtype: Reply
        """
        return await self.connection.call('ready', {'isReady': is_ready})

    def _give_input(self, call):
        control_id = call.data['input']['controlID']
        for scene in self._scenes.values():
            if control_id in scene.controls:
                scene.controls[control_id]._give_input(call)
                break

    def _on_scene_delete(self, call):
        if call.data['sceneID'] not in self._scenes:
            return

        self.scenes[call.data['sceneID']].delete(call)
        del self.scenes[call.data['sceneID']]

    def _on_scene_create_or_update(self, call):
        for scene in call.data.scenes:
            if scene['sceneID'] not in self._scenes:
                self._scenes[scene['sceneID']] = Scene(self, scene['sceneID'])

            self._scenes[scene['sceneID']]._apply_changes(scene, call)

    def _on_control_delete(self, call):
        if call.data['sceneID'] in self._scenes:
            self._scenes[call.data['sceneID']]._on_control_delete(call)

    def _on_control_update_or_create(self, call):
        if call.data['sceneID'] in self._scenes:
            self._scenes[call.data['sceneID']].\
                _on_control_update_or_create(call)

    @staticmethod
    async def connect(discovery=Discovery(), **kwargs):
        """
        Creates a new interactive connection. Most arguments will be passed
        through into the Connection constructor.

        :param discovery:
        :type discovery: Discovery
        :param kwargs:
        :rtype: State
        """

        if 'address' not in kwargs:
            kwargs['address'] = await discovery.find()

        connection = Connection(**kwargs)
        await connection.connect()
        return State(connection)
