# -*- coding: utf-8 -*-
'''
    Fiorella HTTP contact handlers.
'''

# This file is part of fiorella.

# Distributed under the terms of the last AGPL License.
# The full license is in the file LICENCE, distributed as part of this software.

__author__ = 'Jean Chassoul'


import ujson as json
import motor

from tornado import gen
from tornado import web

import logging

# Fiorella system contacts
from fiorella.system import contacts

# errors, string to boolean, check JSON, new resource, content type validation.
from fiorella.tools import errors, str2bool, check_json, new_resource, content_type_validation

# system handler.
from fiorella.handlers import BaseHandler


#@content_type_validation
class Handler(contacts.Contacts, BaseHandler):
    '''
        Contacts HTTP request handlers
    '''

    @gen.coroutine
    def head(self, account=None, contact_uuid=None, page_num=0):
        '''
            Head contacts
        '''
        # logging request query arguments
        logging.info('request query arguments {0}'.format(self.request.arguments))

        # request query arguments
        query_args = self.request.arguments

        # get the current frontend logged username
        username = self.get_current_username()

        # if the user don't provide an account we use the frontend username as last resort
        account = (query_args.get('account', [username])[0] if not account else account)

        # query string checked from string to boolean
        checked = str2bool(str(query_args.get('checked', [False])[0]))

        if not contact_uuid:
            # get list of contacts
            contacts = yield self.get_contact_list(account, checked, page_num)
            self.set_status(200)
            self.finish({'contacts':contacts})
        else:
            # try to get stuff from cache first
            logging.info('Getting contacts:{0} from cache'.format(contact_uuid))

            data = self.cache.get('contacts:{0}'.format(contact_uuid))

            if data is not None:
                logging.info('contacts:{0} done retrieving!'.format(contact_uuid))
                result = data
            else:
                data = yield self.get_contact(account, contact_uuid)
                if self.cache.add('contacts:{0}'.format(contact_uuid), data, 60):
                    logging.info('new cache entry {0}'.format(str(data)))
                    result = data
            
            if not result:

                # -- need moar info

                self.set_status(400)
                self.finish({'missing':account})
            else:
                self.set_status(200)
                self.finish(result)

    @gen.coroutine
    def get(self, account=None, contact_uuid=None, page_num=0):
        '''
            Get contacts
        '''
        # logging request query arguments
        logging.info('request query arguments {0}'.format(self.request.arguments))

        # request query arguments
        query_args = self.request.arguments

        # get the current frontend logged username
        username = self.get_current_username()

        # if the user don't provide an account we use the frontend username as last resort
        account = (query_args.get('account', [username])[0] if not account else account)

        # query string checked from string to boolean
        checked = str2bool(str(query_args.get('checked', [False])[0]))

        if not contact_uuid:
            # get list of directories
            contacts = yield self.get_contact_list(account, checked, page_num)
            self.set_status(200)
            self.finish({'contacts':contacts})
        else:
            # try to get stuff from cache first
            logging.info('contact_uuid {0}'.format(contact_uuid.rstrip('/')))
            
            data = self.cache.get('contacts:{0}'.format(contact_uuid))

            if data is not None:
                logging.info('contacts:{0} done retrieving!'.format(contact_uuid))
                result = data
            else:
                data = yield self.get_contact(account, contact_uuid.rstrip('/'))
                if self.cache.add('contacts:{0}'.format(contact_uuid), data, 60):
                    logging.info('new cache entry {0}'.format(str(data)))
                    result = data

            if not result:

                # -- need moar info

                self.set_status(400)
                self.finish({'missing account {0} contact_uuid {1} page_num {2} checked {3}'.format(
                    account, contact_uuid.rstrip('/'), page_num, checked):result})
            else:
                self.set_status(200)
                self.finish(result)

    # @web.authenticated
    @gen.coroutine
    def post(self):
        '''
            Create contact
        '''
        # post structure
        #struct = yield check_json(self.request.body)

        struct = self.request.body

        logging.error(struct)

        # format_pass = (True if struct else False)
        # if not format_pass:
        #     self.set_status(400)
        #     self.finish({'JSON':format_pass})
        #     return

        # settings database
        db = self.settings.get('db')

        # logging new contact structure
        # logging.info('new contact structure {0}'.format(str(struct)))

        # logging request query arguments
        logging.info(self.request.arguments)

        # request query arguments
        query_args = self.request.arguments

        self.set_status(201)
        self.finish({'status':'acknowledge'})
        
        return

        # get account from new contact struct
        account = struct.get('account', None)

        # get the current frontend logged username
        username = self.get_current_username()

        # if the user don't provide an account we use the frontend username as last resort
        account = (query_args.get('account', [username])[0] if not account else account)

        # we use the front-end username as last resort
        # if not struct.get('account'):
        #     struct['account'] = account

        logging.warning(account)

        new_contact = yield self.new_contact(struct)

        if 'error' in new_contact:
            scheme = 'contact'
            reason = {'duplicates': [
                (scheme, 'account'),
                (scheme, 'phone_number')
            ]}
            message = yield self.let_it_crash(struct, scheme, new_contact, reason)

            logging.warning(message)
            self.set_status(400)
            self.finish(message)
            return

        if struct.get('has_directory'):

            resource = {
                'directory': struct.get('directory_uuid'),
                'resource': 'contacts',
                'uuid': new_contact
            }

            update = yield new_resource(db, resource, 'directories', 'directory')

            logging.info('update {0}'.format(update))

        self.set_status(201)
        self.finish({'uuid':new_contact})

    # @web.authenticated
    @gen.coroutine
    def patch(self, contact_uuid):
        '''
            Modify contact
        '''
        logging.info('request.arguments {0}'.format(self.request.arguments))
        logging.info('request.body {0}'.format(self.request.body))

        struct = yield check_json(self.request.body)

        logging.info('patch received struct {0}'.format(struct))

        format_pass = (True if not dict(struct).get('errors', False) else False)
        if not format_pass:
            self.set_status(400)
            self.finish({'JSON':format_pass})
            return

        account = self.request.arguments.get('account', [None])[0]

        if not account:
            # if not account we try to get the account from struct
            account = struct.get('account', None)

        logging.warning('account {0} uuid {1}'.format(account, contact_uuid))

        result = yield self.modify_contact(account, contact_uuid, struct)

        if not result:
            self.set_status(400)
            system_error = errors.Error('missing')
            error = system_error.missing('contact', contact_uuid)
            self.finish(error)
            return

        self.set_status(200)
        self.finish({'message': 'update completed successfully'})

    # @web.authenticated
    @gen.coroutine
    def put(self, contact_uuid):
        '''
            Replace contact
        '''
        logging.info('request.arguments {0}'.format(self.request.arguments))
        logging.info('request.body {0}'.format(self.request.body))

        struct = yield check_json(self.request.body)

        logging.info('put received struct {0}'.format(struct))

        format_pass = (True if not struct.get('errors') else False)
        if not format_pass:
            self.set_status(400)
            self.finish({'JSON':format_pass})
            return

        account = self.request.arguments.get('account', [None])[0]

        result = yield self.replace_contact(account, contact_uuid, struct)

        if not result:
            self.set_status(400)
            system_error = errors.Error('missing')
            error = system_error.missing('contact', contact_uuid)
            self.finish(error)
            return

        self.set_status(200)
        self.finish({'message': 'replace completed successfully'})

    # @web.authenticated
    @gen.coroutine
    def delete(self, contact_uuid):
        '''
            Delete contact
        '''
        logging.info(self.request.arguments)

        query_args = self.request.arguments

        account = query_args.get('account', [None])[0]

        logging.info('account {0} uuid {1}'.format(account, contact_uuid))

        result = yield self.remove_contact(account, contact_uuid)

        if not result:
            self.set_status(400)
            system_error = errors.Error('missing')
            error = system_error.missing('contact', contact_uuid)
            self.finish(error)
            return

        self.set_status(204)
        self.finish()

    @gen.coroutine
    def options(self, contact_uuid=None):
        '''
            Resource options
        '''
        self.set_header('Allow', 'HEAD, GET, POST, PATCH, PUT, DELETE, OPTIONS')
        self.set_status(200)

        message = {
            'Allow': ['HEAD', 'GET', 'POST', 'OPTIONS']
        
        }

        # return resource documentation examples?

        POST = {
            "POST": {
                "description": "Create contact",
                "parameters": {

                    "email": {
                        "type": "string",
                        "description": "Email",
                        "required": False
                    },

                    "phone_number": {
                        "type": "string",
                        "description": "Phone number",
                        "required": True
                    },

                    "first_name": {
                        "type": "string",
                        "description": "First name",
                        "required": True
                    },
                
                    "last_name": {
                        "type": "string",
                        "description": "Last name",
                    },
                    "country": {
                        "type": "string",
                        "description": "Country"
                    },
                    "city": {
                        "type": "string",
                        "description": "City"
                    },
                    "state": {
                        "type": "string",
                        "description": "State"
                    },
                    "zip_code": {
                        "type": "string",
                        "description": "Zip code"
                    },
                    #"labels": {
                    #    "type": "array/string",
                    #    "description": "Labels to associate with this issue."
                    #}
                },

                "example": {
                    "title": "Found a error, bug, inconsistency, your system is under attack.",
                    "body": "I'm having a problem with this.",
                    "assignee": "cebus",
                    "alert": 1,
                    "labels": [
                        "Label1",
                        "Label2"
                    ]
                }
            }
        }
        if not contact_uuid:
            message['POST'] = POST
        else:
            message['Allow'].remove('POST')
            message['Allow'].append('PUT')
            message['Allow'].append('PATCH')
            message['Allow'].append('DELETE')

        self.finish(message)