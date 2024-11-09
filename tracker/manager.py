# manager.py
import socket
import threading
import pickle

class Tracker:
    def __init__(self, port=5008):
        self.port = port
        self.active_peers = []
        self.peer_sockets = {}
        self.lock = threading.Lock()

        # Write tracker IP and port to tracker.txt at initialization
        self.write_tracker_info()

    def write_tracker_info(self):
        # Retrieve the tracker IP and write to tracker.txt
        ip = socket.gethostbyname(socket.gethostname())
        with open("tracker.txt", "w") as file:
            file.write(f"{ip} {self.port}")
        print(f"Tracker information written to tracker.txt: {ip}:{self.port}")

    def start(self):
        # Start the tracker to listen for incoming peer connections
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('', self.port))
        server_socket.listen(10)
        print(f"Tracker running on port {self.port}")

        while True:
            client_socket, client_address = server_socket.accept()
            threading.Thread(target=self.handle_peer, args=(client_socket, client_address)).start()

    def handle_peer(self, peer_socket, peer_address):
        # Register a peer and update active peer list
        peer_port = int(peer_socket.recv(1024).decode())
        peer_entry = (peer_address[0], peer_port)

        with self.lock:
            self.active_peers.append(peer_entry)
            self.peer_sockets[peer_entry] = peer_socket

        # Broadcast updated peer list to all connected peers
        self.broadcast_peer_list()

        # Listen for 'quit' message to handle peer disconnection
        while True:
            data = peer_socket.recv(1024).decode()
            if data == "quit":
                with self.lock:
                    self.active_peers.remove(peer_entry)
                    del self.peer_sockets[peer_entry]
                peer_socket.close()
                self.broadcast_peer_list()
                print(f"Peer {peer_entry} left the network")
                break

    def broadcast_peer_list(self):
        # Send the active peer list to all connected peers
        peer_data = pickle.dumps(self.active_peers)
        with self.lock:
            for peer, socket in self.peer_sockets.items():
                try:
                    socket.sendall(peer_data)
                except (BrokenPipeError, ConnectionResetError):
                    print(f"Failed to send peer list to {peer}.")

if __name__ == "__main__":
    tracker = Tracker()
    tracker.start()
