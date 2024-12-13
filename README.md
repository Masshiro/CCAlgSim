# CCAlgSim
CSC546 Project: Simulation Study on Congestion Control Algorithms

# Metrics  
- Sequential packet reception ratio

- Throughput

- Loss ratio

- Average RTT

- Jitter (RFC 3550)

$$
J_i = J_{i-1} + \frac{\vert RTT_{i+1}-RTT_i\vert - J_{i-1}}{16}, \quad J_0 = 0
$$