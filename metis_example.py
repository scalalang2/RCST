import numpy as np
import pymetis

if __name__ == "__main__":
    adjacency_list = [np.array([4, 2, 1]), # 0 번째 인덱스가 엮여 있는 것
                      np.array([0, 2, 3]),
                      np.array([4, 3, 1, 0]),
                      np.array([1, 2, 5, 6]),
                      np.array([0, 2, 5]),
                      np.array([4, 3, 6]),
                      np.array([5, 3])]
    weight_list = [
        1,
        2,
        3,
        4,
        5,
        6,
        7
    ]

    n_cuts, membership = pymetis.part_graph(2,
                                            adjacency=adjacency_list,
                                            vweights=weight_list)
    # n_cuts = 3
    # membership = [1, 1, 1, 0, 1, 0, 0]

    nodes_part_0 = np.argwhere(np.array(membership) == 0).ravel()  # [3, 5, 6]
    nodes_part_1 = np.argwhere(np.array(membership) == 1).ravel()  # [0, 1, 2, 4]

    print(nodes_part_0)
    print(nodes_part_1)