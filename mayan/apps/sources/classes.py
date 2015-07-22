from __future__ import unicode_literals

import base64
import os
import urllib

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.core.files import File

from converter import TransformationResize, converter_class


class PseudoFile(File):
    def __init__(self, file, name):
        self.name = name
        self.file = file
        self.file.seek(0, os.SEEK_END)
        self.size = self.file.tell()
        self.file.seek(0)


class SourceUploadedFile(File):
    def __init__(self, source, file, extra_data=None):
        self.file = file
        self.source = source
        self.extra_data = extra_data


class Attachment(File):
    def __init__(self, part, name):
        self.name = name
        self.file = PseudoFile(
            StringIO(part.get_payload(decode=True)), name=name
        )


class StagingFile(object):
    """
    Simple class to extend the File class to add preview capabilities
    files in a directory on a storage
    """
    def __init__(self, staging_folder, filename=None, encoded_filename=None):
        self.staging_folder = staging_folder
        if encoded_filename:
            self.encoded_filename = str(encoded_filename)
            self.filename = base64.urlsafe_b64decode(
                urllib.unquote_plus(self.encoded_filename)
            )
        else:
            self.filename = filename
            self.encoded_filename = base64.urlsafe_b64encode(filename)

    def __unicode__(self):
        return unicode(self.filename)

    def as_file(self):
        return File(
            file=open(self.get_full_path(), mode='rb'), name=self.filename
        )

    def get_full_path(self):
        return os.path.join(self.staging_folder.folder_path, self.filename)

    def get_image(self, size=None, as_base64=True, transformations=None):
        converter = converter_class(file_object=open(self.get_full_path()))

        if size:
            converter.transform(
                transformation=TransformationResize(
                    **dict(zip(('width', 'height'), (size.split('x'))))
                )
            )

        # Interactive transformations
        for transformation in transformations:
            converter.transform(transformation=transformation)

        image_data = converter.get_page()

        if as_base64:
            base64_data = base64.b64encode(image_data.read())
            return 'data:%s;base64,%s' % ('image/png', base64_data)
        else:
            return image_data

    def delete(self):
        os.unlink(self.get_full_path())
