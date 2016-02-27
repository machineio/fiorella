# -*- coding: utf-8 -*-
'''
    Fiorella lead API
'''

# This file is part of fiorella.

# Distributed under the terms of the last AGPL License.
# The full license is in the file LICENCE, distributed as part of this software.

__author__ = 'Jean Chassoul'


import zmq

import logging

import motor

import uuid

import pylibmc as mc

from tornado import ioloop

# system periodic cast callback
from tornado.ioloop import PeriodicCallback as PeriodicCast
from tornado import gen
from tornado import web

from tornado.web import RequestHandler


from fiorella.handlers import contacts



from fiorella.system import server_push, server_pub, client

from fiorella.tools import options
from fiorella.tools import indexes

from fiorella.tools import periodic

from fiorella.tools import new_resource, zmq_external_logger

from multiprocessing import Process

from zmq.eventloop import ioloop


# ioloop
ioloop.install()

# db global variable
db = False

# cache glogbal variable
cache = False

# global logger
logger = False


def main():
    '''
        Fiorella main function
    '''
    # Fiorella daemon options
    opts = options.options()

    # Set document database
    document = motor.MotorClient(opts.mongo_host, opts.mongo_port).howler
    
    # Set memcached backend
    memcache = mc.Client(
        [opts.memcached_host],
        binary=opts.memcached_binary,
        behaviors={
            "tcp_nodelay": opts.memcached_tcp_nodelay,
            "ketama": opts.memcached_ketama
        }
    )

    # Set default database
    global db
    db = document
    
    # Set default cache
    global cache
    cache = memcache

    # logging system spawned
    logging.info('Fiorella system {0} spawned'.format(uuid.uuid4()))

    # logging database hosts
    logging.info('MongoDB server: {0}:{1}'.format(opts.mongo_host, opts.mongo_port))

    if opts.ensure_indexes:
        logging.info('Ensuring indexes...')
        indexes.ensure_indexes(db)
        logging.info('DONE.')

    cache_enabled = opts.cache_enabled
    if cache_enabled:
        logging.info('Memcached server: {0}:{1}'.format(opts.memcached_host, opts.memcached_port))

    external_log = opts.external_log
    if external_log:
        global logger
        logger = zmq_external_logger()

    base_url = opts.base_url

    application = web.Application(

        [   

            (r'/leads/?', contacts.Handler),

        ],

        db = db,
        cache = cache,
        debug = opts.debug,
        domain = opts.domain,
        page_size = opts.page_size,
        cookie_secret = opts.cookie_secret, # cookie settings
        max_retries = opts.max_retries,
        retry_time = opts.retry_time,
        wait_time = opts.wait_time,
        max_calls = opts.max_calls,
        asterisk_user = opts.asterisk_user,
        asterisk_group = opts.asterisk_group,
        spool_dir = opts.spool_dir,
        tmp_dir = opts.tmp_dir
    )

    # Setting up server process
    application.listen(opts.port)
    logging.info('Listening on http://{0}:{1}'.format(opts.host, opts.port))
    ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    '''
        Fiorella outbound campaign system
    '''
    main()