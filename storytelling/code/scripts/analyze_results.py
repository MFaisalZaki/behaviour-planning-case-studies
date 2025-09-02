import os
import json
from collections import defaultdict
from utilities import getkeyvalue

def load_results(dir):
    results = []
    for file in os.listdir(dir):
        filepath = os.path.join(dir, file)
        if os.path.isdir(filepath): continue
        if not file.endswith('.json'): continue
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # for now but it should not be.
                data['k'] = int(file[file.rfind('-')+1:].replace('.json', ''))
                results.append(data)
                # results.append(json.load(f))
        except:
            print(f"Failed to load results from {filepath}")
    return results


def analyze_results(dir):
    analysis_results = defaultdict(dict)
    results = load_results(dir)
    k_values_list = set(map(lambda e: e['k'], results))
    planner_list = set(map(lambda e: e['tag'], results))
    story_list = set(map(lambda e: e['story'], results))

    # planner_list.remove('kstar')

    for entry in filter(lambda e: len(e['plans']), results):
        if entry['k'] not in analysis_results: analysis_results[entry['k']] = defaultdict(dict)
        if entry['tag'] not in analysis_results[entry['k']]: analysis_results[entry['k']][entry['tag']] = defaultdict(int)
        analysis_results[entry['k']][entry['tag']][getkeyvalue(entry, 'story')] = getkeyvalue(entry, 'behaviour-count')
    
    # dump in CSV format:
    # k, Story, planner, behaviour count
    dumpdir = os.path.join(dir, 'analysis')
    os.makedirs(dumpdir, exist_ok=True)
    with open(os.path.join(dumpdir, 'analysis.csv'), 'w') as f:
        f.write(f'k, Story, {", ".join(sorted(planner_list))}\n')
        for k in sorted(k_values_list):
            for story in sorted(story_list):
                for planner in sorted(planner_list):
                    if not story in analysis_results[k][planner]: analysis_results[k][planner][story] = 0
                planners_results = ", ".join(map(str,[analysis_results[k][planner][story] for planner in sorted(planner_list)]))
                f.write(f"{k}, {story.replace('qurm_cerm_','').replace('-problem','')}, {planners_results}\n")
    
    # dump a transposed version of the CSV:
    # Story, k, planner, behaviour count
    with open(os.path.join(dumpdir, 'analysis-transposed.csv'), 'w') as f:
        f.write(f'k, Story, {", ".join(sorted(planner_list))}\n')
        for k in sorted(k_values_list):
            for story in sorted(story_list):
                for planner in sorted(planner_list):
                    if not story in analysis_results[k][planner]: analysis_results[k][planner][story] = 0
                planners_results = ", ".join(map(str,[analysis_results[k][planner][story] for planner in sorted(planner_list)]))
                story_name = story.replace('cerm_qurm_','').replace('-problem','').replace('problem-','')
                f.write(f"{k}, {story_name}, {planners_results}\n")
    
    pass



    print("Analyzing results...")


if __name__ == '__main__':
    analysis_results = analyze_results(os.path.join(os.path.dirname(__file__), '..', 'sandbox-non-intentional', 'results'))
    analysis_results = analyze_results(os.path.join(os.path.dirname(__file__), '..', 'sandbox-intentional', 'results'))
    pass