from src.helpers import *
from src.sender import Sender
from src.strategies import *
from collections import defaultdict
from datetime import datetime


# generate_trace_file(10, './traces/low_10mbps.trace', 60)
# generate_trace_file(30, './traces/med_30mbps.trace', 60)
# generate_trace_file(100, './traces/high_100mbps.trace', 60)


RUN_TIMES = 2
DURATION_PER_RUN = 3 # seconds
LAMBDAS = {
    'low': 0.7 * 10 * 1e6 / 12000.0,
    'med': 0.7 * 30 * 1e6 / 12000.0,
    'high': 0.7 * 100 * 1e6 / 12000.0,
}
EXP_SETTINGS = {
    'low': {
        'mahimahi': {
            'delay': 88,
            'queue_size': 26400,
            'trace_file': 'low_10mbps.trace'
        },
        'lambda': LAMBDAS['low']
    },
    'med': {
        'mahimahi': {
            'delay': 88,
            'queue_size': 26400,
            'trace_file': 'med_30mbps.trace'
        },
        'lambda': LAMBDAS['med']
    },
    'high': {
        'mahimahi': {
            'delay': 88,
            'queue_size': 1104620,
            'trace_file': 'high_100mbps.trace'
        },
        'lambda': LAMBDAS['high']
    }
}


def one_run(setting):
    port = get_open_udp_port()
    res = run_with_mahimahi(setting['mahimahi'], DURATION_PER_RUN, [Sender(port, PoissonPacketStrategy(1000, setting['lambda']))], print_flag=False)
    return res

def main():
    # Get all available CC algorithms
    options = check_available_ccalgs()
    if len(options) >= 2:
        options = options[0:2]
    else:
        raise ValueError(f"Host machine should have more than 2 algorithms to run this script.")

    exp_results = {}
    for cc_alg in options:
        # switch the algorithm and verify
        set_congestion_control(cc_alg)
        curr_ccalg = check_current_algorithm()
        print(f'\n=> Switched to congestion control algorithm: {curr_ccalg}')

        # run each setting multiple times
        exp_results[cc_alg] = defaultdict(dict)
        for setting in EXP_SETTINGS:
            multi_run_results = []
            for i in range(RUN_TIMES):
                print(f"\n=> => Setting: {setting}; Run ({i+1}/{RUN_TIMES})")
                res = one_run(EXP_SETTINGS[setting])
                multi_run_results.append(res)
            exp_results[cc_alg][setting] = {key: [d[key] for d in multi_run_results] for key in multi_run_results[0]}
    
    current_date = datetime.now().strftime("%m-%d_%H-%M")
    output_dir = '/app/results'  # Directories mounted in the container
    file_name = f"{output_dir}/output_{current_date}.json"
    os.makedirs(output_dir, exist_ok=True)

    with open(file_name, 'w') as json_file:
        json.dump(exp_results, json_file, indent=4)
    print(f"\nExperient is done. Results are saved to {file_name}.")

    return exp_results


if __name__ == "__main__":
    main()