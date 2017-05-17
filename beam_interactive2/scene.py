from ._util import random_etag, Resource


class Scene(Resource):
    """
    Scene is a container for controls in interactive. Groups can be assigned
    to scenes.
    """

    def __init__(self, sceneID, etag=random_etag(), controls=[], is_new=True):
        super(Scene, self).__init__(
            data={'sceneID': sceneID, 'etag': etag},
            immutable=['sceneID', 'etag'],
            is_new=is_new)

        with self._ignore_setter():
            self.controls = controls
