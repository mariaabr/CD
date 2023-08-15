"""Middleware to communicate with PubSub Message Broker."""
from collections.abc import Callable
from enum import Enum
from queue import LifoQueue, Empty
from typing import Any
import socket
import json
import pickle
import xml.etree.ElementTree as et
from src.protocol import PubSubProto


class MiddlewareType(Enum):
    """Middleware Type."""

    CONSUMER = 1
    PRODUCER = 2


class Queue:
    """Representation of Queue interface for both Consumers and Producers."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""

        self.topic = topic      #tipo channel do chat server
        self.type = _type       #tipo de client consumer ou producer
        self.serialcode = 0     #tipo de linguagem json, xml, pickle

        self.HOST = 'localhost' # remote host
        self.PORT = 5000        # same port as used by the server
        self.address = ((self.HOST, self.PORT))

        self.socketmdlware = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketmdlware.connect(self.address)

    def push(self, value):
        """Sends data to broker."""
        
        #print("pushhhhhhhhhhhhhhhhh")
        if self.type.value == 2:
            PubSubProto.send_msg(self.socketmdlware, self.serialcode, PubSubProto.publish(self.topic, value))

    def pull(self) -> tuple((str, Any)):
        """Receives (topic, data) from broker.

        Should BLOCK the consumer!"""

        # msg = PubSubProto.recv_msg(self.socketmdlware)
        # if msg is None or msg.message is None: return None
        # if msg.type == "TopicListReply":  
        #     return msg.lst
        # else:
        #     return (msg.topic, int(msg.message))

        #print("ola pu1111111111")
        
        #if self.type == MiddlewareType.CONSUMER:
#
        data = PubSubProto.recv_msg(self.socketmdlware)
        #print ("data", data)
        #print("hello middleware")

        if data is None or data.message is None:
            return None
        
        if data.type == "replylist":  
            return data.lst
        else:
            return (data.topic, int(data.message))

        # pp
        # if data:
        #     return data["topic"], data["message"]
        # else:
        #     return None

    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        
        PubSubProto.send_msg(self.socketmdlware, self.serialcode, PubSubProto.request_lst())

    def cancel(self):
        """Cancel subscription."""

        PubSubProto.send_msg(self.socketmdlware, self.serialcode, PubSubProto.cancel_sub(self.topic))


class JSONQueue(Queue):
    """Queue implementation with JSON based serialization."""

    def __init__(self, topic, _type = MiddlewareType.CONSUMER):
        super().__init__(topic, _type)
        self.serialcode = 0
        
        if _type.value == 1:
            PubSubProto.send_msg(self.socketmdlware, self.serialcode, PubSubProto.subscribe(topic))

       

class XMLQueue(Queue):
    """Queue implementation with XML based serialization."""

    def __init__(self, topic, _type = MiddlewareType.CONSUMER):
        super().__init__(topic, _type)
        self.serialcode = 1
        
        if _type.value == 1:
            PubSubProto.send_msg(self.socketmdlware, self.serialcode, PubSubProto.subscribe(topic))



class PickleQueue(Queue):
    """Queue implementation with Pickle based serialization."""

    def __init__(self, topic, _type = MiddlewareType.CONSUMER):
        super().__init__(topic, _type)
        self.serialcode = 2
        
        if _type.value == 1:
            PubSubProto.send_msg(self.socketmdlware, self.serialcode, PubSubProto.subscribe(topic))

