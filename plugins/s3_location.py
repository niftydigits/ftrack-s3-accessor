import ftrack_api
import ftrack_api.entity.location
import ftrack_api.accessor.disk
import ftrack_api.structure.id
import logging
import os

from s3 import S3Accessor


def configure_locations(event):
    '''Configure locations for session.'''
    session = event['data']['session']

    # Find location(s) and customise instances.
    location = session.query('Location where name is "studio.remote"').one()
    ftrack_api.mixin(location, ftrack_api.entity.location.UnmanagedLocationMixin)

    bucket_name = os.getenv("FTRACK_S3_ACCESSOR_BUCKET", "ftrack")

    # Setup accessor to use bucket
    location.accessor = S3Accessor(bucket_name)
    location.structure = ftrack_api.structure.id.IdStructure()
    location.priority = 30

    # Setup any other locations you require


def register(session):
    if not isinstance(session, ftrack_api.session.Session):
        return
    logging.info('Registering s3 accessor')

    session.event_hub.subscribe(
        'topic=ftrack.api.session.configure-location and source.user.username={}'.format(
            session.api_user
        ), configure_locations
    )
