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
#     Copyright 2009-2013 Carson Gee

#     This file is part of formunculous.
#     Copyright 2009-2013 Carson Gee

VERSION = (2, 2, 6, 'alpha', 1 )

def get_version():
    
    version = '%s.%s.%s' % (VERSION[0], VERSION[1], VERSION[2],)
    if VERSION[3] != 'final':
        version = '%s%s%s' % (version, VERSION[3], VERSION[4])
    
    return version


from django.template import add_to_builtins
import django
