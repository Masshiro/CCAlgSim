import json
import time
import random
from typing import Dict, List, Optional, Tuple

class SenderStrategy(object):
    def __init__(self) -> None:
        self.seq_num = 0
        self.next_ack = 0
        self.sent_bytes = 0
        self.start_time = time.time()
        self.total_acks = 0
        self.num_duplicate_acks = 0
        self.curr_duplicate_acks = 0
        self.rtts: List[float] = []
        self.cwnds: List[int] = []
        self.unacknowledged_packets: Dict = {}
        self.times_of_acknowledgements: List[Tuple[float, int]] = []
        self.ack_count = 0
        self.slow_start_thresholds: List = []
        self.time_of_retransmit: Optional[float] = None
        self.total_sent_packets = 0

    def next_packet_to_send(self):
        raise NotImplementedError

    def process_ack(self, ack: str):
        raise NotImplementedError

class PoissonPacketStrategy(SenderStrategy):
    def __init__(self, rate_lambda: float) -> None:
        super().__init__()
        # self.cwnd = cwnd
        self.rate_lambda = rate_lambda
        self.next_send_time = 0
        self.expected_next_ack = 0  # Tracks the expected next acknowledgment sequence number
        self.sequential_ack_count = 0  # Counts sequential acknowledgments

    # def window_is_open(self) -> bool:
    #     return self.seq_num - self.next_ack < self.cwnd

    def next_packet_to_send(self) -> Optional[str]:
        current_time = time.time()
        # if not self.window_is_open() or current_time < self.next_send_time:
        #     return None
        if current_time < self.next_send_time:
            return None

        serialized_data = json.dumps({
            'seq_num': self.seq_num,
            'send_ts': current_time,
            'sent_bytes': self.sent_bytes
        })
        self.unacknowledged_packets[self.seq_num] = True
        self.seq_num += 1
        self.total_sent_packets += 1

        # Schedule the next packet send time based on the Poisson process
        inter_departure_time = random.expovariate(self.rate_lambda)
        self.next_send_time = current_time + inter_departure_time

        return serialized_data

    def process_ack(self, serialized_ack: str) -> None:
        ack = json.loads(serialized_ack)
        if ack.get('handshake'):
            return

        self.total_acks += 1
        self.times_of_acknowledgements.append(((time.time() - self.start_time), ack['seq_num']))
        if self.unacknowledged_packets.get(ack['seq_num']) is None:
            # Duplicate ack
            self.num_duplicate_acks += 1
            self.curr_duplicate_acks += 1

            if self.curr_duplicate_acks == 3:
                # Received 3 duplicate acks, retransmit
                self.curr_duplicate_acks = 0
                self.seq_num = ack['seq_num'] + 1
        else:
            del self.unacknowledged_packets[ack['seq_num']]
            if ack['seq_num'] == self.expected_next_ack:
                self.sequential_ack_count += 1
            self.next_ack = max(self.next_ack, ack['seq_num'] + 1)
            self.sent_bytes += ack['ack_bytes']
            rtt = float(time.time() - ack['send_ts'])
            self.rtts.append(rtt)
            self.ack_count += 1
            self.expected_next_ack = ack['seq_num'] + 1
        # self.cwnds.append(self.cwnd)

    def sequential_ack_ratio(self) -> float:
        if self.total_acks == 0:
            return 0.0
        return self.sequential_ack_count / self.total_acks


class RenoStrategy(SenderStrategy):
    def __init__(self, slow_start_thresh: int, initial_cwnd: int, rate_lambda: float) -> None:
        self.slow_start_thresh = slow_start_thresh
        self.cwnd = initial_cwnd
        self.rate_lambda = rate_lambda
        self.sequential_ack_count = 0  # Sequential ACK counter

        # Track duplicate ACKs for fast retransmission
        self.num_duplicate_acks = 0
        self.duplicated_ack = None
        self.retransmitting_packet = False
        self.time_of_retransmit = None
        super().__init__()

    def window_is_open(self) -> bool:
        return self.seq_num - self.next_ack < self.cwnd

    def next_packet_to_send(self) -> Optional[str]:
        current_time = time.time()

        # Poisson-based inter-departure time
        inter_departure_time = random.expovariate(self.rate_lambda)
        if current_time < self.start_time + inter_departure_time:
            return None

        if not self.window_is_open():
            return None

        # Create packet
        send_data = {
            'seq_num': self.seq_num,
            'send_ts': current_time
        }
        self.unacknowledged_packets[self.seq_num] = send_data
        self.seq_num += 1
        return json.dumps(send_data)

    def process_ack(self, serialized_ack: str) -> None:
        ack = json.loads(serialized_ack)
        if ack.get('handshake'):
            return

        self.total_acks += 1
        self.times_of_acknowledgements.append(((time.time() - self.start_time), ack['seq_num']))

        if self.unacknowledged_packets.get(ack['seq_num']) is None:
            # Duplicate ACK received
            self.num_duplicate_acks += 1
            if self.duplicated_ack and ack['seq_num'] == self.duplicated_ack['seq_num']:
                self.curr_duplicate_acks += 1
            else:
                self.duplicated_ack = ack
                self.curr_duplicate_acks = 1

            if self.curr_duplicate_acks == 3:
                # Fast retransmit
                self.slow_start_thresh = max(1, self.cwnd // 2)  # Halve cwnd
                self.cwnd = self.slow_start_thresh  # Enter congestion avoidance
                self.num_duplicate_acks = 0
                self.retransmitting_packet = True
        elif ack['seq_num'] >= self.next_ack:
            # Successful ACK, move window
            self.unacknowledged_packets = {
                k: v for k, v in self.unacknowledged_packets.items()
                if k > ack['seq_num']
            }
            self.next_ack = max(self.next_ack, ack['seq_num'] + 1)
            self.ack_count += 1
            self.sent_bytes += ack['ack_bytes']
            rtt = float(time.time() - ack['send_ts'])
            self.rtts.append(rtt)

            # Count sequential ACKs
            if ack['seq_num'] == self.next_ack - 1:
                self.sequential_ack_count += 1

            if self.cwnd < self.slow_start_thresh:
                # In slow start
                self.cwnd += 1
            else:
                # Additive increase in congestion avoidance
                self.cwnd += 1.0 / self.cwnd

        self.cwnds.append(self.cwnd)
        self.slow_start_thresholds.append(self.slow_start_thresh)

    def sequential_ack_ratio(self) -> float:
        if self.total_acks == 0:
            return 0.0
        return self.sequential_ack_count / self.total_acks


class CubicStrategy(SenderStrategy):
    def __init__(self, slow_start_thresh: int, initial_cwnd: int, rate_lambda: float) -> None:
        self.slow_start_thresh = slow_start_thresh
        self.cwnd = initial_cwnd
        self.rate_lambda = rate_lambda
        self.sequential_ack_count = 0  # Sequential ACK counter

        # Cubic parameters
        self.C = 0.4  # Cubic scaling factor
        self.cwnd_max = initial_cwnd  # Last maximum cwnd
        self.t_start = time.time()  # Start time for cubic function

        super().__init__()

    def window_is_open(self) -> bool:
        return self.seq_num - self.next_ack < self.cwnd

    def cubic_window_growth(self) -> float:
        # Time elapsed since the last congestion event
        t = time.time() - self.t_start
        K = (self.cwnd_max / self.C) ** (1 / 3)  # Calculate K
        cwnd = self.C * (t - K) ** 3 + self.cwnd_max  # Cubic growth
        return max(1, cwnd)

    def next_packet_to_send(self) -> Optional[str]:
        current_time = time.time()
        if not self.window_is_open():
            return None

        # Poisson-based inter-departure time
        inter_departure_time = random.expovariate(self.rate_lambda)
        if current_time < self.start_time + inter_departure_time:
            return None

        # Create packet
        send_data = {
            'seq_num': self.seq_num,
            'send_ts': current_time
        }
        self.unacknowledged_packets[self.seq_num] = send_data
        self.seq_num += 1
        return json.dumps(send_data)

    def process_ack(self, serialized_ack: str) -> None:
        ack = json.loads(serialized_ack)
        if ack.get('handshake'):
            return

        self.total_acks += 1
        self.times_of_acknowledgements.append(((time.time() - self.start_time), ack['seq_num']))

        if self.unacknowledged_packets.get(ack['seq_num']) is None:
            # Duplicate ack handling
            self.num_duplicate_acks += 1
            if self.num_duplicate_acks == 3:
                self.slow_start_thresh = max(1, self.cwnd // 2)
                self.cwnd = 1
                self.cwnd_max = self.cwnd  # Update cubic parameters
                self.t_start = time.time()
        elif ack['seq_num'] >= self.next_ack:
            # Successful ACK, move window
            self.unacknowledged_packets = {
                k: v for k, v in self.unacknowledged_packets.items()
                if k > ack['seq_num']
            }
            self.next_ack = max(self.next_ack, ack['seq_num'] + 1)
            self.ack_count += 1
            self.sent_bytes += ack['ack_bytes']
            rtt = float(time.time() - ack['send_ts'])
            self.rtts.append(rtt)

            # Count sequential ACKs
            if ack['seq_num'] == self.next_ack - 1:
                self.sequential_ack_count += 1

            if self.cwnd < self.slow_start_thresh:
                # In slow start
                self.cwnd += 1
            else:
                # In congestion avoidance, cubic growth
                self.cwnd = self.cubic_window_growth()

        self.cwnds.append(self.cwnd)
        self.slow_start_thresholds.append(self.slow_start_thresh)
    
    def sequential_ack_ratio(self) -> float:
        if self.total_acks == 0:
            return 0.0
        return self.sequential_ack_count / self.total_acks