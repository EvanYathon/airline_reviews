# bootstrap_skmodel.py
#
# @author: Evan Yathon
#
# May 27th 2019
#
# This script contains two functions.  The first is bootstrap_model,
# a function that creates bootstrapped coefficients from an input
# sklearn model.  It is set up to run in parallel with `joblib`.
# The second function makes use of bootstrap_model and runs it the
# specified number of times to get an estimate of the sampling
# distribution of each coefficient in order to get estimates of
# standard error.
#


from joblib import Parallel, delayed
import pandas as pd
import numpy as np

def bootstrap_model(skmodel, skmodel_args, X, y, random_state):
    """
    Function for retrieving bootstrapped model coefficients in parallel

    Parameters:
        skmodel (sci-kit learn model object): for example, LogisiticRegression
        skmodel_args (dict): dictionary of argument value pairs to unpack for use in skmodel
        X (pandas dataframe or numpy array): dataframe/array of predictors
        Y (pandas dataframe or numpy array): dataframe/array of response values
        random_state (int): random state to bootstrap from

    Return:
        array of coefficients for each feature in X
    """

    if not (isinstance(X, pd.core.frame.DataFrame) or isinstance(X, np.ndarray)) and not (isinstance(y, pd.core.frame.DataFrame) or isinstance(y, np.ndarray)):
        raise TypeException("X and y must both be pandas dataframes.  Note that geopandas\
        dataframes must first be coerced into pandas dataframes.")

    # coerce the

    # initiate the model
    model = skmodel(**skmodel_args)

    # get useful info for later use
    feature_names = [str(col) for col in X.columns]
    response_name = [str(col) for col in y.columns]
    n_rows, n_features = X.shape

    # merge X and y
    merged = pd.concat([pd.DataFrame(X), pd.DataFrame(y)], axis = 1)

    # create bootstrap sample
    bootstrap = merged.sample(n_rows, replace = True, random_state = random_state)

    # separate into X and y again for use in model fitting
    X_bootstrap = bootstrap.drop(columns = response_name)
    y_bootstrap = bootstrap[response_name]

    # fit model with specified parameters
    model.fit(X_bootstrap, y_bootstrap)

    # get bootstrapped coefficients and wrangle them into the correct shape
    coefs = model.coef_.flatten()

    # return coefficient estimates for this bootstrap
    return coefs


def parallel_bootstrap(skmodel, skmodel_args, X, y, n_bootstraps, n_jobs = -1):
    """
    Wrapper for bootstrap_model to create multiple bootstrapped coefficients
    in parallel.

    Parameters:
        skmodel (sci-kit learn model object): for example, LogisiticRegression
        skmodel_args (dict): dictionary of argument value pairs to unpack for use in skmodel
        X (pandas dataframe): dataframe of predictors
        Y (pandas dataframe): dataframe of response values
        n_bootstraps (int): number of bootstraps to perform and estimate
                            coeffients from
        n_jobs (int): number of threads/cores to use

    Return:
        n_bootstrap arrays of coefficients for each feature in X

    Example usage:

        # load and condition some data
        from sklearn.datasets import load_breast_cancer
        bc = load_breast_cancer()
        X = pd.DataFrame(bc["data"])
        X.columns = bc.feature_names
        y = pd.DataFrame(bc["target"])
        # reduce to less features for this example
        X = X.iloc[:,0:5]

        params = {"solver" : "lbfgs"}
        parallel_bootstrap(LogisticRegression, skmodel_args = params,
                                        X = X, y = y, n_bootstraps = 500)
    """

    bootstrapped_coefs = Parallel(n_jobs = n_jobs, backend = "loky")(
        delayed(bootstrap_model)(skmodel, skmodel_args, X, y, state) for state in range(n_bootstraps))

    return np.array(bootstrapped_coefs)
