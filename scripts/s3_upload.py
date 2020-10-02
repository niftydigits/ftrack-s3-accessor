import ftrack_api.structure.id
from ftrack_s3_accessor.s3 import S3Accessor
import os

'''
Creates a component under a known existing asset version
'''
session = ftrack_api.Session()
location = session.query(
    'Location where name is "studio.remote"'
).one()
bucket_name = os.getenv("FTRACK_S3_ACCESSOR_BUCKET", "ftrack")
location.accessor = S3Accessor(bucket_name)
location.structure = ftrack_api.structure.id.IdStructure()
location.priority = 30

version = session.get('AssetVersion', '87d07110-962b-11ea-8647-927195c3dfa3')
version.create_component(path='/home/ian/Downloads/trailer_1080p.mov', location=location)
