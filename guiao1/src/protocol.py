"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
import time
from datetime import datetime
from socket import socket


class Message:
    """Message Type."""

    def __init__(self, command):
        self.command = command

    def __toStr__(self):
        return self.__str__()
    
class JoinMessage(Message):
    """Message to join a chat channel."""

    def __init__(self, command, channel):
        super().__init__(command)
        self.channel = channel

    def __str__(self):
        return f'{{"command": "{self.command}", "channel": "{self.channel}"}}'

class RegisterMessage(Message):
    """Message to register username in the server."""

    def __init__(self, command, username):
        super().__init__(command)
        self.username = username

    def __str__(self):
        return f'{{"command": "{self.command}", "user": "{self.username}"}}'
     
class TextMessage(Message):
    """Message to chat with other clients."""

    def __init__(self, command, message, channel = None):
        super().__init__(command)
        self.message = message
        self.channel = channel

    def __str__(self):
        self.ts_value = round(time.time())
        if self.channel is None:
            return f'{{"command": "{self.command}", "message": "{self.message}", "ts": {self.ts_value}}}'
        else:
            return f'{{"command": "{self.command}", "message": "{self.message}", "channel": "{self.channel}", "ts": {self.ts_value}}}'

class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""

        return RegisterMessage("register", username) # command = "register"

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        
        return JoinMessage("join", channel) # command = "join"
    
    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""

        return TextMessage("message", message, channel) # command = "message"

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        
        msg_encode = str(msg).encode("utf-8")
        length = len(str(msg_encode))
        if length >= 2**16:
            raise CDProtoBadFormat()
        connection.sendall(length.to_bytes(2, byteorder = "big") + msg_encode)

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""

        try:
            size = connection.recv(2)
            msg_size = int.from_bytes(size, "big")
            msg = connection.recv(msg_size)

            msg_decode = json.loads(msg.decode("utf-8")) # convert str to a python object
            # erro no decode, porque?
            
            if msg_decode["command"] == "register":
                return CDProto.register(msg_decode["user"])
            elif msg_decode["command"] == "join":
                return CDProto.join(msg_decode["channel"])
            elif msg_decode["command"] == "message":
                if "channel" in msg_decode:
                    return CDProto.message(msg_decode["message"], msg_decode["channel"])
                else:
                    return CDProto.message(msg_decode["message"])
        except:
            raise CDProtoBadFormat()

class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")