import socket
import time
import numpy as np
import json

class Sender:
    def __init__(self, port: int, lambda_rate: float):
        """
        Initialize Sender
        :param port: sender's binding port
        :param lambda_rate: Poisson process's λ (packets per second)
        """
        self.port = port
        self.lambda_rate = lambda_rate
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', port))
        self.peer_address = None
        self.sequence_number = 0
        self.sent_packets = []  # record sent time & seq number

    def handshake(self, peer_address):
        """
        Handshake with Receiver to determine destination address
        :param peer_address: receiver's address (IP, Port)
        """
        self.peer_address = peer_address
        handshake_msg = json.dumps({'handshake': True}).encode()
        self.sock.sendto(handshake_msg, self.peer_address)
        print(f"[Sender] Handshake sent to {self.peer_address}")

    def run(self, duration: int):
        """
        Continuously send packets that match the Poisson distribution
        :param duration: duration of the experiment in seconds
        """
        start_time = time.time()
        while time.time() - start_time < duration:
            # Generate the next sending interval according to 
            # the Poisson distribution
            inter_arrival_time = np.random.exponential(1 / self.lambda_rate)
            time.sleep(inter_arrival_time)

            # generate packet
            packet = {
                'sequence_number': self.sequence_number,
                'timestamp': time.time()
            }
            
            # send packet
            self.sock.sendto(packet, self.peer_address)
            self.sent_packets.append(packet)
            self.sequence_number += 1
            print(f"[Sender] Packet sent to {self.peer_address} at {time.time()}")