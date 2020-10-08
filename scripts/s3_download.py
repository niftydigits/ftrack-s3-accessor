import ftrack_api.structure.id
import ftrack_api.accessor.disk
import os

from ftrack_s3_accessor.s3 import S3Accessor

'''
Copies a component from a s3 location to a local location
'''
session = ftrack_api.Session()
s3_location = session.query(
    'Location where name is "studio.remote"'
).one()
bucket_name = os.getenv("FTRACK_S3_ACCESSOR_BUCKET", "ftrack")
s3_location.accessor = S3Accessor(bucket_name)
s3_location.structure = ftrack_api.structure.id.IdStructure()
s3_location.priority = 30

ftrack_location = session.query(
    'Location where name is "ftrack.connect"'
).one()
ftrack_location.structure = ftrack_api.structure.id.IdStructure()
ftrack_location.accessor = ftrack_api.accessor.disk.DiskAccessor(
    prefix="/home/ian/ftrack_storage"
)

version = session.get('AssetVersion', '87d07110-962b-11ea-8647-927195c3dfa3')

for component in version['components']:
    if component['name'] == 'main':
        ftrack_location.add_component(component, s3_location)
