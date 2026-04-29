import csv
import itertools
import time
from pathlib import Path

from network_analysis import build_communities, calculate_path_logic, dijkstra_path, build_graph

#Generate a CSV file of all possible pairs of node paths in the graph for benchmarking & testing 
def export_relation_csv(json_file='bangladesh_news.json', output_file='node_relations.csv'):
    #build graph & extract vnodes 
    graph = build_graph(json_file, exclude_terms=['bangladesh'])
    nodes = sorted(graph.nodes())
    output_path = Path(output_file)

    #get communtiies for confidence & time for runtime
    lookup_table, x = build_communities(graph)
    start_time = time.perf_counter()

    with output_path.open('w', newline='', encoding='utf-8') as csv_file:
        #set up CSV writwer
        writer = csv.DictWriter(
            csv_file,
            fieldnames=['actor1', 'actor2', 'relation_exist', 'relation_label', 'confidence', 'runtime_seconds'],
        )
        writer.writeheader()

        #loop through all possible pairs of nodes, run path, and log resultd
        for node_a, node_b in itertools.combinations(nodes, 2):
            pair_start = time.perf_counter()
            if graph.has_node(node_a) and graph.has_node(node_b):
                path, x = dijkstra_path(graph, node_a, node_b)
                if path is not None:
                    result = calculate_path_logic(graph, path, partition=lookup_table)
                    relation_label = result['sign']
                    confidence = result['confidence']
                    relation_exist = 1
                else:
                    relation_label = 0
                    confidence = 0.0
                    relation_exist = 0
            else:
                relation_label = 0
                confidence = 0.0
                relation_exist = 0

            sec_passed = time.perf_counter() - pair_start
            writer.writerow(
                {
                    'actor1': node_a,
                    'actor2': node_b,
                    'relation_exist': relation_exist,
                    'relation_label': relation_label,
                    'confidence': round(confidence, 6),
                    'runtime_seconds': round(sec_passed, 6),
                }
            )

    total_runtime = time.perf_counter() - start_time
    print(f'Wrote {output_path.resolve()}')
    print(f'Pairs exported: {len(nodes) * (len(nodes) - 1) // 2}')
    print(f'Runtime seconds: {total_runtime:.6f}')


if __name__ == '__main__':
    export_relation_csv()
