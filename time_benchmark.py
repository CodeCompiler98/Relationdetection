import csv
import json
import random
import time
from pathlib import Path

import matplotlib.pyplot as plt

from graph_build import build_graph
from network_analysis import build_communities, dijkstra_path, calculate_path_logic

# const for benchmarking 
GRAPH_FRACTIONS = [1.0, 0.5, 0.25, 0.125]
REPEATS = 3


def benchmark(csv_path="node_relations.csv", json_path="bangladesh_news.json"):
    #load in all rows from our known relation CSV
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    results = []
    with open(json_path, "r", encoding="utf-8") as file:
        articles = json.load(file)
    
    print(f"Loaded {len(rows)} relation rows")
    print(f"Loaded {len(articles)} articles")

    #Take different fractions of the graph to see how it scales up as more nodes and edges are introduced 
    for fraction in GRAPH_FRACTIONS:
        classify_times = []

        #take in the JSON articles, select a random fraction of them, and build the graph with it (logging the build time)
        sample_size = max(1, int(len(articles) * fraction))
        sampled_articles = random.sample(articles, sample_size)

        build_start = time.perf_counter()
        graph = build_graph(sampled_articles, exclude_terms=["bangladesh"], draw=False)
        build_time = time.perf_counter() - build_start


        #see how long the comm detection takes
        community_start = time.perf_counter()
        partition, x = build_communities(graph)
        community_time = time.perf_counter() - community_start

        #grab the new node list, looks to benchamrk pair masterlist and filters it down to only those currently in the graph
        graph_nodes = set(graph.nodes())
        graph_rows = [
            row
            for row in rows
            if row["actor1"].strip() in graph_nodes and row["actor2"].strip() in graph_nodes
        ]
        #if no rows after filtering skip this fraction (too small)
        if not graph_rows:
            print(f"fraction={fraction:.3f} produced no usable relation rows, skipping")
            continue

        #loop X amont of times to reduce noise, take the average, & log results
        for x in range(REPEATS):
            sample = list(graph_rows)

            #For each row, run the path tracing and path logic like normal to log the total time
            classify_start = time.perf_counter()
            for row in sample: 
                actor1 = row["actor1"].strip()
                actor2 = row["actor2"].strip()
                path, x = dijkstra_path(graph, actor1, actor2)
                if path is not None:
                    calculate_path_logic(graph, path, partition=partition)

            classify_time = time.perf_counter() - classify_start
            classify_times.append(classify_time)

        #Log values for all iterations for printing 
        avg_classify_time = sum(classify_times) / len(classify_times)
        avg_total_time = build_time + community_time + avg_classify_time
        results.append((sample_size, len(graph_rows), avg_total_time))

        #print out  results for this fracrtion
        print(f"fraction={fraction:.3f} articles={sample_size} rows={len(graph_rows)} " 
              f"build={build_time:.6f}s communities={community_time:.6f}s " 
              f"classify={avg_classify_time:.6f}s total={avg_total_time:.6f}s"
        )

    return results


def plot_results(results, output_file="relation_scaling.png"):
    #grab values to plot
    sizes = [articles for articles, effective_rows, elapsed in results]
    times = [elapsed for articles, effective_rows, elapsed in results]

    #set up plot & save it
    plt.figure(figsize=(8, 5))
    plt.plot(times, sizes, marker="o")
    plt.xlabel("Average runtime (seconds)")
    plt.ylabel("Article count")
    plt.title("Relation Algorithm Scaling")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    print(f"Saved plot to {Path(output_file).resolve()}")


if __name__ == "__main__":
    results = benchmark("node_relations.csv", "bangladesh_news.json")
    plot_results(results)
