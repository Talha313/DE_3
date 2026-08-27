# ================================================================================================= #
# Filename  : HMD-Scikit Learn-Tutorial-2026.py
# Purpose   : A tutorial on scikit-learn for AI 620: Fundamentals of Data Engineering.
#             This tutorial covers basic concepts in 
#             Module 3: Model Development: Features, Training and Evaluation
#
# Commands  : conda install anaconda::scikit-learn
#             conda install conda-forge::pandas
#             conda install conda-forge::matplotlib
#             conda install conda-forge::imbalanced-learn
#             To run this code, type >> python HMD-Scikit Learn-Tutorial-2026.py
#
# Remarks   : As you work through this tutorial, make sure to focus on understanding 
#             the concepts. Don’t blindly trust the code; analyze it, question it, and 
#             ensure you understand why it works. Feel free to point out any mistakes, 
#             oversights, or omissions.
#
# Author    : Dr. Hassan Mohy-ud-Din (hassan.mohyuddin@lums.edu.pk)
# Date      : March 1, 2026
# ================================================================================================= #

import numpy                                                            as np
import pandas                                                           as pd

import matplotlib.pyplot                                                as plt

from sklearn.pipeline               import Pipeline                     as SkPipeline   # does not support resampling methods
from sklearn.compose                import ColumnTransformer

from sklearn.experimental           import enable_iterative_imputer
from sklearn.impute                 import (SimpleImputer, KNNImputer,
                                            IterativeImputer)
from sklearn.preprocessing          import (StandardScaler, MinMaxScaler, 
                                            RobustScaler, OneHotEncoder)

from sklearn.datasets               import make_classification, make_regression
from sklearn.model_selection        import (train_test_split, StratifiedKFold, 
                                            GridSearchCV, cross_val_score)

from sklearn.svm                    import OneClassSVM
from sklearn.ensemble               import IsolationForest
from sklearn.linear_model           import LogisticRegression

from sklearn.metrics                import (roc_auc_score, f1_score, precision_score, 
                                            recall_score, roc_curve, classification_report,
                                            confusion_matrix, ConfusionMatrixDisplay)

from imblearn.pipeline              import Pipeline                                     # same as sklearn Pipeline but supports resampling methods
from imblearn.over_sampling         import SMOTE, SMOTENC

# ================================================================================================= #
# Define global terms, objects, executors, variables upfront.
rng             = np.random.default_rng(42)

# ================================================================================================= #
# Generate a regression dataset.
W, z            = make_regression(n_samples         = 3000,     # number of data points
                                  n_features        = 20,       # total features
                                  n_informative     = 10,       # features actually influencing target
                                  noise             = 15.0,     # Gaussian noise (realism)
                                  bias              = 50.0,     # intercept term
                                  effective_rank    = None,     # input set is well conditioned, centered and gaussian with unit variance
                                  shuffle           = True,     # shuffle the samples and the features
                                  random_state      = 42)

# We won't be using the variables "W" and "z" in future to avoid mixing with this dataset.
# This is a tutorial on how to create a synthetic dataset for regression task.

# ================================================================================================= #
# Generate a realistic classification dataset which includes:
# - informative and redundant features,
# - class imbalance,
# - label noise,
# - missing values (MCAR and MAR style),
# - outliers, and
# - feature scaling variations.

# Generate a base classification dataset.
X, y            = make_classification(n_samples     = 8000,         # total data points
                                      n_features    = 20,           # total number of features
                                      n_informative = 8,            # useful/relevant features
                                      n_redundant   = 5,            # linear combinations of informative
                                      n_repeated    = 0,            # number of duplicated features
                                      n_classes     = 2,            # binary classification
                                      weights       = [0.7, 0.3],   # class imbalance
                                      class_sep     = 1.0,          # separation between classes: (= 0.5) hard, (= 1.0) moderate, (= 2.0) easy
                                      hypercube     = True,         # clusters are put on the vertices of a hypercube
                                      flip_y        = 0.02,         # label noise
                                      random_state  = 42)

print("\n----- Shape of feature matrix -----\n", X.shape) 
print("\n----- Shape of label vector -----\n"  , y.shape) 

# Convert to pandas dataframe
df              = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(X.shape[1])])
df["target"]    = y

print("\n----- The first five rows of the dataframe -----\n", df.head())

# ----------------------------------------------------------------------------------- #
# Add categorical variables with different number of categories.
# These are string-based categorical variables, which can later be encoded.

# Small category variable (3 categories)
df["gender"]    = rng.choice(["male", "female", "other"], size=len(df))

# Medium category variable (5 categories)
df["region"]    = rng.choice(["north", "south", "east", "west", "central"], size=len(df))

# Large category variable (10 categories)
df["type"]      = rng.choice([f"type_{i}" for i in range(10)], size=len(df))

# CAUTION: Before adding the categorical variables, the response variable ("target")
# was the last column in the DataFrame. After adding new categorical columns, they
# were appended to the end, pushing "target" away from the final position. To maintain
# a clean and consistent structure, we will move the "target" column back to the last
# (rightmost) position in the DataFrame.

target          = df.pop("target")
df["target"]    = target

# Print to confirm
print("\n----- The first five rows of the dataframe -----\n", df.head())

# ----------------------------------------------------------------------------------- #
# Introduce missingness

df_original     = df.copy()

# MCAR (Missing Completely at Random)
missing_mask    = rng.uniform(size = df.shape) < 0.05       # 5% missing
df              = df.mask(missing_mask)

# MAR (Missing Depends on Feature Value)
# Example: Higher values are more likely to be missing.
# This makes missingness structured, which is realistic.
prob_missing    = 1 / (1 + np.exp(-df["feature_0"]))  # sigmoid
mar_mask        = rng.uniform(size=len(df)) < (prob_missing * 0.1)       # 10% missingness

# Missingness in feature_1 depends on feature_0, but not on feature_1 itself.
# Example 1: Older patients are more likely to have blood pressure recorded; younger patients might skip.
# Example 2: People with higher education are more likely to report their income.
# Example 3: Patients with known heart disease are more likely to have cholesterol measured.
# Example 4: Customers who buy frequently are more likely to leave a review.
# Example 5: Students who attend class regularly are more likely to take optional exams.
df.loc[mar_mask, "feature_1"] = np.nan

# ----------------------------------------------------------------------------------- #
# Add outliers.
# Inject extreme values into 1% of samples. We simulate heavy-tailed distortions.

n_outliers      = int(0.01 * len(df))                # 1% outliers
outlier_indices = rng.choice(df.index, size=n_outliers, replace = False)

df.loc[outlier_indices, "feature_2"] *= 10
df.loc[outlier_indices, "feature_3"] += 50

# ----------------------------------------------------------------------------------- #
# Introduce different feature scales.
df["feature_4"] *= 1000   # large scale
df["feature_5"] *= 0.001  # tiny scale

# ----------------------------------------------------------------------------------- #
# Add irrelevant noise features (also known as distractor features).

for i in range(3):
    df[f"noise_{i}"] = rng.normal(size = len(df))

# Again, moving the "target" column back to the last position in the DataFrame.
target          = df.pop("target")
df["target"]    = target

# ----------------------------------------------------------------------------------- #
# Add mild nonlinearity.
df["feature_6"] = df["feature_6"] ** 2

# ----------------------------------------------------------------------------------- #
# Quick reality check.
# Gives a quick overview of your data: central tendency, spread, and extremes.
print(df.isna().mean())
print(df.describe())

print("\n-----------------------------------------------\n")

print("\n----- Pairwise correlation -----\n"        , df.select_dtypes(include=np.number).corr())    # pairwise correlation between numeric columns
print("\n----- Datatypes of features -----\n"       , df.dtypes)                                     # which columns are numeric, object (string), boolean, etc.
print("\n----- Count duplicated features -----\n"   , df.duplicated().sum())                         # counts duplicate rows
print("\n----- Simple statistics -----\n"           , df.describe(include='object'))                 # counts, unique values, top frequent value, frequency for categorical columns
print("\n----- Dataset summary -----\n")            ; df.info()                                      # compact view of number of rows, non-null counts, and data types

# ================================================================================================= #
# Encode categorical columns.

# df_orig_masked  = df.copy()
# df['gender']    = df['gender'].map({'male': 0, 'female': 1})

# NOTE: The code above demonstrates manual encoding of the 'gender' column. This approach 
# can be applied to each categorical feature individually. However, below we will show a 
# more efficient method which encodes all categorical features at once using pd.get_dummies 
# in a single statement.

# One-hot encoding for multiple feature categories.
# df              = pd.get_dummies(df, drop_first=True)

# Again, moving the "target" column back to the last position in the DataFrame.
target          = df.pop("target")
df["target"]    = target

print("\n----- Simple statistics -----\n"                   , df.describe)                                  # summary
print("\n----- Pairwise correlation -----\n"                , df.select_dtypes(include='number').corr())    # pairwise correlation between numeric columns
print("\n----- The first five rows of the dataframe -----\n", df.head())
print("\n----- Categotrical columns -----\n"                , df.select_dtypes(include=['object', 'category']))

# ================================================================================================= #
# Before preprocessing, we first split the data into training, validation, and test sets.

# Extract the dataset from the pandas dataframe. 
Xdata                                   = df.drop("target", axis=1)     # features
ydata                                   = df["target"]                  # target

# Check for NaNs and +-Infs in the "target" vector. 
print("\n----- NaNs in the data \n-----\n"  , np.isnan(ydata).sum())
print("\n----- Infs in the data \n-----\n"  , np.isinf(ydata).sum())

# We cannot have missing or infinite responses in the "target" vector.
mask                                    = ydata.notna() & (~np.isinf(ydata))
Xnew                                    = Xdata[mask]
ynew                                    = ydata[mask]

# Print shape of features and target.
print("\n----- Shape of feature matrix -----\n" , Xnew.shape) 
print("\n----- Shape of label vector -----\n"   , ynew.shape) 

# First split into "train-val" set and "test" set.
X_trainval, X_test, y_trainval, y_test  = train_test_split(Xnew, ynew, test_size = 0.2, 
                                                           random_state = 42, shuffle = True, 
                                                           stratify = ynew)

# Now, split "train-val" into "train" and "val" datasets.
X_train, X_val, y_train, y_val          = train_test_split(X_trainval, y_trainval, test_size=0.1, 
                                                           random_state = 42, shuffle = True, 
                                                           stratify = y_trainval)

cv                                      = StratifiedKFold(n_splits = 5, shuffle = True, 
                                                          random_state = 42)

# Print shapes for (some) confirmation.
print("\n----- Shape of X_train and y_train -----\n", X_train.shape , y_train.shape) 
print("\n----- Shape of X_val and y_val -----\n"    , X_val.shape   , y_val.shape)
print("\n----- Shape of X_test and y_test -----\n"  , X_test.shape  , y_test.shape)

# ================================================================================================= #
# We now make pipeline(s) by adding:
# - imputation,
# - one-hot encoding (of categorical variables),
# - scaling (of numerical features),
# - SMOTE (synthetic minority oversampling technique),
# - model (classifier),
# - cross-validation, and
# - inference/deployment/validation without data leakage.

# Separate Features by Type.
# Identify feature types.
numeric_features        = df.select_dtypes(include=['float16', 'float32', 'float64', 'int']).columns.drop('target')
categorical_features    = df.select_dtypes(include=['object']).columns

print("\n----- Numerical Features -----\n"  , numeric_features)
print("\n----- Categorical Features-----\n" , categorical_features)

# Pipeline Example # 1.
numeric_pipeline        = SkPipeline([("imputer", SimpleImputer(strategy = "mean")),
                                      ("scaler" , StandardScaler())])

categorical_pipeline    = SkPipeline([("imputer", SimpleImputer(strategy = "most_frequent")),
                                      ("encoder", OneHotEncoder(handle_unknown = "ignore"))])

preprocessor1           = ColumnTransformer([("num", numeric_pipeline       , numeric_features),
                                             ("cat", categorical_pipeline   , categorical_features)])

pipeline1               = Pipeline([("preprocess"   , preprocessor1),
                                    ("smote"        , SMOTE(random_state = 42)),
                                    ("model"        , LogisticRegression(max_iter = 1000))])

# Pipeline Example # 2.
# Median imputation with robust scaling (robust to outliers).
numeric_pipeline        = SkPipeline([("imputer", SimpleImputer(strategy = "median")),
                                      ("scaler" , RobustScaler())])

preprocessor2           = ColumnTransformer([("num", numeric_pipeline       , numeric_features),
                                             ("cat", categorical_pipeline   , categorical_features)])

pipeline2               = Pipeline([("preprocess"   , preprocessor2),
                                    ("smote"        , SMOTE(random_state = 42)),
                                    ("model"        , LogisticRegression(max_iter = 1000))])

# Pipeline Example # 3.
# Preferred when the relationship between numerical features are local.
numeric_pipeline        = SkPipeline([("imputer", KNNImputer(n_neighbors = 3)),
                                      ("scaler" , MinMaxScaler())])

preprocessor3           = ColumnTransformer([("num", numeric_pipeline       , numeric_features),
                                             ("cat", categorical_pipeline   , categorical_features)])

pipeline3               = Pipeline([("preprocess"   , preprocessor3),
                                    ("smote"        , SMOTE(k_neighbors = 3, random_state = 42)),
                                    ("model"        , LogisticRegression(max_iter = 1000))])

# Pipeline Example # 4.
# IterativeImputer is a scikit-learn method that fills missing values by modeling each 
# feature as a function of other features and iteratively refining the predictions.
# Preferred for complex missing data patterns and features are related (not independent).
numeric_pipeline        = SkPipeline([("imputer", IterativeImputer(random_state = 42)),
                                      ("scaler" , RobustScaler())])

preprocessor4           = ColumnTransformer([("num", numeric_pipeline       , numeric_features),
                                             ("cat", categorical_pipeline   , categorical_features)])

pipeline4               = Pipeline([("preprocess"   , preprocessor4),
                                    ("smote"        , SMOTE(random_state = 42)),
                                    ("model"        , LogisticRegression(max_iter = 1000))])

# ================================================================================================= #
# Training, validation, and inference (with cross-validation).
scores                  = cross_val_score(pipeline4, X_train, y_train, cv=cv, scoring="roc_auc")

print("\n----- Cross-val AUROC -----\n", scores.mean())

# Fit a model.
pipeline4.fit(X_train, y_train)

# Validation scores.
print("\n----- Val AUROC -----\n", pipeline4.score(X_val, y_val))

# Inference scores.
print("\n----- Test AUROC -----\n", pipeline4.score(X_test, y_test))

# ================================================================================================= #
# Examples of pipeline with SMOTENC oversample which is preferred for 
# cateogrical-heavy datasets.
# SMOTENC stands for Synthetic Minority Over-sampling Technique for nominal and continuous features.
# For numerical features, it uses the Euclidean distance to identify k-nearest neighbors.
# For categorical features, it uses the Hamming distance to identify k-nearest neighbors.
categorical_feature_indices = list(range(len(numeric_features), len(numeric_features) + \
                                         sum([len(df[col].dropna().unique()) for col in categorical_features])))

# Pipeline Example # 1.
pipeline1a                  = Pipeline([("preprocess"   , preprocessor1),
                                        ("smote"        , SMOTENC(categorical_features = categorical_feature_indices, 
                                                                  random_state = 42)),
                                        ("model"        , LogisticRegression(max_iter=1000))])

# Pipeline Example # 2.
pipeline2a                  = Pipeline([("preprocess"   , preprocessor2),
                                        ("smote"        , SMOTENC(categorical_features = categorical_feature_indices, 
                                                                  random_state = 42)),
                                        ("model"        , LogisticRegression(max_iter=1000))])

# Pipeline Example # 4.
pipeline4a                  = Pipeline([("preprocess"   , preprocessor4),
                                        ("smote"        , SMOTENC(categorical_features = categorical_feature_indices, 
                                                                  random_state = 42)),
                                        ("model"        , LogisticRegression(max_iter=1000))])

# ================================================================================================= #
# Tuning hyperparameters with grid search.
param_grid                  = [{"smote__sampling_strategy"  : [0.5, 1.0],
                                "model__C"                  : [0.1, 1, 10]}]

grid_search                 = GridSearchCV(pipeline1, param_grid, cv=cv, scoring="roc_auc", n_jobs=-1)
grid_search.fit(X_train, y_train)

print("\n----- Best Params -----\n"     , grid_search.best_params_)
print("\n----- Best CV AUROC -----\n"   , grid_search.best_score_)
print("\n----- Val AUROC -----\n"       , grid_search.score(X_test, y_test))    # consider "val" dataset as the hold-out dataset

# Fetch the best pipeline.
best_pipeline1              = grid_search.best_estimator_

# Predict on the test set.
y_pred                      = best_pipeline1.predict(X_test)
print("\n----- Test predictions -----\n"    , y_pred)

# Probabilistic predictions.
y_proba                     = best_pipeline1.predict_proba(X_test)[:, 1]        # probability of positive class
print("\n----- Test probabilities -----\n"  , y_proba)

# Compute performance metrics.
auroc                       = roc_auc_score(y_test, y_proba)
print("\n----- Test AUROC -----\n"          , auroc)

f1                          = f1_score(y_test, y_pred)
print("\n----- Test F1 score -----\n"       , f1)

# Print classification report.
print("\n----- Test report -----\n"         , classification_report(y_test, y_pred))

# ================================================================================================= #
# Plot ROC curve.
y_true                      = y_test
fpr, tpr, thresholds        = roc_curve(y_true, y_proba)

plt.figure(figsize = (8,6))
plt.plot(fpr, tpr, color = 'blue', lw = 2, label = f'ROC curve (AUROC = {auroc:.2f})')
plt.plot([0,1], [0,1], color = 'gray', lw = 1, linestyle = '--', label = 'Logistic Regression')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve')
plt.legend(loc = 'lower right')
plt.grid(True)
plt.show()

# ================================================================================================= #
# Tabulate confusion matrix.
cm                          = confusion_matrix(y_true, y_pred)
print("\n----- Test Confusion Matrix -----\n", cm)

disp                        = ConfusionMatrixDisplay(confusion_matrix = cm, 
                                                     display_labels = best_pipeline1.classes_)
disp.plot(cmap=plt.cm.Blues)
plt.title("Confusion Matrix")
plt.show()

# ================================================================================================= #