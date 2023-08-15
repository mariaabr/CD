"""CD Chat server program."""
import logging
import socket
import selectors

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename="server.log", level=logging.DEBUG)

class Server:
    """Chat Server process."""
    
    print("server class")

    def __init__(self):

        self.HOST = 'localhost' # remote host
        self.PORT = 50003 # same port as used by the server
        self.server_socket = socket.socket()
        print("here server init")
        self.server_selector = selectors.DefaultSelector()

        self.clientsDic = {} # dicionario de clients como chave
        

    # functions site selectors python documentation
    def accept(self, sock, mask):
        conn, addr = sock.accept()  # Should be ready
        print('accepted connection with',conn, 'from', addr)
        self.clientsDic[conn] = "home"
        conn.setblocking(False)

        print(self.clientsDic)
        self.server_selector.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):

        try:
            msg = CDProto.recv_msg(conn)  # -> receives client message
            print(msg)

            print('echoing', repr(msg), 'to', conn)

            if msg:
                if msg.command == "join":
                    self.clientsDic[conn] = msg.channel
                    print(self.clientsDic)

                elif msg.command == "message":
                    channel = self.clientsDic[conn]
                    for key in self.clientsDic:
                        if self.clientsDic[key] == channel: # search channel clients
                            if key != conn:
                                CDProto.send_msg(key, msg)

            else:
                self.clientsDic.pop(conn)
                print('closing', conn)
                self.server_selector.unregister(conn)
                # conn.close()

        except CDProtoBadFormat as exception:
            self.clientsDic.pop(conn)
            self.server_selector.unregister(conn)
            print("Error receiving data... \n")

    def loop(self): # self e uma referencia a propria classe
        """Loop indefinetely."""

        self.server_socket.bind((self.HOST, self.PORT)) # bind(ip, port)
        self.server_socket.listen(100) # listen ->  s.listen(1) posso ter no maximo 1 ligacao
        print("waiting for a client connection...")
        self.server_selector.register(self.server_socket, selectors.EVENT_READ, self.accept)

        while True:
            events = self.server_selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)