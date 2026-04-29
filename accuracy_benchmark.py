import csv
from collections import Counter
from graph_build import GraphBuilder
from network_analysis import build_communities, dijkstra_path, calculate_path_logic, build_graph



def evaluate(manual_sample_csv, confidence_threshold):
    # eval our algo using a munually labeled subset of the actor pairs (using current known relations)
    # apply confience filter based on communtiies 

    #build our graph
    graph = build_graph("bangladesh_news.json", exclude_terms=["bangladesh"])
    partition, x = build_communities(graph)
    
    #read in manual sample
    rows = []
    with open(manual_sample_csv, "r") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    
    correct = 0
    evaluated = 0 
    unfiltered_correct = 0
    unfitlered_evaluated = 0
    all_actual_labels = []
    filtered_actual_labels = []
    
    #loop through manuak smaple, run actual logic, comapre results and filter out low confidence predictions 
    for row in rows:
        #read in manual 
        actor1 = row["actor1"].strip()
        actor2 = row["actor2"].strip()
        actual = int(row["actual_relation"])
        all_actual_labels.append(actual)
        
        path, x = dijkstra_path(graph, actor1, actor2)
        
        #check if no path 
        if path is not None:
            result = calculate_path_logic(graph, path, partition=partition)
            predicted = result['sign']
            confidence = result['confidence']
        else:
            predicted = 0
            confidence = 0.0

        #unfiltered tracking
        unfitlered_evaluated += 1
        if predicted == actual:
            unfiltered_correct += 1
        
        #apply fitler
        if confidence < confidence_threshold:
            continue
        
        #log my results
        evaluated += 1
        filtered_actual_labels.append(actual)
        if predicted == actual:
            correct += 1
    
    #print out results 
    accuracy = correct / evaluated if evaluated > 0 else 0
    unfitlered_accuracy = unfiltered_correct / unfitlered_evaluated 
    print(f"Confidence threshold: {confidence_threshold}") 
    print(f"Evaluated: {evaluated} pairs")
    print(f"Correct: {correct}")
    print(f"Accuracy: {accuracy*100:.2f}%")
    print("----")
    print(f"Unfiltered Evaluated: {unfitlered_evaluated} pairs")
    print(f"Unfiltered Correct: {unfiltered_correct}")
    print(f"Unfiltered Accuracy: {unfitlered_accuracy*100:.2f}%") 

if __name__ == "__main__":
    evaluate("benchmark.csv", confidence_threshold=0.5)


