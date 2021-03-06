"""Robust Bayesian Committee Machine Regression"""

import numpy as np

from sklearn.cluster import Birch


def birch_cluster_partitioning(X, points_per_expert):
    """Return a list of lists each containing a partition of the indices of the
    data to be fit that is generated by splitting along clusters found via
    Birch clustering approach."""
    sample_sets = []
    num_samples = X.shape[0]
    indices = np.arange(num_samples)

    num_clusters = int(
            float(num_samples) / points_per_expert)
    birch = Birch(n_clusters=num_clusters, threshold=0.2)
    labels = birch.fit_predict(X)
    unique_labels = np.unique(labels)

    # Fill each inner list i with indices matching its label i
    for label in unique_labels:
        sample_sets.append([i for i in indices if labels[i] == label])
    return sample_sets


def random_partitioning(X, points_per_expert):
    """
    Return a list of lists each containing a random partition of the indices of
    the data to be fit.
    """
    sample_sets = []
    num_samples = X.shape[0]
    indices = np.arange(num_samples)

    np.random.shuffle(indices)

    for i in range(0, num_samples, points_per_expert):
        if (i + points_per_expert) >= num_samples:
            points_per_expert = num_samples - i
        sample_sets.append(indices[i:i + points_per_expert])
    return sample_sets
