#!/usr/bin/python
# 
# Copyright (C) 2010, Intel Corporation.
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.  
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307 USA.
#
# Authors:
#              Wei, Zhang <wei.z.zhang@intel.com>
#
# Description:
#   define some data structure here
#


###############################################################################
class LimitedAttributes(object):
    """the limited attributes class

       LimitedAttributes is limited in following 4 aspects:
       1. LIMITED_NAMES    list defines the attributes need to be limited
       2. LIMITED_DEFAULTS dict defines the default value
       3. LIMITED_TYPES    dict defines the type limitation
       4. LIMITED_VALUES   dict defines the value limitation

       Besides these LIMITED attributes, the sub-class could have other
       attributes defined in common way
    """

    # overwrite following variables in sub-class
    LIMITED_NAMES    = []
    LIMITED_DEFAULTS = {}
    LIMITED_TYPES    = {}
    LIMITED_VALUES   = {}

    def __setattr__(self, name, value):
        """limit the attribute's type/name/value
        """

        if name in self.LIMITED_NAMES:
            if value is not None:

                # TYPE limitation
                if name in self.LIMITED_TYPES:
                    if None != self.LIMITED_TYPES[name] and \
                       0    != self.LIMITED_TYPES[name] and \
                       type(value) not in self.LIMITED_TYPES[name]:
                        print "attribute *%s*'s value *%s* is not in limited_type scope: *%s*, set to None" \
                              %(name, value, self.LIMITED_TYPES[name])
                        value = None

                # VALUE limitation
                if name in self.LIMITED_VALUES:
                    if None != self.LIMITED_VALUES[name] and \
                       0    != self.LIMITED_VALUES[name] and \
                       value not in self.LIMITED_VALUES[name]:
                        print "attribute *%s*'s value *%s* is not in limited_value scope: *%s*, set to None" \
                               %(name, value, self.LIMITED_VALUES[name])
                        value = None

        object.__setattr__(self, name, value)


    def __getattr__(self, name):
        """just return None for non-set attribute if name in LIMITED_NAMES
        """
        if name in self.LIMITED_NAMES:
            return None
        else:
            return object.__getattribute__(self, name)


    def get(self, name):
        """ *get* value set before or the default value if name in LIMITIED_NAMES
            *get* value in __dict__ if name not in LIMITED_NAMES but in __dict__
        """

        if name in self.LIMITED_NAMES:
            if name in self.__dict__:
                value = object.__getattribute__(self, name)
                if value is None and name in self.LIMITED_DEFAULTS:
                    return self.LIMITED_DEFAULTS[name]
                else:
                    return value
            else:
                if name in self.LIMITED_DEFAULTS:
                    return self.LIMITED_DEFAULTS[name]
                else:
                    return None

        elif name in self.__dict__:
            return self.__dict__[name]

        else:
            print "key *%s* is invalid for %s"%(name, self.__class__.__name__)
            return None
