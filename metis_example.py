import networkx as nx
import metis

if __name__ == "__main__":
    G = nx.Graph()
    G.add_edges_from([(0, 1), (0, 2), (0, 3), (1, 2), (3, 4)])

    # set graph weight
    for i, value in enumerate([1, 5, 10, 2, 4]):
        G.nodes[i]['node_value'] = value

    G.graph['node_weight_attr'] = 'node_value'

    # Graph partitioning by metis
    (cut, parts) = metis.part_graph(G, 2)

    # result: [1, 0, 1, 0, 0]
    print(parts)