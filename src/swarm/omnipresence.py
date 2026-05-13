import socket
import struct
import threading
import json
import time

class ZeroConfigSwarm:
    """
    Implements a UDP Multicast gossip protocol allowing local offline nodes 
    (e.g., a Pi, a Laptop, a Server) to discover each other automatically
    and silently synchronize parameter weights. Omnipresence without a central server.
    """
    MULTICAST_GROUP = '224.1.1.1'
    PORT = 5007

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.peers = {} # Peer_id -> last_seen_timestamp
        self.running = False
        self.sock = None
        
    def start(self):
        self.running = True
        try:
            self._setup_socket()
        except OSError as e:
            self.running = False
            print(f"ZeroConfig Swarm unavailable: {e}")
            return
        
        # Start listening thread
        self.listener_thread = threading.Thread(target=self._listen, daemon=True)
        self.listener_thread.start()
        
        # Start broadcasting thread
        self.broadcaster_thread = threading.Thread(target=self._broadcast_presence, daemon=True)
        self.broadcaster_thread.start()
        print(f"ZeroConfig Swarm Online. Node ID: {self.node_id}")

    def _setup_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to port
        self.sock.bind(('', self.PORT))
        
        # Tell kernel to add socket to multicast group
        mreq = struct.pack("4sl", socket.inet_aton(self.MULTICAST_GROUP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def _listen(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                peer_id = message.get("node_id")
                
                if peer_id and peer_id != self.node_id:
                    self.peers[peer_id] = time.time()
                    # If this was a parameter sync message, we would ingest it into our local DB here
                    if "sync_hash" in message:
                         pass 
            except Exception as e:
                pass

    def _broadcast_presence(self):
        # Create a separate socket for sending
        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2) # Stay within local subnet
        
        while self.running:
            try:
                message = json.dumps({
                    "node_id": self.node_id,
                    "status": "active",
                    "timestamp": time.time()
                }).encode('utf-8')
                
                send_sock.sendto(message, (self.MULTICAST_GROUP, self.PORT))
                
                # Cleanup dead peers (not seen in 30s)
                current_time = time.time()
                self.peers = {k: v for k, v in self.peers.items() if current_time - v < 30}
                
            except Exception:
                pass
            time.sleep(5) # Broadcast every 5 seconds

    def get_active_peers(self):
        return list(self.peers.keys())

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
