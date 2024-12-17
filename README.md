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

# Run

- `docker build -t cc-project .` (about 12 seconds)
- `docker build --no-cache -t cc-project .` (about 4 minutes)

- `docker run --rm --privileged -it cc-project bash`

- `docker run --rm --privileged -it -v $(pwd)/results:/app/results cc-project`

# Design

## Simulated Bandwidth
- low, median and high: 10, 30, 100 Mbps

## Corresponding $\lambda$ rates
- Calculation method: $\lambda_{\max} = \frac{B}{1500\times 8}$
- Set twice maximum bandwith as target packeting rate: $\lambda_i = 2*\lambda_{\max}$

# TODO
- [x] Switch CC algorithms simply with script
- [x] Enable `mahimahi` to simulate the link
- [x] Modify `main.py` so that it can automatically run the whole experiment
- [x] Output formatted (maybe json) files for report drafting
- [x] Draw figures
