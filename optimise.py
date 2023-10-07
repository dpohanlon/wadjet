import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams["axes.facecolor"] = "FFFFFF"
rcParams["savefig.facecolor"] = "FFFFFF"
rcParams["xtick.direction"] = "in"
rcParams["ytick.direction"] = "in"

rcParams.update({"figure.autolayout": True})

rcParams["figure.figsize"] = (16, 9)

from ortools.sat.python import cp_model

import networkx as nx


def optimisePlacement(connected_pairs, sequential_groups):

    # Create a model.
    model = cp_model.CpModel()

    # Number of strips
    num_strips = (
        max(
            max(max(pair) for pair in connected_pairs),
            max(max(group) for group in sequential_groups),
        )
        + 1
    )

    # Variables
    indices = [
        model.NewIntVar(0, num_strips - 1, "index_{}".format(i))
        for i in range(num_strips)
    ]

    # All different constraint
    model.AddAllDifferent(indices)

    # Add sequential constraints
    for group in sequential_groups:
        for i in range(len(group) - 1):
            model.Add(indices[group[i]] + 1 == indices[group[i + 1]])

    # Objective Function: Minimize total connection length.
    abs_diff_vars = []
    for pair in connected_pairs:
        abs_diff = model.NewIntVar(
            0, num_strips - 1, "abs_diff_{}_{}".format(pair[0], pair[1])
        )
        abs_diff_vars.append(abs_diff)

        # This creates the absolute difference.
        model.AddAbsEquality(abs_diff, indices[pair[0]] - indices[pair[1]])

    model.Minimize(sum(abs_diff_vars))

    # Solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        print("Objective value =", solver.ObjectiveValue())
        # for i in range(num_strips):
        # print('Strip', i, 'has index', solver.Value(indices[i]))
    else:
        print("The problem does not have an optimal solution.")

    return [solver.Value(indices[i]) for i in range(num_strips)]


def connectedComponentStrips(connections):

    G = nx.Graph()

    for node, neighbors in connections.items():
        for neighbor in neighbors:
            G.add_edge(node, neighbor)

    nx.draw_networkx(G)
    plt.savefig("circuit_graph.pdf")
    plt.clf()

    S = [G.subgraph(c).copy() for c in nx.connected_components(G)]
    strips = [list(s.nodes) for s in S]

    return strips


if __name__ == "__main__":

    # Define connected pairs. (s1, s2) implies strips s1 and s2 should be connected.
    connected_pairs = [(0, 1), (1, 2), (1, 3), (1, 4)]

    # Groups of strips that need to be sequential
    sequential_groups = [(1, 3, 4)]

    optimisePlacement(
        connected_pairs=connected_pairs, sequential_groups=sequential_groups
    )
