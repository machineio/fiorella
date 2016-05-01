# -*- coding: utf-8 -*-

import os
import base64
import tornado.options

from tornado.options import parse_config_file

# ownership missing

secret = base64.b64encode("I've said before that I'm a remarkably unsentimental monkey.")
config_path = 'fiorella.conf'

def options():
    '''
        Fiorella monkey configuration options
    '''
    tornado.options.define('ensure_indexes', 
        default=True, type=bool,
        help=('Ensure collection indexes'))

    # Set config and stuff
    tornado.options.define('config', 
        type=str, help='path to config file',
        callback=lambda path: parse_config_file(path, final=False))

    # debugging
    tornado.options.define('debug',
        default=False, type=bool,
        help=('Turn on autoreload and log to stderr only'))

    # logging dir
    tornado.options.define('logdir',
        type=str, default='log',
        help=('Location of logging (if debug mode is off)'))

    tornado.options.define('domain',
        default='iofun.io', type=str,
        help='Application domain, e.g: "example.com"')

    # Server settings
    tornado.options.define('host', 
        default='127.0.0.1', type=str,
        help=('Server hostname'))

    tornado.options.define('port',
        default=8888, type=int,
        help=('Server port'))

    # Overlord node settings
    tornado.options.define('overlord_host', default='127.0.0.1', type=str,
                            help=('Overlord hostname or ip address'))

    tornado.options.define('overlord_port', default=8899, type=int,
                            help=('Overlord port'))

    # MongoDB database settings
    tornado.options.define('mongo_host',
        type=str, help=('MongoDB hostname or ip address'))

    tornado.options.define('mongo_port', 
        default=27017, type=int,
        help=('MongoDB port'))

    # PostgreSQL database settings
    tornado.options.define('sql_host',
        type=str, help=('PostgreSQL hostname or ip address'))

    tornado.options.define('sql_port',
        default=5432, type=int,
        help=('PostgreSQL port'))

    tornado.options.define('sql_database',
        type=str, help=('PostgreSQL database'))

    tornado.options.define('sql_user',
        type=str, help=('PostgreSQL username'))

    tornado.options.define('sql_password',
        type=str, help=('PostgreSQL username password'))

    tornado.options.define('memcached_host',
        default='127.0.0.1', type=str,
        help=('Memcached host'))

    tornado.options.define('memcached_port',
        default=11211, type=int,
        help=('Memcached port'))

    tornado.options.define('memcached_binary',
        default=True, type=bool,
        help=('Memcached binary'))

    tornado.options.define('memcached_tcp_nodelay',
        default=True, type=bool,
        help=('Memcached tcp_nodelay'))

    tornado.options.define('memcached_ketama',
        default=True, type=bool,
        help=('Memcached ketama'))

    tornado.options.define('cache_enabled',
        default=False, type=bool,
        help=('Enable cache'))
    
    # ZMQ external PUB logger
    tornado.options.define('external_log',
        default=False, type=bool,
        help=('External logger'))

    tornado.options.define('base_url',
        default='api', type=str,
        help=('Base url, e.g. "api"'))

    tornado.options.define('page_size',
        default=20, type=int,
        help=('Set a custom page size up to 100'))

    tornado.options.define('cookie_secret',
        default=secret, type=str,
        help=('Secure cookie secret string'))

    # this need to change to mailgun_key and mailgun_api

    tornado.options.define('api_key',
        default='key-348c3d4a39568cd19c1c7e41ff6944d4',
        type=str,
        help=('Secure key mailgun'))

    tornado.options.define('api_url',
        default="https://api.mailgun.net/v3/codemachine.io/messages",
        type=str,
        help=('Mail API URL'))

    tornado.options.define('max_retries',
        default=2, type=int,
        help=('Max retries'))
    
    tornado.options.define('retry_time',
        default=300, type=int,
        help=('Outbound calling retry time'))

    tornado.options.define('wait_time',
        default=45, type=int,
        help=('Wait time'))

    tornado.options.define('max_calls',
        default=10, type=int,
        help=('Maximum number of concurrent calls'))

    tornado.options.define('asterisk_user',
        default='asterisk', type=str,
        help=('non-root Asterisk user'))

    tornado.options.define('asterisk_group',
        default='asterisk', type=str,
        help=('non-root Asterisk group'))

    tornado.options.define('spool_dir',
        default='/var/spool/asterisk/outgoing/', type=str,
        help=('Asterisk spool dir'))

    tornado.options.define('tmp_dir',
        default='/tmp/', type=str,
        help=('tmp outbound call files'))

    tornado.options.define('server_delay', default=2.0)

    tornado.options.define('client_delay', default=1.0)

    tornado.options.define('num_chunks', default=40)

    # Parse config file, then command line...
    # so command line switches take precedence
    if os.path.exists(config_path):
        print('Loading', config_path)
        tornado.options.parse_config_file(config_path)
    else:
        print('No config file at', config_path)

    tornado.options.parse_command_line()
    result = tornado.options.options

    for required in (
        'domain', 'host', 'port', 'base_url',
    ):
        if not result[required]:
            raise Exception('%s required' % required)

    return result