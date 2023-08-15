# coding: utf-8

import socket
import selectors
import signal
import logging
import argparse
import time

# configure logger output format
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Load Balancer')


# used to stop the infinity loop
done = False

sel = selectors.DefaultSelector()

policy = None
mapper = None


# implements a graceful shutdown
def graceful_shutdown(signalNumber, frame):  
    logger.debug('Graceful Shutdown...')
    global done
    done = True


# n to 1 policy
class N2One:
    def __init__(self, servers):
        self.servers = servers  

    def select_server(self):
        return self.servers[0]

    def update(self, *arg):
        pass


# round robin policy
class RoundRobin:
    def __init__(self, servers):
        self.servers = servers
        self.nextindex = -1

    def select_server(self):
        self.nextindex = self.nextindex + 1
        if(self.nextindex == len(self.servers)):
            self.nextindex = 0
        return self.servers[self.nextindex]
    
    def update(self, *arg):
        pass


# least connections policy
class LeastConnections:
    def __init__(self, servers):
        self.servers = servers
        self.dict_connections = {}
        for server in servers:
            self.dict_connections[server] = 0


    def select_server(self):
        self.less_connections = min(self.dict_connections.items(), key = lambda t: t[1])[1]
        print("Connections", self.less_connections)

        for server, value in self.dict_connections.items():
            # print("server", server)
            # print("value", value)

            if value == self.less_connections:
                # data = self.dict_connections[server]
                # print("data", data)
                self.dict_connections[server] += 1
                return server
        return None

    def update(self, *arg): # como assim?!, update a que?
        print("update", *arg)
        print("arg0", arg[0])
        server = arg[0]
        print("server", server)

        self.dict_connections[server] -= 1 #funcionou do nada, nao percebi
        print(">>", self.dict_connections)


# least response time
class LeastResponseTime:
    def __init__(self, servers):
        self.servers = servers
        self.starttime = time.time()
        self.dict_connections = {}
        self.dict_leasttime = {}
        for server in servers:
            self.dict_connections[server] = 0
            self.dict_leasttime[server] = ([self.starttime], 0)

    def select_server(self):

        """dict times"""
        self.less_time = min(self.dict_leasttime.values(), key=lambda t: t[1])[1]
        list_server = []
        for server, value in self.dict_leasttime.items():
            if value[1] == self.less_time:
                list_server.append(server)

        if len(list_server) == 1:
            data = self.dict_leasttime[server]
            self.dict_leasttime[server] = (data[0], data[1])
            return list_server[0]
    
        """dict connections"""
        self.less_connections = min(self.dict_connections.values())
        print("Connections", self.less_connections)

        for server, value in self.dict_connections.items():
            # print("server", server)
            # print("value", value)

            if value == self.less_connections:
                # data = self.dict_connections[server]
                # print("data", data)
                self.dict_connections[server] += 1
                return server
            
        return None

    def update(self, *arg): # nao entendo o que é suposto fazer no update 
        server = arg[0]
        data = self.dict_leasttime[server]
        print("data", data)
        times = data[0]
        print("times here", times)
        print("time time", time.time())
        print("times -1", times[-1])
        times.append(time.time() - times[-1])
                
        if(data[1] == 0):
            times.remove(self.starttime)

        avg = sum(times)/len(times)
        self.dict_leasttime[server] = (times, avg)


POLICIES = {
    "N2One": N2One,
    "RoundRobin": RoundRobin,
    "LeastConnections": LeastConnections,
    "LeastResponseTime": LeastResponseTime
}

class SocketMapper:
    def __init__(self, policy):
        self.policy = policy
        self.map = {}

    def add(self, client_sock, upstream_server):
        client_sock.setblocking(False)
        sel.register(client_sock, selectors.EVENT_READ, read)
        upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream_sock.connect(upstream_server)
        upstream_sock.setblocking(False)
        sel.register(upstream_sock, selectors.EVENT_READ, read)
        logger.debug("Proxying to %s %s", *upstream_server)
        self.map[client_sock] =  upstream_sock

    def delete(self, sock):
        paired_sock = self.get_sock(sock)
        sel.unregister(sock)
        sock.close()
        sel.unregister(paired_sock)
        paired_sock.close()
        if sock in self.map:
            self.map.pop(sock)
        else:
            self.map.pop(paired_sock)

    def get_sock(self, sock):
        for client, upstream in self.map.items():
            if upstream == sock:
                return client
            if client == sock:
                return upstream
        return None
    
    def get_upstream_sock(self, sock):
        return self.map.get(sock)

    def get_all_socks(self):
        """ Flatten all sockets into a list"""
        return list(sum(self.map.items(), ())) 

def accept(sock, mask):
    client, addr = sock.accept()
    logger.debug("Accepted connection %s %s", *addr)
    mapper.add(client, policy.select_server())

def read(conn,mask):
    data = conn.recv(4096)
    if len(data) == 0: # No messages in socket, we can close down the socket
        mapper.delete(conn)
    else:
        mapper.get_sock(conn).send(data)


def main(addr, servers, policy_class):
    global policy
    global mapper

    # register handler for interruption 
    # it stops the infinite loop gracefully
    signal.signal(signal.SIGINT, graceful_shutdown)

    policy = policy_class(servers)
    mapper = SocketMapper(policy)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(addr)
    sock.listen()
    sock.setblocking(False)

    sel.register(sock, selectors.EVENT_READ, accept)

    try:
        logger.debug("Listening on %s %s", *addr)
        while not done:
            events = sel.select(timeout=1)
            for key, mask in events:
                if(key.fileobj.fileno()>0):
                    callback = key.data
                    callback(key.fileobj, mask)
                
    except Exception as err:
        logger.error(err)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pi HTTP server')
    parser.add_argument('-a', dest='policy', choices=POLICIES)
    parser.add_argument('-p', dest='port', type=int, help='load balancer port', default=8080)
    parser.add_argument('-s', dest='servers', nargs='+', type=int, help='list of servers ports')
    args = parser.parse_args()
    
    servers = [('localhost', p) for p in args.servers]
    
    main(('127.0.0.1', args.port), servers, POLICIES[args.policy])
