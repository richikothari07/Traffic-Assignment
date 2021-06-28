import networkx as nx
import fast_graph as fgh

def node_objects(graph):
    ''' Input - networkx graph
    Output - Node_Objects'''
    return {i.node_id: i for i in graph.nodes}

def k_shortest_paths(graph, from_edge, to_edge, k):
    ''' Input - networkx graph, starting edge of route, ending edge of route, k - no. of shortest paths'''
    X = nx.shortest_simple_paths(graph, from_edge, to_edge)
    for counter, path in enumerate(X):
        print([i.node_id for i in path])
        if counter == k-1:
         break

