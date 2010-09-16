from django.core.management.base import NoArgsCommand
from django.utils.translation import ugettext as _
from django.conf import settings


import os
from distutils.dir_util import copy_tree

class Command(NoArgsCommand):

    help = _("""
This command will copy the Formunculous static media (css/js/images)
into a subfolder called "formunculous" into the MEDIA_ROOT folder
defined in your settings.py file. It will overwrite any duplicate
files in the directory.
""")


    def handle_noargs(self, **options):

        # Find the location of our media by getting our file location
        # and modifying the path from there.
        location = os.path.dirname(__file__)
        media_from = os.path.normpath('%s/../../media/formunculous' % location)
        media_to = os.path.normpath(settings.MEDIA_ROOT)
        media_to += '/formunculous'

        # Using the distutils copytree because it allows for the folder
        # to already exist (nice for upgrades).
        copy_tree(media_from, media_to)

        
        
        print(_("Copied %s to %s creating any needed directories" % (media_to, media_from) ))
        
        
