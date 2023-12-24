# -*- coding: utf-8 -*-
"""KNNCF: Skopt 11.686%.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LWEQCIEW1bWm9IoL_8zXQnxg_eRGlY6P
"""

# Commented out IPython magic to ensure Python compatibility.
from google.colab import drive
drive.mount('/gdrive')
# %cd /gdrive/My Drive/RecSys/libs

# Commented out IPython magic to ensure Python compatibility.
# %load_ext Cython

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
import numpy as np
import scipy as sp
import scipy.sparse as sps
import matplotlib.pyplot as plt
import random
from scipy import stats
from scipy.optimize import fmin
import pandas as pd

from Data_manager.split_functions.split_train_validation_random_holdout import split_train_in_two_percentage_global_sample

data = pd.read_csv(filepath_or_buffer="data_train.csv",
                   sep=",")
data.columns = ["UserID", "ItemID", "Interaction"]

mapped_id, original_id = pd.factorize(data["UserID"].unique())
user_original_ID_to_index = pd.Series(mapped_id, index=original_id)

mapped_id, original_id = pd.factorize(data["ItemID"].unique())
item_original_ID_to_index = pd.Series(mapped_id, index=original_id)

data["UserID"] = data["UserID"].map(user_original_ID_to_index)
data["ItemID"] = data["ItemID"].map(item_original_ID_to_index)


URM_all = sps.coo_matrix((data["Interaction"].values,
                          (data["UserID"].values, data["ItemID"].values)))

URM_all.tocsr()

URM_train_validation, URM_test = split_train_in_two_percentage_global_sample(URM_all, train_percentage = 0.8)
URM_train, URM_validation = split_train_in_two_percentage_global_sample(URM_train_validation, train_percentage = 0.8)

URM_all, URM_train_validation, URM_train, URM_validation, URM_test

"""#Try some hyperparameter with Skopt"""

from Evaluation.Evaluator import EvaluatorHoldout
#from sklearn.model_selection import train_test_split

#URM_train_validation, URM_test = train_test_split(URM_all, random_state=42, test_size=0.2)
#URM_train, URM_validation = train_test_split(URM_train_validation, random_state=42, test_size=0.2)


evaluator_validation = EvaluatorHoldout(URM_validation, cutoff_list=[10])
evaluator_test = EvaluatorHoldout(URM_test, cutoff_list=[10])

URM_train.shape, URM_validation.shape, URM_test.shape

pip install scikit-optimize

from skopt.space import Real, Integer, Categorical

hyperparameters_range_dictionary = {
    "topK": Integer(5, 1000),
    "shrink": Integer(0, 1000),
    "normalize": Categorical([True, False]),
    "feature_weighting" : Categorical(["TF-IDF", "none"])
}

from Recommenders.KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
from HyperparameterTuning.SearchBayesianSkopt import SearchBayesianSkopt

recommender_class = ItemKNNCFRecommender

hyperparameterSearch = SearchBayesianSkopt(recommender_class,
                                         evaluator_validation=evaluator_validation,
                                         evaluator_test=evaluator_test)

from HyperparameterTuning.SearchAbstractClass import SearchInputRecommenderArgs

recommender_input_args = SearchInputRecommenderArgs(
    CONSTRUCTOR_POSITIONAL_ARGS = [URM_train],     # For a CBF model simply put [URM_train, ICM_train]
    CONSTRUCTOR_KEYWORD_ARGS = {},
    FIT_POSITIONAL_ARGS = [],
    FIT_KEYWORD_ARGS = {},
    EARLYSTOPPING_KEYWORD_ARGS = {},
)
recommender_input_args_last_test = SearchInputRecommenderArgs(
    CONSTRUCTOR_POSITIONAL_ARGS = [URM_train_validation],     # For a CBF model simply put [URM_train_validation, ICM_train]
    CONSTRUCTOR_KEYWORD_ARGS = {},
    FIT_POSITIONAL_ARGS = [],
    FIT_KEYWORD_ARGS = {},
    EARLYSTOPPING_KEYWORD_ARGS = {},
)

import os

output_folder_path = "result_experiments_KNN_/"

# If directory does not exist, create
if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)

n_cases = 300  # using 10 as an example
n_random_starts = int(n_cases*0.3)
metric_to_optimize = "MAP"
cutoff_to_optimize = 10

hyperparameterSearch.search(recommender_input_args,
                       recommender_input_args_last_test = recommender_input_args_last_test,
                       hyperparameter_search_space = hyperparameters_range_dictionary,
                       n_cases = n_cases,
                       n_random_starts = n_random_starts,
                       save_model = "last",
                       output_folder_path = output_folder_path, # Where to save the results
                       output_file_name_root = recommender_class.RECOMMENDER_NAME, # How to call the files
                       metric_to_optimize = metric_to_optimize,
                       cutoff_to_optimize = cutoff_to_optimize,
                      )

from Recommenders.DataIO import DataIO

data_loader = DataIO(folder_path = output_folder_path)
search_metadata = data_loader.load_data(recommender_class.RECOMMENDER_NAME + "_metadata.zip")

search_metadata.keys()

hyperparameters_df = search_metadata["hyperparameters_df"]
hyperparameters_df

result_on_validation_df = search_metadata["result_on_validation_df"]
result_on_validation_df

best_hyperparameters = search_metadata["hyperparameters_best"]
best_hyperparameters

"""#Let's submit"""

#{'topK': 17, 'shrink': 310, 'normalize': True, 'feature_weighting': 'TF-IDF'}  val:2,75 test:3,55
from Recommenders.KNN.ItemKNNCFRecommender import ItemKNNCFRecommender

recommender2 = ItemKNNCFRecommender(URM_all)
recommender2.fit(topK= 17, shrink= 310, normalize= True, feature_weighting= 'TF-IDF')

users_to_recommend_raw = pd.read_csv(filepath_or_buffer="/gdrive/My Drive/RecSys/libs/data_target_users_test.csv",
                   sep=",",
                  dtype={"user_id": np.int32}).to_numpy()
users_to_recommend = []
for elem in users_to_recommend_raw:
  users_to_recommend.append(elem[0])

len(users_to_recommend)

ratings = pd.read_csv("/gdrive/My Drive/RecSys/libs/data_train2.csv",
                       sep=",",
                       names=["user_id", "item_id", "ratings"],
                       header=None,
                       dtype={"user_id": np.int64,
                               "item_id": np.int64,
                               "ratings": np.int64})
ratings.shape

def preprocess_data(ratings: pd.DataFrame):
    unique_users = ratings.user_id.unique()
    unique_items = ratings.item_id.unique()

    num_users, min_user_id, max_user_id = unique_users.size, unique_users.min(), unique_users.max()
    num_items, min_item_id, max_item_id = unique_items.size, unique_items.min(), unique_items.max()

    print(num_users, min_user_id, max_user_id)
    print(num_items, min_item_id, max_item_id)

    mapping_user_id = pd.DataFrame({"mapped_user_id": np.arange(num_users), "user_id": unique_users})
    mapping_item_id = pd.DataFrame({"mapped_item_id": np.arange(num_items), "item_id": unique_items})

    ratings = pd.merge(left=ratings,
                       right=mapping_user_id,
                       how="inner",
                       on="user_id")

    ratings = pd.merge(left=ratings,
                       right=mapping_item_id,
                       how="inner",
                       on="item_id")

    return ratings

ratings = preprocess_data(ratings)

users_ids_and_mappings = ratings[ratings.user_id.isin(users_to_recommend)][["user_id", "mapped_user_id"]].drop_duplicates()
items_ids_and_mappings = ratings[["item_id", "mapped_item_id"]].drop_duplicates()
users_ids_and_mappings

def prepare_submission(ratings: pd.DataFrame, users_to_recommend: np.array, urm_train: sps.csr_matrix):
    users_ids_and_mappings = ratings[ratings.user_id.isin(users_to_recommend)][["user_id", "mapped_user_id"]].drop_duplicates()
    items_ids_and_mappings = ratings[["item_id", "mapped_item_id"]].drop_duplicates()

    mapping_to_item_id = dict(zip(ratings.mapped_item_id, ratings.item_id))


    recommendation_length = 10
    submission = []
    for idx, row in users_ids_and_mappings.iterrows():
        user_id = row.user_id
        mapped_user_id = row.mapped_user_id
        recommendations = recommender2.recommend(mapped_user_id,recommendation_length)
        submission.append((user_id, [mapping_to_item_id[item_id] for item_id in recommendations]))

    users_recommended = [elem[0] for elem in submission]

    missing_users = []
    top10 = [20, 15,  9,  8,  6,  7,  3,  1,  4,  2]
    for elem in users_to_recommend:
      if elem not in users_recommended:
        missing_users.append(elem)

    for i in range(len(missing_users)):
      missing_users[i] = (missing_users[i], [top10[elem] for elem in range(10)])

    return submission, missing_users

URM_train = URM_all.tocsr()
submission, missing_users = prepare_submission(ratings, users_to_recommend, URM_train)
len(submission), len(missing_users)

submission = submission + missing_users
len(submission)

submission.sort()

def write_submission(submissions):
    with open("./KNNCF_SKOPT_3_0.csv", "w") as f:
        for user_id, items in submissions:
          f.write(f"{user_id},{' '.join(str(item) for item in items)}\n")

write_submission(submission)