import xml.etree.ElementTree as ET
import pandas as pd
from scipy.sparse import csr_matrix

def find_routes(edge_id, routes_file):
    """
        edge_id = J081_L03
        routes_file = xml file
        Output:
            ["J082_L01 -J082_L04 J081_L03 -J081_L02",
             "J082_L01 ... -J081_L03 -J081_L02",
             "J082_L10 -J082_L04 J081_L03 -J081_L11"]
    """

    root = ET.parse(routes_file).getroot()
    routes = []
    for type_tag in root.findall('vehicle/route'):
        route = type_tag.get('edges')
        if edge_id in route:
            routes.append(route)

    return routes


def find_zones(routes_file, taz_file, edge_id):
    """
        {
            taz_0:{taz_1:1, taz_2:0,,,,},
        {taz_1:{}}
        }

        matrix
    """
    alist = find_routes(edge_id, routes_file)
    root = ET.parse(taz_file).getroot()
    source = {}
    sink = {}
    zones = []
    list_of_zones = []
    # find the sink ids and store in empty dictionary sink
    for type_tag, type_tag1 in zip(root.findall('taz/tazSink'), root.findall('taz')):
        zone1 = type_tag1.get('id')
        edge_end = type_tag.get('id')
        sink[edge_end] = zone1
    # find the source ids and store in empty dictionary source
    for type_tag, type_tag1 in zip(root.findall('taz/tazSource'), root.findall('taz')):
        edge_start = type_tag.get('id')
        zone2 = type_tag1.get('id')
        source[edge_start] = zone2
    # common dictionary containing all sink and source ids with their respective edge ids
    taz_ids = {**sink, **source}
    # find the edge_Source and edge_Sink from the routes and store in list
    for i in range(len(alist)):
        routes = alist[i]
        edge_list = routes.split()
        a = [edge_list[0], edge_list[-1]]
        zones.append(a)
    # replace the edge ids with their taz ids and store in list
    for i in zones:
        C = (pd.Series(i)).map(taz_ids)
        D = list(C)
        list_of_zones.append(D)

    # matrix formation
    origin = []
    destination = []
    for i in list_of_zones:
        origin.append(i[0])
        destination.append(i[1])
    dictionary = {'origin': list(origin), 'destination': list(destination)}
    df = pd.DataFrame(dictionary)
    matrix = df.pivot_table(values='destination', index="origin", columns='destination',
           fill_value=0, aggfunc=len)

    # Sparse matrix
    S = csr_matrix(matrix)

    return S

def find_all_matrices(edges_list, routes_file, taz_file):
    """

    :param edges_list: list of edges
    :param routes_file: routes file
    :param taz_file: taz file
    :return: list of matrices
    """
    matrix_list = []
    for i in edges_list:
        matrix = find_zones(routes_file, taz_file, i)
        matrix_list.append(matrix)

    return matrix_list






