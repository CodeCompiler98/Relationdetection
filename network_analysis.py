import networkx as nx
from graph_build import build_graph
import math

#library ref source I used: https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html 
def build_communities(graph): 
    # Run the louvain community detection algo, use these communites for calculating confidence values
    # return a dictionary mapping the nodes to its community, and a dictionary of the communties
    communities = nx.community.louvain_communities(graph, weight="strength", seed=30, resolution=0.7)
    lookup_table = {}

    for com_id, com in enumerate(communities):
        for node in com:
            lookup_table[node] = com_id

    return lookup_table, communities


def dijkstra_path(graph, start, end):
    #Use Dijkstra's algo to find the lowest cost path between two actors
    #path is the inversion of strength so it should pick the highest quality paths 
    try:
        path = nx.dijkstra_path(graph, start, end, weight="cost")
        cost = nx.dijkstra_path_length(graph, start, end, weight="cost")
    except nx.NetworkXNoPath:
        # if no path exists
        path = None
        cost = math.inf
    except nx.NodeNotFound:
        # if start or end node doesn't exist
        path = None
        cost = math.inf
    return path, cost

def calculate_path_logic(graph, path, partition=None, lambda_decay=0.15, community_boost=2.2):
    #use the path and the communties to calculate the relational logic & confidence of the decsion 

    #catch any emptyp paths & return default values
    if not path:
        return {
            "sign": 0,
            "confidence": 0.0,
        } 
    
    #define vars
    relationship_score = 1
    intensity_score = 0.0
    same_community_edges = 0
    edge_details = []

    #iterate through given path & apply relationship logic 
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]

        stats = graph[u][v]
        goldstein = stats.get("goldstein", 0.0)
        #Apply social logic, ‘the friend of my friend is my friend’ (+ * + = +), 
        #‘the enemy of my enemy is my friend’ (- * - = +), and lastly ‘the enemy of my friend is my enemy’ (- * + =  -)
        sign = 1 if goldstein > 0 else -1 if goldstein < 0 else 0
        if sign != 0:
            relationship_score *= sign

        #Capture how strong & how well documented relation is for cofnidence scoring
        strength = max(float(stats.get("strength", 0.0)), 0.0)
        intensity_score += math.log1p(strength)
        if partition is not None and partition.get(u) == partition.get(v):
            same_community_edges += 1
    
    #calculate confidence values (based on itensity, length, and community structure)
    #more defined relationships better, long path worse, same community better-
    length = len(path) - 1
    length_decay = math.exp(-lambda_decay * length) 
    raw_score = intensity_score * length_decay * (community_boost * (same_community_edges / max(length, 1)))
    confidence = 1.0 / (1.0 + math.exp(-raw_score))

    return {
        "sign": relationship_score,
        "confidence": confidence,
    }

def main():
    graph = build_graph("bangladesh_news.json", exclude_terms=["bangladesh"])
    lookup, comm = build_communities(graph)
    path, cost = dijkstra_path(graph, "NEPAL", "HINDU")
    if path == None:
        print("No path found or nodes do not exist.")
        return
    result = calculate_path_logic(graph, path, partition=lookup)
    print (f"Path: {path}, Cost: {cost}, Sign: {result["sign"]}, Confidence: {result["confidence"]:.2f}")
        
if __name__ == "__main__":
    main()
    
    