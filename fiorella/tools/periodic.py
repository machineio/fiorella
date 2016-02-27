# -*- coding: utf-8 -*-
'''
    Fiorella periodic tools.
'''

# This file is part of fiorella.

# Distributed under the terms of the last AGPL License. 
# The full license is in the file LICENCE, distributed as part of this software.

__author__ = 'Jean Chassoul'


import motor

import ujson as json

import glob
import uuid

import logging

from contextlib import contextmanager
from tornado import gen

from tornado import httpclient

import requests 

from bson import objectid


httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')

http_client = httpclient.AsyncHTTPClient()


@gen.coroutine
def get_usernames(db):
    '''        
        Get all the username accounts
    '''
    usernames = []
    try:
        query = db.accounts.find({},{'account':1, '_id':0})
        while (yield query.fetch_next):
            account = query.next_object()
            usernames.append(account)
    except Exception, e:
        logging.error(e)
        message = str(e)

    raise gen.Return(usernames)

@gen.coroutine
def get_unassigned_cdr(db):
    '''
        Periodic task that returns the unassigned CDR.
    '''
    result = []
    try:
        query = db.calls.find({
            'assigned':{'$exists':False}
        }).limit(1000)
        
        for c in (yield query.to_list()):
            result.append(c)
            
    except Exception, e:
        logging.exception(e)
        raise gen.Return(e)
    
    raise ren.Return(result)

@gen.coroutine
def process_outbound_calls():
    '''
        Periodic task that process outbound calls.
    '''
    current = glob.glob('/var/spoo/l/asterisk/outgoing*.call')

@gen.coroutine
def process_assigned_false(db):
    '''
        Periodic task that process assigned flag on calls resource.
    '''

    result = []

    def _got_call(message, error):
        '''
            got call
        '''
        if message:
            channel = (message['channel'] if 'channel' in message else False)

            if channel:
                account = [a for a in _account_list 
                           if ''.join(('/', a['account'], '-')) in channel]

                account = (account[0] if account else False)

                if account:
                    struct = {
                        'account':account['account'],
                        'resource':'calls',
                        'id':message['_id']
                    }
                    result.append(struct)
        elif error:
            logging.error(error)
            return error
        else:
            #logging.info('got call result: %s', result)
            return result
    try:
        _account_list = yield get_usernames(db)

        db.calls.find({
            'assigned':False
        }).limit(1000).each(_got_call)
    except Exception, e:
        logging.exception(e)
        raise gen.Return(e)

@gen.coroutine
def process_assigned_records(db):
    '''
        Periodic task that process unassigned records.
    '''
    result = []

    def _got_record(message, error):
        '''
            got record
        '''
        if error:
            logging.error(error)
            return error

        elif message:
            channel = (True if 'channel' in message else False)
            # get channel the value
            channel = (message['channel'] if channel else channel)

            if channel:
                account = [a for a in _account_list
                           if ''.join(('/', a['account'], '-')) in channel]
                account = (account[0] if account else False)

                if account:
                    struct = {
                        'account':account['account'],
                        'resource':'calls',
                        'id':message['_id']
                    }
                    result.append(struct)    
        else:
            #logging.info('got record result: %s', result)
            return result

    try:
        _account_list = yield get_usernames(db)

        db.calls.find({
            'assigned':{'$exists':False}
        }).limit(1000).each(_got_record)
    except Exception, e:
        logging.exception(e)
        raise gen.Return(e)

@gen.coroutine
def assign_record(db, account, callid):
    '''
        Update record assigned flag
    '''
    try:
        result = yield db.calls.update(
            {'_id':objectid.ObjectId(callid)}, 
            {'$set': {'assigned': True,
                      'accountcode':account}}
        )

    except Exception, e:
        logging.exception(e)
        raise e

        return

    raise gen.Return(result)


@gen.coroutine
def periodic_outbound_callback():
    '''
        periodic outbound callback function
    '''
    results = yield [
        periodic.process_assigned_false(db),
        periodic.process_outbound_call(db)
    ]

    if all(x is None for x in results):
        result = None
    else:
        result = list(itertools.chain.from_iterable(results))

        for record in result:

            flag = yield periodic.assign_call(
                db,
                record.get('account'),
                record.get('uuid')
            )

            resource = yield new_resource(db, record)
    if result:
        logging.info('periodic records {0}'.format(result))