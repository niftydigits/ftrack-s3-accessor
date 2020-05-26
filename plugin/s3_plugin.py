import ftrack_api
import ftrack_api.entity.location
import ftrack_api.accessor.disk
import ftrack_api.structure.id

from s3 import S3Accessor


def configure_locations(event):
    '''Configure locations for session.'''
    session = event['data']['session']

    # Find location(s) and customise instances.
    location = session.query('Location where name is "test.s3"').one()
    ftrack_api.mixin(location, ftrack_api.entity.location.UnmanagedLocationMixin)
    location.accessor = S3Accessor('ftrackaccessor')
    location.structure = ftrack_api.structure.id.IdStructure()
    location.priority = 30


def register(session):
    '''Register plugin with *session*.'''
    session.event_hub.subscribe(
        'topic=ftrack.api.session.configure-location',
        configure_locations
    )
