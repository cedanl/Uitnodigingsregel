from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
import joblib

# Random Forest Regressor model for training 
def randomforestregressormodel_train(dataset_train, random_seed, dropout_column, rf_parameters):
    X = dataset_train.drop(dropout_column, axis=1).values
    y = dataset_train[dropout_column].values
    rf = RandomForestRegressor(random_state=random_seed)
    
    # Hyperparameter tuning using gridsearchCV
    grid_model = GridSearchCV(rf, rf_parameters, refit = True, n_jobs = -1, verbose = 0)
    grid_model.fit(X, y) 
    best_params = grid_model.best_params_
    best_rf_model = RandomForestRegressor(**best_params)
    best_rf_model.fit(X, y) 
    
    # Save model 
    joblib.dump(best_rf_model, 'models/random_forest_regressor.joblib')
    return best_rf_model

# lasso regression model for training 
def lassoregressionmodel_train (dataset_train_sdd, random_seed, dropout_column, alpha_range): 
    X = dataset_train_sdd.drop(dropout_column, axis=1).values
    y = dataset_train_sdd[dropout_column].values
    lasso_model = Lasso(random_state = random_seed)
    param = {'alpha':alpha_range}
    
    # Hyperparameter tuning using gridsearchCV
    lasso_grid_search = GridSearchCV(lasso_model, param_grid = param, refit = False, cv=5, n_jobs = -1, verbose = 0)
    lasso_grid_search.fit(X, y)
    best_params = lasso_grid_search.best_params_
    best_lasso_model = Lasso(**best_params)
    best_lasso_model.fit(X, y) 
    
    # Save model 
    joblib.dump(best_lasso_model, 'models/lasso_regression.joblib')
    return best_lasso_model

# Support vector machine model for training 
def supportvectormachinemodel_train(dataset_train_sdd, random_seed, dropout_column, svm_parameters):
    X = dataset_train_sdd.drop(dropout_column, axis=1).values
    y = dataset_train_sdd[dropout_column].values
    
    # Hyperparameter tuning using gridsearchCV 
    svm_gridsearch = GridSearchCV(SVC(random_state=random_seed, probability = True), svm_parameters, refit = False, n_jobs = -1, verbose = 0) 
    svm_gridsearch.fit(X, y)
    best_params = svm_gridsearch.best_params_
    best_svm_model = SVC(**best_params, probability = True)
    best_svm_model.fit(X, y) 

    # Save model 
    joblib.dump(best_svm_model, 'models/support_vector_machine.joblib')
    return best_svm_model