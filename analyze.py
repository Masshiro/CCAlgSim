import matplotlib.pyplot as plt
import json

import numpy as np
from scipy import stats


with open('./results/output_12-15_17-02.json', 'r') as file:
    data = json.load(file)
# print(data['reno']['low']['RTT'])

levels = ['low', 'med', 'high']
metrics = ['Duplicate ACK', 'Sequential Ack', 'Throughput', 'RTT', 'Jitter']
colors = ['#CDC1FF', '#074799', '#FF748B']


def draw_cwnd(cc_alg='reno', level='low', lines_cnt=5):
    plt.figure(figsize=(10, 6))  # 设置图表尺寸


    for idx, sublist in enumerate(data[cc_alg][level]['CWND']):
        if idx +1 == lines_cnt:
            break
        plt.plot(sublist, label=f'List {idx+1}')  # 对每个子列表绘制折线图
        # print(len(sublist), sublist[0])

    # 添加图表标题和图例
    plt.title('Line Plot for Nested List')
    plt.xlabel('Index')
    plt.ylabel('Values')
    plt.legend()
    plt.grid(True)

    # 显示图表
    plt.savefig(f'./results/{cc_alg}_{level}_{lines_cnt}.png', bbox_inches='tight')

# draw_cwnd()
# draw_cwnd(cc_alg='cubic', level='med')
# # print('sssss')
# draw_cwnd(cc_alg='cubic', level='high')



# for l in levels:
#     print(f'Results for {l}')
#     for m in metrics:
#         print(f'# for {m}')
#         print(f'==> reno: {data['reno'][l][m]}')
#         print(f'==>cubic: {data['cubic'][l][m]}')
#     print('='*20)

def output_tabular(cc_alg='cubic', level='low'):
    for r in range(5):
        one_run_data = [str(data[cc_alg][level][m][r]) for m in metrics]
        one_line = f'{r+1} &' + ' & '.join(one_run_data) + " \\\\"
        print(one_line)
        print('\\midrule')

def calculate_stats(cc_alg='cubic', level='low', confidence=0.95):
    stats_names = ['Mean', 'Variance', 'HCI']
    results = []
    for m in metrics:
        one_metric_data = [data[cc_alg][level][m][r] for r in range(5)]
        mean = np.mean(one_metric_data)
        variance = np.var(one_metric_data, ddof=1)
        n = len(one_metric_data)
        se = stats.sem(one_metric_data)
        t_critical = stats.t.ppf((1 + confidence) / 2, df=n-1)
        half_confidence_interval = t_critical * se
        results.append([mean, variance, half_confidence_interval])
    print(results)
    
    for j in range(3):
        # for j in range(len(metrics)):
        one_line_data = [f'{results[i][j]:.2f}' for i in range(len(metrics))]
        one_line = f"\\textbf {stats_names[j]} & " + ' & '.join(one_line_data) + '\\\\'
        print(one_line)
        print('\\midrule')


def draw_5runs_2algs_lines(metric='Throughput', level='low'):
    reno_data = [data['reno'][level][metric][r] for r in range(5)]
    cubic_data = [data['cubic'][level][metric][r] for r in range(5)]
    x = [1, 2, 3, 4, 5]

    plt.plot(x, np.log(reno_data), label="Reno", color=colors[2], marker="o", linestyle=":", lw=2)
    plt.plot(x, np.log(cubic_data), label="Cubic", color=colors[1], marker="s", linestyle="--", lw=2)
    plt.xticks(ticks=x)

    plt.xlabel("Run", fontsize=12)
    plt.ylabel(metric+' (log scale)', fontsize=12)

    plt.legend(loc="upper left", fontsize=10)
    plt.grid(alpha=0.3)
    plt.savefig(f'./results/{level}_{metric}.png', bbox_inches='tight')

def draw_5runs_2alg_lines_all(metric='Throughput'):
    x = [1, 2, 3, 4, 5]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)

    # 绘制第一个子图
    axes[0].plot(x, np.log([data['reno']['low'][metric][r] for r in range(5)]), label="Reno", color=colors[2], marker="o", linestyle=":", lw=2)
    axes[0].plot(x, np.log([data['cubic']['low'][metric][r] for r in range(5)]), label="Cubic", color=colors[1], marker="s", linestyle="--", lw=2)
    axes[0].set_title("Low Bandwidth Level")
    axes[0].legend(loc="lower left", fontsize=14)
    axes[0].set_xlabel("Run", fontsize=12)
    axes[0].set_xticks(ticks=x)

    # 绘制第二个子图
    axes[1].plot(x, np.log([data['reno']['med'][metric][r] for r in range(5)]), label="Reno", color=colors[2], marker="o", linestyle=":", lw=2)
    axes[1].plot(x, np.log([data['cubic']['med'][metric][r] for r in range(5)]), label="Cubic", color=colors[1], marker="s", linestyle="--", lw=2)
    axes[1].set_title("Medium Bandwidth Level")
    axes[1].legend(loc="lower left", fontsize=14)
    axes[1].set_xlabel("Run", fontsize=12)
    axes[1].set_xticks(ticks=x)

    # 绘制第三个子图
    axes[2].plot(x, np.log([data['reno']['high'][metric][r] for r in range(5)]), label="Reno", color=colors[2], marker="o", linestyle=":", lw=2)
    axes[2].plot(x, np.log([data['cubic']['high'][metric][r] for r in range(5)]), label="Cubic", color=colors[1], marker="s", linestyle="--", lw=2)
    axes[2].set_title("High Bandwidth Level")
    axes[2].legend(loc="lower left", fontsize=14)
    axes[2].set_xlabel("Run", fontsize=12)
    axes[2].set_xticks(ticks=x)

    # 添加公共 y 轴标签
    fig.text(0.04, 0.5, f"{metric} (log scale)", va="center", rotation="vertical", fontsize=12)

    # 调整布局以避免重叠
    plt.tight_layout(rect=[0.05, 0.05, 1, 1])
    plt.savefig(f'./results/all_levels_{metric}.png', bbox_inches='tight')


# calculate_stats(cc_alg='cubic', level='high')
        

# output_tabular(cc_alg='cubic', level='high')

def CRN_comparison(metric='Throughput', confidence=.90):
    for level in levels:
        print(f'\nLevel: {level}')
        reno_data = np.array(data['reno'][level][metric])
        cubic_data = np.array(data['cubic'][level][metric])

        diffs = reno_data - cubic_data
        # print(f'diffs: {diffs}')

        mean_diff = np.mean(diffs)
        print(f'mean: {mean_diff}')
        var_diff = np.var(diffs, ddof=1)
        print(f'variance: {var_diff}')

        n = len(diffs)

        t_stat, p_val = stats.ttest_rel(reno_data, cubic_data)
        
        sem = stats.sem(diffs)  # 标准误差
        t_crit = stats.t.ppf((1 + confidence) / 2, n - 1)
        hci = t_crit * sem
        ci_lower = mean_diff - hci
        ci_upper = mean_diff + hci
        print(f'CI ({confidence}): {ci_lower:.2f}, {ci_upper:.2f}')

if __name__ == '__main__':
    # draw_5runs_2algs_lines(level='high')
    # draw_5runs_2alg_lines_all()
    CRN_comparison()
