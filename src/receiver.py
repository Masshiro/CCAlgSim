import socket
import select
import json
import time

class Receiver:
    def __init__(self, port: int):
        """
        Initialize Receiver
        :param port: Receiver's binding port
        """
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', port))
        self.peer_address = None  # sender's IP addr will be recorded during handshake
        self.received_packets = []
        self.out_of_order_count = 0

    def perform_handshake(self):
        """
        Waiting for the handshake with sender so that its IP can be determiend
        """
        print("[Receiver] Waiting for handshake...")
        while self.peer_address is None:
            msg, addr = self.sock.recvfrom(1600)
            decoded_msg = json.loads(msg.decode())
            if decoded_msg.get('handshake'):
                self.peer_address = addr
                print(f"[Receiver] Handshake received from {self.peer_address}")

    def run(self, duration: int=60):
        """
        Starting to receive packets
        :param duration: overall simulation time length(secons)
        """
        start_time = time.time()
        last_sequence = -1
        while time.time() - start_time < duration:
            readable, _, _ = select.select([self.sock], [], [], 1)
            if readable:
                msg, addr = self.sock.recvfrom(1600)
                packet = json.loads(msg.decode())
                self.received_packets.append(packet)

                # 判断是否按顺序接收
                if packet['sequence_number'] < last_sequence:
                    self.out_of_order_count += 1
                last_sequence = packet['sequence_number']
                print(f"[Receiver] Packet received: {packet}")

        # 计算指标
        self.calculate_metrics(duration)
    
    def calculate_metrics(self, duration):
        total_packets = len(self.received_packets)
        in_order_packets = total_packets - self.out_of_order_count
        order_ratio = in_order_packets / total_packets if total_packets > 0 else 0

        print(f"[Receiver] Total packets: {total_packets}")
        print(f"[Receiver] In-order packets: {in_order_packets}")
        print(f"[Receiver] Order ratio: {order_ratio:.2f}")