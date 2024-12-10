import matplotlib.pyplot as plt
from subprocess import Popen
import socket
from threading import Thread
from typing import Dict, List
from src.sender import Sender

RECEIVER_FILE = "run_receiver.py"
AVERAGE_SEGMENT_SIZE = 80

def get_open_udp_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

# def print_performance(sender: Sender, num_seconds: int):
#     print("Results for sender %d:" % sender.port)
#     print("Total Acks: %d" % sender.strategy.total_acks)
#     print("Num Duplicate Acks: %d" % sender.strategy.num_duplicate_acks)
    
#     print("%% duplicate acks: %f" % ((float(sender.strategy.num_duplicate_acks * 100))/sender.strategy.total_acks))
#     print("Throughput (bytes/s): %f" % (AVERAGE_SEGMENT_SIZE * (sender.strategy.ack_count/num_seconds)))
#     print("Average RTT (ms): %f" % ((float(sum(sender.strategy.rtts))/len(sender.strategy.rtts)) * 1000))


def print_performance(sender: Sender, num_seconds: int):
    try:
        total_acks = sender.strategy.total_acks
        num_duplicate_acks = sender.strategy.num_duplicate_acks
        sequential_ack_ratio = sender.strategy.sequential_ack_ratio()
        rtts = sender.strategy.rtts
        ack_count = sender.strategy.ack_count
        throughput = AVERAGE_SEGMENT_SIZE * (ack_count / num_seconds)
        avg_rtt = (float(sum(rtts)) / len(rtts)) * 1000 if rtts else float('inf')
        total_sent_packets = sender.strategy.total_sent_packets  # 获取总发送包数
        loss_rate = ((total_sent_packets - total_acks) / total_sent_packets) * 100 if total_sent_packets > 0 else 0

        print(f"Results for sender with port {sender.port}:")
        print(f"  Total Acks: {total_acks}")
        print(f"  Duplicate Acks: {num_duplicate_acks}")
        print(f"  % Duplicate Acks: {num_duplicate_acks / total_acks * 100:.2f}%")
        print(f"  Sequential Ack Ratio: {sequential_ack_ratio:.2f}")
        print(f"  Throughput (bytes/s): {throughput:.2f}")
        print(f"  Average RTT (ms): {avg_rtt:.2f}")
        print(f"  Packet Loss Rate: {loss_rate:.2f}%")

    except ZeroDivisionError:
        print(f"Error: No valid data for sender {sender.port}. Check the experiment setup.")
    except AttributeError as e:
        print(f"Error: Missing attributes in strategy for sender {sender.port}: {e}")


def run_without_mahimahi(seconds_to_run: int, sender_ip: str, sender_port: int, senders: List):
    # Start the receiver process
    cmd = f"python3 {RECEIVER_FILE} {sender_ip} {sender_port}"
    receiver_process = Popen(cmd, shell=True)

    # Perform handshakes and run senders
    for sender in senders:
        sender.handshake()

    threads = [Thread(target=sender.run, args=[seconds_to_run]) for sender in senders]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Print sender performance
    for sender in senders:
        print_performance(sender, seconds_to_run)

    # Terminate the receiver process
    receiver_process.kill()


def generate_trace_file(bandwidth_mbps, output_file, duration_seconds):
    """
    Generate a Mahimahi trace file for a given bandwidth.

    Parameters:
    bandwidth_mbps (float): Desired bandwidth in Mbps.
    output_file (str): Output trace file name.
    duration_seconds (int): Duration of the trace in seconds.
    """
    # Constants
    mtu_bytes = 1500  # Size of an MTU packet in bytes
    mtu_bits = mtu_bytes * 8  # Size of an MTU packet in bits
    milliseconds_per_second = 1000  # Conversion factor for milliseconds

    # Calculate packets per millisecond
    packets_per_ms = bandwidth_mbps * 1e6 / mtu_bits / milliseconds_per_second

    # Open the output file for writing
    with open(output_file, "w") as f:
        current_time_ms = 0
        for _ in range(int(duration_seconds * milliseconds_per_second)):
            # Write timestamps based on packets per millisecond
            for _ in range(int(packets_per_ms)):
                f.write(f"{current_time_ms}\n")
            # Handle fractional packets
            if packets_per_ms % 1 > 0:
                fractional_chance = packets_per_ms % 1
                if fractional_chance > 0:
                    f.write(f"{current_time_ms}\n")
            current_time_ms += 1

    print(f"Trace file generated: {output_file}")