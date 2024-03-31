import networkx as nx
import numpy as np
import random


def select_highest_scoring_mutation(candidate_road_snapped_networks, num_failure_removal,
                                    weight_random_failure, weight_targeted_failure, weight_radius_of_gyration):
    max_fitness_score = -np.inf
    max_candidate_route_snapped_network = None

    for n in candidate_road_snapped_networks:
        fitness_score = compute_fitness_score(n, num_failure_removal,
                                              weight_random_failure, weight_targeted_failure, weight_radius_of_gyration)
        if fitness_score > max_fitness_score:
            max_fitness_score = fitness_score
            max_candidate_route_snapped_network = n

    return max_candidate_route_snapped_network

def compute_fitness_score(road_snapped_network_graph, num_failure_removal,
                          weight_random_failure, weight_targeted_failure, weight_radius_of_gyration):

    random_failure_robustness = compute_random_failure_robustness(road_snapped_network_graph, num_failure_removal)
    weighted_random_failure_robustness = weight_random_failure * random_failure_robustness

    targeted_failure_robustness = compute_targeted_failure_robustness(road_snapped_network_graph, num_failure_removal)
    weighted_targeted_failure_robustness = weight_targeted_failure * targeted_failure_robustness

    radius_of_gyration = compute_radius_of_gyration(road_snapped_network_graph, 100, weight_radius_of_gyration)
    weighted_radius_of_gyration = weight_radius_of_gyration * radius_of_gyration

    # Will use this return for now to utilize target and random failure nodes 
    return weighted_radius_of_gyration - weighted_random_failure_robustness - weighted_targeted_failure_robustness
    # return weighted_radius_of_gyration

def compute_random_failure_robustness(road_snapped_network_graph, num_removals):
    print(road_snapped_network_graph)
    for i in range(num_removals):
        selected_node = random.choice(road_snapped_network_graph.nodes())
        road_snapped_network_graph.remove_node(selected_node)

    diameter, avg_path_length, giant_component_fraction = compute_network_statistics(road_snapped_network_graph)
    return compute_failure_robustness(road_snapped_network_graph, diameter)

def compute_targeted_failure_robustness(road_snapped_network_graph, num_removals):
    for i in range(num_removals):
        node_degrees = road_snapped_network_graph.degree()
        max_degree = max(node_degrees.values())
        print(node_degrees)
        max_degree_node = get_node_with_degree(node_degrees, max_degree)
        road_snapped_network_graph.remove_node(max_degree_node)

    diameter, avg_path_length, giant_component_fraction = compute_network_statistics(road_snapped_network_graph)
    return compute_failure_robustness(road_snapped_network_graph, diameter)

def compute_failure_robustness(road_snapped_network_graph, max_path_length):
    return float(max_path_length) / float(len(road_snapped_network_graph) - 1)

def compute_radius_of_gyration(road_snapped_network_graph, num_random_values, weight):
    return _get_efficiency_sum(road_snapped_network_graph, num_random_values, weight)

def _get_efficiency_sum(graph, no_of_random_values, weight):
    efficiency_sum = 0.0
    weighted_list = _get_yweighted_list(graph, weight)
    efficiency_sum_list = random.sample(weighted_list.keys(), no_of_random_values)

    for k_x, k_y in efficiency_sum_list:
         temp = weighted_list[(str(k_x), str(k_y))]
         efficiency_sum = float(temp) + float(efficiency_sum)

    return efficiency_sum

def _get_yweighted_list(graph, weight):
    dp = _get_distance_individual(graph)
    dw = _get_total_weighted_distance(graph, weight)
    Y = {}

    for k_x, v_x in graph.nodes_iter(data=True):
        for k_y, v_y in graph.nodes_iter(data=True):
            if nx.has_path(graph, k_x, k_y):
                Y[(str(k_x), str(k_y))] = float(dp[(str(k_x), str(k_y))])/float(dw)
            else:
                Y[(str(k_x), str(k_y))] = 0.0

    return Y

def _get_distance_individual(graph):
    T = {}

    for k_x, v_x in graph.nodes_iter(data=True):
        for k_y, v_y in graph.nodes_iter(data=True):
            if nx.has_path(graph, k_x, k_y):
                shortest_path_nodes = nx.shortest_path(graph, k_x, k_y)
                accumulated_distance = 0.0
                if(len(shortest_path_nodes) > 1):
                    for i in range(0, len(shortest_path_nodes) - 1):
                        edge = graph.get_edge_data(shortest_path_nodes[i], shortest_path_nodes[i + 1]).get('dist')
                        print(edge)
                        accumulated_distance = float(accumulated_distance) + float(edge)
                    T[(str(k_x),str(k_y))] = accumulated_distance
                else:
                    T[(str(k_x), str(k_y))] = 0
            else:
                T[(str(k_x), str(k_y))] = 0

    return T

# new gettwd does not use weighted adjacency matrix
def _get_total_weighted_distance(graph, weight):
    # A = _create_weighted_adjacency_matrix(graph)
    dp = _get_distance_individual(graph)
    w = weight
    total_weighted_distance = 0.0
    T = {}
    for k_x, v_x in graph.nodes_iter(data=True):
        for k_y, v_y in graph.nodes_iter(data=True):
            if nx.has_path(graph, k_x, k_y):
                shortest_path_nodes = nx.shortest_path(graph, k_x, k_y)
                g = get_nodes_shortest_path(shortest_path_nodes, graph)
                T = _get_no_of_transfers(g)
                a = 1.0
            elif not nx.has_path(graph, k_x, k_y):
                a = 10.0

            b = float(dp[(str(k_x), str(k_y))])
            weighted_distance = a * b + (w * T)
            total_weighted_distance = float(total_weighted_distance) + float(weighted_distance)

    return total_weighted_distance

def compute_network_statistics(road_snapped_network_graph):
    path_lengths = get_path_lengths(road_snapped_network_graph)
    print(path_lengths)
    avg_path_length = np.mean(path_lengths)
    max_path_length = max(path_lengths)

    network_size = len(path_lengths)
    gcc = sorted(nx.connected_component_subgraphs(road_snapped_network_graph), key=len, reverse=True)
    giant_component_fraction = float(float(gcc[0].order()) / float(network_size))
    return max_path_length, avg_path_length, giant_component_fraction

def get_path_lengths(snapped_road_network_graph):
    return [sum(nx.single_source_shortest_path_length(snapped_road_network_graph, n).values())
            for n in snapped_road_network_graph]


