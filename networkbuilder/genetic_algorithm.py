from __future__ import absolute_import, division

import networkx as nx
import numpy as np
import random
import osmnx as ox
from routeGenerator import haversine

"""
This is written in somewhat pseudocode.
num_evolutions -> num_generations
num_generated_network_mutations_per_evolution -> num_mutations_per_generation
mutation_probabilities = list of probabilities for mutation that will be randomly selected from
    e.g. [0.1, 0.2, 0.3, 0.4, 0.5] would mean a 0.1 probability for 0 mutations, 0.2 probability for 1 mutation, etc


ASSUMPTION: Input is a jeepney route network, represented as a vector of routes, where each route is a vector of stops
"""

# This implementation takes only 2 parents from the whole generation and generates the population from them
# Instead of the what's in the paper that says the whole population will go through crossovers and mutations
# Cite Nayeem et al for GA with elitism and growing population size
def perform_genetic_algorithm(network_population, population_size, num_elites, num_generations, mutation_probability, 
                              num_mutations_probabilities, num_crossovers_probabilities, mutation_threshold_dist,
                              with_elitism=False, with_growing_population=False, num_mutations_per_generation=1):
    
    # Do this for the assigned number of generations for the GA
    for i in range(num_generations):

        new_network_population = []

        # Evaluate the fitness of each network in the population
        for network in network_population:
            network.fitness_score = compute_fitness_score(network)

        sorted_network_population = sorted(network_population, key=lambda x: x.fitness_score, reverse=True)
        
        # Most naive selection approach: get top two scoring networks as parents
        # But should be random with weighted probabilities so that elites are not always parents
        """
        parent1 = sorted_network_population[0]
        parent2 = sorted_network_population[1]
        """

        # Roulette Wheel Selection 
        # Chromosomes with higher fitness have a bigger "slice of the pie", but are not 
        # guaranteed to be selected as parents
        # This is to prevent premature convergence and ensure that the best networks are not always selected as parents
        max = sum([network.fitness_score for network in sorted_network_population])
        selection_p = [network.fitness_score / max for network in sorted_network_population]
        parent1_index = np.random.choice(sorted_network_population, 1, p=selection_p)
        parent1 = sorted_network_population[parent1_index]
        del selection_p[parent1_index]
        parent2_index = np.random.choice(np.setdiff1d(sorted_network_population, parent1), 1, p=selection_p)
        parent2 = sorted_network_population[parent2_index]

        # Take num_elites number of the best networks and automatically add them to the next generation
        if (with_elitism):
            for i in range(num_elites):
                new_network_population.append(sorted_network_population[i])

        # Ex: population_size = 20 and num_elites = 2
        # If no elitism and no growing population, then we will have 10 iterations to produce 20 in the next generation
        # Also, if elitism and growing population, then we will have 10 iterations to produce 22 in the next generation
        if (not with_elitism and not with_growing_population or with_elitism and with_growing_population):
            num_iterations = population_size / 2

        # If with elitism only, maintain the population size and account for the already added elites
        elif (with_elitism):  
            num_iterations = (population_size - num_elites) / 2

        # Generate the population
        for i in range(num_iterations):
            # Get 2 children from crossovers between the two parents
            child1, child2 = crossover_split_index(parent1, parent2)
            #child1, child2 = crossover_swap_routes(parent1, parent2, num_crossovers_probabilities)

            num_mutations = np.random.choice(len(num_mutations_probabilities), 1, p=num_mutations_probabilities)[0]

            for j in range(num_mutations):
                # Apply mutations to the children based on mutation probability hyperparameter
                if np.random.rand() < mutation_probability:
                    child1 = mutate(child1, mutation_threshold_dist)
                if np.random.rand() < mutation_probability:
                    child2 = mutate(child2, mutation_threshold_dist)
            
            # Add the children to the new population
            new_network_population.append(child1)
            new_network_population.append(child2)

            """
            weird stuff here dont mind
            # Randomly select how many crossovers for this generation
            num_crossovers = np.random.choice(len(crossover_probabilities), 1, p=crossover_probabilities)[0]

            # Perform all crossovers 
            for i in range(num_crossovers):
                # Randomly select two networks from the population
                network1 = random.choice(network_population)
                network2 = random.choice(network_population)

                # Perform crossover on the two networks
                network1, network2 = crossover(network1, network2)

            # Perform mutations
            for network in network_population:
                # Randomly select how many mutations for this network
                # This should be more heavily weighted towards 0 mutations
                num_mutations = np.random.choice(len(mutation_probabilities), 1, p=mutation_probabilities)[0]

                # Perform all mutations
                if num_mutations > 0:
                    for i in range(num_mutations):
                        network = mutate(network)
            """
        # Assign to next generation
        network_population = new_network_population

    return network_population

# This crossover implementation splits both networks at an index and exchanges halves
# Assumes that ideally both networks have the same number of routes (same length)
def crossover_split_index(network1, network2):
    # Split both networks at a random index
    if len(network1) < len(network2):
        split_index = random.randint(0, len(network2))
    else:
        split_index = random.randint(0, len(network1))

    network1_left = network1[:split_index]
    network1_right = network1[split_index:]
    network2_left = network2[:split_index]
    network2_right = network2[split_index:]

    # Swap the right sides of the networks
    network1 = network1_left + network2_right
    network2 = network2_left + network1_right

    return network1, network2

# This crossover implementation randomly selects a route from each network and swaps them
# More similar to the previous thesis implementation
# num_crossovers_probabilities = list of probabilities for crossovers that will be randomly selected from
#    e.g. [0.1, 0.2, 0.3, 0.4, 0.5] would mean a 0.1 probability for 0 crossovers, 0.2 probability for 1 crossover, etc
def crossover_swap_routes(network1, network2, num_crossovers_probabilities):
    num_crossovers = np.random.choice(len(num_crossovers_probabilities), 1, p=num_crossovers_probabilities)[0]

    for i in range(num_crossovers):
        # Randomly select a route from each network
        route1 = random.choice(network1.items())
        route2 = random.choice(network2.items())

        # Swap the routes
        network1[route1[0]] = route2[1]
        network2[route2[0]] = route1[1]

    return network1, network2


# Modify the stop connections of a random route in the network
# Randomly select a route and randomly select a stop in that route
# Then randomly select another stop that is a not too far from the selected stop based on threshold
# Swap connections with that stop
def mutate(network, threshold_dist):
    # Randomly select a route
    random_route = np.random.choice(network.items())

    # Randomly select a stop in the route
    random_stop_index = np.random.choice(len(random_route))
    random_stop = random_route[random_stop_index]

    # Will try searching for a random stop 50 times (arbitrary)
    for i in range(50):
        other_random_route = np.random.choice(network.items())
        other_random_stop_index = np.random.choice(len(other_random_route))
        other_random_stop = other_random_route[other_random_stop_index]

        # Uses the haversine formula but this might screw things up,
        # change distance formula as necessary
        if haversine(random_stop, other_random_stop) < threshold_dist:
            # Swap connections
            random_route[random_stop_index] = other_random_stop
            other_random_route[other_random_stop_index] = random_stop
            break

    return network


"""
COPILOT GENERATED CODE
def perform_genetic_algorithm(population_size, generations, mutation_rate, crossover_rate, selection_rate, fitness_function, crossover_function, mutation_function, selection_function, initial_population=None, verbose=False):
    
    Perform a genetic algorithm on a population of networks.

    Parameters
    ----------
    population_size : int
        The number of networks in the population.
    generations : int
        The number of generations to run the genetic algorithm for.
    mutation_rate : float
        The probability of a mutation occurring.
    crossover_rate : float
        The probability of a crossover occurring.
    selection_rate : float
        The proportion of the population to select for the next generation.
    fitness_function : function
        The function to evaluate the fitness of a network.
    crossover_function : function
        The function to perform crossover on two networks.
    mutation_function : function
        The function to perform mutation on a network.
    selection_function : function
        The function to select networks for the next generation.
    initial_population : list of nx.Graphs
        The initial population of networks. If None, a random population is generated.
    verbose : bool
        Whether to print information about the genetic algorithm.

    Returns
    -------
    list of nx.Graphs
        The final population of networks.
    
    if initial_population is None:
        population = [nx.erdos_renyi_graph(100, 0.1) for i in range(population_size)]
    else:
        population = initial_population

    for generation in range(generations):
        if verbose:
            print("Generation", generation)
        fitnesses = [fitness_function(network) for network in population]
        if verbose:
            print("Mean fitness:", np.mean(fitnesses))
        selected_population = selection_function(population, fitnesses, selection_rate)
        new_population = []
        while len(new_population) < population_size:
            if random.random() < crossover_rate:
                parent1, parent2 = random.sample(selected_population, 2)
                child1, child2 = crossover_function(parent1, parent2)
                new_population.append(child1)
                new_population.append(child2)
            else:
                new_population.append(random.choice(selected_population))
        for i in range(len(new_population)):
            if random.random() < mutation_rate:
                new_population[i] = mutation_function(new_population[i])
        population = new_population

    return population
"""