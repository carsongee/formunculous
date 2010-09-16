from django.core.management.base import NoArgsCommand
from django.utils.translation import ugettext as _
from django.conf import settings


import os
from distutils.dir_util import copy_tree

class Command(NoArgsCommand):

    help = _("""
This command will symlink the Formunculous static media
(css/js/images) folder into a subfolder called "formunculous" in the
MEDIA_ROOT folder defined in your settings.py file. If there is an
existing symlink, it will delete and add the new symlink.  If the 
path already exists and isn't a symlink, it will error out.
""")


    def handle_noargs(self, **options):

        # Find the location of our media by getting our file location
        # and modifying the path from there.
        location = os.path.dirname(__file__)
        media_from = os.path.normpath('%s/../../media/formunculous' % location)
        media_to = os.path.normpath(settings.MEDIA_ROOT)
        media_to += '/formunculous'

        # Check if path exists and if it is a symlink
        if os.path.exists(media_to):
            if not os.path.islink(media_to):
                print("""
The destination exists and is not a symlink, or symlinks are not
supported on this operating system.
""")
                return None
            else:
                os.remove(media_to)
        try:
            os.symlink(media_from, media_to)
        except:
            print("""
Unable to link media, please check your permissions and ensure that
your operating system supports symbolic links.
""")
        
        print( _("Created symlink from %s to %s." % (media_from, media_to) ))
        
        
