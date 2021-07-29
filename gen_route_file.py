import networkx as nx
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
import fast_graph as fgh
import fast_net as ffn
import itertools
import sqlite3
import random


def flatten(t):
    return [item for sublist in t for item in sublist]

def node_objects(graph):
    """
    :param graph: networkx graph
    :return: node objects
    """
    return {i.node_id: i for i in graph.nodes}

def k_shortest_paths(graph, from_edge, to_edge, k):
    """
    :param graph: networkx graph
    :param from_edge: starting node
    :param to_edge: ending node
    :param k: number of shortest paths
    :return: list of k shortest paths
    """
    # gives all paths between from_edge and to_edge
    X = nx.shortest_simple_paths(graph, from_edge, to_edge)
    lists = []
    # store k shortest paths in lists
    for counter, path in enumerate(X):
        s = ([i.node_id for i in path])
        lists.append(s)
        if counter == k - 1:
            break
    return lists

def nested_dict_pairs_iterator(zones):
    for key, value in zones.items():
        if isinstance(value, dict):
            for pair in nested_dict_pairs_iterator(value):
                yield key, *pair
        else:
            yield key, value

def find_ksp_routes(k, tazfile, network_file):
    """
    :param k: number of shortest paths
    :param tazfile: taz file
    :param network_file: network file
    :return: ksp_route_matrix
            zone X zone matrix
            each cell has "k" shortest routes
    """
    # gives a list of source id and sink id for every zone
    taz_file = []
    for pair in nested_dict_pairs_iterator(tazfile):
        taz_file.append(list(pair))

    # stores edge ids with its from_edge and to_edge
    dictionary = {}
    root = ET.parse(network_file).getroot()
    for edge in root.findall('edge'):
        rank = edge.get('id')
        name = edge.get('from')
        name1 = edge.get('to')
        dictionary[rank] = {}
        dictionary[rank]['from'] = name
        dictionary[rank]['to'] = name1

    # convert edge id to node ids
    for i in taz_file:
        for key, value in dictionary.items():
            if i[2] == key:
                i[2] = value['from']

    # find k shortest path for each zone
    k_total = []
    zones = []
    for i in taz_file:
        if i[1] == 'source':
            from_edge = i[2]
            zon = i[0]

            for j in taz_file:
                if j[1] == 'sink':
                    to_edge = j[2]
                    G = fgh.create_network_graph(network_file, True, False)
                    node_obs = node_objects(G)
                    ksp = k_shortest_paths(G, node_obs[from_edge], node_obs[to_edge], k)
                    k_total.append(ksp)
                    zones.append(zon)

    # convert node ids to edge ids
    for i in k_total:
        for s in i:
            for j in range(len(s) - 1):
                for key, value in dictionary.items():
                    if value['from'] == s[j] and value['to'] == s[j + 1]:
                        s[j] = key

            del s[-1]

    # matrix formation
    list1 = zones
    list2 = k_total

    combo = {}
    for i in range(len(list1)):
        if list1[i] in combo:
            combo[list1[i]].append(list2[i])
        else:
            li = [list2[i]]
            combo[list1[i]] = li

    c = []
    for key in tazfile:
        c.append(key)

    df = pd.DataFrame(combo, index=c)
    return df

def distribute(costs):
    """
        costs =[10,20,30]
        output =[0.5,0.3,0.2]
    """
    summation = sum(costs)
    for i in range(len(costs)):
        costs[i] = costs[i] / summation
    return costs[::-1]

def assign_vehs_to_routes(Tij, ksp_route_matrix, netfile, ksp_route_matrix_copy):
    """
    Modified ksp_route_matrix
        TO zone1 zone2 zone3 ...n
FROM
zone1
zone1     [route1:30, route2:70]
zone2
zone3
...n
    """
    # new_df = ksp_route_matrix.copy(deep=True) (it doesn't work - on changing this the original dataframe also changes)
    # Please suggest something for this

    # creates a dictionary of edge as key and their respective weights as value
    weights = {}
    nod = ffn.create_node_objects_dict(netfile)
    eod = ffn.create_edge_objects_dict(netfile, nod)
    for edge in eod:
        weight = eod[edge].get_travel_time()
        weights[edge] = weight

    ratios = []
    for m in ksp_route_matrix_copy:
        for l in ksp_route_matrix_copy[m]:
            for j, i in enumerate(l):
                # replaces the edge with it's weight
                s = list(map(lambda x: weights[x], i))
                # creates total weight of a particular route and replaces the route
                total = sum(s)
                l[j] = total
            # creates cost ratio for every route
            ratio = distribute(l)
            # creates a list of all cost ratios
            ratios.append(ratio)
    # convert Tij matrix into list
    tij = Tij.tolist()
    # flatten Tij
    merged = list(itertools.chain(*tij))
    # list containing vehicles divided according to cost function and Tij
    vehicles = []
    for i, j in zip(merged, ratios):
        s = pd.Series(j)
        assign = (s * i).tolist()
        vehicles.append(assign)
    # appending vehicles distribution and routes list
    G1 = itertools.chain(*vehicles)
    for m in ksp_route_matrix:
        for w in ksp_route_matrix[m]:
            [i.append(j) for i, j in zip(w, G1)]

    # matrix of list containing routes and vehicles assigned to that route as last element
    return ksp_route_matrix


def find_pij(modified_ksp_route_matrix, edge_id):
    """
        n X n with ratios
    """
    # replaces list of ksp_route_matrix with ratio of vehicles assigned if particular edge is present in the list
    # else replaces it with 0
    for m in modified_ksp_route_matrix:
        for j in modified_ksp_route_matrix[m]:
            for i in range(len(j)):
                    if edge_id in j[i]:
                        j[i] = (j[i][-1])/100
                    else:
                        j[i] = 0
    # adds all the ratios for the particular zone and creates pij
    for i in modified_ksp_route_matrix:
        a = 0
        for j in modified_ksp_route_matrix[i]:
            modified_ksp_route_matrix.iloc[a][i] = round((sum(j)), 2)
            a = a+1

    return modified_ksp_route_matrix


def generate_route_file(mod_ksp_routes_matrix):

    root = ET.Element("routes")
    root.text = "\n"
    # converting matrix to list which contains the route and no. of vehicles(last element)
    mk = mod_ksp_routes_matrix.values.tolist()
    m = mk[0]
    for i in m:
        p = 0
        for j in i:
            # y is the route for that particular vehicle
            u = j.copy()
            u.pop()
            y = ' '.join(u)
            vehicles = ['Car', 'Bike', 'Truck']
            proportions = [0.3, 0.6, 0.1]
            prp = [x*100 for x in proportions]
            sample = [item for item, count in zip(vehicles, prp) for i in range(int(count))]
            # assigning depart time(total time = 10 min, distributed among 100 vehicles) and route to each vehicle
            for k in range(round(j[-1])):
                v = ET.Element("vehicle")
                root.append(v)
                v.set('type', random.choice(sample))
                v.set('depart', "{:.2f}".format(p))
                p = p + 0.1
                v.tail = "\n"
                v.text = "\n"
                route = ET.SubElement(v, "route")
                route.set('edges', y)
                route.tail = "\n"

    tree = ET.ElementTree(root)
    tree.write("Route_file.xml", encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":

    network_file = "C:/Users/Richi Kothari/PycharmProjects/untitled/network_practice.xml"
    k = 3
    Tij = np.full((6, 6), 100)
    zone = {"zone1": {"source": 'A8A9', "sink": 'A9A8'},
            "zone2": {"source": 'E4E5', "sink": 'E5E4'},
            "zone3": {"source": 'H0H1', "sink": 'H1H0'},
            "zone4": {"source": 'left5A5', "sink": 'A5left5'},
            "zone5": {"source": 'B8C8', "sink": 'C8B8'},
            "zone6": {"source": 'E7F7', "sink": 'F7E7'}}
    ksp_route_matrix = find_ksp_routes(k, zone, network_file)
    ksp_route_matrix_copy = find_ksp_routes(k, zone, network_file)
    mod_ksp_routes_matrix = assign_vehs_to_routes(Tij, ksp_route_matrix, network_file, ksp_route_matrix_copy)

    generate_route_file(mod_ksp_routes_matrix)
