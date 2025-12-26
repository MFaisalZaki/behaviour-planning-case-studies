import os
import json
from itertools import combinations
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

planner_name_map = {
    'symk': 'SymK',
    'fi-bc': r'$\mathrm{FI_{bc}}$',
    'fi-k': 'FI_k',
    'fi-maxsum': 'FI_max',
    'fbi-seq': r'$\mathrm{FBI_{SMT}}$',

}

color_map = {
    r'$\mathrm{FBI_{SMT}}$': '#1f77b4',  # blue
    r'$\mathrm{FI_{bc}}$': '#2ca02c',  # orange
    # 'FI_k': '#2ca02c',  # green
    # 'FI_max': '#d62728',  # red,
    # 'SymK': '#9467bd',  # purple
}

plt.rcParams.update({
    'font.size': 16,
    'axes.titlesize': 16,
    'axes.labelsize': 16,
    'xtick.labelsize': 16,
    'ytick.labelsize': 16,
    'legend.fontsize': 16,
    'figure.titlesize': 16,
    'mathtext.default': 'regular',
    'font.family': 'serif',
    'mathtext.fontset': 'cm'
})


def read_results(directory):
    results = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), 'r') as f:
                data = json.load(f)
                if data['time-taken'] > 3600: continue
                pass
                # TODO: filter tasks that took more than 1 hour of planning time.
                # TODO: remove after fixing this.
                # data['q'] = 1.2
                # data['k'] = data['k-plans']
                # if not 'info' in data: continue
                domain_instance = data['story']
                if 'w1' in data['story']: continue
                if 'hospital' in data['story']: continue
                if 'marriage' in data['story']: continue
                # if 'robbery' in data['story']: continue
                # if data['info']['tag'] in ['fbi-seq', 'symk']: continue
                if data['tag'] in ['fi-maxsum', 'fi-k'] : continue
                if data['k'] < 5: continue
                if data['k'] > 10: continue
                results.append((data['q'], data['k'], planner_name_map[data['tag']], domain_instance, data['behaviour-count']))
    return results


def plot_classical_experiments(raw_results, q_values, k_values, planners):
    # sorted_order = [r'$\mathrm{FI_{bc}}$', 'FI_max', 'FI_k', r'$\mathrm{FBI_{SMT}}$']
    sorted_order = [r'$\mathrm{FI_{bc}}$', r'$\mathrm{FBI_{SMT}}$']
    for q in q_values:
        planners_groups = {}
        for k in sorted(k_values):
            planners_results = {planner: set(map(lambda o: (o[3],o[4]), filter(lambda x: x[0] == q and x[1] == k and x[2] == planner, raw_results))) for planner in planners}
            _common_instances = sorted(set.intersection(*[set(map(lambda x: x[0], results)) for planner, results in planners_results.items() ]))
            
            filtered_samples = {
                planner: list(map(lambda x:x[1], sorted(list(filter(lambda x: x[0] in _common_instances, results)), key=lambda x: x[0]))) for planner, results in planners_results.items()
            }

            planners_groups[f'k={k}'] = filtered_samples

            # # Convert to long-form DataFrame
            # data = pd.DataFrame([(label, value) for label, values in filtered_samples.items() for value in values], columns=['Planner', 'Behaviour Count'])
            # # Create violin plot
            # plt.figure(figsize=(10, 6))
            # sns.violinplot(x='Planner', y='Behaviour Count', data=data, inner="box", cut=0, palette=color_map, order=sorted_order)

            # # Styling
            # # plt.title('Violin Plot of Planner Samples')
            # plt.grid(True)
            # plt.tight_layout()
            # save the figure
            # plt.savefig(os.path.join(dumpfigs, f"classical-q-{q}-k-{k}.pdf"), bbox_inches='tight')
        # fig, axes = plt.subplots(1, 4, figsize=(20, 5), sharey=False)
        # fig, axes = plt.subplots(1, 3, figsize=(20, 5), sharey=False)
        fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=False)
        # Plot each group in a subplot
        for ax, (group_name, planners) in zip(axes, planners_groups.items()):
            df = pd.DataFrame([(label, val) for label, values in planners.items() for val in values],
                            columns=['Planner', 'Value'])
            sns.violinplot(x='Planner', y='Value', data=df, ax=ax, palette=color_map, order=sorted_order, cut=0, inner='box')
            ax.set_title(group_name, fontsize=25)
            ax.set_xlabel('')
            ax.grid(True)
            ax.tick_params(axis='x', labelsize=25)
            ax.tick_params(axis='y', labelsize=25)
            plt.setp(ax.get_xticklabels(), ha='center')
            plt.tight_layout()

        # Styling
        axes[0].set_ylabel("Behaviour Diversity Count", fontsize=23)
        for ax in axes[1:]:
            ax.set_ylabel("")

        plt.tight_layout()
        plt.savefig(os.path.join(dumpfigs, f"stories-q-{q}-k-{k}-grouped.pdf"), bbox_inches='tight', dpi=600)

def dump_tables(raw_results, q_values, k_values, planners):
    storydomains = set(map(lambda x: x[3], raw_results))
    # sorted_order = [r'$\mathrm{FI_{bc}}$', 'FI_max', 'FI_k', r'$\mathrm{FBI_{SMT}}$']
    sorted_order = [r'$\mathrm{FI_{bc}}$', r'$\mathrm{FBI_{SMT}}$']
    domain_planners_values = [f"$BS_\Delta$,q,k,domain,{', '.join(sorted_order)}"]
    for q in q_values:
        for k in sorted(k_values):
            for storydomain in sorted(storydomains):
                planners_results = {planner: list(map(lambda o: o[4], filter(lambda x: x[0] == q and x[1] == k and x[2] == planner and x[3] == storydomain, raw_results))) for planner in planners}
                
                # check if the list is empty then put a zero
                for planner in planners:
                    if len(planners_results[planner]) > 0: continue
                    planners_results[planner] = [0]

                # we need to get the values for each story domain
                domain_name = storydomain.replace('cerm_qurm_','').replace('-problem','')
                domain_planners_values.append(f'$f_$  ,{q},{k},{domain_name},{", ".join(map(str,[planners_results[planner][-1] for planner in sorted_order]))}')
    
    #dump csv file
    with open(os.path.join(dumpresults, 'storydomains-results.csv'), 'w') as f:
        f.write('\n'.join(domain_planners_values))
        f.write('\n')
    
    pass
            
            
            
            

resultsdir = "/home/ma342/developer/behaviour-planning-case-studies/storytelling/results/raw-results"
dumpfigs = "/home/ma342/developer/behaviour-planning-case-studies/storytelling/results/dump-figs"
dumpresults = "/home/ma342/developer/behaviour-planning-case-studies/storytelling/results/dump-results"

os.makedirs(dumpresults, exist_ok=True)
os.makedirs(dumpfigs, exist_ok=True)

raw_results = read_results(resultsdir)

# get all q values 
q_values = set(map(lambda x: x[0], raw_results))
k_values = set(map(lambda x: x[1], raw_results))
planners = set(map(lambda x: x[2], raw_results))

pass

dump_tables(raw_results, q_values, k_values, planners)
plot_classical_experiments(raw_results, q_values, k_values, planners)




# plot_numeric_experiments("/Users/mustafafaisal/Downloads/paper-results/numeric/behaviour-count-results/fbi-seq-seq-dummy-fbi-seq-seq-common-instances-behaviour-count.json")

# plot_oversub_experiments(0.5, "/Users/mustafafaisal/Downloads/paper-results/oversub/analysis-0.5/behaviour-count-results/symk-fbi-utility-value-common-instances-behaviour-count.json")
# plot_oversub_experiments(0.25, "/Users/mustafafaisal/Downloads/paper-results/oversub/analysis-0.25/behaviour-count-results/symk-fbi-utility-value-common-instances-behaviour-count.json")
# plot_oversub_experiments(0.75, "/Users/mustafafaisal/Downloads/paper-results/oversub/analysis-0.75/behaviour-count-results/symk-fbi-utility-value-common-instances-behaviour-count.json")
# plot_oversub_experiments(1.0, "/Users/mustafafaisal/Downloads/paper-results/oversub/analysis-1.0/behaviour-count-results/symk-fbi-utility-value-common-instances-behaviour-count.json")





# for (planner1, planner2) in combinations(planners, 2):
#     for q in q_values:
#         k_planners_values = {}

#         for k in k_values:
#             planner1_results = list(filter(lambda x: x[0] == q and x[1] == k and x[2] == planner1, raw_results))
#             planner2_results = list(filter(lambda x: x[0] == q and x[1] == k and x[2] == planner2, raw_results))
#             common_domains = set.intersection(set(map(lambda x: x[3], planner1_results)),set(map(lambda x: x[3], planner2_results)))

#             filtered_planner1_results = sorted(filter(lambda x: x[3] in common_domains, planner1_results), key=lambda x: x[3])
#             filtered_planner2_results = sorted(filter(lambda x: x[3] in common_domains, planner2_results), key=lambda x: x[3])
#             assert len(filtered_planner1_results) == len(filtered_planner2_results), f"Different number of results for {planner1} and {planner2} for q={q} and k={k}"

#             # compute normialised mean and std, but use statistics library

#             planner1_mean = sum(map(lambda x: x[4], filtered_planner1_results)) / len(filtered_planner1_results)
#             planner2_mean = sum(map(lambda x: x[4], filtered_planner2_results)) / len(filtered_planner2_results)
#             planner1_std = (sum(map(lambda x: (x[4] - planner1_mean) ** 2, filtered_planner1_results)) / len(filtered_planner1_results)) ** 0.5
#             planner2_std = (sum(map(lambda x: (x[4] - planner2_mean) ** 2, filtered_planner2_results)) / len(filtered_planner2_results)) ** 0.5

#             k_planners_values[k] = {
#                 'planner1': {
#                     'name': planner1,
#                     'mean': round(planner1_mean,3),
#                     'std': round(planner1_std,3),
#                     'count': len(filtered_planner1_results),
#                     'samples': list(map(lambda x: x[4], filtered_planner1_results))
#                 },
#                 'planner2': {
#                     'name': planner2,
#                     'mean': round(planner2_mean,3),
#                     'std': round(planner2_std,3),
#                     'count': len(filtered_planner2_results),
#                     'samples': list(map(lambda x: x[4], filtered_planner2_results))
#                 }
#             }



#         # plot_planners(q, k_values, k_planners_values, dumpfigs)
#     pass



pass