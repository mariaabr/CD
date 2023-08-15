import argparse
import json
import socket
import selectors
import time
import redis
import hashlib
import itertools
from utils import score
from collections import Counter

from protocol import BlackJackProto, BlackJackProtoBadFormat

r = redis.Redis(host='localhost', port=6379, db=0)
serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

socks = dict()
conns = dict()
playing = dict()
ports = []
copy_ports =[]
two_players = []

""" tentativa de fazer consenso por paxos implementação simples , mas não funcional """
class PaxosNode:
    def init(self, node_id, all_nodes):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.proposed_value = None
        self.accepted_value = None
        self.accepted_count = 0
        
    def get_highest_proposal_number(self):
        return self.proposed_value[0] if self.proposed_value else -1
    
    def prepare(self, proposal_number):
        max_proposal_number = proposal_number
        for node in self.all_nodes:
            if node != self:
                max_proposal_number = max(max_proposal_number, node.get_highest_proposal_number())
        return max_proposal_number

    def accept(self, proposal_number, value):
        if proposal_number >= self.get_highest_proposal_number():
            self.proposed_value = (proposal_number, value)
            return True
        return False

    def learn(self):
        proposal_numbers = [node.get_highest_proposal_number() for node in self.all_nodes]
        counter = Counter(proposal_numbers)
        highest_proposal_number,  = counter.most_common(1)[0]
        for node in self.all_nodes:
            if node.get_highest_proposal_number() == highest_proposal_number:
                self.accepted_count += 1
                self.accepted_value = node.proposed_value[1]

    def run_paxos(self, proposal_number, value):
        if self.accept(proposal_number, value):
            for node in self.all_nodes:
                if node != self:
                    node.accept(proposal_number, value)
            self.learn()

#verificar se o deck e o redis tem as coisas certas
def check_fair_result(sock, player, ports, hash):
    print("sou o sock" , sock)
    print("estou jogando:" , player)
    cartas = []
    merged_list = []

    lists = []
    for port in ports :
        elements = json.loads(r.get(port))
        elements = [element for element in elements]
        lists.append(elements)
    # print("LISTS", lists)
    
    
    max_length = max(len(lst) for lst in lists)
    # print("MAXLENGTH", max_length)
    

    array1= lists[0]
    array2=lists[1]

    
    for permutation in itertools.permutations(array1 + array2):
        combination = []
        index1 = 0
        index2 = 0

        # Adiciona os elementos alternadamente, um de cada vez
        for element in permutation:
            if index1 < len(array1) and element == array1[index1]:
                combination.append(array1[index1])
                index1 += 1
            elif index2 < len(array2) and element == array2[index2]:
                combination.append(array2[index2])
                index2 += 1
        new_hash = hashlib.md5(f'{combination}'.encode('utf-8')).hexdigest()

        if new_hash == hash:
            merged_list = combination
            break

    # print("cartas: ", cartas)
    # print("merged_list: ", merged_list)
    new_hash = hashlib.md5(f'{merged_list}'.encode('utf-8')).hexdigest()
    # print("new_hash:", new_hash)

    if new_hash == hash:
        # print("faiiiiiiiiiiiiiir\n")
        batota = BlackJackProto.fair(player)
        print(f"batota {batota}")
        BlackJackProto.send_msg(sock, batota)
        return "fair"
    else:
        # print("UUUUUUUUUUUUNNNNNNNfaiiiiiiiiiiiiiir\n")
        batota = BlackJackProto.unfair(player)
        print(f"batota {batota}")
        BlackJackProto.send_msg(sock, batota)
        return "unfair"

def send_all(action):
    """Sends a message for all players in the game"""
    
    for i in socks:
        sock = socks[i]
        BlackJackProto.send_msg(sock, action)

def get_card(): 
    """ vai buscar uma carta ao deck """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 5000))
    sock.sendall("GC".encode('utf-8'))
    card = sock.recv(4).decode('utf-8').strip()
    sock.close()
    return card

def get_hashCards():
    """ vai buscar hash das cartas ao deck """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 5000))
    sock.sendall("HC".encode('utf-8'))
    cards = sock.recv(36).decode('utf-8').strip()
    sock.close()
    return cards

def update_redis(port, cards):
    """ adicionar as carats ao redis """
    card_string = json.dumps(cards)   
    r.set(port, card_string)
    return

def playalone():
    """ para um jogador jogar sozinho """
    host = 'localhost' # remote host
    player_selector = selectors.DefaultSelector() # selector
    cards = []
    self_port = serversock.getsockname()[1]

    while len(cards) < 2:
        cards.append(get_card())
        update_redis(self_port, cards)
        time.sleep(5)
    # print(cards)
    print("Score:", score(cards))
    
    # chamar a função interact
    key = interact_with_user1(cards)

    while key != "S":
        if key == "H": # perguntar ao stor >> depois de tirar uma carta pode se anunciar W ou D ou só se anuncia na jogada a seguir >> se poder ser na mesma jogada como é que tratamos disso
        # enviar mensagem aos outros jogadores >> tem de esperar pelo jogador anterior
        
            cards.append(get_card())
            update_redis(self_port, cards)
     
            # win e defeat aqui
            if score(cards) > 21:
                print("PERDEU")
                key2 = interact_with_user1(cards)

                while key2 != "D":
                    print("O jogador deve avisar que perdeu(D)")
                    key2 = interact_with_user1(cards)
                return

            elif score(cards) == 21:                    
                print("GANHOU")

                key2 = interact_with_user1(cards)
                
                while key2 != "W":
                    print("O jogador deve avisar que ganhou(W)")
                    key2 = interact_with_user1(cards)
                return
            
        elif key == "W":
            if score(cards) == 21:                    
                print("GANHOU")
                print("Score: " , score(cards))

                key2 = interact_with_user1(cards)
                
                while key2 != "W":
                    print("O jogador deve avisar que ganhou(W)")
                    key2 = interact_with_user1(cards)
                return
            
        elif key == "S":
            if score(cards) > 21:
                print("PERDEU")
                print("Score: " , score(cards))
                
                key2 = interact_with_user1(cards)

                while key2 != "D":
                    print("O jogador deve avisar que perdeu(D)")
                    key2 = interact_with_user1(cards)
                return
        
        print("Score: " , score(cards))
        key = interact_with_user1(cards)

def play(self_port):
    """ jogar com vários jogadores"""
    host = 'localhost' # remote host
    player_selector = selectors.DefaultSelector() # selector
    # print(f"self_port mmmmm {self_port}")
    cards = []
    # self_port = serversock.getsockname()[1]
    next_port = 0
    previousport = 0
    copy_ports.sort()
    # print(f"ports {ports}")
    # print(f"copy_ports {copy_ports}")

    for i in range(len(copy_ports)):
        if copy_ports[i] == self_port:
            next_port = copy_ports[(i+1)%len(copy_ports)]
            previousport = copy_ports[(i-1)%len(copy_ports)]
            # print(f"ola colega {next_port}")
            break

    conn = conns[previousport]    
    sock = socks[next_port]
    # print(f"socket {socks} hereeeeeeeeeeeeeeeeeeee")
    # print(f"socket next_port {socks[next_port]} hereeeeeeeeeeeeeeeeeeee olaaaaaaaaaaaaaaaaaaaaaaaaa")
    # sock.sendall("ola amigo".encode('utf-8'))

    if self_port == min(ports):
        # im first
        card = get_card()
        cards.append(card)
        update_redis(self_port, cards)


        player = BlackJackProto.next(self_port)
        BlackJackProto.send_msg(sock, player)
    
    print(f"{self_port} -> {cards}")
    print(f"next port {next_port}")
    print(f"previous port {previousport}")
    print(f"sock {sock}")
    print(f"conn {conn}")


    while True:
        # print("waiting 111111")
        data = BlackJackProto.recv_msg(conn)
        print(f">{data}<")
        if data.command == "NEXT":
            card = get_card()
            cards.append(card)
            update_redis(self_port, cards)
                

            player = BlackJackProto.next(self_port)
            BlackJackProto.send_msg(sock, player)
            
        elif data.command == "play":
            player = BlackJackProto.next(self_port)
            send_all(player)

        else:
            print(f"unexpected data {data}")
            break
            conn.close()

        if len(cards) == 2:
            break
    
    print(f"{self_port} -> {cards}")

    # otherwise wait for my turn and repeat
    while True:
        # print("waiting 2222222222\n")
        # data = conn.recv(1024).decode('utf-8')
        data = BlackJackProto.recv_msg(conn) 
        
        print(f">{data}<")
        if data.command == "NEXT":
            print("Score: " , score(cards))
            
            if(data.score):
                if score(cards) > int(data.score):
                    winner = BlackJackProto.win(self_port)
                    send_all(winner)
                    # BlackJackProto.send_msg(sock, winner)
                    return
                elif score(cards) < int(data.score):
                    loser = BlackJackProto.defeat(self_port)
                    send_all(loser)
                    # BlackJackProto.send_msg(sock, loser)
                    return
                else:
                    print("Quer continuar a jogar para desempatar?(Y/N)")
                    input = input().upper()
                    if input == "N":
                        print("O jogo acabou empatado!")
                        return
                    elif input == "Y":
                        pass

            key = interact_with_user1(cards)

            if key == "H": # perguntar ao stor >> depois de tirar uma carta pode se anunciar W ou D ou só se anuncia na jogada a seguir >> se poder ser na mesma jogada como é que tratamos disso
            # enviar mensagem aos outros jogadores >> tem de esperar pelo jogador anterior
            
                cards.append(get_card())
                update_redis(self_port, cards)
                # sock.sendall("NEXT".encode('utf-8'))

                #tentativa para o win e o deafeat de informar colegas
                    
                # win e defeat aqui
                if score(cards) > 21:
                    print("PERDEU")
                    print("Score: " , score(cards))

                    # enviar mensagem aos outros jogadores
                    # command = "defeat"
                    key2 = interact_with_user1(cards)

                    while key2 != "D":
                        print("O jogador deve avisar que perdeu(D)")
                        key2 = interact_with_user1(cards)

                    loser = BlackJackProto.defeat(self_port)
                    send_all(loser)
                    # BlackJackProto.send_msg(sock, loser)

                    print(f"self_port {self_port}")
                    
                    if len(ports) > 2 :
                        copy_ports.remove(self_port) # remover a porta do jogador que perdeu para deixar os outros jogar
                        play(sock)
                    return

                elif score(cards) == 21:
                    print("GANHOU")
                    print("Score: " , score(cards))

                    # enviar mensagem aos outros jogadores
                    # command = "win"
                    key2 = interact_with_user1(cards)
                    
                    while key2 != "W":
                        print("O jogador deve avisar que ganhou(W)")
                        key2 = interact_with_user1(cards)

                    winner = BlackJackProto.win(self_port)
                    send_all(winner)
                    # BlackJackProto.send_msg(sock, winner)

                    return

                # sock.sendall("NEXT".encode('utf-8'))
                # for s in socks:
                #     value = socks[s]
                #     player = BlackJackProto.play(self_port)
                #     BlackJackProto.send_msg(value, player)

                #     info = BlackJackProto.recv_msg(conn)

                player = BlackJackProto.next(self_port)
                # send_all(player)
                BlackJackProto.send_msg(sock, player)

            elif key == "S":
                
                player = BlackJackProto.next(self_port)
                # send_all(player)
                BlackJackProto.send_msg(sock, player)

            elif key == "W":
                scores = score(cards)
                player = BlackJackProto.next(self_port, scores)
                # send_all(player)
                BlackJackProto.send_msg(sock, player)
                # partnerScore = BlackJackProto.recv_msg(conn)
                
                if(data.score):
                    partnerScore = data.score
                    # print(f"Partner score: {partnerScore}")

                    if score(cards) > int(partnerScore):
                        winner = BlackJackProto.win(self_port)
                        send_all(player)
                        # BlackJackProto.send_msg(sock, winner)
                        return
                    
                    elif score(cards) < int(partnerScore):
                        loser = BlackJackProto.defeat(self_port)
                        send_all(player)
                        # BlackJackProto.send_msg(sock, loser)
                        return
                        
                    else:
                        player = BlackJackProto.next(self_port)
                        # send_all(player)
                        BlackJackProto.send_msg(sock, player)


            elif key == "D":
                scores = score(cards)
                player = BlackJackProto.next(self_port, scores)
                # send_all(player)
                BlackJackProto.send_msg(sock, player)
                # partnerScore = BlackJackProto.recv_msg(conn)
                
                if(data.score):
                    partnerScore = data.score
                    # print(f"Partner score: {partnerScore}")

                    if score(cards) > int(partnerScore):
                        winner = BlackJackProto.win(self_port)
                        send_all(player)
                        # BlackJackProto.send_msg(sock, winner)
                        return
                    
                    elif score(cards) < int(partnerScore):
                        loser = BlackJackProto.defeat(self_port)
                        
                        # BlackJackProto.send_msg(sock, loser)
                        return
                    
                    else:
                        player = BlackJackProto.next(self_port)
                        # send_all(player)
                        BlackJackProto.send_msg(sock, player)         
    
            else:
                if score(cards) == 21:
                        print("GANHOU")
                        print("Score: " , score(cards))
    
                        # enviar mensagem aos outros jogadores
                        # command = "win"
                        key2 = interact_with_user1(cards)
                        
                        while key2 != "W":
                            print("O jogador deve avisar que ganhou(W)")
                            key2 = interact_with_user1(cards)
    
                        winner = BlackJackProto.win(self_port)
                        send_all(winner)
                        # BlackJackProto.send_msg(sock, winner)
                        return
                
                elif score(cards) > 21:
                        print("PERDEU")
                        print("Score: " , score(cards))
    
                        # enviar mensagem aos outros jogadores
                        # command = "defeat"
                        key2 = interact_with_user1(cards)
    
                        while key2 != "D":
                            print("O jogador deve avisar que perdeu(D)")
                            key2 = interact_with_user1(cards)
    
                        loser = BlackJackProto.defeat(self_port)
                        send_all(loser)
                        # BlackJackProto.send_msg(sock, loser)

                key = interact_with_user1(cards)
            
            # sock.sendall("NEXT".encode('utf-8'))
        
        elif data.command == "play":
            print(f"eu sei que estás a jogar player {player}")
            player = BlackJackProto.next(self_port)
            BlackJackProto.send_msg(sock, player)

        elif data.command == "win":
            print("I lost the game!!")
            return

        elif data.command == "defeat":
            if len(copy_ports) <= 2:
                print("I won the game!!")
                return
            else:
                print(f"self port: {self_port}")
                print(f"player {player}")
            return
            
        else:
            print(f"unexpected data {data}")
            break
            conn.close()

        print(f"Current cards: {cards}")
        print("Score: " , score(cards))
        # key = interact_with_user1(cards)


def main(self_port, players_ports):
    serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversock.bind(('localhost', self_port))
    serversock.listen(4)
    input("Everyone ready?")

    if players_ports != None:
        while len(conns) < len(players_ports):
            print(players_ports[len(conns)])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # estava dentro do ciclo while
            sock.connect(('localhost', players_ports[len(conns)])) # por cada ciclo while ele cria uma conn? diferente
            socks[players_ports[len(conns)]] = sock
            print(f"socksssssssssss: {players_ports[len(conns)]} :", socks )
            conn, addr = serversock.accept()
            print(f"port {self_port}, addr {addr} hereeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
            ports.append(players_ports[len(conns)])
            conns[players_ports[len(conns)]] = conn
            print(f"connnnns :", conns )

    ports.append(self_port)

    if len(ports) == 1:
        playalone()
    else:
        # chosen_ports = choose_ports()
        # print("Chosen ports:", chosen_ports)
        self_port = serversock.getsockname()[1]
        print(f'self_port: {self_port}')
        for p in ports:
            copy_ports.append(p) # copy ports seria para fazer a copia de tas as ports inicialmente conectadas para poder
                                 # remover os jogadores que perderam entretanto e os outros continuarem a jogar
        play(self_port)
        print(f"serversock {serversock}")
        print(f"socks {socks}")
        print(f"conns {conns}")

        # end game
        # seleção de 2 jogadores
        # verificação de vencedor

        if len(ports) > 2 :
            input("Let's vote?")

            # #criar nós no paxos
            # Player1 = PaxosNode("Player1",[])
            # Player2 = PaxosNode("Player2",[])
            # Player3 = PaxosNode("Player3",[])

            # #adicionar os jogadores
            # Player1.all_nodes = [Player1, Player2, Player3]
            # Player2.all_nodes = [Player1, Player2, Player3]
            # Player3.all_nodes = [Player1, Player2, Player3]

            # ##correr para determinado valor
            # Player1.run_paxos(1, "Value 1")
            # Player2.run_paxos(2, "Value 2")
            # Player3.run_paxos(2, "Value 3")

            #player1 = voting()
            #two_players.append(player1)
            #player2 = voting()
            #two_players.append(player2)

            two_players.append(ports[0])
            two_players.append(ports[1])

        else:        
            for p in ports:
                two_players.append(p)

        if self_port in two_players:
            # print(check_fair_result(two_players))
            hash = get_hashCards() 
            print("Hash das cartas ->" , hash)  #### TEM UTILIDADE SEM O BATOTEIRO? socks.get(self_port)

            for s in socks:
                if s in two_players:
                    sendSock = s

            print(socks)
            # print("######### Sou o sock passado ao check:: ", socks.get(self_port))
            result = check_fair_result(socks[sendSock], self_port, ports, hash)
            print(result)
            print(sock)
            response = BlackJackProto.recv_msg(conns[sendSock])
            print(response)  
            
            if result == response.command and result == "fair":
                print("O jogo foi justo, não houve batota")
            elif result == response.command and result == "unfair":
                print("Houve batota")
            else:
                print("Houve batota")
                

    print("END OF THE GAME\n")
    print(self_port, players_ports)

def interact_with_user1(cards):
    """ All interaction with user must be done through this method.
    YOU CANNOT CHANGE THIS METHOD. """

    print(f"Current cards: {cards}")
    print("(H)it")
    print("(S)tand")
    print("(W)in")  # Claim victory
    print("(D)efeat") # Fold in defeat
    key = " "
    while key not in "HSWD":
        key = input("> ").upper()
    return key.upper() 

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--self', required=True, type=int)
    parser.add_argument('-p', '--players', nargs='+', required=False, type=int)
    args = parser.parse_args()
        
    if args.players != None:
        if args.self in args.players:
            print(f"{args.self} must not be part of the list of players")
            exit(1) 

    main(args.self, args.players)