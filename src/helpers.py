import os
import subprocess
import matplotlib.pyplot as plt
from subprocess import Popen
import socket
from threading import Thread
from typing import Dict, List
from src.sender import Sender

RECEIVER_FILE = "run_receiver.py"
AVERAGE_SEGMENT_SIZE = 80


def check_current_algorithm():
    result = subprocess.check_output(['sysctl', 'net.ipv4.tcp_congestion_control'], text=True)
    return result.strip()

def check_available_ccalgs():
    options = subprocess.run(['sysctl', 'net.ipv4.tcp_available_congestion_control'], capture_output=True, text=True).stdout.strip('\n').split('=')[1]
    options = options.split(' ')[1:]
    return options

def set_congestion_control(algorithm='cubic'):
    # obtain all available options
    options = check_available_ccalgs()
    if algorithm not in options:
        raise ValueError(f"{algorithm} is not supported. You can choose from {options}")
    
    try:
        subprocess.run(['sudo', 'sysctl', f'net.ipv4.tcp_congestion_control={algorithm}'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to set congestion control: {e}")


def get_open_udp_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def print_performance(sender: Sender, num_seconds: int, print_flag):
    def cal_jitter(rtt_values): # RFC 3550
        jitter = 0
        for i in range(1, len(rtt_values)):
            diff = abs(rtt_values[i] - rtt_values[i-1])
            jitter += (diff - jitter) / 16
        return jitter
    
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
        jitter = cal_jitter(rtts)

        if print_flag:
            print(f"Results for sender with port {sender.port}:")
            print(f"  Total Acks: {total_acks}")
            print(f"  Duplicate Acks: {num_duplicate_acks}")
            print(f"  Duplicate Acks Ratio: {num_duplicate_acks / total_acks * 100:.2f}")
            print(f"  Sequential Ack Ratio: {sequential_ack_ratio:.2f}")
            print(f"  Throughput (bytes/s): {throughput:.2f}")
            print(f"  Average RTT (ms): {avg_rtt:.2f}")
            print(f"  Packet Loss Rate: {loss_rate:.2f}%")
            print(f"  Jitter (ms): {jitter:.2f}")

        return {
            'Duplicate ACK': round(num_duplicate_acks / total_acks * 100, 2),
            'Sequential Ack': round(sequential_ack_ratio, 2),
            'Throughput': round(throughput, 2),
            'RTT': round(avg_rtt, 2),
            'Jitter': round(jitter, 2)
        }

    except ZeroDivisionError:
        print(f"Error: No valid data for sender {sender.port}. Check the experiment setup.")
    except AttributeError as e:
        print(f"Error: Missing attributes in strategy for sender {sender.port}: {e}")


def run_without_mahimahi(seconds_to_run: int, sender_ip: str, sender_port: int, senders: List, print_flag=None):
    print("[info] Running withOUT mahimahi")
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
        results = print_performance(sender, seconds_to_run, print_flag)

    # Terminate the receiver process
    receiver_process.kill()
    return results


def run_with_mahimahi(mahimahi_settings: Dict, seconds_to_run: int, senders: List, print_flag=None):
    def generate_mahimahi_command(mahimahi_settings: Dict) -> str:
        if mahimahi_settings.get('loss'):
            loss_directive = "mm-loss downlink %f" % mahimahi_settings.get('loss')
        else:
            loss_directive = ""
        return "mm-delay {delay} {loss_directive} mm-link traces/{trace_file} traces/{trace_file} --downlink-queue=droptail --downlink-queue-args=bytes={queue_size}".format(
        delay=mahimahi_settings['delay'],
        queue_size=mahimahi_settings['queue_size'],
        loss_directive=loss_directive,
        trace_file=mahimahi_settings['trace_file']
        )
    
    print("[info] Running with mahimahi")
    mahimahi_cmd = generate_mahimahi_command(mahimahi_settings)

    sender_ports = " ".join(["$MAHIMAHI_BASE %s" % sender.port for sender in senders])
    
    cmd = f"{mahimahi_cmd} -- sh -c 'python3 {RECEIVER_FILE} {sender_ports}'"
    receiver_process = Popen(cmd, shell=True)

    for sender in senders:
        sender.handshake()
    threads = [Thread(target=sender.run, args=[seconds_to_run]) for sender in senders]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    # Print sender performance
    for sender in senders:
        results = print_performance(sender, seconds_to_run, print_flag)

    # Terminate the receiver process
    receiver_process.kill()
    return results


def generate_trace_file(bandwidth_mbps, output_file, duration_seconds):
    """
    Generate a Mahimahi trace file for a given bandwidth.

    Parameters:
    bandwidth_mbps (float): Desired bandwidth in Mbps.
    output_file (str): Output trace file name.
    duration_seconds (int): Duration of the trace in seconds.
    more info for trace file: https://n13eho.github.io/mahimahiformatandtransform/
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