import warnings
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import seaborn as sns
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio
from scipy.stats import ttest_ind
import plotly
import json
from src.Predictive_Maintenance.logger import logging

ARTIFACTS_DIR = "artifacts/eda/"

warnings.filterwarnings("ignore")

df = pd.read_csv("notebooks/data/data.csv")

def setup(df: pd.DataFrame) -> pd.DataFrame:
    def type_of_failure(row_name):
        if df.loc[row_name, 'TWF'] == 1:
            df.loc[row_name, 'type_of_failure'] = 'TWF'
        elif df.loc[row_name, 'HDF'] == 1:
            df.loc[row_name, 'type_of_failure'] = 'HDF'
        elif df.loc[row_name, 'PWF'] == 1:
            df.loc[row_name, 'type_of_failure'] = 'PWF'
        elif df.loc[row_name, 'OSF'] == 1:
            df.loc[row_name, 'type_of_failure'] = 'OSF'
        elif df.loc[row_name, 'RNF'] == 1:
            df.loc[row_name, 'type_of_failure'] = 'RNF'

    df.apply(lambda row: type_of_failure(row.name), axis=1)
    df['type_of_failure'].replace(np.NaN, 'no failure', inplace=True)
    df.drop(['TWF', 'HDF', 'PWF', 'OSF', 'RNF'], axis=1, inplace=True)
    logging.info("Created type_of_failure column")
    return df

def save_plot(fig, filename):
    filepath = Path(ARTIFACTS_DIR, filename)
    fig.write_image(filepath)
    return str(filepath)

def question_one(df):
    category_counts = df['type_of_failure'].value_counts()
    total_samples = len(df)
    category_percentages = (category_counts / total_samples) * 100
    categories = list(category_percentages.index)
    percentage_labels = list(category_percentages)
    percentage_labels = [f'{num:.2f}%' for num in percentage_labels]
    fig = px.histogram(df, x='type_of_failure', category_orders={'type_of_failure': categories})
    fig.update_traces(text=percentage_labels, textposition='auto')
    plot_path = save_plot(fig, 'question_one.png')
    logging.info("EDA Question 1 complete")
    return plot_path

def question_two(df):
    category_counts = df['Type'].value_counts()
    total_samples = len(df)
    category_percentages = (category_counts / total_samples) * 100
    categories = list(category_percentages.index)
    percentage_labels = list(category_percentages)
    percentage_labels = [f'{num:.2f}%' for num in percentage_labels]
    fig = px.histogram(df, x='Type', category_orders={'Type': categories})
    fig.update_traces(text=percentage_labels, textposition='auto')
    plot_path = save_plot(fig, 'question_two.png')
    logging.info("EDA Question 2 complete")
    return plot_path

def question_three(df):
    num_cols = ['Air temperature [K]', 'Process temperature [K]', 'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']
    fig1 = make_subplots(rows=5, cols=1, subplot_titles=num_cols, vertical_spacing=0.04)

    for i, col in enumerate(num_cols):
        box_plot = go.Box(x=df[col], name=col)
        fig1.add_trace(box_plot, row=i+1, col=1)

    fig1.update_layout(
        title="Distribution of Numerical Features",
        height=1200,
        width=900,
        title_text="Box plots"
    )

    plot_path1 = save_plot(fig1, 'question_three_boxplots.png')

    outlier_cols = ['Torque [Nm]', 'Rotational speed [rpm]']
    fig2 = make_subplots(rows=1, cols=2, subplot_titles=outlier_cols, vertical_spacing=0.03)

    for i, col in enumerate(outlier_cols):
        box_plot = go.Histogram(x=df[col], name=col)
        fig2.add_trace(box_plot, row=1, col=i+1)

    fig2.update_layout(
        title='Distribution of Torque and Rotational speed',
        yaxis_title='Frequency',
        title_text="Histograms",
        width=900
    )

    plot_path2 = save_plot(fig2, 'question_three_histograms.png')
    logging.info("EDA Question 3 complete")
    return {'boxplots': plot_path1, 'histograms': plot_path2}

def question_four(df):
    corr_matrix = df[['Air temperature [K]', 'Process temperature [K]', 'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]', 'Machine failure']].corr()
    fig = px.imshow(corr_matrix, zmin=-1, zmax=1, text_auto=True)
    fig.update_layout(
        title='Correlation Matrix',
        height=600,
        width=800
    )
    
    plot_path = save_plot(fig, 'question_four_correlation_matrix.png')

    test_cols = ['Air temperature [K]','Process temperature [K]', 'Rotational speed [rpm]', 'Torque [Nm]','Tool wear [min]']
    values = []
    for col in test_cols:
        failed = df[df['Machine failure'] == 1][col]
        non_failed = df[df['Machine failure'] == 0][col]
        t, p = ttest_ind(failed, non_failed)
        values.append([t, p])

    values = pd.DataFrame(values, columns=['test-statistic', 'p-value'], index=test_cols)
    alpha = 0.05
    values['Hypothesis'] = values['p-value'].apply(lambda p: 'Reject null hypothesis' if p < alpha else 'Accept null hypothesis')
    value_path = Path(ARTIFACTS_DIR, 'question_four_ttest.json')
    values.to_json(value_path, orient='split')
    logging.info("EDA Question 4 complete")
    return {'correlation_matrix': plot_path, 'ttest': str(value_path)}

def question_five(df):
    num_cols = ['Air temperature [K]','Process temperature [K]', 'Rotational speed [rpm]', 'Torque [Nm]','Tool wear [min]']
    fig = make_subplots(rows=5, cols=1, subplot_titles=num_cols, vertical_spacing=0.03, horizontal_spacing=0.01)
    for i, col in enumerate(num_cols):
        violin_trace = go.Violin(x=df['Type'], y=df[col], name=col, box_visible=True, meanline_visible=True)
        fig.add_trace(violin_trace, row=i+1, col=1)
    fig.update_layout(height=2000, width=800, title_text="Subplots")
    plot_path = save_plot(fig, 'question_five_violin_plots.png')
    logging.info("EDA Question 5 complete")
    return plot_path

def question_six(df):
    num_cols = ['Air temperature [K]', 'Process temperature [K]', 'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']

    fig = make_subplots(rows=5, cols=5, shared_xaxes=True, shared_yaxes=True, vertical_spacing=0.02, horizontal_spacing=0.02)

    for i, col1 in enumerate(num_cols):
        for j, col2 in enumerate(num_cols):
            if i == j:
                fig.add_trace(go.Histogram(x=df[col1], name=col1, showlegend=False), row=i+1, col=j+1)
            else:
                fig.add_trace(go.Scatter(x=df[col2], y=df[col1], mode='markers', name=f'{col1} vs {col2}', showlegend=False, marker=dict(size=3)), row=i+1, col=j+1)

    fig.update_layout(
        title="Pair Plot of Continuous Variables",
        height=1200,
        width=1200,
        title_x=0.5
    )

    plot_path = save_plot(fig, 'question_six_pairplot.png')
    logging.info("EDA Question 6 complete")
    return plot_path

# def question_seven(df):
#     df['Date'] = pd.to_datetime(df['Date'])
#     df['Year'] = df['Date'].dt.year

#     failure_counts = df[df['Machine failure'] == 1].groupby('Year').size()

#     fig = px.line(failure_counts, x=failure_counts.index, y=failure_counts.values, title="Machine Failure Trend Over Time")
#     fig.update_xaxes(title="Year")
#     fig.update_yaxes(title="Failure Count")
#     plot_path = save_plot(fig, 'question_seven_trend.png')
#     logging.info("EDA Question 7 complete")
#     return plot_path

def question_eight(df):
    num_cols = ['Air temperature [K]', 'Process temperature [K]', 'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']
    fig = make_subplots(rows=len(num_cols), cols=1, subplot_titles=num_cols, vertical_spacing=0.03)

    for i, col in enumerate(num_cols):
        for product_type in df['Type'].unique():
            data = df[df['Type'] == product_type][col]
            fig.add_trace(go.Box(y=data, name=product_type), row=i+1, col=1)

    fig.update_layout(height=1200, width=800, title="Distribution of Continuous Variables by Product Type")
    plot_path = save_plot(fig, 'question_eight_boxplots.png')
    logging.info("EDA Question 8 complete")
    return plot_path

def question_nine(df):
    fig = px.scatter(df, x='Air temperature [K]', y='Machine failure', title="Machine Failure vs. Air Temperature")
    fig.update_yaxes(title="Machine Failure (1=Yes, 0=No)")
    plot_path = save_plot(fig, 'question_nine_scatter.png')
    logging.info("EDA Question 9 complete")
    return plot_path

def get_eda_obj():
    with open(Path(ARTIFACTS_DIR, 'eda.json'), 'r') as f:
        eda_json = json.load(f)
    return eda_json

def run_eda(df):
    eda_results = {}
    df = setup(df)
    eda_results['question_one'] = question_one(df)
    eda_results['question_two'] = question_two(df)
    eda_results['question_three'] = question_three(df)
    eda_results['question_four'] = question_four(df)
    eda_results['question_five'] = question_five(df)
    eda_results['question_six'] = question_six(df)
    # eda_results['question_seven'] = question_seven(df)
    eda_results['question_eight'] = question_eight(df)
    eda_results['question_nine'] = question_nine(df)
    with open(Path(ARTIFACTS_DIR, 'eda.json'), 'w') as f:
        json.dump(eda_results, f)
    logging.info("EDA completed and results saved")

if __name__ == "__main__":
    df = pd.read_csv("notebooks/data/data.csv")
    run_eda(df)
    logging.info("EDA script executed successfully")
    
    import webbrowser
    from pathlib import Path

    ARTIFACTS_DIR = "artifacts/eda"

    def open_plot(filename):
        filepath = Path(ARTIFACTS_DIR, filename)
        webbrowser.open(f'file://{filepath.absolute()}')

    # Example: Open the plot for question one
    open_plot('question_one.png')
