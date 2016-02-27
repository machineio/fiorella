# -*- coding: utf-8 -*-
'''
    Fiorella HTTP base handlers.
'''

# This file is part of fiorella.

# Distributed under the terms of the last AGPL License.
# The full license is in the file LICENCE, distributed as part of this software.

__author__ = 'Jean Chassoul'

import os
import uuid
import base64
import logging

from tornado import gen
from tornado import web

from zmq.eventloop import ioloop

from fiorella import errors

from fiorella.tools import check_json


def get_command(msg):
    print("Received control command: %s" % msg)
    if msg[0] == "Exit":
        print("Received exit command, client will stop receiving messages")
        should_continue = False
        ioloop.IOLoop.instance().stop()

def process_message(msg):
    print("Processing ... %s" % msg)


class BaseHandler(web.RequestHandler):
    '''
        System application request handler

        gente d'armi e ganti
    '''

    def initialize(self, **kwargs):
        '''
            Initialize the Base Handler
        '''
        super(BaseHandler, self).initialize(**kwargs)

        # System database
        self.db = self.settings.get('db')

        # System cache
        self.cache = self.settings.get('cache')

        # Page settings
        self.page_size = self.settings.get('page_size')

        # Call file settings
        self.max_retries = self.settings.get('max_retries') 
        self.retry_time = self.settings.get('retry_time')
        self.wait_time = self.settings.get('wait_time')

        # outbound settings
        self.max_calls = self.settings.get('max_calls')
        self.spool_dir = self.settings.get('spool_dir')
        self.tmp_dir = self.settings.get('tmp_dir')

    def set_default_headers(self):
        '''
            Fiorella default headers
        '''
        self.set_header("Access-Control-Allow-Origin", self.settings.get('domain', 'iofun.io'))

    def get_current_username(self):
        '''
            Return the username from a secure cookie
        '''
        return self.get_secure_cookie('username')

    @gen.coroutine
    def let_it_crash(self, struct, scheme, error, reason):
        '''
            Let it crash.
        '''

        str_error = str(error)
        error_handler = errors.Error(error)
        messages = []

        if error and 'Model' in str_error:
            message = error_handler.model(scheme)

        elif error and 'duplicate' in str_error:
            
            for name, value in reason.get('duplicates'):

                if value in str_error:

                    message = error_handler.duplicate(
                        name.title(),
                        value,
                        struct.get(value)
                    )

                    messages.append(message)
            
            message = ({'messages':messages} if messages else False)

        elif error and 'value' in str_error:
            message = error_handler.value()

        elif error is not None:
            logging.warning(str_error)
            
            message = {
                'error': u'nonsense',
                'message': u'there is no error'
            }

        else:
            quotes = PeopleQuotes()
            
            message = {
                'status': 200,
                'message': quotes.get()
            }

        raise gen.Return(message)