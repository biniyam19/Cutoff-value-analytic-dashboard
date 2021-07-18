
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from plotly import graph_objs as go
import numpy as np
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import collections
from dash.exceptions import PreventUpdate
from scipy import stats
from sklearn import preprocessing
from sklearn.metrics import confusion_matrix


df = pd.read_csv("DataScientist_test_data.csv")
diagnosis_numeric = df['diagnosis'].apply(lambda x:1 if x=="M" else 0)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MATERIA])
server = app.server

df = df.iloc[:,2:32]# selecting the appropriate features
df = df.apply(pd.to_numeric, errors='coerce')
features = df.columns
card_selector = dbc.Card(
    [  dbc.CardBody(
            [
                #html.H4("Learn Dash with Charming Data", className="card-title"),
                html.H6("Feature:", className="card-subtitle"),
        dcc.Store(id='intermediate-value'), dcc.Store(id='youden-index'), dcc.Dropdown(
        id='xaxis',
        options=[{'label': i, 'value': i} for i in features],
        value = 'texture_mean', clearable=False, style={"color": "#000000"}), html.Label('Cutoff'),
    dcc.Slider(id='slider-sen', value= 0, tooltip = { 'always_visible': True } )

            ]
        ),
    ],
    color="dark",   
    inverse=True,   # change color of text 
    outline=False,  
)
    
card_graph1 = dbc.Card(
        dcc.Graph(id='feature-graphic', figure={}), body=True, color="secondary",
)

card_graph12 = dbc.Card(
        dcc.Graph(id='sen-spec-fig', figure={}), body=True, color="secondary",
)
   
app.layout = html.Div([html.Div(html.Div(
            children=[
                html.H1(
                    children="Breast Cancer Biomarker\'s Cutoff Analysis", style={'color': '#000000', 'font-size': '20px' }, className="header-title")]))  ,
    dbc.Row([dbc.Col(card_selector, width=3, style={'margin-right': '50px'})], justify="end"),
    dbc.Row([    
             dbc.Col(card_graph1, width=5, className='h-10'),
             dbc.Col(card_graph12, width=7, className='h-10')], style={'margin-left': '50px', 'margin-right': '40px'}, 
        className='h-50 row mt-3', justify="around")])
    
@app.callback(
    Output('intermediate-value', 'data'),
    Input('xaxis', 'value'))

def clean_Data(xaxis_name):
    x=df[xaxis_name]
    return x

@app.callback([Output(component_id='slider-sen', component_property='min'),
               Output(component_id='slider-sen', component_property='max'),
               Output(component_id='slider-sen', component_property='step')],
              [Input(component_id='intermediate-value', component_property='data')])
   
def update_slider(selection):
    minimum = min(selection)
    maximum = max(selection)
    step = (maximum-minimum)/100
    return minimum, maximum, step 

@app.callback(
    Output('sen-spec-fig', 'figure'),
    [Input('xaxis', 'value'),
    Input('slider-sen', 'value')])

def Youden_index_calculator(xaxis, cut_off):
    sen_temp = []
    spec_temp = []
    youdens_inputs = []
    x = df[xaxis]
    cutoffs = np.linspace(start=min(x), stop = max(x), num = 1000)

    for cutoff in cutoffs:
        label_temp = x.apply(lambda x: 1 if x > cutoff else 0)
        conf_mat = confusion_matrix(label_temp,diagnosis_numeric)
       
        #compute TN, FN, FP, TP
        TN = conf_mat.flatten()[0]
        FN = conf_mat.flatten()[1]
        FP = conf_mat.flatten()[2]
        TP = conf_mat.flatten()[3]
        
        #compute sensitivity and specificity
        sensitivity = TP/(TP+FN)
        specificity = TN/(TN+FP)
        PPV           = TP/(TP+FP)
        NPV           = TN/(TN+FN)
        Youden_ind    = (TP/(TP+FN)) + (TN/(TN+FP))
        #appending current values
        youdens_inputs.append([sensitivity, specificity, PPV, NPV, Youden_ind, cutoff])
    
    youdens_inputs_df = pd.DataFrame(youdens_inputs)
    youdens_inputs_df.columns = ['sensitivity', 'specificity', 'PPV', 'NPV', 'Youden_ind', 'cutoff']
    selected_df = youdens_inputs_df[youdens_inputs_df.cutoff>cut_off].reset_index(drop=True)
    sen  = selected_df.sensitivity[0]
    spec = selected_df.specificity[0]
    ppv  = selected_df.PPV[0]
    npv  = selected_df.NPV[0]
    youden_ind = sen + spec
#     return { 'data':[{
#         'y':['Sensitivity','Specificity','PPV','NPV'] , 'x':[sen, spec, ppv, npv], 'type':'bar', 'name':'Cutoff value', 'orientation': 'h' 
#     }]
        
#     }
    if (sen+spec) > (youden_ind-0.1):
        return {'data':[go.Bar( y= ['sen+spec', 'NPV', 'PPV','Spec','Sen'] , x= [youden_ind,npv, ppv, spec, sen], orientation= 'h', marker=dict(color='#0000FF')
        )],  'layout': {'title': 'Cutoff\'s resulting metrics ({})'.format(xaxis.replace("_", " ").title())}}
    else:
        return {'data':[go.Bar( y= ['sen+spec', 'NPV', 'PPV','Spec','Sen'] , x= [youden_ind,npv, ppv, spec, sen], orientation= 'h', marker=dict(color='#FF0000') 
        )],  'layout': {'title': 'Cutoff\'s resulting metrices {}'.format(xaxis.replace("_", " ").title()) }}

@app.callback(
    Output('feature-graphic', 'figure'),
    [Input('intermediate-value', 'data'),
    Input('xaxis', 'value')])

def update_graph(selected_var, xaxis):   
    Hist_df = pd.DataFrame(selected_var)
    Hist_df.columns = ['selected_var']
    Hist_df['diagnosis']= diagnosis_numeric
    #print(Hist_df)
    malignant = Hist_df[Hist_df.diagnosis==0]
    benign = Hist_df[Hist_df.diagnosis==1]

    return {
        'data':[go.Histogram(
            x=malignant['selected_var'], histnorm='probability', marker=dict(color='#00ff00'), name='Benign'
        ), go.Histogram(
            x=benign['selected_var'], histnorm='probability', marker=dict(color='#FFA500'), name = 'Malignant'
        )], 'layout': {'title': 'Histogram of {}'.format(xaxis.replace("_", " ").title()) + ' by Diagnosis', 'xaxis':dict(title = xaxis.replace("_", " ").title()),
                       'yaxis': dict(title = 'Density')}
#         
    }

@app.callback(
    Output('youden-index', 'data'),
    [Input('xaxis', 'value')])

def update_youden(xaxis):
    
    #initializing 
    #cut_off = 200
    sen_temp = []
    spec_temp = []
    youdens_inputs = []
    x = df[xaxis]
    cutoffs = np.linspace(start=min(x), stop = max(x), num = 1000)

    for cutoff in cutoffs:
        label_temp = x.apply(lambda x: 1 if x > cutoff else 0)
        conf_mat = confusion_matrix(label_temp,diagnosis_numeric)
       
        #compute TN, FN, FP, TP
        TN = conf_mat.flatten()[0]
        FN = conf_mat.flatten()[1]
        FP = conf_mat.flatten()[2]
        TP = conf_mat.flatten()[3]
        
        #compute sensitivity and specificity
        sensitivity = TP/(TP+FN)
        specificity = TN/(TN+FP)
        PPV           = TP/(TP+FP)
        NPV           = TN/(TN+FN)
        Youden_ind    = (TP/(TP+FN)) + (TN/(TN+FP))
        #appending current values
        youdens_inputs.append([sensitivity, specificity, PPV, NPV, Youden_ind, cutoff])
    
    youdens_inputs_df = pd.DataFrame(youdens_inputs)
    youdens_inputs_df.columns = ['sensitivity', 'specificity', 'PPV', 'NPV', 'Youden_ind', 'cutoff']
    
    return youdens_inputs_df.Youden_ind

@app.callback([Output(component_id='slider-youden', component_property='min'),
               Output(component_id='slider-youden', component_property='max'),
               Output(component_id='slider-youden', component_property='step')],
              [Input(component_id='youden-index', component_property='data')])
   
def update_slider_youden(youden):
    minimum = min(youden)
    maximum = max(youden)
    step = 0.01
    return minimum, maximum, step 
   
if __name__ == '__main__':
    app.run_server(debug=False)    

