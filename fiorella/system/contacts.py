# -*- coding: utf-8 -*-
'''
    Fiorella contacts system logic.
'''

# This file is part of fiorella.

# Distributed under the terms of the last AGPL License.
# The full license is in the file LICENCE, distributed as part of this software.

__author__ = 'Jean Chassoul'


import arrow
import motor
import uuid

import logging

from tornado import gen

from fiorella.messages import contacts

from fiorella.tools import clean_structure, clean_results


class Contacts(object):
    '''
        Fiorella contacts
    '''

    @gen.coroutine
    def get_contact_list(self, account, checked, page_num):
        '''
            Get contact list
        '''
        page_num = int(page_num)
        page_size = self.settings.get('page_size')
        contact_list = []

        # remove phone_2, phone_3 and contact_requests from query stuff and db.
        query = self.db.contacts.find(
            {
                'account':account,
                'checked':checked
            },
            {
                '_id':0,
                'phone_2':0,
                'phone_3':0,
                'contact_requests':0
            }
        )

        q = query

        q = q.sort([('_id', -1)]).skip(int(page_num) * page_size).limit(page_size)

        try:
            while (yield q.fetch_next):
                contact = contacts.Contact(q.next_object())
                contact_list.append(clean_structure(contact))
        except Exception, e:
            logging.exception(e)
            raise gen.Return(e)

        finally:
            raise gen.Return(contact_list)

    @gen.coroutine
    def get_contact(self, account, contact_uuid):
        '''
            Get contact
        '''
        message = None
        logging.info('{0} get contact {1}'.format(account, contact_uuid))
        try:
            result = yield self.db.contacts.find_one(
                {'account':account,
                 'uuid': contact_uuid},
                {'_id':0, 'phone_2':0, 'phone_3':0, 'contact_requests':0} # remove this stuff from db.
            )

            logging.info('{0} this is the result'.format(str(result)))
            if result:
                contact = contacts.Contact(result)
                contact.validate()
                message = clean_structure(contact)
        except Exception, e:
            logging.exception(e)
            raise e
        finally:
            raise gen.Return(message)

    @gen.coroutine
    def new_contact(self, struct):
        '''
            New contact
        '''
        # if check dir fail remove directory uuid
        if not struct.get('has_directory', False):
            struct.pop('directory_uuid', None)
            
        try:
            contact = contacts.Contact(struct)
            contact.validate()
            contact = clean_structure(contact)
        except Exception, e:
            logging.error(e)
            raise e

        try:
            result = yield self.db.contacts.insert(contact)
            message = contact.get('uuid')
        except Exception, e:
            logging.error(e)
            message = str(e)

        raise gen.Return(message)

    @gen.coroutine
    def modify_contact(self, account, contact_uuid, struct):
        '''
            Modify contact
        '''
        try:
            contact = contacts.ModifyContact(struct)
            contact.validate()
            contact = clean_structure(contact)
        except Exception, e:
            logging.error(e)
            raise e

        try:
            result = yield self.db.contacts.update(
                {'account':account,
                 'uuid':contact_uuid},
                {'$set':contact}
            )
            logging.info(result)            
        except Exception, e:
            logging.error(e)
            message = str(e)

        raise gen.Return(bool(result.get('n')))

    @gen.coroutine
    def replace_contact(self, account, contact_uuid, struct):
        '''
            Replace contact
        '''
        try:
            contact = contacts.Contact(struct)
            contact.validate()
            contact = clean_structure(contact)
        except Exception, e:
            logging.error(e)
            raise e

        try:
            result = yield self.db.contacts.update(
                {'account':account,
                 'uuid':contact_uuid},
                {'$set':contact}
            )
            logging.info(result)            
        except Exception, e:
            logging.error(e)
            message = str(e)

        raise gen.Return(bool(result.get('n')))

    @gen.coroutine
    def remove_contact(self, account, contact_uuid):
        '''
            Remove contact
        '''
        message = None
        try:
            message = yield self.db.contacts.remove(
                {'account':account, 'uuid':contact_uuid}
            )
        except Exception, e:
            logging.error(e)
            message = str(e)

        raise gen.Return(bool(message.get('n')))