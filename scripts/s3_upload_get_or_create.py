import ftrack_api.structure.id
from ftrack_s3_accessor.s3 import S3Accessor
import os

asset_type_map = {
    'Scene': ['blend'],
    'Movie': ['mov', 'mp4']
}

paths_to_upload = [
    '/home/ian/Downloads/Junk Shop.blend',
]


def get_asset_type(asset_ext):
    for asset_type_name, asset_type_exts in asset_type_map.items():
        if asset_ext in asset_type_exts:
            return session.query('AssetType where name is "{}"'.format(asset_type_name)).one()


def get_or_create(entity_type, parent, entity_name):
    results = session.query("{} where parent.id is {} and name is '{}'".format(entity_type, parent['id'], entity_name))

    if len(results) == 0:
        return session.create(entity_type, {"name": entity_name, 'parent': parent})
    return results.one()


def get_or_create_asset(asset_type, asset_parent, asset_name):
    results = session.query("Asset where parent.id is {} and name is '{}' and type.id is {}".format(
        asset_parent['id'], asset_name, asset_type["id"]
    ))

    if len(results) == 0:
        return session.create('Asset', {
            'name': asset_name,
            'type': asset_type,
            'parent': asset_parent
        })
    return results.one()


session = ftrack_api.Session()
location = session.query(
    'Location where name is "studio.remote"'
).one()
bucket_name = os.getenv("FTRACK_S3_ACCESSOR_BUCKET", "ftrack")
location.accessor = S3Accessor(bucket_name)
location.structure = ftrack_api.structure.id.IdStructure()
location.priority = 30

project_name = "demo_generic"
project = session.query('Project where name is "{}"'.format(project_name)).one()
task = get_or_create("Task", project, entity_name="Test S3 Upload")

for path_to_upload in paths_to_upload:
    basename = os.path.basename(path_to_upload)
    basename_root, path_ext = os.path.splitext(basename)
    asset = get_or_create_asset(
        asset_type=get_asset_type(path_ext.lstrip(".")),
        asset_parent=task['parent'],
        asset_name=basename_root
    )
    asset_version = session.create('AssetVersion', {
        'asset': asset,
        'task': task
    })
    session.commit()
    version = session.get('AssetVersion', asset_version['id'])
    version.create_component(path=path_to_upload, location=location)
