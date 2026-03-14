import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import yaml
from sklearn.calibration import CalibratedClassifierCV

# Load default settings
def load_settings(config_file='config.yaml', settings_type='default'):
    """Load settings from YAML config file"""
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    if settings_type == 'default':
        settings = config['default_settings']
    elif settings_type == 'custom':
        settings = config['custom_settings']
    else:
        raise ValueError("No settings found. Choose 'default' or 'custom'.")
    return settings

settings = load_settings()

def dynamische_evaluatie(model="lasso", data=None):
    """"
    Deze functie evalueert de voorspelling van het model obv de uitnodigingsregel van Eegdeman et al. (2022).
    Iemand wordt uitgenodigd (= lasso1 = 1):
        1) als hij/zij in werkelijkheid is uitgevallen; en
        2) als zijn rank goed bepaald is (i = het aantal leerlingen dat wordt uitgenodigd)

    e.g. als er maar 10 leerlingen uitgenodigd worden, dan worden ook de top 10 leerlingen met de hoogste kans op uitval uitgenodigd,
    en obv hiervan worden de precisie en recall bepaald

    Parameters:
        model, geeft aan om welk model het gaat, default lasso
        data, df met de daadwerkelijke en voorspelde uitval en de rank

    Returns:
        data, df met de totaal correct voorspelde uitvalwaarden en de precisiewaarden
    """
    # Get dropout column from settings
    dropout_col = settings.get('dropout_column', 'Dropout')
    
    # Bepaal correct voorspelde waarde door telkens een leerling te identificeren als "risico op dropout",
    # als de leerling dan geïdentificeerd is en ook daadwerkelijk een dropout is, dan is het dus een correcte voorspelling
    data["{}1".format(model)] = np.where(((data[dropout_col]==1) & (data["yhat2_rank"] <= data["i"])), 1, 0)

    # Bepaal dynamisch: de voorspelde kans op uitval wordt geordend van hoog naar laag (yhat2_rank). Obv deze ordening worden mensen uitgenodigd.
    # Dus eerst wordt degene bovenaan de lijst uitgenodigd, als hij / zij dan daadwerkelijk is uitgevallen, dan is er een precision van 100%
    # omdat hij / zij gedetecteerd is als "risico op uitval" en dan ook echt is uitgevallen. Vervolgens wordt de volgende in de lijst uitgenodigd en dan degene daarna.
    # Als iemand wordt uitgenodigd, maar niet uitgevallen blijkt te zijn, dan daalt de precision.
    totale_uitval = len(data[data[dropout_col] == 1])
    for i in range(0, len(data)):
        if i < 1:
            data.loc[i, "totalcorrect{}1".format(model)] = data.loc[i, "{}1".format(model)]
            data.loc[i, "precision{}".format(model)] = round(data.loc[i, "totalcorrect{}1".format(model)] / data.loc[i, "i"], 2)
            data.loc[i, "recall{}".format(model)] = round(data.loc[i, "totalcorrect{}1".format(model)] / totale_uitval, 2)
            data.loc[i, "perc_uitgenodigde_studenten"] = round((data.loc[i, "i"] / len(data))* 100, 1)
        else:
            data.loc[i, "totalcorrect{}1".format(model)] = data.loc[i, "{}1".format(model)] + data.loc[i-1, "totalcorrect{}1".format(model)]
            data.loc[i, "precision{}".format(model)] = round(data.loc[i, "totalcorrect{}1".format(model)] / data.loc[i, "i"], 2)
            data.loc[i, "recall{}".format(model)] = round(data.loc[i, "totalcorrect{}1".format(model)] / totale_uitval, 2)
            data.loc[i, "perc_uitgenodigde_studenten"] = round((data.loc[i, "i"] / len(data))* 100, 1)
    data.drop(["i", "{}1".format(model),"totalcorrect{}1".format(model)], axis=1, inplace = True)
    return data

def prepare_model_predictions(validation_data, model, model_name):
    """Helper function to prepare predictions and rankings for a model.
    
    Parameters:
        validation_data: DataFrame containing validation data
        model: Trained model object
        model_name: String identifier for the model
        
    Returns:
        DataFrame with predictions and rankings
    """
    # Get dropout column from settings
    dropout_col = settings.get('dropout_column', 'Dropout')
    
    X_val = validation_data.drop(dropout_col, axis=1)
    
    # Handle different model types for predictions
    if hasattr(model, 'predict_proba'):
        pred = model.predict_proba(X_val)[:, 1]  # For SVM
    else:
        pred = model.predict(X_val)  # For RF and Lasso
        
    # Create and prepare DataFrame
    data = pd.DataFrame({dropout_col: validation_data[dropout_col], "yhat2": pred})
    data = data.sort_values(by=["yhat2"], ascending=False).reset_index(drop=True)
    data["yhat2_rank"] = data["yhat2"].rank(method='dense', ascending=False)
    data["i"] = data.index + 1
    
    return dynamische_evaluatie(model_name, data)

def save_plot(plt, plot_type):
    """Helper function to save plot with consistent settings.
    
    Parameters:
        plt: matplotlib.pyplot object
        plot_type: String identifier for the plot type
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    figures_dir = os.path.join(project_root, 'reports', 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    plot_path = os.path.join(figures_dir, f'{plot_type}_plot.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

def generate_precision_plot(validation_data, rf_model, lasso_model, svm_model, validation_data_scaled=None, do_save=False):
    """
    Generate a precision plot comparing the three models.

    Args:
        validation_data (pd.DataFrame): Validation dataset (unscaled, used for RF)
        rf_model: Random Forest model
        lasso_model: Lasso model
        svm_model: SVM model
        validation_data_scaled (pd.DataFrame): Scaled validation dataset (used for Lasso and SVM)
        do_save (bool): Whether to save the plot to a file
    """
    # Get dropout column from settings
    dropout_col = settings.get('dropout_column', 'Dropout')

    # Use scaled validation data for Lasso and SVM, unscaled for RF
    rf_results = prepare_model_predictions(validation_data, rf_model, "rf")
    scaled_data = validation_data_scaled if validation_data_scaled is not None else validation_data
    lasso_results = prepare_model_predictions(scaled_data, lasso_model, "lasso")
    svm_results = prepare_model_predictions(scaled_data, svm_model, "svm")
    
    # Calculate dropout rate
    dropout_rate = (len(validation_data[validation_data[dropout_col] == 1]) / len(validation_data)) * 100
    
    # Create precision plot
    plt.figure(figsize=(10, 6))
    plt.plot(lasso_results.perc_uitgenodigde_studenten, lasso_results.precisionlasso * 100, label='lasso')
    plt.plot(rf_results.perc_uitgenodigde_studenten, rf_results.precisionrf * 100, '-.', label='rf')
    plt.plot(svm_results.perc_uitgenodigde_studenten, svm_results.precisionsvm * 100, '--', label='svm')
    plt.axhline(y=dropout_rate, linestyle=':', label='gem')
    
    plt.xlim(0, 100)
    plt.ylim(0, 101)
    plt.xlabel("% uitgenodigde studenten")
    plt.ylabel("Precision %")
    plt.legend()
    plt.title('Precision tegen perc uitgenodigde studenten')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if do_save:
        save_plot(plt, 'precision')
    
    return plt.gcf()

def generate_sensitivity_plot(validation_data, rf_model, lasso_model, svm_model, validation_data_scaled=None, do_save=False):
    """
    Generates a sensitivity (recall) plot comparing the performance of different models.

    Parameters:
        validation_data: DataFrame containing validation data with 'Dropout' column (unscaled, used for RF)
        rf_model: Trained Random Forest model
        lasso_model: Trained Lasso model
        svm_model: Trained SVM model
        validation_data_scaled: DataFrame containing scaled validation data (used for Lasso and SVM)
        do_save: Boolean, whether to save the plot to file (default False)
    """
    # Get dropout column from settings
    dropout_col = settings.get('dropout_column', 'Dropout')

    # Use scaled validation data for Lasso and SVM, unscaled for RF
    rf_results = prepare_model_predictions(validation_data, rf_model, "rf")
    scaled_data = validation_data_scaled if validation_data_scaled is not None else validation_data
    lasso_results = prepare_model_predictions(scaled_data, lasso_model, "lasso")
    svm_results = prepare_model_predictions(scaled_data, svm_model, "svm")
    
    # Create sensitivity plot
    plt.figure(figsize=(10, 6))
    plt.plot(lasso_results.perc_uitgenodigde_studenten, lasso_results.recalllasso * 100, label='lasso')
    plt.plot(rf_results.perc_uitgenodigde_studenten, rf_results.recallrf * 100, '-.', label='rf')
    plt.plot(svm_results.perc_uitgenodigde_studenten, svm_results.recallsvm * 100, '--', label='svm')
    
    # Add diagonal reference line
    x = lasso_results.perc_uitgenodigde_studenten
    y = [i for i in np.arange(0, 100, 100 / len(x))]
    plt.plot(x, y, ':', label='gem')
    
    plt.xlim(0, 100)
    plt.ylim(0, 101)
    plt.xlabel("% uitgenodigde studenten")
    plt.ylabel("Sensitivity %")
    plt.legend()
    plt.title('Sensitivity tegen perc uitgenodigde studenten')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if do_save:
        save_plot(plt, 'sensitivity')
    
    return plt.gcf()

def generate_svm_importance_plot(validation_data, svm_model, train_data_sdd=None, do_save=False):
    """
    Generate feature importance plot for SVM model using perturbation method.
    Uses scaled training data if provided, otherwise uses validation data.
    
    Parameters:
        validation_data: DataFrame containing validation data with 'Dropout' column
        svm_model: Trained SVM model
        train_data_sdd: DataFrame containing scaled training data (optional)
        do_save: Boolean, whether to save the plot to file (default False)
    """
    
    # Get dropout column from settings
    dropout_col = settings.get('dropout_column', 'Dropout')
    
    # Use training data if provided, otherwise use validation data
    data = train_data_sdd.copy() if train_data_sdd is not None else validation_data.copy()
    
    # Clean and prepare data
    data = data.fillna(data.mean())
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.fillna(data.mean())
    
    X = data.drop(dropout_col, axis=1)
    y = data[dropout_col]
    
    # Get feature names
    feature_names = X.columns
    
    # Calibrate the model
    calibrated_svm = CalibratedClassifierCV(svm_model, method="sigmoid", cv="prefit")
    calibrated_svm.fit(X, y)
    
    # Get original probabilities
    prob_original = calibrated_svm.predict_proba(X)[:, 1]
    
    # Calculate feature importance using perturbation
    perturbation = 1.0  # Selected (optimal magnitude from testing
    feature_stds = X.std()
    prob_changes = []
    
    for feature_name in feature_names:
        X_perturbed = X.copy()
        feature_perturbation = perturbation * feature_stds[feature_name]
        X_perturbed[feature_name] = X_perturbed[feature_name] + feature_perturbation
        prob_perturbed = calibrated_svm.predict_proba(X_perturbed)[:, 1]
        prob_change = np.mean(prob_perturbed - prob_original)
        prob_changes.append(prob_change)
    
    # Create importance plot
    plt.figure(figsize=(14, 10))  
    
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': prob_changes
    })
    feature_importance['abs_importance'] = abs(feature_importance['importance'])
    feature_importance = feature_importance.sort_values('abs_importance', ascending=True)
    
    y_pos = np.arange(len(feature_names))
    plt.barh(y_pos, feature_importance['importance'], 
             color=['red' if change < 0 else 'green' for change in feature_importance['importance']])
    plt.yticks(y_pos, feature_importance['feature'], fontsize=9)  
    
    for i, v in enumerate(feature_importance['importance']):
        plt.text(v, i, f' {v:.4f}', va='center')
    
    plt.xlabel("Belang van Feature (Gemiddelde Verandering in Voorspelde Kans)")
    plt.title("SVM Feature Importance (Geschaalde Verstoring)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if do_save:
        save_plot(plt, 'svm_importance')
    
    return plt.gcf()



def save_model_metrics(train_data, train_data_scaled, validation_data, validation_data_scaled, rf_model, lasso_model, svm_model):
    """
    Calculate and save model evaluation metrics for all models.
    
    Parameters:
        train_data: DataFrame containing unscaled training data (for Random Forest)
        train_data_scaled: DataFrame containing scaled training data (for Lasso and SVM)
        validation_data: DataFrame containing unscaled validation data (for Random Forest)
        validation_data_scaled: DataFrame containing scaled validation data (for Lasso and SVM)
        rf_model: Trained Random Forest model
        lasso_model: Trained Lasso model
        svm_model: Trained SVM model
    """
    # Initialize metrics dictionary
    metrics = {
        'Random Forest': {},
        'Lasso': {},
        'SVM': {}
    }
    
    # Prepare data for each model
    # Random Forest uses unscaled data
    X_train_rf = train_data.drop('Dropout', axis=1)
    y_train_rf = train_data['Dropout']
    X_val_rf = validation_data.drop('Dropout', axis=1)
    y_val_rf = validation_data['Dropout']
    
    # Lasso and SVM use scaled data
    X_train_scaled = train_data_scaled.drop('Dropout', axis=1)
    y_train_scaled = train_data_scaled['Dropout']
    X_val_scaled = validation_data_scaled.drop('Dropout', axis=1)
    y_val_scaled = validation_data_scaled['Dropout']
    
    # Calculate metrics for each model using appropriate data
    models = {
        'Random Forest': (rf_model, X_train_rf, y_train_rf, X_val_rf, y_val_rf),
        'Lasso': (lasso_model, X_train_scaled, y_train_scaled, X_val_scaled, y_val_scaled),
        'SVM': (svm_model, X_train_scaled, y_train_scaled, X_val_scaled, y_val_scaled)
    }
    
    for name, (model, X_train, y_train, X_val, y_val) in models.items():
        # Get predictions based on model type
        if name == 'SVM' and hasattr(model, 'predict_proba'):
            # SVM uses predict_proba
            y_train_pred_proba = model.predict_proba(X_train)[:, 1]
            y_train_pred = (y_train_pred_proba >= 0.5).astype(int)
            y_val_pred_proba = model.predict_proba(X_val)[:, 1]
            y_val_pred = (y_val_pred_proba >= 0.5).astype(int)
        else:
            # Regression models (Lasso and RF)
            y_train_pred = model.predict(X_train)
            y_val_pred = model.predict(X_val)
        
        # Calculate R2 and MSE for training
        mse_train = np.mean((y_train - y_train_pred) ** 2)
        r2_train = 1 - np.sum((y_train - y_train_pred) ** 2) / np.sum((y_train - np.mean(y_train)) ** 2)
        
        # Calculate R2 and MSE for validation
        mse_val = np.mean((y_val - y_val_pred) ** 2)
        r2_val = 1 - np.sum((y_val - y_val_pred) ** 2) / np.sum((y_val - np.mean(y_val)) ** 2)
        
        metrics[name]['r2_train'] = r2_train
        metrics[name]['r2_val'] = r2_val
        metrics[name]['mse_train'] = mse_train
        metrics[name]['mse_val'] = mse_val
        
        # Calculate confusion matrix (using validation set)
        y_val_pred_binary = (y_val_pred >= 0.5).astype(int)
        tp = np.sum((y_val == 1) & (y_val_pred_binary == 1))
        fp = np.sum((y_val == 0) & (y_val_pred_binary == 1))
        fn = np.sum((y_val == 1) & (y_val_pred_binary == 0))
        tn = np.sum((y_val == 0) & (y_val_pred_binary == 0))
        
        # Calculate precision and sensitivity
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        metrics[name]['precision'] = precision
        metrics[name]['sensitivity'] = sensitivity
        metrics[name]['confusion_matrix'] = {
            'tp': tp, 'fp': fp,
            'fn': fn, 'tn': tn
        }
    
    # Save metrics to file
    reports_dir = os.path.join(settings['PROJ_ROOT'], 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    with open(os.path.join(reports_dir, 'model_evaluation.txt'), 'w') as f:
        f.write("Model Evaluation Metrics\n")
        f.write("=" * 80 + "\n\n")
        
        for model_name, model_metrics in metrics.items():
            f.write(f"{model_name} Metrics:\n")
            f.write("-" * 40 + "\n")
            f.write(f"R² (Training): {model_metrics['r2_train']:.3f}\n")
            f.write(f"R² (Validation): {model_metrics['r2_val']:.3f}\n")
            f.write(f"MSE (Training): {model_metrics['mse_train']:.3f}\n")
            f.write(f"MSE (Validation): {model_metrics['mse_val']:.3f}\n")
            f.write(f"Precision: {model_metrics['precision']:.3f}\n")
            f.write(f"Sensitivity: {model_metrics['sensitivity']:.3f}\n")
            f.write("\nConfusion Matrix:\n")
            cm = model_metrics['confusion_matrix']
            f.write(f"True Positives: {cm['tp']}\n")
            f.write(f"False Positives: {cm['fp']}\n")
            f.write(f"False Negatives: {cm['fn']}\n")
            f.write(f"True Negatives: {cm['tn']}\n")
            f.write("\n" + "=" * 80 + "\n\n")
    
    return metrics

def save_threshold_analysis(train_data, train_data_scaled, validation_data, validation_data_scaled, rf_model, lasso_model, svm_model):
    """
    Generate and save threshold analysis for each model.
    Uses the same prepare_model_predictions/dynamische_evaluatie pipeline as the plots
    to ensure consistent precision/recall values.

    Parameters:
        train_data: DataFrame containing unscaled training data (for Random Forest)
        train_data_scaled: DataFrame containing scaled training data (for Lasso and SVM)
        validation_data: DataFrame containing unscaled validation data (for Random Forest)
        validation_data_scaled: DataFrame containing scaled validation data (for Lasso and SVM)
        rf_model: Trained Random Forest model
        lasso_model: Trained Lasso model
        svm_model: Trained SVM model
    """
    # Use the same pipeline as the plots: prepare_model_predictions -> dynamische_evaluatie
    model_configs = {
        'Random Forest': (validation_data, rf_model, 'rf'),
        'Lasso': (validation_data_scaled, lasso_model, 'lasso'),
        'SVM': (validation_data_scaled, svm_model, 'svm')
    }

    metrics = {}
    for name, (data, model, short_name) in model_configs.items():
        eval_results = prepare_model_predictions(data, model, short_name)
        precision_col = f'precision{short_name}'
        recall_col = f'recall{short_name}'
        pct_col = 'perc_uitgenodigde_studenten'

        model_metrics = []
        for _, row in eval_results.iterrows():
            model_metrics.append({
                'percentage': row[pct_col],
                'precision': row[precision_col],
                'recall': row[recall_col]
            })
        metrics[name] = pd.DataFrame(model_metrics)

    # Save results to file
    reports_dir = os.path.join(settings['PROJ_ROOT'], 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    with open(os.path.join(reports_dir, 'threshold_analysis.txt'), 'w') as f:
        f.write("Threshold Analysis Results\n")
        f.write("=" * 80 + "\n\n")

        for name, df in metrics.items():
            f.write(f"{name} Model:\n")
            f.write("-" * 40 + "\n")
            f.write("Percentage  Precision  Recall\n")
            f.write("-" * 40 + "\n")

            # Write metrics for key percentages (find closest match)
            key_percentages = [1, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100]
            for p in key_percentages:
                closest_idx = (df['percentage'] - p).abs().idxmin()
                row = df.loc[closest_idx]
                f.write(f"{row['percentage']:>9.1f}%  {row['precision']:>9.3f}  {row['recall']:>7.3f}\n")

            f.write("\n" + "=" * 80 + "\n\n")

    return metrics

def get_stoplight_evaluation(precision, recall):
    if precision >= 40 and recall >= 40:
        return "🟢", "Betrouwbaar", "Model presteert goed voor gerichte interventies"
    elif precision >= 30 and recall >= 30:  # Yellow threshold at 30%
        return "🟡", "Gebruik met voorzichtigheid", "Model geeft matig signaal"
    else:
        return "🔴", "Niet bruikbaar", "Model heeft verbetering nodig"

def generate_stoplight_evaluation(model_predictions, invite_pct=20):
    """
    Generates a stoplicht evaluation dashboard for all models showing their usability
    based on precision and recall at different invitation percentages.
    
    Parameters:
        model_predictions: Dictionary with model names as keys and tuples of (data, model, needs_scaling) as values
        invite_pct: main decision threshold percentage (default 20%)
    
    Returns:
        Dict with evaluation results for each model
    """
    def get_summary_message(precision, recall, pct, total_students, total_dropouts):
        # Calculate numbers from percentages
        n_invited = int(total_students * pct / 100)  # Calculate from percentage
        n_identified = int(total_dropouts * recall / 100)  # Number of dropouts identified
        n_correct = int(n_invited * precision / 100)  # Correct predictions among invited

        return (
            f"Bij {pct}% uitgenodigde studenten ({n_invited} uit {total_students} studenten):\n"
            f"- {recall:.1f}% van alle uitvallers wordt geïdentificeerd ({n_identified} van {total_dropouts} uitvallers)\n"
            f"- {precision:.1f}% van de uitgenodigde studenten valt daadwerkelijk uit ({n_correct} van {n_invited} uitgenodigde studenten)"
        )

    def get_metrics_from_eval_results(eval_results, model_name, threshold_pct):
        """Extract precision and recall at a given threshold from dynamische_evaluatie results."""
        pct_col = 'perc_uitgenodigde_studenten'
        precision_col = f'precision{model_name}'
        recall_col = f'recall{model_name}'

        # Find the row closest to the threshold percentage
        closest_idx = (eval_results[pct_col] - threshold_pct).abs().idxmin()
        precision = eval_results.loc[closest_idx, precision_col]
        recall = eval_results.loc[closest_idx, recall_col]

        return precision, recall

    # Get evaluation results for each model using the same pipeline as the plots
    # Map model display names to the short names used by prepare_model_predictions
    model_name_map = {'Random Forest': 'rf', 'Lasso': 'lasso', 'SVM': 'svm'}

    eval_results_all = {}
    model_data_info = {}
    for model_name, (data, model, needs_scaling) in model_predictions.items():
        dropout_col = settings.get('dropout_column', 'Dropout')
        try:
            short_name = model_name_map.get(model_name, model_name.lower())
            eval_results = prepare_model_predictions(data, model, short_name)
            eval_results_all[model_name] = (eval_results, short_name)
            model_data_info[model_name] = {
                'total_students': len(data),
                'total_dropouts': int(data[dropout_col].sum())
            }
        except Exception as e:
            print(f"Warning: Prediction failed for {model_name}: {e}")
            eval_results_all[model_name] = (None, model_name.lower())
    
    # Create figure with subplots
    fig = plt.figure(figsize=(12, 8))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 2])
    
    # Stoplight dashboard (top)
    ax_dashboard = fig.add_subplot(gs[0, :])
    ax_dashboard.axis('off')
    
    # Summary table (middle)
    ax_summary = fig.add_subplot(gs[1, :])
    ax_summary.axis('off')
    
    # Find metrics for different thresholds
    thresholds = [20, 30, 40, 50]  # Percentages to evaluate
    summary_data = []
    evaluation_metrics = {}

    for model_name, (eval_results, short_name) in eval_results_all.items():
        if eval_results is None:
            continue
        model_metrics = []
        for threshold in thresholds:
            precision, recall = get_metrics_from_eval_results(eval_results, short_name, threshold)
            # precision and recall from dynamische_evaluatie are already as fractions (0-1)
            model_metrics.append((threshold, precision, recall))

            # If this is the main threshold (20%), get stoplight evaluation
            if threshold == invite_pct:
                prec_pct = precision * 100
                rec_pct = recall * 100
                stoplight, status, message = get_stoplight_evaluation(prec_pct, rec_pct)
                info = model_data_info[model_name]
                summary = get_summary_message(prec_pct, rec_pct, threshold, info['total_students'], info['total_dropouts'])
                evaluation_metrics[model_name] = {
                    'precision': prec_pct,
                    'recall': rec_pct,
                    'status': status,
                    'message': message,
                    'dutch_summary': summary
                }

        # Add to summary table data
        summary_data.append([
            model_name,
            *[f"{p*100:.1f}% / {r*100:.1f}%" for _, p, r in model_metrics]
        ])
    
    # Create main dashboard table (20% threshold)
    dashboard_data = []
    for model_name, metrics in evaluation_metrics.items():
        dashboard_data.append([
            model_name,
            f"{metrics['precision']:.1f}%",
            f"{metrics['recall']:.1f}%",
            metrics['status']
        ])
    
    # Create dashboard table
    dashboard_table = ax_dashboard.table(
        cellText=dashboard_data,
        colLabels=['Model', 'Precisie', 'Recall', 'Status'],
        loc='center',
        cellLoc='center',
        colWidths=[0.3, 0.2, 0.2, 0.3]
    )
    
    # Style the dashboard table
    dashboard_table.auto_set_font_size(False)
    dashboard_table.set_fontsize(10)
    dashboard_table.scale(1, 1.5)
    
    # Add dashboard title
    ax_dashboard.set_title('Model Bruikbaarheid Dashboard (20% Uitnodigingen)', 
                          pad=20, fontsize=12)
    
    # Create summary table
    summary_table = ax_summary.table(
        cellText=summary_data,
        colLabels=['Model', '20% (P/R)', '30% (P/R)', '40% (P/R)', '50% (P/R)'],
        loc='center',
        cellLoc='center',
        colWidths=[0.2, 0.2, 0.2, 0.2, 0.2]
    )
    
    # Style the summary table
    summary_table.auto_set_font_size(False)
    summary_table.set_fontsize(10)
    summary_table.scale(1, 1.5)
    
    # Add summary title
    ax_summary.set_title('Model Prestaties bij Verschillende Uitnodigingspercentages\n(Precisie / Recall)', 
                        pad=20, fontsize=12)
    
    # Add precision and recall plots (bottom)
    ax_precision = fig.add_subplot(gs[2, 0])
    ax_recall = fig.add_subplot(gs[2, 1])
    
    # Plot precision and recall for each model using eval results
    for model_name, (eval_results, short_name) in eval_results_all.items():
        if eval_results is None:
            continue
        pct_col = 'perc_uitgenodigde_studenten'
        precision_col = f'precision{short_name}'
        recall_col = f'recall{short_name}'

        percentages = eval_results[pct_col].values
        precisions = eval_results[precision_col].values * 100
        recalls = eval_results[recall_col].values * 100

        # Plot precision
        ax_precision.plot(percentages, precisions, label=model_name)

        # Plot recall
        ax_recall.plot(percentages, recalls, label=model_name)
    
    # Add threshold lines
    for threshold in thresholds:
        ax_precision.axvline(x=threshold, color='gray', linestyle='--', alpha=0.5, label=f'{threshold}% drempel' if threshold == thresholds[0] else None)
        ax_recall.axvline(x=threshold, color='gray', linestyle='--', alpha=0.5, label=f'{threshold}% drempel' if threshold == thresholds[0] else None)
    
    # Add yellow threshold line
    ax_precision.axhline(y=30, color='yellow', linestyle='--', alpha=0.5, label='Gele drempel')
    ax_recall.axhline(y=30, color='yellow', linestyle='--', alpha=0.5, label='Gele drempel')
    
    # Set plot properties
    for ax, title, ylabel in [(ax_precision, 'Precisie per Uitnodigingspercentage', 'Precisie %'),
                             (ax_recall, 'Recall per Uitnodigingspercentage', 'Recall %')]:
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 101)
        ax.set_xlabel('% Uitgenodigde Studenten')
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    plt.tight_layout()
    
    # Save the plot
    save_plot(plt, 'model_usability_dashboard')
    
    # Save summary table to a separate file
    reports_dir = os.path.join(settings['PROJ_ROOT'], 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    with open(os.path.join(reports_dir, 'model_summary_table.txt'), 'w', encoding='utf-8') as f:
        f.write("Model Prestaties bij Verschillende Uitnodigingspercentages\n")
        f.write("=" * 80 + "\n\n")
        f.write("Format: Precisie% / Recall%\n\n")
        f.write(f"{'Model':<20} {'20%':<15} {'30%':<15} {'40%':<15} {'50%':<15}\n")
        f.write("-" * 80 + "\n")
        for row in summary_data:
            f.write(f"{row[0]:<20} {row[1]:<15} {row[2]:<15} {row[3]:<15} {row[4]:<15}\n")
    
    # Find the best model based on precision and recall at invite_pct
    best_model = None
    best_score = -1
    for model_name, metrics in evaluation_metrics.items():
        # Calculate a combined score (you can adjust the weights)
        score = (metrics['precision'] * 0.6 + metrics['recall'] * 0.4)  # Weight precision slightly higher
        if score > best_score:
            best_score = score
            best_model = model_name
    
    # Add recommendation to evaluation metrics
    evaluation_metrics['Aanbeveling'] = {'model': best_model}
    
    return evaluation_metrics

def extract_model_data(lines, model_name):
    """
    Extract model data from threshold analysis file lines.
    
    Parameters:
        lines: List of lines from threshold analysis file
        model_name: Name of the model to extract data for
        
    Returns:
        List of dictionaries with precision, recall, and percentage data
    """
    data = []
    start_collecting = False
    for line in lines:
        # Look for model section headers
        if f"{model_name} Model:" in line:
            start_collecting = True
            continue
        if start_collecting and line.strip() and not line.startswith("-"):
            if "Percentage" in line or "Precision" in line or "Recall" in line:
                continue
            if "=" in line:  # Stop at separator line
                break
            # Parse the data line - format: "1%      0.000    0.000"
            parts = line.strip().split()
            if len(parts) >= 3:
                try:
                    # Remove % symbol and convert to float
                    pct_str = parts[0].replace('%', '')
                    precision = float(parts[1]) * 100  # Convert to percentage
                    recall = float(parts[2]) * 100     # Convert to percentage
                    pct = float(pct_str)
                    
                    data.append({
                        'Precisie (%)': precision,
                        'Recall (%)': recall,
                        '% Uitgenodigd': pct
                    })
                except (ValueError, IndexError):
                    continue
    return data

def sort_and_filter_data(data):
    """
    Sort and filter data to show specific percentages.
    Uses closest-match to handle percentages that don't land exactly on target values.

    Parameters:
        data: List of dictionaries with model data

    Returns:
        DataFrame with filtered and sorted data
    """
    df = pd.DataFrame(data)
    target_pcts = [2.5, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]

    # For each target percentage, find the closest available row
    selected_rows = []
    for target in target_pcts:
        closest_idx = (df['% Uitgenodigd'] - target).abs().idxmin()
        selected_rows.append(df.loc[closest_idx])

    result = pd.DataFrame(selected_rows).drop_duplicates()
    result = result.sort_values('% Uitgenodigd')
    return result

def process_evaluation_results(evaluation_results):
    """
    Process evaluation results to create model results list and recommendation.
    
    Parameters:
        evaluation_results: Dictionary with evaluation results from generate_stoplight_evaluation
        
    Returns:
        Tuple of (model_results, best_model, best_metrics, recommendation_display, recommendation_text)
    """
    # Read and parse the threshold analysis data
    try:
        with open('reports/threshold_analysis.txt', 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []
    
    model_results = []
    for model_name, metrics in evaluation_results.items():
        if model_name != 'Aanbeveling':
            if metrics['status'] == "Betrouwbaar":
                indicator = "🟢 🟢 🟢 Het model kan worden gebruikt 🟢 🟢 🟢"
            elif metrics['status'] == "Gebruik met voorzichtigheid":
                indicator = "🟡 🟡 🟡 Gebruik met voorzichtigheid 🟡 🟡 🟡"
            else:
                indicator = "🔴 🔴 🔴 Niet bruikbaar 🔴 🔴 🔴"
            
            # Extract data
            model_data = extract_model_data(lines, model_name) if model_name in ['Random Forest', 'Lasso', 'SVM'] else None
            
            model_results.append({
                'name': model_name,
                'indicator': indicator,
                'metrics': metrics,
                'data': model_data
            })

    best_model = evaluation_results['Aanbeveling']['model']
    best_metrics = evaluation_results[best_model]

    if best_metrics['status'] == "Betrouwbaar":
        recommendation_display = "🟢 🟢 🟢 Het model kan worden gebruikt 🟢 🟢 🟢"
        recommendation_text = "Op basis van de evaluatie kan het model worden gebruikt."
    elif best_metrics['status'] == "Niet bruikbaar":
        recommendation_display = "🔴 🔴 🔴 Niet bruikbaar 🔴 🔴 🔴"
        recommendation_text = "Op basis van de evaluatie kan het model NIET worden gebruikt."
    else:
        recommendation_display = "🟡 Gebruik met voorzichtigheid 🟡"
        recommendation_text = f"Op basis van de evaluatie wordt het {best_model} model aanbevolen voor gebruik met voorzichtigheid."

    return model_results, best_model, best_metrics, recommendation_display, recommendation_text

def display_model_results(model_results, model_name):
    """
    Display results for a specific model.
    
    Parameters:
        model_results: List of model results from process_evaluation_results
        model_name: Name of the model to display
        
    Returns:
        String with formatted model results
    """
    result_text = ""
    for result in model_results:
        if result['name'] == model_name:
            result_text += result['indicator'] + "\n"
            result_text += f"\n**Precisie:** {result['metrics']['precision']:.1f}%\n"
            result_text += f"**Recall:** {result['metrics']['recall']:.1f}%\n"
            result_text += f"**Status:** {result['metrics']['status']}\n"
            result_text += f"**Evaluatie:** {result['metrics']['message']}\n"
            result_text += f"\n**Samenvatting:**\n"
            result_text += result['metrics']['dutch_summary'] + "\n"
            
            # Always show the table section, even if data is missing
            result_text += "\n**Prestaties bij Verschillende Uitnodigingspercentages**\n"
            
            if result['data'] and len(result['data']) > 0:
                df = sort_and_filter_data(result['data'])
                df = df.round(1)
                result_text += "\n| % Uitgenodigd | Precisie (%) | Recall (%) |\n"
                result_text += "|:-------------:|:------------:|:----------:|\n"
                for _, row in df.iterrows():
                    result_text += f"| {row['% Uitgenodigd']:>11.1f} | {row['Precisie (%)']:>11.1f} | {row['Recall (%)']:>10.1f} |\n"
            else:
                result_text += "\n*Geen gedetailleerde data beschikbaar voor dit model.*\n"
                result_text += "\n| % Uitgenodigd | Precisie (%) | Recall (%) |\n"
                result_text += "|:-------------:|:------------:|:----------:|\n"
                result_text += f"| 20.0 | {result['metrics']['precision']:>11.1f} | {result['metrics']['recall']:>10.1f} |\n"
            break
    
    return result_text

def get_coefficient_table(X_train, model, X_train_original):
    """
    Get coefficients for Lasso model, using original data for feature names.
    
    Parameters:
        X_train: DataFrame containing standardized training data
        model: Trained Lasso model
        X_train_original: DataFrame containing original (unstandardized) training data
        
    Returns:
        Series with coefficients scaled back to original scale
    """
    if isinstance(X_train, pd.DataFrame):
        # Get coefficients from standardized data
        coefs = pd.Series(model.coef_, index=X_train.columns)
        # Scale coefficients back to original scale
        feature_stds = X_train_original.std()
        coefs = coefs / feature_stds
    else:
        coefs = pd.Series(model.coef_, index=[f'Feature {i}' for i in range(len(model.coef_))])
    return coefs

def get_top_svm_features(validation_data, svm_model, train_data_sdd=None, n_features=5):
    """
    Helper function to get top N features from SVM model.
    
    Parameters:
        validation_data: DataFrame containing validation data with 'Dropout' column
        svm_model: Trained SVM model
        train_data_sdd: DataFrame containing scaled training data (optional)
        n_features: Number of top features to return (default 5)
        
    Returns:
        List of tuples with (feature_name, importance) sorted by importance
    """
    
    # Get dropout column from settings
    dropout_col = settings.get('dropout_column', 'Dropout')
    
    # Use training data if provided, otherwise use validation data
    data = train_data_sdd.copy() if train_data_sdd is not None else validation_data.copy()
    
    # Clean and prepare data
    data = data.fillna(data.mean())
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.fillna(data.mean())
    
    X = data.drop(dropout_col, axis=1)
    feature_names = X.columns
    
    # Calibrate the model
    calibrated_svm = CalibratedClassifierCV(svm_model, method="sigmoid", cv="prefit")
    calibrated_svm.fit(X, data[dropout_col])
    
    # Get original probabilities
    prob_original = calibrated_svm.predict_proba(X)[:, 1]
    
    # Calculate feature importance using perturbation
    perturbation = 1.0
    feature_stds = X.std()
    feature_importance = []
    
    for feature_name in feature_names:
        X_perturbed = X.copy()
        feature_perturbation = perturbation * feature_stds[feature_name]
        X_perturbed[feature_name] = X_perturbed[feature_name] + feature_perturbation
        prob_perturbed = calibrated_svm.predict_proba(X_perturbed)[:, 1]
        prob_change = np.mean(prob_perturbed - prob_original)
        feature_importance.append((feature_name, abs(prob_change)))
    
    # Sort by importance and get top N
    feature_importance.sort(key=lambda x: x[1], reverse=True)
    return feature_importance[:n_features]

def analyze_missing_data(data):
    """
    Analyze missing data in a DataFrame and return summary statistics.
    
    Parameters:
        data: DataFrame to analyze
        
    Returns:
        Tuple of (missing_summary_df, total_missing, total_rows, total_cols, missing_cols)
    """
    missing_summary = pd.DataFrame({
        'Type': data.dtypes,
        'Aantal_Missing': data.isnull().sum(),
        'Percentage_Missing': (data.isnull().sum() / len(data) * 100).round(1)
    })
    
    total_missing = data.isnull().sum().sum()
    total_rows = len(data)
    total_cols = len(data.columns)
    missing_cols = (data.isnull().sum() > 0).sum()
    
    return missing_summary, total_missing, total_rows, total_cols, missing_cols

def parse_model_metrics(metrics_file_path='reports/model_evaluation.txt'):
    """
    Parse model evaluation metrics from file and return formatted data.
    
    Parameters:
        metrics_file_path: Path to the model evaluation file
        
    Returns:
        List of dictionaries with model metrics data
    """
    try:
        with open(metrics_file_path, 'r') as f:
            metrics_text = f.read()
    except FileNotFoundError:
        return []
    
    metrics_data = []
    lines = metrics_text.split('\n')
    current_model = None
    r2_train = None
    r2_test = None
    mse_train = None
    mse_test = None
    
    for line in lines:
        line = line.strip()
        if 'Metrics:' in line and not line.startswith('Model Evaluation') and not line.startswith('='):
            current_model = line.split(' Metrics:')[0].strip()
            # Reset values for new model
            r2_train = None
            r2_test = None
            mse_train = None
            mse_test = None
        elif 'R² (Training):' in line and current_model:
            r2_train = float(line.split(':')[1].strip())
        elif 'R² (Validation):' in line and current_model:
            r2_test = float(line.split(':')[1].strip())
        elif 'MSE (Training):' in line and current_model:
            mse_train = float(line.split(':')[1].strip())
        elif 'MSE (Validation):' in line and current_model:
            mse_test = float(line.split(':')[1].strip())
            # Add the complete model data if we have all values
            if all(v is not None for v in [r2_train, r2_test, mse_train, mse_test]):
                metrics_data.append({
                    'Model': current_model,
                    'R² (train)': r2_train,
                    'MSE (train)': mse_train,
                    'R² (test)': r2_test,
                    'MSE (test)': mse_test
                })
    
    return metrics_data

def display_top_features(model, data, model_type, n_features=5, dropout_column='Dropout'):
    """
    Display top features for any model type.
    
    Parameters:
        model: Trained model object
        data: DataFrame containing the data
        model_type: String indicating model type ('rf', 'lasso', 'svm')
        n_features: Number of top features to display
        dropout_column: Name of the dropout column
        
    Returns:
        String with formatted feature importance table
    """
    X = data.drop(dropout_column, axis=1)
    
    if model_type == 'rf':
        # Random Forest feature importances
        feature_importances = pd.Series(
            model.feature_importances_,
            index=X.columns
        )
        top_features = feature_importances.iloc[feature_importances.abs().argsort()[::-1]].head(n_features)
        
        result = "\n| Feature | Belang |\n"
        result += "|:--------|:-------|\n"
        for feature, importance in top_features.items():
            result += f"| {feature} | {importance:.4f} |\n"
            
    elif model_type == 'lasso':
        # Lasso coefficients
        coefs = pd.Series(model.coef_, index=X.columns)
        top_coefs = coefs.iloc[coefs.abs().argsort()[::-1]].head(n_features)
        
        result = "\n| Feature | Coefficient |\n"
        result += "|:--------|:------------|\n"
        for feature, coef in top_coefs.items():
            result += f"| {feature} | {coef:.4f} |\n"
            
    elif model_type == 'svm':
        # SVM feature importance using perturbation method
        top_features = get_top_svm_features(data, model, n_features=n_features)
        
        result = "\n| Feature | Belang |\n"
        result += "|:--------|:-------|\n"
        for feature, importance in top_features:
            result += f"| {feature} | {importance:.4f} |\n"
    
    return result 