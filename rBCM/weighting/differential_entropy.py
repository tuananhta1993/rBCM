"Weighting and combination of sets of predictions into a single prediction."

import numpy as np


def differential_entropy_weighting(predictions, sigma, prior_std):
    """Weight the predictions of experts and reduce to a single prediction.

    This formula can be described as:
        The differential entropy between the prior predictive distribution and
        the posterior predictive distribution.

    See 'jmlr.org/proceedings/papers/v37/deisenroth15.pdf' page 5 for a better
    description of this weighting and the exact formulas.

    Args:
        predictions : array, shape = (n_locations, y_num_columns, num_experts)
            The values predicted by each expert

        sigma : array, shape = (n_locations, num_experts)
            The uncertainty of each expert at each location

        prior_std : float
            The standard deviation of the prior used to fit the GPRs

    Returns:
        preds : array, shape = (n_locations, y_num_columns)
            Mean of predictive distribution at query points

        rbcm_var : array, shape = (n_locations, )
            Variance of predictive distribution at query points
    """
    # We sometimes can be given zeros here and cannot deal with it, so set any
    # zeros to a very small number.
    sigma[sigma == 0] = 1E-9
    var = np.power(sigma, 2)
    log_var = np.log(var)
    prior_var = np.power(prior_std, 2)
    log_prior_var = np.repeat(np.log(prior_var), sigma.shape[0])

    # Compute beta weights, page 5 right hand column
    beta = 0.5 * (log_prior_var[:, np.newaxis] - log_var[:, :])

    # Combine the experts according to their beta weight
    preds_old, var_old = _combine(predictions, var, beta, prior_var)
    return preds_old, var_old


def _combine(predictions, var, beta, prior_var):
    """Calculate a single prediction from many with the given beta weights.

    This should be able to accept any general measure of uncertainty, beta.

    This is the OLD version of this function which is based on naive loops, but
    is easier to understand logically and check for correctness. This (hopeful)
    correctness is used to verify correctness of the new version which utilizes
    numpy's einsum() function for performance.

    Args:
        predictions : array-like, shape = (n_locations, n_features, n_experts)
            Values predicted by some sklearn predictor that offers var as well

        var : array-like, shape = (n_locations, n_experts)
            Variances corresponding to the predictions

    Returns:
        predictions : array, shape = (n_locations, n_features)

        rbcm_var : array, shape = (n_locations)
    """
    inv_var = 1 / var
    inv_prior_var = 1 / prior_var
    num_locations = predictions.shape[0]
    num_features = predictions.shape[1]
    num_experts = predictions.shape[2]

    # Compute Eq. 22
    left_term = np.zeros(num_locations)
    right_term = np.zeros(num_locations)

    for loc in range(num_locations):
        left_term[loc] = np.dot(beta[loc, :], inv_var[loc, :])
        right_term[loc] = inv_prior_var * (1 - np.sum(beta[loc, :]))

    rbcm_inv_var = left_term + right_term

    # Computer Eq. 21
    rbcm_var = 1 / rbcm_inv_var
    rbcm_var = rbcm_var
    preds = np.zeros((num_locations, num_features))

    for loc in range(num_locations):
        for feat in range(num_features):
            summation = 0
            for exp in range(num_experts):
                summation += beta[loc, exp] * inv_var[loc, exp] * predictions[loc, feat, exp]
            preds[loc, feat] = summation

    for loc in range(preds.shape[0]):
        preds[loc, :] = rbcm_var[loc] * preds[loc, :]

    return preds, rbcm_var
