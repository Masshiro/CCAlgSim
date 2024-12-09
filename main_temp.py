from src.helpers import generate_trace_file

generate_trace_file(10, './traces/low_10mbps.trace', 60)
generate_trace_file(30, './traces/med_30mbps.trace', 60)
generate_trace_file(100, './traces/high_100mbps.trace', 60)