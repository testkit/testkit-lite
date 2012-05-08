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
#   validate xml utils
#

from lxml import etree

def validate_xml(schemafile, xmlfile):
    try:
        schema_doc = etree.parse(schemafile)
        schema = etree.XMLSchema(schema_doc)
        tree = etree.parse(xmlfile)
        if schema and not schema.validate(tree):
            raise Exception("schema validation for *%s* error: \n %s" \
                            % (xmlfile, schema.error_log))
        return True
    except Exception, e:
        print "failed to validate xml *%s*:\n%s" %(xmlfile, e)
        return False
