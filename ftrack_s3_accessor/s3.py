import os

from io import BytesIO

BOTO_AVAILABLE = False

try:
    import boto3

    BOTO_AVAILABLE = True
except ImportError:
    pass

from ftrack_api.accessor.base import Accessor
from ftrack_api.data import FileWrapper
from ftrack_api.exception import (AccessorOperationFailedError,
                                  AccessorUnsupportedOperationError,
                                  AccessorResourceInvalidError,
                                  AccessorResourceNotFoundError,
                                  AccessorContainerNotEmptyError,
                                  AccessorParentResourceNotFoundError)


class S3File(FileWrapper):
    """S3 Buffered File.
    """

    def __init__(self, key, mode='rb'):
        """Initialise S3 file with S3 *key* and *mode*."""
        self.key = key
        self.mode = mode
        wrapped_file = BytesIO()
        super(S3File, self).__init__(wrapped_file)
        self._read()

    def flush(self):
        """Flush all changes."""
        super(S3File, self).flush()
        self._write()

    def _read(self):
        """Read all remote content from key into wrapped_file."""
        position = self.tell()
        self.seek(0)
        self.key.download_fileobj(self.wrapped_file)
        if not self.wrapped_file.closed:
            self.seek(position)

    def _write(self):
        """Write current data to remote key."""
        position = self.tell()
        self.seek(0)
        self.key.upload_fileobj(self.wrapped_file)
        if not self.wrapped_file.closed:
            self.seek(position)


class S3Accessor(Accessor):
    """Provide Amazon S3 location access.

    To use, please first install the :term:`Boto3` package.
    """

    def __init__(self, bucket_name):
        """Initialise location accessor.

        *bucket_name* is the name of the bucket to provide access to using
        *access_key* and *secretKey* credentials.
        """
        if not BOTO_AVAILABLE:
            raise NotImplementedError(
                'S3Accessor not available as failed to import boto3 package. '
                'Please install boto3 if you want to use this accessor.'
            )

        self.bucket_name = bucket_name
        self._s3 = None
        self._bucket = None
        super(S3Accessor, self).__init__()

    def __deepcopy__(self, memo):
        """Return a new S3Accessor instance

        There is a known issue on some operating systems when using :term:`Boto`
        >= 2.29 against :term:`Python` >= 2.7. The issue typically manifests
        itself with the following error::

            TypeError: cannot deepcopy this pattern object

        To work around the issue we return a new instance of the accessor which
        does not contain the compiled patterns in the Boto internals.
        """
        return S3Accessor(self.bucket_name)

    @property
    def s3(self):
        """Return S3 resource."""
        if self._s3 is None:
            self._s3 = boto3.resource('s3')

        return self._s3

    @property
    def bucket(self):
        """Return bucket."""
        if self._bucket is None:
            self._bucket = self.s3.Bucket(self.bucket_name)

        return self._bucket

    def list(self, resource_identifier):
        """Return list of entries in *resource_identifier* container.

        Each entry in the returned list should be a valid resource identifier.

        Raise :py:class:`~ftrack.ftrackerror.AccessorResourceNotFoundError` if
        *resourceIdentifier* does not exist or
        :py:class:`~ftrack.ftrackerror.AccessorResourceInvalidError` if
        *resourceIdentifier* is not a container.

        """
        if not resource_identifier.endswith('/'):
            resource_identifier += '/'

        if resource_identifier == '/':
            resource_identifier = ''

        listing = []
        for entry in self.bucket.objects.filter(Prefix=resource_identifier, Delimiter='/'):
            if entry.name != resource_identifier:
                listing.append(entry.name.rstrip('/'))

        return listing

    def exists(self, resource_identifier):
        """Return if *resourceIdentifier* is valid and exists in location."""
        # Root directory always exists
        if not resource_identifier:
            return True

        return (self.is_container(resource_identifier) or
                self.is_file(resource_identifier))

    def is_file(self, resource_identifier):
        """Return whether *resource_identifier* refers to a file."""
        # Root is a directory
        if not resource_identifier:
            return False

        resource_identifier = resource_identifier.rstrip('/')
        try:
            s3_object = self.bucket.Object(resource_identifier)
        except self.s3.meta.client.exceptions.ClientError as error:
            if error.status == 403:
                # Permission denied
                return False

            else:
                raise AccessorOperationFailedError(
                    operation='is_file',
                    resourceIdentifier=resource_identifier,
                    details=error
                )

        return s3_object.meta.data is not None

    def is_container(self, resource_identifier):
        """Return whether *resource_identifier* refers to a container."""
        # Root is a directory
        if not resource_identifier:
            return True

        # Check if list request returns any files. This avoids relying on the
        # presence of a special empty file for directories.
        if not resource_identifier.endswith('/'):
            resource_identifier += '/'

        s3_objects = self.bucket.objects.filter(Prefix=resource_identifier, Delimiter='/')

        try:
            next(iter(s3_objects))
        except StopIteration:
            return False
        else:
            return True

    def is_sequence(self, resource_identifier):
        """Return whether *resource_identifier* refers to a file sequence."""
        raise AccessorUnsupportedOperationError('is_sequence')

    def open(self, resource_identifier, mode='rb'):
        """Return :py:class:`~ftrack.Data` for *resourceIdentifier*."""
        if self.is_container(resource_identifier):
            raise AccessorResourceInvalidError(
                resource_identifier,
                message='Cannot open a directory: {resource_identifier}'
            )

        s3_object = self.bucket.Object(resource_identifier)

        if s3_object is None:
            if 'w' not in mode and 'a' not in mode:
                raise AccessorResourceNotFoundError(resource_identifier)

            if not self.is_container(self.get_container(resource_identifier)):
                raise AccessorResourceNotFoundError(
                    self.get_container(resource_identifier)
                )

            # New file
            s3_object = self.bucket.Object(resource_identifier)
            s3_object.put(Body='')

        elif 'w' in mode:
            # Truncate file
            s3_object.put(Body='')

        return S3File(s3_object, mode=mode)

    def remove(self, resource_identifier):
        """Remove *resourceIdentifier*.

        Raise :py:class:`~ftrack.ftrackerror.AccessorResourceNotFoundError` if
        *resourceIdentifier* does not exist.

        """
        if self.is_file(resource_identifier):
            self.bucket.objects.filter(Prefix=resource_identifier).delete()

        elif self.is_container(resource_identifier):
            contents = self.list(resource_identifier)
            if contents:
                raise AccessorContainerNotEmptyError(resource_identifier)

            self.bucket.objects.filter(resource_identifier + '/').delete()

        else:
            raise AccessorResourceNotFoundError(resource_identifier)

    def get_container(self, resource_identifier):
        """Return resourceIdentifier of container for *resourceIdentifier*.

        Raise
        :py:class:`~ftrack.ftrackerror.AccessorParentResourceNotFoundError` if
        container of *resourceIdentifier* could not be determined.

        """
        if os.path.normpath(resource_identifier) in ('/', ''):
            raise AccessorParentResourceNotFoundError(
                resource_identifier,
                message='Could not determine container for '
                        '{resource_identifier} as it is the root.'
            )

        return os.path.dirname(resource_identifier.rstrip('/'))

    def make_container(self, resource_identifier, recursive=True):
        """Make a container at *resourceIdentifier*.

        If *recursive* is True, also make any intermediate containers.

        """
        if not resource_identifier:
            # Root bucket directory
            return

        if not resource_identifier.endswith('/'):
            resource_identifier += '/'

        if self.exists(resource_identifier):
            if self.is_file(resource_identifier):
                raise AccessorResourceInvalidError(
                    resource_identifier,
                    message=('Resource already exists as a file: '
                             '{resourceIdentifier}')
                )

            else:
                return

        parent = self.get_container(resource_identifier)
        if not self.is_container(parent):
            if recursive:
                self.make_container(parent, recursive=recursive)
            else:
                raise AccessorParentResourceNotFoundError(parent)

        s3_object = self.bucket.Object(resource_identifier)
        s3_object.put(Body='')
