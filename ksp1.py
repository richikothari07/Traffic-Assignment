import networkx as nx
import fast_graph as fgh

def node_objects(graph):
    return {i.node_id: i for i in graph.nodes}

def k_shortest_paths(graph, from_edge, to_edge, k):
    X = nx.shortest_simple_paths(graph, from_edge, to_edge)
    for counter, path in enumerate(X):
        print([i.node_id for i in path])
        if counter == k-1:
         break

netfile = "C:/Users/Richi Kothari/PycharmProjects/untitled/network_practice.xml"
G = fgh.create_network_graph(netfile, True, False)
node_obs = node_objects(G)
k_shortest_paths(G, node_obs['A0'], node_obs['A1'], 3)
