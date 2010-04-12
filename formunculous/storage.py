#     This file is part of formunculous.
#
#     formunculous is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     formunculous is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with formunculous.  If not, see <http://www.gnu.org/licenses/>.
#     Copyright 2009,2010 Carson Gee

from django.core.files.storage import FileSystemStorage
from django.conf import settings

# Still need to deal with access control to these files using this
# storage system.  Likely move this class out to another file
# that handles viewing these files and the permissions they recieve


class ApplicationStorage(FileSystemStorage):
    """
       Does file replacement on file fields instead of renaming them
    """

    def __init__(self, location=None, base_url=None):
        if location is None:
            self.location = settings.APP_STORAGE_ROOT
        if base_url is None:
            # This app could be run from any url, grab the url from the
            # base view.
            self.base_url = "%sstorage/" % settings.APP_STORAGE_URL
        super(ApplicationStorage, self).__init__(location=self.location,
                                                 base_url=self.base_url)
        
    
    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
            self.delete(name)
        return name

def upload_to_path(instance, filename):
    # Save the instance to get the ID
    return "%s/%s/%s/%s" % ( instance.app.app_definition.slug,
                                instance.app.id, instance.field_def.slug,
                                filename)

