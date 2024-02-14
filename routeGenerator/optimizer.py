from __future__ import absolute_import, division

import networkx as nx
import numpy as np
import random
import routegenerator as ru


from preprocessor.utils import get_location_road_graph
from routegenerator.computations import generate_route_network



def perform_genetic_algorithm(stop_nodes, road_snapped_network,
                              max_walking_dist, num_evolutions, num_generated_network_mutations_per_evolution,
                              route_mutation_probabilities,
                              num_failure_removal, weight_random_failure, weight_targeted_failure, weight_gyration):
    location_road_graph = get_location_road_graph()

    for i in range(num_evolutions):
        num_mutations = np.random.choice(len(route_mutation_probabilities), 1, route_mutation_probabilities)[0]

        mutations = []
        for j in range(num_generated_network_mutations_per_evolution):
            # if num_mutations > 0 then randomly select n (which is ALSO EQUAL to num_mutations)
            #  routes to be replaced by a new route
            # replace the routes with the newly generated routes
            # append the modified network to the mutations list
            if num_mutations > 0:
                mutation_route_network = list(road_snapped_network)
                new_route_network = generate_route_network(stop_nodes, max_walking_dist, num_mutations)
                for i in range(0, num_mutations):
                    selected_route_index = np.random.randint(len(road_snapped_network))
                    mutation_route_network[selected_route_index] = new_route_network[i]
                    mutation_route_network = ru.utils.snap_route_network_to_road(mutation_route_network, output_graph=True,
                                                                    location_road_graph=location_road_graph)
            mutations.append(mutation_route_network)

        # pick the highest scoring mutation among the num_generated_network_mutations_per_evolution
        mutations.append(ru.snap_route_network_to_road(road_snapped_network, output_graph=True))
        road_snapped_network = select_highest_scoring_mutation(mutations, num_failure_removal)

    return road_snapped_network


def select_random_routes(route_network, num_routes):
    return random.sample(route_network, num_routes)


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

    # return weighted_radius_of_gyration - weighted_random_failure_robustness - weighted_targeted_failure_robustness
    return weighted_radius_of_gyration


def compute_random_failure_robustness(road_snapped_network_graph, num_removals):
    print(road_snapped_network_graph)
    for i in range(num_removals):
        selected_node = random.choice(road_snapped_network_graph.nodes())
        road_snapped_network_graph.remove_node(selected_node)

    diameter, avg_path_length, giant_component_fraction = compute_network_statistics(road_snapped_network_graph)
    return compute_failure_robustness(road_snapped_network_graph, diameter)


def compute_network_statistics(road_snapped_network_graph):
    path_lengths = get_path_lengths(road_snapped_network_graph)
    print(path_lengths)
    avg_path_length = np.mean(path_lengths)
    max_path_length = max(path_lengths)

    network_size = len(path_lengths)
    gcc = sorted(nx.connected_component_subgraphs(road_snapped_network_graph), key=len, reverse=True)
    giant_component_fraction = float(float(gcc[0].order()) / float(network_size))
    return max_path_length, avg_path_length, giant_component_fraction


def compute_failure_robustness(road_snapped_network_graph, max_path_length):
    return float(max_path_length) / float(len(road_snapped_network_graph) - 1)


def get_path_lengths(snapped_road_network_graph):
    return [sum(nx.single_source_shortest_path_length(snapped_road_network_graph, n).values())
            for n in snapped_road_network_graph]


def compute_targeted_failure_robustness(road_snapped_network_graph, num_removals):
    for i in range(num_removals):
        node_degrees = road_snapped_network_graph.degree()
        max_degree = max(node_degrees.values())
        print(node_degrees)
        max_degree_node = get_node_with_degree(node_degrees, max_degree)
        road_snapped_network_graph.remove_node(max_degree_node)

    diameter, avg_path_length, giant_component_fraction = compute_network_statistics(road_snapped_network_graph)
    return compute_failure_robustness(road_snapped_network_graph, diameter)


def get_node_with_degree(node_degrees, degree):
    print(type(node_degrees))
    print(node_degrees)
    for k, v in node_degrees.iteritems():
        if v == degree:
            return k
    return None


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


def _create_weighted_adjacency_matrix(graph):
    w = 10
    adjacency_matrix = {}

    for k_x, v_x in graph.nodes_iter(data=True):
        for k_y, v_y in graph.nodes_iter(data=True):
            if nx.has_path(graph, k_x, k_y):
                shortest_path_nodes = nx.shortest_path(graph, k_x, k_y)
                accumulated_distance = 0.0

                if len(shortest_path_nodes) > 1:
                    for i in range(0, len(shortest_path_nodes) - 1):
                        edge = graph.get_edge_data(shortest_path_nodes[i], shortest_path_nodes[i + 1]).get('dist')
                        accumulated_distance = float(accumulated_distance) + float(edge)

                    adjacency_matrix[(str(k_x), str(k_y))] = accumulated_distance
                else:
                    adjacency_matrix[(str(k_x), str(k_y))] = 0
            elif not nx.has_path(graph, k_x, k_y):
                coordinate1 = (v_x["lat"], v_x["lon"])
                coordinate2 = (v_y["lat"], v_y["lon"])
                adjacency_matrix[(str(k_x), str(k_y))] = euclidean(coordinate1, coordinate2) * w
            elif k_x == k_y:
                adjacency_matrix[(str(k_x), str(k_y))] = 0

    return adjacency_matrix


def euclidean(x, y):
    sum_square = 0.0
    for i in range(len(x)):
        sum_square += (x[i] - y[i]) ** 2

    return sum_square ** 0.5


def get_nodes_shortest_path(shortest_path_nodes, graph):
    new_graph = nx.Graph()

    for k_y, v_y in graph.nodes_iter(data=True):
        for elem in shortest_path_nodes:
            if elem == k_y:
                new_graph.add_node(k_y, lat=v_y.get('lat'), lon=v_y.get('lon'), route_id = v_y.get('route_id'))

    return graph


def _get_no_of_transfers(graph):
    temp = []
    p = graph.copy()
    no_of_tranfer = 0

    for k_y, v_y in p.nodes_iter(data=True):
        if (len(p.nodes()) > 1):
            if str(v_y.get("route_id")) not in temp:
                temp.append(str(v_y.get("route_id")))
            no_of_transfer = len(temp)-1
        else:
            no_of_tranfer = 0

    return no_of_tranfer
