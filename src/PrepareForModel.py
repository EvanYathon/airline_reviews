# PrepareForModel.py
#
# @author: Evan Yathon
#
# May 8th 2019
#
# This script contains a class that prepares a data frame for modelling.  It
# does this by one hot encoding specified variables, dropping one column that
# is chosen by index or by name.  This is specifically suited for regression
# modules from the statsmodels package.
#
# Example usage:
# example_data = {"id": [1,2,3,4,5,6,7,8],
#                "price":[22., 21., 17., 35.,12.,17.,18.,19.],
#               "colour": ['ruby', 'white', 'red', 'ruby','ruby','white', 'ruby', 'white'],
#               "type" : ["pinot_noir","gewurtz","cab_sauv","cab_sauv", "pinot_grigio", "pinot_noir", "chardonnay", "chardonnay"],
#               "target" : [0.,0.,1.,1.,0.,1.,1.,1.]}
#
# example_data = pd.DataFrame(example_data)
#
# # Do it the list way:
# foo = PrepareForModel(example_data)
# foo.make_dummy_df(["type","colour"], cat_to_drop = 0)
#
# # Do it the dict way:
# foo = PrepareForModel(example_data)
# foo.make_dummy_df({"type" : "pinot_noir", "colour" : "red"})

class PrepareForModel:

    """
    PrepareForModel prepares a dataframe with some categorical variable content
    for use in sci-kit learn or stats package regression or other models.

    Arguments:
        df (pd.DataFrame): dataframe that contains various features, some categorical

    Attributes:
        ref_levels (list): list of reference variables that are dropped from the dataframe.
    """

    def __init__(self, df):

        # ensure that df is in the form of a pandas dataframe
        if not isinstance(df, pd.DataFrame):
            raise Exception("the df argument should be a pandas dataframe class or subclass")

        self.df = df.copy()
        self.df_orig = df.copy()
        self.ref_levels = []

    def make_dummy_df(self, dummy_vars, cat_to_drop = 0, drop_cat = True, add_intercept = True):
        """
        Saves a pandas dataframe ready for statistical modelling with packages like statsmodel.
        Ensures that categorical variables are one hot encoded

        Arguments:
            dummy_vars (list or dict): can be a list of column names with columns to be converted to
                                       dummy variables.  Alternatively can be a dict with keys as
                                       column names to be converted to dummies, and values as the
                                       category to be dropped.
            cat_to_drop (int): if dummy_vars is type dict then this value will be ignored.  Otherwise
                               it is the index of the category to drop in each variable specified in
                               dummy_vars
            add_intercept (bool): whether to add an intercept column of 1s, default True
            drop_cat (bool): whether to drop a column that is being coverted to dummies, default True

        Return:
            Pandas Dataframe with selected variables one hot encoded and an intercept column

        Examples:
        ## example_data = {"id": [1,2,3,4],
                        "price":[22., 21., 17., 35.],
                        "colour": ['red', 'white', 'ruby', 'white'],
                        "type" : ["cab sauv", "pinot grigio", "pinot noir", "chardonnay"]}

        ## example_data = pd.DataFrame(example_data)
        ## example = PrepareForModel(example_data)
        ## example.make_dummy_df(['colour', 'type'], 0)
        """

        # reset reference levels, if remaking then previous information would be there
        self.ref_levels = []

        # reset to original data.  Ensures that make_dummy_df can be rerun multiple times
        self.df = self.df_orig.copy()

        # check if dummy_vars is a dict or a list to determine how to drop categories
        if isinstance(dummy_vars, list):
            drop_by_index = True

            # make sure that cat_to_drop is within the index range of the selected variables
            for var in dummy_vars:
                if self.df[var].nunique() < (cat_to_drop + 1):
                    raise Exception("For column {} the number of categories was \
lower than the specified index ({}) to drop.".format(var, cat_to_drop))
        else:
            drop_by_index = False

        # loop through categorical columns in dummy_vars list/dict
        for var in dummy_vars:

            # convert given variable to a dummy variable
            current_dummy = pd.DataFrame(self.df[var])
            current_dummy = pd.get_dummies(current_dummy, prefix = var)


            # drop one level as specified by dummy_vars, if drop_cat is true
            if drop_cat == True:

                # scenario where dummy_vars is a list
                if drop_by_index == True:
                    dummy_to_drop = current_dummy.columns[cat_to_drop]
                    current_dummy = current_dummy.drop([dummy_to_drop], axis = 1)

                    # keep note of the dropped level in ref_levels
                    self.ref_levels.append(dummy_to_drop)

                # scenario where dummy_vars is a dict
                if drop_by_index == False:
                    dummy_to_drop = var + "_" + dummy_vars[var]
                    current_dummy = current_dummy.drop([dummy_to_drop], axis = 1)

                    # keep note of the dropped level in ref_levels
                    self.ref_levels.append(dummy_to_drop)

            # concat with original dataframe
            self.df = pd.concat([self.df, current_dummy], axis=1)

        # drop pre-dummy categorical columns from original dataframe
        if drop_by_index == True:
            self.df = self.df.drop(dummy_vars, axis=1)

        if drop_by_index == False:
            self.df = self.df.drop(dummy_vars.keys(), axis=1)

        # if int add is true, add int
        if add_intercept == True:
            self.df['intercept'] = 1.0

        return self.df
