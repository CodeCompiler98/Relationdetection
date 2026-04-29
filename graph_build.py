import json
from turtle import position
from zipfile import Path
import networkx as nx 
from collections import defaultdict
import math

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

class EdgeStats:
    def __init__(self):
        self.count = 0
        self.goldstein_sum = 0.0
        self.goldstein_abs_sum = 0.0
        self.goldstein_count = 0

    def add_event(self, goldstein):
        self.count += 1
        self.goldstein_sum += goldstein
        self.goldstein_abs_sum += abs(goldstein)
        self.goldstein_count += 1

class GraphBuilder:
    def __init__(self, exclude_terms):
        self.exclude_terms = exclude_terms
        self.graph = nx.Graph()
        self.edge_data = defaultdict(EdgeStats)
        self.seen_articles = set()

    def process_article(self, article):
        #cheeck if article has been processed (ensure to dups)
        article_id = article.get("source_url")
        if article_id in self.seen_articles:
            return
        self.seen_articles.add(article_id)

        #track edge pairs for this article to prevet double relationship coiunting per article & 
        #use aerticle_pairs to average goldstein values so if one article has 3 different events of vary goldtein valies
        #between the same actors we only count the relation once but avg the goldstein valus for that relation in that article (basically article level weighting for edges)
        article_pairs = defaultdict(EdgeStats)
        seen_relations = set() 

        #go through all of the relations of the article ro pull out actors & their relations
        for event in article.get("events", []):
            #grab data to check for duplicates
            actor1 = event.get("Actor1Name")
            actor2 = event.get("Actor2Name")
            event_code = event.get("EventCode")

            #ensure valid feilds & skip already recorded actor relations if the same type undeer the same article
            if not actor1 or not actor2 or actor1 == actor2:
                continue
            elif any(term.lower() in self.exclude_terms for term in (actor1, actor2)):
                continue
            pair = tuple(sorted((actor1, actor2)))
            relation_key = (pair, event_code)
            if relation_key in seen_relations:
                continue
            seen_relations.add(relation_key)

            #If the event relation in the article is valid & unique (to that article) add the data feilds 
            article_pairs[pair].add_event(float(event.get("GoldsteinScale")))
        #once we have collected all of the edge relations for the article, add them to the main graph statistics  
        for pair, edge_stats in article_pairs.items():
            #add raw data to edge
            self.edge_data[pair].count += article_pairs[pair].count
            self.edge_data[pair].goldstein_sum += article_pairs[pair].goldstein_sum
            self.edge_data[pair].goldstein_abs_sum += article_pairs[pair].goldstein_abs_sum
            self.edge_data[pair].goldstein_count += article_pairs[pair].goldstein_count

    def calc_graph_values(self):
        for pair, edge_stats in self.edge_data.items():
            #puill data from the edge stats object
            frequency = edge_stats.count
            goldstein_count = edge_stats.goldstein_count
            goldstein_abs_sum = edge_stats.goldstein_abs_sum
            goldstein_sum = edge_stats.goldstein_sum
            
            #Computer derived vals 
            avg_goldstein = goldstein_sum / goldstein_count if goldstein_count else 0.0
            avg_abs_goldstein = goldstein_abs_sum / goldstein_count if goldstein_count else 0.0

            #strength For Louvain used to determine how much interaction a pair has together, by seeing the intensity and frequency
            strength = math.log1p(frequency) * avg_abs_goldstein
            #traversal strength measures what edge linsk are the best quality: well documented, more intense measurable events 
            #over 1 due to Dijkstra algo fidning lowest cost path
            cost = 1.0 / (1 + strength)

            #Create graph struct
            self.graph.add_edge(pair[0], pair[1])

            #store all values in the actual graph
            self.graph.edges[pair]["frequency"] = frequency 
            self.graph.edges[pair]["abs_goldstein"] = avg_abs_goldstein 
            self.graph.edges[pair]["goldstein"] = avg_goldstein 
            self.graph.edges[pair]["strength"] = strength
            self.graph.edges[pair]["cost"] = cost
        return self.graph

def draw_graph(G):
    edges = list(G.edges(data=True))

    #get the values we want displayed in the graph
    goldstein = [d.get("goldstein", 0.0) for x, y, d in edges]
    weight = [d.get("weight", 1.0) for x, y, d in edges]

    #use mcolors to have that color matching to goldstein value in a spectrum
    norm = mcolors.TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "ryg", ["red", "yellow", "green"]
    )
    edge_colors = [cmap(norm(g)) for g in goldstein]

    #change edge & node sises based on strength and importance
    max_w = max(weight) if weight else 1
    edge_widths = [0.5 + 2.5 * (np.log1p(w) / np.log1p(max_w)) for w in weight]
    node_sizes = [80 + 40 * G.degree(n) for n in G.nodes()]

    #draw graph with values
    fig, ax = plt.subplots(figsize=(14, 10))
    pos = nx.spring_layout(G, seed=30, k=1.8, iterations=200)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes, node_color="lightblue")
    nx.draw_networkx_edges(G, pos, ax=ax, width=edge_widths, edge_color=edge_colors, alpha=0.4)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=6)

    #add graph legend & helpers
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label="Goldstein")

    ax.set_title("Actor Network")
    ax.axis("off")

    plt.tight_layout()

    plt.savefig('network.png', dpi=150)
    print(f"Saved plot to {Path('network.png').resolve()}")


def build_graph(source, exclude_terms, draw=False):
    # open either the JSON file or a preloaded article list (from benchamrk)
    if isinstance(source, (str, Path)):
        with open(source, "r") as file:
            articles = json.load(file)
    else:
        articles = source
    
    #Set up important data vars for graph construct
    graph_stats = GraphBuilder(exclude_terms)

    #Loop through each article from JSOn file to pull out its relevant relations 
    for article in articles: 
        graph_stats.process_article(article)

    #after processing event event in every article, compute derived metrics & create graph 
    graph = graph_stats.calc_graph_values() 

    #optional to show graph
    if draw:
        draw_graph(graph)

    return graph

if __name__ == "__main__":
    graph = build_graph("bangladesh_news.json", exclude_terms=["bangladesh"])





