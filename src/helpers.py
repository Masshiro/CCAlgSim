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