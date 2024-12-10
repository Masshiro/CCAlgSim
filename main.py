from src.helpers import *
from src.sender import Sender
from src.strategies import *

# generate_trace_file(10, './traces/low_10mbps.trace', 60)
# generate_trace_file(30, './traces/med_30mbps.trace', 60)
# generate_trace_file(100, './traces/high_100mbps.trace', 60)

port = get_open_udp_port()
run_without_mahimahi(60, '127.0.0.1', port, [Sender(port, PoissonPacketStrategy(1000, 10))])