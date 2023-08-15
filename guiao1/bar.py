from src.client import Client

if __name__ == "__main__":
    c = Client("Bar")
    c.connect() # connect to server
    
    c.loop() # send messages