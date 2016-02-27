# -*- coding: utf-8 -*-
'''
    Fiorella indexes.
'''

# This file is part of fiorella.

# Distributed under the terms of the last AGPL License.
# The full license is in the file LICENCE, distributed as part of this software.

__author__ = 'Jean Chassoul'


def ensure_indexes(db):
    '''
        Ensure database indexes
    '''
    db.outbound.ensure_index([('uuid', 1)], unique=True)
    # contacts indexes
    db.contacts.ensure_index([('uuid', 1)], unique=True)
    db.contacts.ensure_index([('account', 1), ('phone_number', 1)], unique=True)
    # directories indexes
    db.directories.ensure_index([('uuid', 1)], unique=True)
    db.directories.ensure_index([('resources.contacts.contains', 1)])
    db.directories.ensure_index([('account', 1), ('name', 1)], unique=True)