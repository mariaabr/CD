"""Message Broker"""
import enum
from typing import Dict, List, Any, Tuple
import socket
import selectors

from src.protocol import PubSubProto, PubSubProtoBadFormat

class Serializer(enum.Enum):
    """Possible message serializers."""

    JSON = 0
    XML = 1
    PICKLE = 2

class Broker:
    """Implementation of a PubSub Message Broker."""

    def __init__(self):
        """Initialize broker."""
        self.canceled = False
        self.host = "localhost"
        self.port = 5000

        self.brokersocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.brokersocket.bind((self.host, self.port)) # bind(ip, port)
        self.brokerselector = selectors.DefaultSelector()
        self.brokersocket.listen() # listen ->  s.listen(1) posso ter no maximo 1 ligacao

        self.topics = [] # [topic1, topic2, topic3, ...] -> stores existing topics
        self.lastmsg = {} # {topic1: lastMessage1, topic2: lastMessage2, ...} -> stores last message in each
        self.serialtypes = {} # {consumer1: serializationType1, consumer2: serializationType2, ...} -> stores each consumers searialization type
        self.subscriptions = {} # {topic1: [consumer1a, consumer1b, ...], topic2: [consumer2a, consumer 2b, ...], ...} -> stores all subscriptions
        
        self.brokerselector.register(self.brokersocket, selectors.EVENT_READ, self.accept)

    # copiado do primeiro projeto, alterar
    def accept(self, socket, mask):
        conn, addr = socket.accept()  # Should be ready

        self.brokerselector.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):

        # try:
        msg = PubSubProto.recv_msg(conn)  # -> receives message

        if msg:
            if msg.type == "subscribe":
                #if conn in self.serialtypes:
                #    serialcode = self.serialtypes.get(conn)   
                self.subscribe(msg.topic, conn, self.serialCode(conn))

            elif msg.type == "publish":
            
                self.put_topic(msg.topic, msg.message)

                if msg.topic in self.subscriptions:
                    #print("subscriptions: ", self.subscriptions)
                    for key in self.list_subscriptions(msg.topic):
                        #if key[0] in self.serialtypes:
                        #    serialcode = self.serialtypes.get(key[0])
                        PubSubProto.send_msg(key[0], self.serialCode(key[0]), msg)
                else:
                    self.subscriptions[msg.topic] = []

            elif msg.type == "requestlist":
                #if conn in self.serialtypes:
                #    serialcode = self.serialtypes.get(conn)
                PubSubProto.send_msg(conn, self.serialtypes, PubSubProto.request_lst(self.list_topics()))

            elif msg.type == "unsubscribe":
                self.unsubscribe(msg.topic, conn)

        else:
            # self.clientsDic.pop(conn)
            self.unsubscribe("", conn)
            self.brokerselector.unregister(conn)

        # except PubSubProtoBadFormat as exception:
        #     # self.clientsDic.pop(conn)
        #     self.unsubscribe("", conn)
        #     self.brokerselector.unregister(conn)
            # conn.close()

    def list_topics(self) -> List[str]:
        """Returns a list of strings containing all topics containing values."""
        
        lst_tpcs_msg = []

        for topic in self.lastmsg.keys():
            if self.lastmsg.get(topic) is not None:
                lst_tpcs_msg.append(topic)

        #print("list_tpcs_msg: ", lst_tpcs_msg)
        return lst_tpcs_msg

    def get_topic(self, topic):
        """Returns the currently stored value in topic."""

        for top in self.lastmsg.keys():
            if top == topic:
                return self.lastmsg.get(topic)
            
        return None # se a funcao nao der return no for

        # if topic in self.lastmsg:
        #     return self.lastmsg[topic]
        # else:
        #     return None

    def put_topic(self, topic, value):
        """Store in topic the value."""

        if topic not in self.topics:
            # self.topics[topic] = [value]
            self.topics.append(topic)
            self.subscriptions[topic]=[]
        
            for top in self.topics:
                if(topic.startswith(top)):
                    for sub in self.subscriptions[top]:
                        if sub not in self.subscriptions[topic]:
                            self.subscriptions[topic].append(sub)

        #print("value:", value)

        self.lastmsg[topic] = value
        # self.subscriptions[topic].append(value)
        #print("topics: ", self.topics)
        #print("latsmsg: ", self.lastmsg)
        #print("latsmsg value: ", self.lastmsg[topic])
        #print("subscriptions_msgvalue: ", self.subscriptions)

    def list_subscriptions(self, topic: str) -> List[Tuple[socket.socket, Serializer]]:
        """Provide list of subscribers to a given topic."""

        lst = []
        print("subscriptions: ", self.subscriptions, "\n")
        for conn in self.subscriptions[topic]:
            lst.append((conn, self.serialtypes[conn]))

        return lst
    
#         #print("chaves" , self.subscriptions.keys())
#         if topic in self.subscriptions.keys():
#             print("list_sub: ", self.subscriptions[topic])
#             return self.subscriptions[topic]
#         return

        # lst = []
        # for conn in self.subscriptions[topic]:
        #     lst.append((conn, self.serialtypes[conn]))
        
        # print("list_sub: ", lst)

        # return lst

        #lst_sub_tpcs = []
        #for top in self.subscriptions.keys():
        #    print(self.subscriptions)
        #    #print(topic)
        #    if top == topic:
        #        # return self.subscriptions.get(topic)
        #        #print(self.serialtypes)
        #        #print(topic)
        #        #print(self.serialtypes[topic])
        #        #print(lst_sub_tpcs)
        #        for conn in self.subscriptions[top]:
        #            lst_sub_tpcs.append((topic, self.serialtypes[conn]))
        #return lst_sub_tpcs

    def subscribe(self, topic: str, address: socket.socket, _format: Serializer = None):
        """Subscribe to topic by client in address."""
        
        serialcode = _format

        print("hello0")
        if address not in self.serialtypes:
            if serialcode == Serializer.JSON or serialcode == None or serialcode == 0:
                self.serialtypes[address] = Serializer.JSON
            elif serialcode == Serializer.XML or serialcode == 1:
                self.serialtypes[address] = Serializer.XML
            elif serialcode == Serializer.PICKLE or serialcode == 2:
                self.serialtypes[address] = Serializer.PICKLE

        if topic in self.topics: #devemos usar , naõ apagar mas quero testar sem
            print("hello1")
            if topic not in self.subscriptions:
                self.topics.append(topic)
                self.subscriptions[topic]=[]
                print("hello2")
     
                for top in self.topics:
                    if(topic.startswith(top)):
                        print("hello3")
                        for sub in self.subscriptions[top]:
                            if sub not in self.subscriptions[topic]:
                                print("hello4")
                                self.subscriptions[topic].append(sub)
                                
            if address not in self.subscriptions[topic]:
                self.subscriptions[topic].append(address)
                print("subscriptions2: ", self.subscriptions)

            if topic in self.lastmsg and self.lastmsg[topic] is not None:
                PubSubProto.send_msg(address, self.serialCode(address), PubSubProto.publish(topic, self.lastmsg[topic]))
            return
             
        else: # devemos usar , não apagar mas quero testar sem
           self.put_topic(topic, None)
           self.subscribe( topic , address, serialcode)
    
    def unsubscribe(self, topic, address):
        """Unsubscribe to topic by client in address."""
        
        # conn = address # nao percebi

        if topic != "":
            for top in self.topics:
                if(top.startswith(topic)):
                    self.subscriptions[top].remove(address)

        else:
            for top in self.topics:
                if (address in self.subscriptions.get(top)):
                    print("lis_subs: ", self.subscriptions, "\n")
                    self.subscriptions[top].remove(address)
                    
                # if(self.subscriptions.get(top).get(address)):
                # if(address in self.subscriptions.get(top)):

    def serialCode(self, conn):
        if conn in self.serialtypes:
            return self.serialtypes[conn]

        
    def run(self):
        """Run until canceled."""

        # self.brokersocket.bind((self.host, self.port)) # bind(ip, port)
        # self.brokersocket.listen(100) # listen ->  s.listen(1) posso ter no maximo 1 ligacao
        # self.brokerselector.register(self.brokersocket, selectors.EVENT_READ, self.accept)

        while not self.canceled:
            events = self.brokerselector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)







