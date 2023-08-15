from src.server import Server

if __name__ == "__main__":
    s = Server() # cria o server

    s.loop() # acepts and receive mesages
