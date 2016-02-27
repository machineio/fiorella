# -*- coding: utf-8 -*-
'''
    Fiorella outbound system logic.
'''

# This file is part of fiorella.

# Distributed under the terms of the last AGPL License.
# The full license is in the file LICENCE, distributed as part of this software.

__author__ = 'Jean Chassoul'


# TODO: clean CallFile class it's more old than stuff.
import zmq

from zmq.eventloop import ioloop, zmqstream

from fiorella.handlers import get_command
from fiorella.handlers import process_message

import time
import random
import os
import re
import tempfile

from tornado import gen


def server_push(port="5556"):
    '''
        PUSH process
    '''
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.bind("tcp://*:%s" % port)
    print "Running server on port: ", port
    # serves only 5 request and dies
    for reqnum in range(10):
        if reqnum < 6:
            socket.send("Continue")
        else:
            socket.send("Exit")
            break
        time.sleep (1)

def server_pub(port="5558"):
    '''
        PUB process
    '''
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)
    publisher_id = random.randrange(0,9999)
    print "Running server on port: ", port
    # serves only 5 request and dies
    for reqnum in range(10):
        # Wait for next request from client
        topic = random.randrange(8,10)
        messagedata = "server#%s" % publisher_id
        print "%s %s" % (topic, messagedata)
        socket.send("%d %s" % (topic, messagedata))
        time.sleep(1)

def client(port_push, port_sub):
    '''
        Client process
    '''
    context = zmq.Context()
    socket_pull = context.socket(zmq.PULL)
    socket_pull.connect ("tcp://localhost:%s" % port_push)
    stream_pull = zmqstream.ZMQStream(socket_pull)
    stream_pull.on_recv(get_command)
    print("Connected to server with port %s" % port_push)

    socket_sub = context.socket(zmq.SUB)
    socket_sub.connect ("tcp://localhost:%s" % port_sub)
    socket_sub.setsockopt(zmq.SUBSCRIBE, "9")
    stream_sub = zmqstream.ZMQStream(socket_sub)
    stream_sub.on_recv(process_message)
    print("Connected to publisher with port %s" % port_sub)

    ioloop.IOLoop.instance().start()
    print("Worker has stopped processing messages.")


# a scheduler class seems like to much overhead and could be generate confusion
# it seems to be more clean and practical to keep the old periodic module
# storing periodic callback functions there.

class Scheduler(object):
    '''
        System periodic callbacks

        class tornado.ioloop.PeriodicCallback(callback, callback_time)

        Schedules the given callback to be called periodically.

        The callback is called every callback_time milliseconds.
        If the callback runs for longer than callback_time milliseconds, 
        subsequent invocations will be skipped to get back on schedule.

        start must be called after the PeriodicCallback is created
    '''

    @gen.coroutine
    def periodic_outbound_callback(self):
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


class CallException(Exception):
    '''
        Call Exception
    '''
    pass


class CallError(CallException):
    '''
        Call Error
    '''
    pass


class CallFile(object):
    '''
        Asterisk Call File Generator.
    '''

    def __init__(self):
        self.params = {}
        self._file_options()

    def _file_options(self):
        fileargs = ('Account',
                    'Channel', 'Callerid', 'MaxRetries', 'RetryTime',
                    'WaitTime', 'Context', 'Extension', 'Priority',
                    'Setvar', 'Setvar', 'Setvar', 'Setvar', 'Setvar')

        for i in range(0, len(fileargs)):
            self.params[i] = fileargs[i]

    def input_args(self, path, args):
        if not re.search(r'^/(\w+\W?\w+)+/$', path):
            raise CallError('Invalid path: %s' % path)

        if len(args) != len(self.params):
            raise CallError('INPUT args %s NOT EQUAL file_options %s' % (len(args), len(self.params)))

    def generate_call(self, path, *args):
        self.input_args(path, args)

        (fd, path) = tempfile.mkstemp(suffix = '.call', dir = path)

        file = os.fdopen(fd, 'w')
        for i in range(0, len(args)):
            if i == 0:
                file.write(''.join((self.params[i], ': ', str(args[i]))))
            else:
                file.write(''.join(('\n', self.params[i], ': ', str(args[i]))))
        file.close()
        
        return path


def main():
    '''
        __init__ main function process
    '''
    testing = CallFile()
    x = testing.generate_call('/home/ooo/',
        'godzilla',
        'SIP/godzilla_18777786075/18883829578',
        '18777786075',
        '5',
        '300',
        '45',
        'DID_18777786075',
        '18777786075',
        '1',
        'keyword="sdsd|34"'
    )


if __name__=='__main__':
    main()
    