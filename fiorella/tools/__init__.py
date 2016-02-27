# -*- coding: utf-8 -*-
'''
    Fiorella system tools.
'''

# This file is part of fiorella.

# Distributed under the terms of the last AGPL License. 
# The full license is in the file LICENCE, distributed as part of this software.

__author__ = 'Jean Chassoul'


import os, os.path

#import arrow
import ujson as json

import logging

import motor

from tornado import gen
from fiorella import errors

import zmq

from zmq.log.handlers import PUBHandler


@gen.coroutine
def check_json(struct):
    '''
        Check for malformed JSON
    '''
    try:
        struct = json.loads(struct)
    except Exception, e:
        api_error = errors.Error(e)
        error = api_error.json()

        logging.exception(e)
        raise gen.Return(error)

        return

    raise gen.Return(struct)

def clean_structure(struct):
    '''
        clean structure
    '''
    struct = struct.to_primitive()

    struct = {
        key: struct[key] 
            for key in struct
                if struct[key] is not None
    }

    return struct

def clean_results(results):
    '''
        clean results
    '''
    results = results.to_primitive()

    # results.get('results')
    results = results['results']

    results = [
        {
            key: dic[key]
                for key in dic
                    if dic[key] is not None 
        } for dic in results 
    ]

    return {'results': results}

def content_type_validation(handler_class):
    '''
        Content type validation

        @content_type_validation decorator
    '''

    def wrap_execute(handler_execute):
        '''
            Content-Type checker

            Wrapper execute function
        '''
        def ctype_checker(handler, kwargs):
            '''
                Content-Type checker implementation
            '''
            content_type = handler.request.headers.get("Content-Type", "")
            if content_type is None or not content_type.startswith('application/json'):
                handler.set_status(415)
                handler._transforms = []
                handler.finish({
                    'status': 415,
                    'reason': 'Unsupported Media Type',
                    'message': 'Must ACCEPT application/json: '\
                    '[\"%s\"]' % content_type 
                })
                return False
            return True

        def _execute(self, transforms, *args, **kwargs):
            '''
                Execute the wrapped function
            '''
            if not ctype_checker(self, kwargs):
                return False
            return handler_execute(self, transforms, *args, **kwargs)

        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class

@gen.coroutine
def new_resource(db, struct, collection=None, scheme=None):
    '''
        New resource
    '''
    import uuid as _uuid
    from schematics import models as _models
    from schematics import types as _types


    class HowlerResource(_models.Model):
        '''
            Fiorella resource
        '''
        uuid = _types.UUIDType(default=_uuid.uuid4)
        campaign = _types.UUIDType(required=False)
        directory = _types.UUIDType(required=False)
        resource  = _types.StringType(required=True)


    # Calling getattr(x, "foo") is just another way to write x.foo
    collection = getattr(db, collection)    
    
    try:
        message = HowlerResource(struct)
        message.validate()
        message = message.to_primitive()
    except Exception, e:
        logging.exception(e)
        raise e
        return

    resource = 'resources.{0}'.format(message.get('resource'))

    try:
        message = yield collection.update(
            {
                'uuid': message.get(scheme)
            },
            {
                '$addToSet': {
                    '{0}.contains'.format(resource): message.get('uuid')
                },
                '$inc': {
                    'resources.total': 1,
                    '{0}.total'.format(resource): 1
                }
            }
        )
    except Exception, e:
        logging.exception(e)
        raise e
        return

    raise gen.Return(message)

def time_in_range(start, end, x):
    '''
        Return true if x is in the range [start, end]
    '''
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

def spool_calls(spool):
    '''
        Return number of current call files
    '''
    return len([
        name for name in os.listdir(spool) 
        if os.path.isfile(''.join((spool, name)))
    ])

def str2bool(boo):
    '''
        String to boolean
    '''
    return boo.lower() in ('yes', 'true', 't', '1')

def zmq_external_logger(host='localhost', port='8899'):
    '''
        This publish logging messages over a zmq.PUB socket
    '''
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect('tcp://{0}:{1}'.format(host, port))
    handler = PUBHandler(socket)
    logger = logging.getLogger()
    logger.addHandler(handler)
    handler.root_topic = 'logging'
    return logger
