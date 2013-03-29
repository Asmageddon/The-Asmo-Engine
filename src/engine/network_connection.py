import threading
import socket, select
import time

class NetworkConnection(threading.Thread):
    def __init__(self, port, host = False):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port

        self.data_in = []
        self.data_out = []

        if self.host:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(("0.0.0.0", self.port))
            #Allow reusing the socket immediately (on Linux at least)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket = None
        else:
            self.server_socket = None
            self.socket = None

        self.running = True

    def connect(self, host_ip):
        if self.host: return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.connect((host_ip, self.port))

        print "Connected to server"

    def run(self):
        self.running = True

        if self.host:
            self.server_socket.listen(5)
            while self.socket is None and self.running:
                try:
                    client, address = self.server_socket.accept()
                    self.socket = client
                    print "Client connected"
                except:
                    print "Client not connected, connection shut down"


        prev_data = ""

        while self.running:
            if self.socket is None:
                time.sleep(0.25) #Don't waste CPU cycles
                continue

            #Accept incoming data and push it onto the queue
            data = self.socket.recv(4096)
            if not data:
                self.socket.close()
                self.running = False
                continue

            #Handle stuff that got broken into multiple parts
            # a.k.a. sending the map via one .send()
            if not data.endswith("\n"):
                prev_data += data
                continue
            elif prev_data != "":
                data = prev_data + data
                prev_data = ""

            if "\n" in data[:-1]:
                data = data.split("\n")
            else:
                data = [data]

            for d in data:
                if d:
                    self.data_in.append(d)

        print "Shutting down networking thread"

    def connected(self):
        return self.socket is not None

    def close(self):
        self.running = False

        if self.server_socket is not None:
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.server_socket.close()
            self.server_socket = None
            print "Closed server socket"

        if self.socket is not None:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                pass #Might be closed by the other endpoint already
            self.socket.close()
            self.socket = None
            print "Closed client socket"


    def receive(self):
        """Usage: for data in connection.receive(): blah blah"""
        while len(self.data_in) > 0:
            data = self.data_in[0]
            self.data_in = self.data_in[1:]
            yield data

    def send(self, data):
        try:
            self.socket.send(data + "\n")
        except:
            self.close()
