"""Protocol PubSub - Computação Distribuida Assignment 3."""
import json
import pickle
import time
from datetime import datetime
from socket import socket
import enum
import xml.etree.ElementTree as et

class Serializer(enum.Enum):
    """Possible message serializers."""
    JSON = 0
    XML = 1
    PICKLE = 2

class Message:
    """Message Type."""

    def __init__(self, type):
        self.type = type

class SubMessage(Message):
    """Message Subscribe"""

    def __init__(self, topic):
        super().__init__("subscribe")
        self.topic = topic

    def __repr__(self):
        return f'{{"typemsg": "{self.type}", "topic": "{self.topic}"}}'
    
    def strXml(self):
        return "<?xml version=\"1.0\"?><data typemsg=\"{}\" topic=\"{}\"></data>".format(self.type, self.topic)
    
    def strPickle(self):
        return  {"typemsg": self.type, "topic": self.topic}

class PubMessage(Message):
    """Message Publish"""

    def __init__(self,topic, message):
        super().__init__("publish")
        self.topic = topic
        self.message = message

    def __repr__(self):
        return f'{{"typemsg": "{self.type}", "topic": "{self.topic}", "message": "{self.message}"}}'
    
    def strXml(self):
        return "<?xml version=\"1.0\"?><data typemsg=\"{}\" topic=\"{}\" message=\"{}\"></data>".format(self.type, self.topic, self.message)
    
    def strPickle(self):
        return  {"typemsg": self.type, "topic": self.topic, "message": self.message}

class ListReqMessage(Message):
    """Message Request Listing"""

    def __init__(self):
        super().__init__("requestlist")

    def __repr__(self):
        return f'{{"typemsg": "{self.type}"}}'
    
    def strXml(self):
        return "<?xml version=\"1.0\"?><data typemsg=\"{}\"></data>".format(self.type)
    
    def strPickle(self):
        return  {"typemsg": self.type}

class ListRepMessage(Message):
    """Message Request Listing"""

    def __init__(self, lst):
        super().__init__("replylist")
        self.lst = lst

    def __repr__(self):
        return f'{{"typemsg": "{self.type}", "lst": "{self.lst}"}}'

    def strXML(self):
        return "<?xml version=\"1.0\"?><data typemsg=\"{}\" lst=\"{}\"></data>".format(self.type, self.lst)

    def strPickle(self):
        return {"typemsg": self.type, "lst": self.lst}
    

class unSubMessage(Message):
    """Message to cancel Subscribe"""

    def __init__(self, topic):
        super().__init__("unsubscribe")
        self.topic = topic

    def __repr__(self):
        return f'{{"typemsg": "{self.type}", "topic": "{self.topic}"}}'
    
    def strXml(self):
        return "<?xml version=\"1.0\"?><data typemsg=\"{}\" topic=\"{}\"></data>".format(self.type, self.topic)
    
    def strPickle(self):
        return  {"typemsg": self.type, "topic": self.topic}


class PubSubProto:
    """PubSub Protocol."""

    @classmethod
    def subscribe(self, topic) -> SubMessage:
        return SubMessage(topic)
    
    @classmethod
    def request_lst(self, lst = None) -> ListReqMessage:
        if lst:
            return ListRepMessage(lst)
        return ListReqMessage(lst)

    @classmethod
    def publish(self, topic, message) -> PubMessage:
        return PubMessage(topic, message)

    @classmethod
    def cancel_sub(self, topic) -> unSubMessage:
        return unSubMessage(topic)

    @classmethod
    def send_msg(self, connection: socket, serialcode, msg: Message):
        """Send a message"""

        if serialcode == None: serialcode = 0
        if type(serialcode) == str: serialcode = int(serialcode)
        if isinstance(serialcode, enum.Enum): serialcode = serialcode.value

        connection.send(serialcode.to_bytes(1, byteorder = "big"))

        if serialcode == Serializer.JSON or serialcode == 0:

            msgjson = json.loads(msg.__repr__())
            msg_jsonencode = (json.dumps(msgjson)).encode('utf-8')
            # print("encode json:", msg_jsonencode)
            length = len(msg_jsonencode)
            # if length >= 2**16:
            #     raise PubSubProtoBadFormat()
            connection.send(length.to_bytes(2, 'big'))
            # print("msg_jsonencode before send(): ", msg_jsonencode, "\n")
            connection.send(msg_jsonencode)
            # print("cucu: ", conn2) 
            # connection.sendall(length.to_bytes(2, byteorder = "big") + msg_jsonencode)

        elif serialcode == Serializer.XML or serialcode == 1:

            msg_xmlencode = (msg.strXml()).encode('utf-8') # o que passa?
            print("encode xml:", msg_xmlencode)
            length = len(msg_xmlencode)
            # if length >= 2**16:
            #     raise PubSubProtoBadFormat()
            connection.send(length.to_bytes(2, 'big'))
            connection.send(msg_xmlencode) 
            # connection.sendall(length.to_bytes(2, byteorder = "big") + msg_xmlencode)

        elif serialcode == Serializer.PICKLE or serialcode == 2:

            msg_pickleencode = pickle.dumps(msg.strPickle()) # o que passa?
            print("encode pickle:", msg_pickleencode)
            length = len(msg_pickleencode)
            # if length >= 2**16:
            #     raise PubSubProtoBadFormat()
            connection.send(length.to_bytes(2, 'big'))
            connection.send(msg_pickleencode)
            # connection.sendall(length.to_bytes(2, byteorder = "big") + msg_pickleencode)

    @classmethod
    def recv_msg(self, connection: socket) -> Message:
        """Receive a message"""

        #print("estou aqui")
        sizeserialcode = connection.recv(1)
        serialcode = int.from_bytes(sizeserialcode, 'big')
        
        size = connection.recv(2)
        if size is None: return None
        msg_size = int.from_bytes(size, 'big')
        if msg_size == 0: return None
        # recv_msg = connection.recv(msg_size)
        
        try:

            if serialcode == None or serialcode == Serializer.JSON or serialcode == 0:
                recv_msg = connection.recv(msg_size)
                recv_msg = recv_msg.decode('utf-8')
                if recv_msg == "": return None
                #print("recv_msg before json.loads(): ", recv_msg, "\n")
                msg_decode = json.loads(recv_msg)
                #print("decode json:", msg_decode)

            elif serialcode == Serializer.XML or serialcode == 1:
                print("cheguei ao xmlllllllll")
                recv_msg = connection.recv(msg_size)
                msg_decode = recv_msg.decode('utf-8')  
                if recv_msg == "": return None        
                msg_decode = {}                                        # decode content into message
                root = et.fromstring(recv_msg) 
                for element in root.keys():
                    msg_decode[element] = root.get(element)

                print("decode xml:", msg_decode)
            
            elif serialcode == Serializer.PICKLE or serialcode == 2:
                recv_msg = connection.recv(msg_size)
                if recv_msg == "": return None
                msg_decode = pickle.loads(recv_msg)
                # print("decode pickle:", msg_decode)
            
        except json.JSONDecodeError as err:
            print("errrrouuuuuuu")
            raise PubSubProtoBadFormat(recv_msg)
        
        if isinstance(msg_decode, dict):
            if msg_decode["typemsg"] == "subscribe":
                return self.subscribe(msg_decode["topic"])
            elif msg_decode["typemsg"] == "publish":
                return self.publish(msg_decode["topic"], msg_decode["message"])
            elif msg_decode["typemsg"] == "requestlist":
                return self.request_lst()
            elif msg_decode["typemsg"] == "replylist":
                return self.request_lst(msg_decode["lst"])
            elif msg_decode["typemsg"] == "unsubscribe":
                return self.subscribe(msg_decode["topic"])
            else:
                return None

class PubSubProtoBadFormat(Exception):
    """Exception when source message is not PubSubProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_topic(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")