"""Protocol for BlackJack game - Computação Distribuida Recurso"""

import json
from socket import socket

class Message:
    """Message Type."""

    def __init__(self, command):
        self.command = command

    def __toStr__(self):
        return self.__str__()

class PlayMessage(Message): # como lidamos com o facto de porder ser hit ou stand? --------------------------------------------------------------
    """Message represents a play"""

    def __init__(self, command, self_port):
        super().__init__(command)
        self.self_port = self_port

    def __str__(self):
        return f'{{"command": "{self.command}", "player": "{self.self_port}"}}'
    
class NextMessage(Message): # como lidamos com o facto de porder ser hit ou stand? --------------------------------------------------------------
    """Message represents a play"""

    def __init__(self, command, self_port, score = None):
        super().__init__(command)
        self.self_port = self_port
        self.score = score

    def __str__(self):
        if self.score is None:
            return f'{{"command": "{self.command}", "player": "{self.self_port}"}}'
        else:
            return f'{{"command": "{self.command}", "player": "{self.self_port}", "score": "{self.score}"}}'

class WinMessage(Message):
    """Message represents a win"""

    def __init__(self, command, self_port):
        super().__init__(command)
        self.self_port = self_port

    def __str__(self):
        return f'{{"command": "{self.command}", "player": "{self.self_port}"}}'

class DefeatMessage(Message):
    """Message represents a defeat"""

    def __init__(self, command, self_port):
        super().__init__(command)
        self.self_port = self_port

    def __str__(self):
        return f'{{"command": "{self.command}", "player": "{self.self_port}"}}'
    
class FairMessage(Message):
    """Message represents a play"""

    def __init__(self, command, self_port):
        super().__init__(command)
        self.self_port = self_port

    def __str__(self):
        return f'{{"command": "{self.command}", "player": "{self.self_port}"}}'
    
class UnfairMessage(Message):
    """Message represents a play"""

    def __init__(self, command, self_port):
        super().__init__(command)
        self.self_port = self_port

    def __str__(self):
        return f'{{"command": "{self.command}", "player": "{self.self_port}"}}'
    


# # usada no consenso e voting
# class PrepareMessage(Message):
#     """Message represents a prepare request."""

#     def __init__(self, proposal_number, self_port):
#         super().__init__("prepare")
#         self.proposal_number = proposal_number
#         self.self_port = self_port

#     def __str__(self):
#         return f'{{"command": "{self.command}", "proposal_number": {self.proposal_number}, "player": "{self.self_port}"}}'

# class PromiseMessage(Message):
#     """Message represents a promise response."""

#     def __init__(self, proposal_number, accepted_proposal, accepted_value, self_port):
#         super().__init__("promise")
#         self.proposal_number = proposal_number
#         self.accepted_proposal = accepted_proposal
#         self.accepted_value = accepted_value
#         self.self_port = self_port

#     def __str__(self):
#         return f'{{"command": "{self.command}", "proposal_number": {self.proposal_number}, "accepted_proposal": {self.accepted_proposal}, "accepted_value": "{self.accepted_value}", "player": "{self.self_port}"}}'

class BlackJackProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def play(cls, player: str) -> PlayMessage:
        """Creates a PlayMessage object."""

        return PlayMessage("play", player) # command = "play"
    
    @classmethod
    def next(cls, player: str, score: int = None) -> NextMessage:
        """Creates a PlayMessage object."""

        return NextMessage("NEXT", player, score) # command = "NEXT"

    @classmethod
    def win(cls, player: str) -> WinMessage:
        """Creates a WinMessage object."""
        
        return WinMessage("win", player) # command = "win"
    
    @classmethod
    def defeat(cls, player: str) -> DefeatMessage:
        """Creates a DefeatMessage object."""

        return DefeatMessage("defeat", player) # command = "defeat"
    

    @classmethod
    def fair(cls, player: str) -> FairMessage:
        """Creates a DefeatMessage object."""

        return FairMessage("fair", player) # command = "fair"
    
    @classmethod
    def unfair(cls, player: str) -> UnfairMessage:
        """Creates a DefeatMessage object."""

        return UnfairMessage("unfair", player) # command = "unfair"
    
    # @classmethod
    # def prepare(cls, proposal_number, player):
    #     """Creates a PrepareMessage object."""
    #     return PrepareMessage(proposal_number, player)

    # @classmethod
    # def promise(cls, proposal_number, accepted_proposal, accepted_value, player):
    #     """Creates a PromiseMessage object."""
    #     return Pro
    
    
    @classmethod
    def send_msg(cls, connection: socket, self_port: Message):
        """Sends through a connection a Message object."""
        
        msg_encode = str(self_port).encode("utf-8")
        length = len(str(msg_encode))
        if length >= 2**16:
            raise BlackJackProtoBadFormat()
        connection.sendall(length.to_bytes(2, byteorder = "big") + msg_encode)

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""

        try:
            size = connection.recv(2)
            msg_size = int.from_bytes(size, "big")
            self_port = connection.recv(msg_size)

            msg_decode = json.loads(self_port.decode("utf-8")) # convert str to a python object
            # erro no decode, porque?
            print(f"msg dec {msg_decode}")
            if msg_decode["command"] == "NEXT":
                if "score" in msg_decode:
                    return BlackJackProto.next(msg_decode["player"], msg_decode["score"])
                else:
                    return BlackJackProto.next(msg_decode["player"])
                
            elif msg_decode["command"] == "play":
                return BlackJackProto.play(msg_decode["player"])
            elif msg_decode["command"] == "win":
                return BlackJackProto.win(msg_decode["player"])
            elif msg_decode["command"] == "defeat":
                return BlackJackProto.defeat(msg_decode["player"])
            elif msg_decode["command"] == "fair":
                return BlackJackProto.fair(msg_decode["player"])
            elif msg_decode["command"] == "unfair":
                return BlackJackProto.unfair(msg_decode["player"])
            # elif msg_decode["command"] == "prepare":
            #     return BlackJackProto.prepare(msg_decode["proposal_number"], msg_decode["player"])
            # elif msg_decode["command"] == "promise":
            #     return BlackJackProto.promise( msg_decode["proposal_number"], msg_decode["accepted_proposal"], msg_decode["accepted_value"], msg_decode["player"])
        except:
            raise BlackJackProtoBadFormat()

class BlackJackProtoBadFormat(Exception):
    """Exception when source player is not BlackJackProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original player that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original player as a string."""
        return self._original.decode("utf-8")