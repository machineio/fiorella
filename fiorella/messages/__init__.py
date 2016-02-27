# -*- coding: utf-8 -*-
'''
    Fiorella system message models.
'''

# This file is part of fiorella.

# Distributed under the terms of the last AGPL License.
# The full license is in the file LICENCE, distributed as part of this software.

__author__ = 'Jean Chassoul'


import uuid

from schematics import models
from schematics import types
from schematics.types import compound


# here we make and configure outbound campaigns


'''
class OutboundCampaign(models.Model):
    uuid = types.UUIDType(default=uuid.uuid4)
    name = types.StringType(required=True)
    channel = types.StringType(required=True)
    context = types.StringType(required=True)
    extension = types.StringType(required=True)

    prefix = types.StringType()
    description = types.StringType()
'''


class SimpleResource(models.Model):
    '''
        Simple resource
    '''
    contains = compound.ListType(types.UUIDType())

    total = types.IntType()


class Resource(models.Model):
    ''' 
        Resource
    '''
    calls = compound.ModelType(SimpleResource)
    contacts = compound.ModelType(SimpleResource)
    directories = compound.ModelType(SimpleResource)

    total = types.IntType()