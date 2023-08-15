"""CD Chat client program"""
import logging
import sys
import socket
import selectors
import fcntl
import os

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client: # mantem estado
    """Chat Client process."""


    def __init__(self, name: str = "Foo"): # construtor
        # call parent, super class -> super().parent_class
        """Initializes chat client."""

        self.HOST = 'localhost' # remote host
        self.PORT = 50003 # same port as used by the server
        self.name = name
        print(self.HOST)
        print(self.PORT)
        print(self.name)
        self.client_selector = selectors.DefaultSelector() # selector
        self.channel= None

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.HOST, self.PORT))
        self.s.setblocking(False)
        print("Welcome client {}!".format(self.name))
        regist = CDProto.register(self.name)
        CDProto.send_msg(self.s, regist)


    def msg_server(self, s, mask):
        """Read server's answers"""

        msg = CDProto.recv_msg(self.s)
        print("Received message >>> {}".format(msg.message))

    
    def msg_input(self, s, mask):
        """Read user's inputs"""

        # msg = sys.stdin.readline()
        msg= input()
        join_command = "/join"

        if msg.rstrip() == "exit":
            self.s.close()
            self.client_selector.close()
            sys.exit(0)

        elif join_command in msg:
            channel_name = msg.replace(join_command, "")
            self.channel = channel_name
            join_channel = CDProto.join(channel_name)
            print(join_channel)
            CDProto.send_msg(self.s, join_channel)

        else:
            msg2 = CDProto.message(msg, self.channel)
            CDProto.send_msg(self.s, msg2)


    def loop(self):
        """Loop indefinetely."""   
    
        # Set sys.stdin non-blocking
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

        self.client_selector.register(self.s, selectors.EVENT_READ, self.msg_server)
        self.client_selector.register(sys.stdin, selectors.EVENT_READ, self.msg_input)

        while True:
            sys.stdout.write("Waiting for message... \n")
            sys.stdout.write("\n")
            sys.stdout.write("-> ")
            sys.stdout.flush()

            events = self.client_selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj,mask)