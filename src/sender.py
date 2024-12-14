import sys
import json
import socket
import select
import time
from tqdm import tqdm
from src.strategies import SenderStrategy

READ_FLAGS = select.POLLIN | select.POLLPRI
WRITE_FLAGS = select.POLLOUT
ERR_FLAGS = select.POLLERR | select.POLLHUP | select.POLLNVAL
READ_ERR_FLAGS = READ_FLAGS | ERR_FLAGS
ALL_FLAGS = READ_FLAGS | WRITE_FLAGS | ERR_FLAGS


class Sender(object):
    def __init__(self, port: int, strategy: SenderStrategy) -> None:
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', port))
        self.poller = select.poll()
        self.poller.register(self.sock, ALL_FLAGS)
        self.poller.modify(self.sock, ALL_FLAGS)
        self.peer_addr = None

        self.strategy = strategy

        # bind_ip, bind_port = self.sock.getsockname()
        # print(f"Sender: Socket is bound to IP: {bind_ip}, Port: {bind_port}")

    def send(self) -> None:
        next_segment =  self.strategy.next_packet_to_send()
        if next_segment is not None:
            self.sock.sendto(next_segment.encode(), self.peer_addr) # type: ignore
        time.sleep(0)

    def recv(self):
        serialized_ack, addr = self.sock.recvfrom(1600)
        self.strategy.process_ack(serialized_ack.decode())


    def handshake(self):
        """Handshake to establish connection with receiver."""

        while True:
            msg, addr = self.sock.recvfrom(1600)
            parsed_handshake = json.loads(msg.decode())
            if parsed_handshake.get('handshake') and self.peer_addr is None:
                self.peer_addr = addr
                self.sock.sendto(json.dumps({'handshake': True}).encode(), self.peer_addr)
                print('[sender] Connected to receiver: %s:%s' % addr)
                break
        self.sock.setblocking(0)

    
    def run(self, seconds_to_run: int):
        """
        Run the sender with a progress bar indicating the elapsed time.
        """
        curr_flags = ALL_FLAGS
        TIMEOUT = 1000  # ms
        start_time = time.time()

        # Initialize the progress bar
        with tqdm(total=seconds_to_run, desc="Progress", unit="s") as pbar:
            while time.time() - start_time < seconds_to_run:
                elapsed_time = time.time() - start_time

                # Update the progress bar
                pbar.update(int(elapsed_time - pbar.n))

                events = self.poller.poll(TIMEOUT)
                if not events:
                    self.send()
                for fd, flag in events:
                    assert self.sock.fileno() == fd

                    if flag & ERR_FLAGS:
                        pbar.close()
                        sys.exit('Error occurred to the channel')

                    if flag & READ_FLAGS:
                        self.recv()

                    if flag & WRITE_FLAGS:
                        self.send()
            pbar.update(seconds_to_run - pbar.n)
