import ast 
import databasewrappers_exp as dbexp
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_table_experiments as dt
import pandas as pd
import io
import os
import json
import plotly 
import base64
from lmfit.model import save_modelresult
from lmfit.model import load_modelresult
#from unittest.mock import patch
##########################################
#Load Data
##########################################
#eventually add everything in folder and create a dropdown that loads that data sinto data 
database = 'dqdvDataBaseDemo.db'
if not os.path.exists(database): 
	print('That database does not exist-creating it now.')
	dbexp.dbfs.init_master_table(database)
#datatype = 'CALCE'
#for now just use some data we have 
#data = pd.read_excel('data/Clean_Whole_Sets/CS2_33_12_16_10CleanSet.xlsx')
data = dbexp.dbfs.get_file_from_database('CS2_33_10_04_10CleanSet', 'dqdvDataBase_sortedpeaks4.db')
#these are just initial values to use:
slidmax = 15
slidmax2 = 15
#charge, discharge = dbexp.ccf.sep_char_dis(data, datatype)

#df_dqdv = ccf.calc_dv_dqdv('data/CS2_33/CS2_33_10_04_10.xlsx')
#df_dqdv = ccf.calc_dv_dqdv(data)
#charge, discharge = ccf.sep_char_dis(data)



##########################################
#App Layout 
##########################################
app = dash.Dash() #initialize dash 

Introduction= dcc.Markdown('''
        # dQ/dV
        ## Interface for visualizing battery cycle data
        #'''), #Add some Markdown


app.layout = html.Div([
    html.Div([
        html.H1('Quantitative dQ/dV Analysis and Visualization'),
        ]),

    html.Div([
        html.Br(),
        html.Div([html.H3('Choose existing data: '), 
		html.Div([html.Div([html.H6('Here are the files currently available in the database: ')],
	    style={'width': '90%', 'textAlign': 'left', 'margin-left':'50px'}),
	    html.Div([dcc.Dropdown(id ='available-data', options = 'options')], style={'width': '80%', 'vertical-align':'center', 'margin-left': '50px'}),
		html.Div(id = 'gen-desc-confirmation')])], style = {'width':'43%', 'display': 'inline-block', 'vertical-align': 'top'}),

        html.Div([html.H3('Or load in your own data: '),
        html.Div([html.Div([html.H5('1. Input your datatype: ')],style={'width': '40%', 'textAlign': 'left', 'display': 'inline-block', 'margin-left':'50px'}),
        		html.Div([dcc.Dropdown(id='input-datatype', 
        			options =[{'label':'Arbin', 'value':'CALCE'},{'label':'MACCOR', 'value':'MACCOR'}],  
        			placeholder='datatype')], 
        		style={'width': '40%', 'vertical-align':'top', 'display': 'inline-block', 
        		'margin-right': '10px', 'margin-left': '10px'})],
        		),

        html.Div([html.Div([html.H5('2. Upload your data: ')], style={'width': '40%', 'textAlign': 'left', 'display': 'inline-block', 'margin-left':'50px'}), 
            	html.Div([dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '98%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    #'margin': '10px'
                },
                multiple=False)], style= {'width': '40.2%', 'display': 'inline-block', 'margin-right': '10px', 'margin-left': '10px'}),
                html.Div(id = 'output-data-upload', style={'margin-left':'50px', 'font-size': '20px'}),
                html.Div(['Note: data will be saved in database with the original filename.'],
                	style={'margin-left':'50px', 'font-style':'italic'}), 
                html.Div(['Once data is uploaded, refresh this page and select the new data from the dropdown menu to the left.'],
                	style={'margin-left':'50px', 'font-style': 'italic'})],
                )], style = {'width': '55%', 'display': 'inline-block'}),
	        
        #html.H6('Input lower voltage range to exclude from the clean data: '),
        #dcc.Input(id='input-voltrange1', type='text', placeholder='0' ),
        #html.H6('Input upper voltage range to exclude from the clean data: '),
        #dcc.Input(id ='input-voltrange2', type='text', placeholder='0.03'),
        
        ##################

    
     
#################################################################3
    ]),

    html.Div([
        html.Br(),
        html.Div([html.H6('Cycle Number')], style ={'textAlign': 'left'}),
        dcc.Slider(
            id='cycle--slider',
            min=0,
            #min=charge['Cycle_Index'].min(),
            #max=data['Cycle_Index'].max(),
            max = slidmax,
            #value=charge['Cycle_Index'].max(),
            #value = data['Cycle_Index'].max(),
            value = slidmax2,
            step=1,
            included=True,
            marks={str(each): str(each) for each in range(slidmax)},
            #data['Cycle_Index'].unique()},
            #includes a mark for each step
            )
        ],
        style={
                'width': '98%',
                'margin': '10px'
                }
        ),

    html.Div([
        html.Br(),
        dcc.Graph(id='charge-graph'), #initialize a simple plot
        #html.Br(),
        #dcc.Graph(id='discharge-graph'),
        ],style={
            'columnCount': 1,
            'width':'98%',
            'height': '80%',
            }
        ),
    
    html.Div([
    	html.H4(['Explore Descriptors']),
        dcc.Checklist(id = 'show-poly', 
            options=[
                {'label': 'Show Polynomial Baseline', 'value': 'show'},
            ],
            values=['show'])]),
    html.Div([ 
	dcc.RadioItems(id = 'cd-to-plot', options=[ # 'sortedloc-c-1'
            {'label': '(+) dQ/dV', 'value': 'c-'}, 
            {'label': '(-) dQ/dV', 'value': 'd-'}
        ],
        value = ['c-'], labelStyle={'display': 'inline-block'}),
    dcc.RadioItems(id = 'desc-to-plot', options=[
        {'label': 'Peak Locations', 'value': 'sortedloc-'}, 
        {'label': 'Peak Areas', 'value': 'sortedarea-'},
        {'label': 'Peak Height', 'value': 'sortedactheight-'},
    ],
    value = ['sortedloc-'], labelStyle={'display': 'inline-block'}),
    dcc.Checklist(id = 'desc-peaknum-to-plot', 
        options=[
            {'label': 'Peak 1', 'value': '1'}, 
            {'label': 'Peak 2', 'value': '2'},
            {'label': 'Peak 3', 'value': '3'},
            {'label': 'Peak 4', 'value': '4'},
            {'label': 'Peak 5', 'value': '5'}, 
            {'label': 'Peak 6', 'value': '6'}, 
            {'label': 'Peak 7', 'value': '7'}, 
            {'label': 'Peak 8', 'value': '8'}, 
            {'label': 'Peak 9', 'value': '9'}, 
            {'label': 'Peak 10', 'value': '10'},
        ],
        values=['1'], labelStyle={'display': 'inline-block'})]),

    html.Div([
        html.Br(),
        dcc.Graph(id='model-graph'), #initialize a simple plot
        #html.Br(),
        #dcc.Graph(id='discharge-graph'),
        ],style={
            'columnCount': 1,
            'width':'98%',
            'height': '80%',
            }
        ),
    html.H4(['Update Model']),
    html.Div(['New Peak Detection Threshold (default is 0.7, must be between 0 and 1): '], style={'font-style':'italic'}), 
    html.Div([dcc.Input(id = 'new-peak-threshold', placeholder = 'threshold for peak detection')]),
    html.Div(['Location of new charge peak(s), separate each with a commma (V): '], style={'font-style':'italic'}), 
    html.Div([dcc.Input(id = 'charge-newpeak', placeholder = 'charge new peak')]),
    html.Div(['Location of new discharge peak(s), separate each with a commma (V): '], style={'font-style':'italic'}), 
    html.Div([dcc.Input(id = 'discharge-newpeak', placeholder = 'discharge new peak')]),
    html.Div(['After updating the threshold or new peak locations, you can update the preview of the model (one cycle shown here),'+
    	' and then update the model in the database once the model appears to be optimal.'], style={'font-style':'italic'}), 
    html.Div(id = 'update-model-ans'),
    html.Button('Update Preview of Model', id = 'update-model-button'),
    html.Button('Update Model in Database', id = 'update-model-indb-button'),    
    html.Div([
        html.H4('DataTable'),
        dt.DataTable(
            #rows=charge.to_dict('records'), #converts df to dict
            rows=[{}],
            #columns=sorted(charge.columns), #sorts columns
            row_selectable=True,
            filterable=True,
            selected_row_indices=[],
            id='datatable'
            ),
        html.Div(id='selected-indexes'),

        #html.H4('Discharge DataTable'),
        #dt.DataTable(
            #rows=discharge.to_dict('records'), #converts df to dict
         #   rows=[{}],
            #columns=sorted(discharge.columns), #sorts columns
         #   row_selectable=True,
        #    filterable=True,
        #    selected_row_indices=[],
        #    id='discharge-datatable'
        #    ),
        #html.Div(id='selected-indexes'),
        ],
        style={
            'width': '98%',
            #'height': '60px',
            #'lineHeight': '60px',
            'margin': '10px'
            },
        ), 
    html.Div(id='hidden-div', style={'display':'none'}) #this is so we can have a callback to run the process data function on the raw data inputted


])

##########################################
#Interactive Parts
##########################################

#@patch('databasewrappers_exp.process_data.input', create=True)

def parse_contents(contents, filename, datatype, thresh1, thresh2):
	# this is just to be used to get a df from an uploaded file

    if contents == None:
    	return html.Div(['No file has been uploaded, or the file uploaded was empty.'])
    else: 
    	content_type, content_string = contents.split(',')
    	decoded = base64.b64decode(content_string)
    # try: 
    	cleanset_name = filename.split('.')[0] + 'CleanSet'
    	#this gets rid of any filepath in the filename and just leaves the clean set name as it appears in the database 
    		#check to see if the database exists, and if it does, check if the file exists.
    	ans_p = dbexp.if_file_exists_in_db(database, filename)
    	if ans_p == True: 
    		df_clean = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    		v_toappend_c = []
    		v_toappend_d = []
    		new_peak_thresh = 0.7 # just as a starter value 
    		feedback = generate_model(v_toappend_c, v_toappend_d, df_clean, filename, new_peak_thresh)
    		return html.Div(['That file exists in the database: ' + str(filename.split('.')[0])])
    		#df = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    	else:
    		dbexp.process_data(filename, database, decoded, datatype, thresh1, thresh2)
    		df_clean = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    		v_toappend_c = []
    		v_toappend_d = []
    		new_peak_thresh = 0.7 # just as a starter value
    		feedback = generate_model(v_toappend_c, v_toappend_d, df_clean, filename, new_peak_thresh)
    		# maybe split the process data function into getting descriptors as well?
    		#since that is the slowest step 
    		return html.Div(['New file has been processed: ' + str(filename)])
    		
    		#df = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    	#have to pass decoded to it so it has the contents of the file
    # except Exception as e:
    #     print('THERE WAS A PROBLEM PROCESSING THE FILE: ' + str(e))
    #     #df = None
    #     return html.Div([
    #         'There was an error processing this file.'+ str(filename)
    #     ])
    #return html.Div([
    #        'Something else happened.'
    #    ])

	    #mocked_input.side_effect = ['CALCE', 'y', '4.17', '4.25']
	#try:   
    #this should take a raw file and process it, then put it in the database
########################################################################################
#########################################################################################
# this part should be ran everytime something is updated, keeping the filename. whenever the dropdown menu changes
def pop_with_db(filename, database):
    cleanset_name = filename.split('.')[0] + 'CleanSet'
    rawset_name = filename.split('.')[0] + 'Raw'
    #this gets rid of any filepath in the filename and just leaves the clean set name as it appears in the database 
    ans = dbexp.if_file_exists_in_db(database, filename)
    print(ans)
    if ans == True: 
    	# then the file exists in the database and we can just read it 
    	df_clean = dbexp.dbfs.get_file_from_database(cleanset_name, database)
    	df_raw = dbexp.dbfs.get_file_from_database(rawset_name, database)
    	datatype = df_clean.loc[0,('datatype')]
    	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
    	# for each cycle in the clean set, separate into charge and discharge and find peak indices for every cycle
    	#######################################comment all this out later
    	# chargeloc_dict = {}
    	# dischloc_dict = {}
    	# windowlength = 11
    	# polyorder = 1
    	# # change these to be user inputs - they are just the windowlength and polyorder for peak finding - not the overall one
    	# for each_cyc in df_clean[cycle_ind_col].unique():
    	# 	clean_charge, clean_discharge = dbexp.ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==each_cyc], datatype)
    	# 	i_charge, volts_i_ch = dbexp.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype)
    	# 	i_discharge, volts_i_dc = dbexp.descriptors.fitters.peak_finder(clean_discharge, 'd', windowlength, polyorder, datatype)
    	# 	#lenmax (equal to 200 here) does literally nothing as the code is written now on 9.13.18
    	# 	# this returns the peak locations as found by peakutils -plot these as vertical lines on
    	# 	chargeloc_dict.update({each_cyc: volts_i_ch})
    	# 	dischloc_dict.update({each_cyc: volts_i_dc})
    	############################################################
    else:
    	df_clean = None
    	df_raw = None
    	peakloc_dict = {}
    return df_clean, df_raw

def get_model_dfs(df_clean, datatype, cyc, v_toappend_c, v_toappend_d, lenmax, peak_thresh):
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
	clean_charge, clean_discharge = dbexp.ccf.sep_char_dis(df_clean[df_clean[cycle_ind_col] ==cyc], datatype)
	windowlength = 75
	polyorder = 3
	#####################################
	# length_dict = {key: len(value) for key, value in import_dictionary.items()}
 #    lenmax = max(length_dict.values())
    ######################################
	# speed this up by moving the initial peak finder out of this, and just have those two things passed to it 
	i_charge, volts_i_ch, peak_heights_c = dbexp.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype, lenmax, peak_thresh)
	#chargeloc_dict.update({cyc: volts_i_ch})
	V_series_c = clean_charge[volt_col]
	dQdV_series_c = clean_charge['Smoothed_dQ/dV']
	par_c, mod_c, indices_c = dbexp.descriptors.fitters.model_gen(V_series_c, dQdV_series_c, 'c', i_charge, cyc, v_toappend_c)
	model_c = dbexp.descriptors.fitters.model_eval(V_series_c, dQdV_series_c, 'c', par_c, mod_c)			
	if model_c is not None:
		mod_y_c = mod_c.eval(params = model_c.params, x = V_series_c)
		myseries_c = pd.Series(mod_y_c)
		myseries_c = myseries_c.rename('Model')
		model_c_vals = model_c.values
		new_df_mody_c = pd.concat([myseries_c, V_series_c, dQdV_series_c, clean_charge[cycle_ind_col]], axis = 1)
	else:
		mod_y_c = None
		new_df_mody_c = None
		model_c_vals = None
	# now the discharge: 
	i_discharge, volts_i_dc, peak_heights_d= dbexp.descriptors.fitters.peak_finder(clean_discharge, 'd', windowlength, polyorder, datatype, lenmax, peak_thresh)
	V_series_d = clean_discharge[volt_col]
	dQdV_series_d = clean_discharge['Smoothed_dQ/dV']
	par_d, mod_d, indices_d = dbexp.descriptors.fitters.model_gen(V_series_d, dQdV_series_d, 'd', i_discharge, cyc, v_toappend_d)
	model_d = dbexp.descriptors.fitters.model_eval(V_series_d, dQdV_series_d, 'd', par_d, mod_d)			
	if model_d is not None:
		mod_y_d = mod_d.eval(params = model_d.params, x = V_series_d)
		myseries_d = pd.Series(mod_y_d)
		myseries_d = myseries_d.rename('Model')
		new_df_mody_d = pd.concat([-myseries_d, V_series_d, dQdV_series_d, clean_discharge[cycle_ind_col]], axis = 1)
		model_d_vals = model_d.values
	else:
		mod_y_d = None
		new_df_mody_d = None
		model_d_vals = None
	# save the model parameters in the database with the data
	if new_df_mody_c is not None or new_df_mody_d is not None: 
		new_df_mody = pd.concat([new_df_mody_c, new_df_mody_d], axis = 0)
	else: 
		new_df_mody = None
	# combine the charge and discharge
	# update model_c_vals and model_d_vals with peak heights 
	
	return new_df_mody, model_c_vals, model_d_vals, peak_heights_c, peak_heights_d

def generate_model(v_toappend_c, v_toappend_d, df_clean, filename, peak_thresh):
	# run this when get descriptors button is pushed, and re-run it when user puts in new voltage 
	# create model based off of initial peaks 
	# show user model, then ask if more peak locations should be used (shoulders etc)
	datatype = df_clean.loc[0,('datatype')]
	(cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)

	chargeloc_dict = {}
	param_df = pd.DataFrame(columns = ['Cycle','Model_Parameters_charge', 'Model_Parameters_discharge'])
	#ans = dbexp.if_file_exists_in_db(database, filename)
	#if ans == True:
		#return html.Div(['A model for that filename already exists in the database.'])
	#else: 
	####################################################################
	length_list = [len(df_clean[df_clean[cycle_ind_col]==cyc]) for cyc in df_clean[cycle_ind_col].unique() if cyc != 1]
	lenmax = max(length_list)
	####################################################################
	mod_pointsdf = pd.DataFrame()
	for cyc in df_clean[cycle_ind_col].unique():
		#######################################################################9.15.18
		#i_charge, volts_i_ch = dbexp.descriptors.fitters.peak_finder(clean_charge, 'c', windowlength, polyorder, datatype)
		new_df_mody, model_c_vals, model_d_vals, peak_heights_c, peak_heights_d = get_model_dfs(df_clean, datatype, cyc, v_toappend_c, v_toappend_d, lenmax, peak_thresh)
		mod_pointsdf = mod_pointsdf.append(new_df_mody)
		param_df = param_df.append({'Cycle': cyc, 'Model_Parameters_charge': str(model_c_vals), 'Model_Parameters_discharge': str(model_d_vals), 'charge_peak_heights': str(peak_heights_c), 'discharge_peak_heights': str(peak_heights_d)}, ignore_index = True)
		#param_df = param_df.append({'Cycle': cyc, 'C/D': 'discharge', 'Model_Parameters': str(model_d_vals)}, ignore_index = True)
	# want this outside of for loop to update the db with the complete df of new params 
	dbexp.dbfs.update_database_newtable(mod_pointsdf, filename.split('.')[0]+ '-ModPoints', database)
	# this will replace the data table in there if it exists already 
	dbexp.dbfs.update_database_newtable(param_df, filename.split('.')[0] + 'ModParams', database)
	
	dbexp.param_dicts_to_df(filename.split('.')[0] + 'ModParams', database)		
			#save_model(model, path, saveas)
			# for index in indices: hjkhj

			# 	print('sigma for '+ str(index)+': '+ str(model.values['a'+str(index)+'_sigma']))
			# 	print('fraction for '+ str(index)+': '+ str(model.values['a'+str(index)+'_fraction']))
			# 	print('center for '+ str(index)+': '+ str(model.values['a'+str(index)+'_center']))
			# 	print('amplitude for '+ str(index)+': '+ str(model.values['a'+str(index)+'_amplitude']))
			# 	print('')
			# then discharge cycle:
#return html.Div([str(model.values)])
	return html.Div(['That model has been added to the database'])

##############################################################################################
#@app.callback(
#	Output('hidden-div', 'hidden'),
#	[Input('upload-data', 'contents'), 
#	 Input('upload-data', 'filename'), 
#	 Input('upload-data', 'last_modified')])

#def process_new_rawdata(contents, filename, date):
#	dbexp.process_data('data/example_files/Raw_Data_Examples/'+filename, database)
#	return None

@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename'), 
               Input('input-datatype', 'value')]) 
               #Input('input-voltrange1', 'value'), 
               #Input('input-voltrange2', 'value')])
def update_output(contents, filename, value):
	#value here is the datatype, then voltagerange1, then voltagerange2
    thresh1 = 0
    thresh2 = 0
    children = parse_contents(contents, filename, value, thresh1, thresh2)
    return children

@app.callback(Output('available-data', 'options'), 
			  [Input('output-data-upload', 'children')])
def update_dropdown(children):
	options = [{'label':i[:-3], 'value':i[:-3]} for i in dbexp.get_db_filenames(database)]
	return options

@app.callback(Output('update-model-ans', 'children'), 
			  [Input('available-data', 'value'), 
			   Input('charge-newpeak', 'value'), 
			   Input('discharge-newpeak', 'value'),
			   Input('update-model-indb-button', 'n_clicks'), 
			   Input('new-peak-threshold', 'value')])
def update_model_indb(filename, new_charge_vals, new_discharge_vals, n_clicks, new_peak_thresh):
	if n_clicks is not None:
		int_list_c = []
		int_list_d = []
		if new_charge_vals is not None: 
			new_list_c = new_charge_vals.split(',')
			for i in new_list_c:
			    int_list_c.append(float(i))
		else: 
			None
		if new_discharge_vals is not None: 
			new_list_d = new_discharge_vals.split(',')
			for i in new_list_d:
			    int_list_d.append(float(i))
		else: 
			None
		cleanset_name = filename.split('.')[0] + 'CleanSet'
		df_clean = dbexp.dbfs.get_file_from_database(cleanset_name, database)
		feedback = generate_model(int_list_c, int_list_d, df_clean, filename, new_peak_thresh)
	else:
		feedback = html.Div(['Model has not been updated yet.'])
	return feedback
	# maybe split the process data function into getting descriptors as well?
    		#since that is the slowest step 
# Make this app callback from a drop down menu selecting a filename in the database
# populate dropdown using master_table column= Dataset_Name
# sdksl
#@app.callback(Output('model-output', 'children'), 
#			  [Input('upload-data', 'filename')])
#def get_model_feedback(filename):
#	cleanset_name = filename.split('.')[0] + 'CleanSet'
#	rawset_name = filename.split('.')[0] + 'Raw'
#    #this gets rid of any filepath in the filename and just leaves the clean set name as it appears in the database 
#	ans = dbexp.if_file_exists_in_db(database, filename)
#	if ans == True: 
 #		# then the file exists in the database and we can just read it 
#		df_clean = dbexp.dbfs.get_file_from_database(cleanset_name, database)
#		v_toappend_c = [3.4]
#		v_toappend_d = [3.7]
#		feedback = generate_model(v_toappend_c, v_toappend_d, df_clean, filename)
#	else: 
#		feedback = html.Div(['That did not work.'])
#	return feedback


@app.callback( #update slider 
    Output('cycle--slider', 'max'),
    [Input('available-data', 'value')])

def update_slider_max(filename):
    data, raw_data= pop_with_db(filename, database)
    #charge, discharge = dbexp.ccf.sep_char_dis(data, datatype)
    datatype = data.loc[0,('datatype')]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
    slidmax = data['Cycle_Index'].max()
    return data['Cycle_Index'].max()

@app.callback(#update slider marks
	Output('cycle--slider', 'marks'), 
	[Input('available-data', 'value')])

def update_slider_marks(filename):
	data, raw_data= pop_with_db(filename, database)
	return {str(each): str(each) for each in data['Cycle_Index'].unique()}

@app.callback( #update slider 
    Output('cycle--slider', 'value'),
    [Input('available-data', 'value')])

def update_slider_value(filename):
    data, raw_data = pop_with_db(filename, database)
    #charge, discharge = dbexp.ccf.sep_char_dis(data, datatype)
    datatype = data.loc[0,('datatype')]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
    slidmax2 = data['Cycle_Index'].max()
    return data['Cycle_Index'].max()



@app.callback( #decorator wrapper for table 
        Output('datatable', 'selected_row_indices'), #component_id, component_property 
        [Input('charge-graph','clickData')],
        [State('datatable','selected_row_indices')]
        )

def update_selected_row_indices(clickData, selected_row_indices):
    if clickData:
        for point in clickData['points']:
            if point['pointNumber'] in selected_row_indices:
                selected_row_indices.remove(point['pointNumber'])
            else:
                selected_row_indices.append(point['pointNumber'])
    return selected_row_indices

@app.callback( #decorator wrapper for plot
        Output('charge-graph','figure'),
        [Input('cycle--slider','value'),
         Input('available-data', 'value'), # this will be the filename of the file 
         #Input('input-datatype', 'value'),
         Input('datatable','selected_row_indices')]
         #Input('upload-data','contents')]
        )

def update_figure1(selected_step,filename, selected_row_indices):
    data, raw_data= pop_with_db(filename, database)
    datatype = data.loc[0,('datatype')]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
    #stupid change
    modset_name = filename.split('.')[0] + '-ModPoints'
    df_model = dbexp.dbfs.get_file_from_database(modset_name, database)
    if df_model is not None: 
        filt_mod = df_model[df_model[cycle_ind_col] == selected_step]

    #(charge, discharge) = dbexp.ccf.sep_char_dis(data, datatype)
    # grab datattype from file:
    if data is not None:
        filtered_data = data[data[cycle_ind_col] == selected_step]
    if raw_data is not None:
        raw_filtered_data= raw_data[raw_data[cycle_ind_col]== selected_step]
    
    #filt_chargeloc = chargeloc_dict[selected_step] # this returns a list [] of peak indices
    #filt_disloc = dischloc_dict[selected_step]
    for i in filtered_data[cycle_ind_col].unique():
        if data is not None:
            dff = filtered_data[filtered_data[cycle_ind_col] == i]
        if raw_data is not None:
            dff_raw = raw_filtered_data[raw_filtered_data[cycle_ind_col] == i]
        if df_model is not None:
            dff_mod = filt_mod[filt_mod[cycle_ind_col] == i]
        fig = plotly.tools.make_subplots(
            rows=1,cols=2,
            subplot_titles=('Raw Cycle','Smoothed Cycle'),
            shared_xaxes=True)
        marker = {'color': ['#0074D9']}
                #fig.append_trace({'x': [2.0, 2.0],'y': [0, 2.0], 'type': 'line', 'name': 'Peak Position'}, 1, 2

        for i in (selected_row_indices or []):
            marker['color'][i] = '#FF851B'
        if data is not None:
            fig.append_trace({
                'x': dff[volt_col],
                'y': dff['Smoothed_dQ/dV'],
                'type': 'scatter',
                'marker': marker,
                'name': 'Smoothed Data'
                }, 1, 2)
        if raw_data is not None:
            fig.append_trace({
                'x': dff_raw[volt_col],
                'y': dff_raw['dQ/dV'],
                'type': 'scatter',
                'marker': marker,
                'name': 'Raw Data'
                }, 1, 1)
        if df_model is not None:   
            fig.append_trace({
                'x':dff_mod[volt_col], 
                'y':dff_mod['Model'] ,
                'type': 'scatter',
                'name': 'Model'
                }, 1,2)
        #fig.append_trace({'x': (2.0, 2.0),'y': (0, 2.0), 'type': 'line', 'name': 'Peak Position'}, 1, 2)
        # shapes = list()
        # for vline in filt_chargeloc:
        # 	shapes.append({'type':'line',
        # 		   'x0' : vline, 
        # 		   'y0':0, 
        # 		   'x1':vline, 
        # 		   'y1': dff['dQ/dV'].max(), 
        # 		   'line': {
        # 		   	   'color':'rgb(128, 0, 128)',
        # 		   	   'width': 2, 
        # 		   	   'dash': 'dashdot'}})
        # for vline in filt_disloc:
        # 	shapes.append({'type':'line',
        # 		   'x0' : vline, 
        # 		   'y0':0, 
        # 		   'x1':vline, 
        # 		   'y1': dff['dQ/dV'].min(), 
        # 		   'line': {
        # 		   	   'color':'rgb(128, 0, 128)',
        # 		   	   'width': 2, 
        # 		   	   'dash': 'dashdot'}})
        
        fig['layout']['showlegend'] = False
        #fig['layout']['shapes'] = shapes
        fig['layout']['xaxis1'].update(title = 'Voltage (V)')
        fig['layout']['xaxis2'].update(title = 'Voltage (V)')
        fig['layout']['yaxis1'].update(title = 'dQ/dV')
        fig['layout']['yaxis2'].update(title = 'dQ/dV')
        fig['layout']['height'] = 600
        fig['layout']['margin'] = {
            'l': 40,
            'r': 10,
            't': 60,
            'b': 200
            }
        #fig['layout']['yaxis'] = {'title': 'dQ/dV'}
    return fig

@app.callback( #decorator wrapper for plot
        Output('model-graph','figure'),
        [
         Input('available-data', 'value'), # this will be the filename of the file 
         #Input('input-datatype', 'value'),
         #Input('datatable','selected_row_indices'),
         Input('charge-newpeak', 'value'), 
         Input('discharge-newpeak', 'value'),
         Input('new-peak-threshold', 'value'), 
         Input('update-model-button', 'n_clicks'), 
         Input('show-poly', 'values'), 
         Input('desc-to-plot', 'value'),
         Input('cd-to-plot', 'value'), 
         Input('desc-peaknum-to-plot', 'values')]
         #Input('upload-data','contents')]
        )

def update_figure2(filename, charge_newpeaks, discharge_newpeaks, peak_thresh, n_clicks, show_poly, desc_to_plot, cd_to_plot, peaknum_to_plot):
    """ This is  a function to evaluate the model on a sample plot before updating the database"""
    data, raw_data= pop_with_db(filename, database)
    datatype = data.loc[0,('datatype')]
    (cycle_ind_col, data_point_col, volt_col, curr_col, dis_cap_col, char_cap_col, charge_or_discharge) = dbexp.ccf.col_variables(datatype)
    selected_step = round(data[cycle_ind_col].max()/2) +1 
    # select a cycle in the middle of the set
    dff_data= data[data[cycle_ind_col] == selected_step]
    ###################################################
    length_list = [len(data[data[cycle_ind_col]==cyc]) for cyc in data[cycle_ind_col].unique() if cyc != 1]
    lenmax = max(length_list)
	###################################################
    dff_raw = raw_data[raw_data[cycle_ind_col]==selected_step]
    peak_vals_df = dbexp.dbfs.get_file_from_database(filename.split('.')[0] + 'ModParams-descriptors',database)
    if n_clicks is not None:
    	# if the user has hit the update-model-button - remake model
        int_list_c = []
        int_list_d = []
        if charge_newpeaks is not None: 
            new_list_c = charge_newpeaks.split(',')
            for i in new_list_c:
                int_list_c.append(float(i))
        else: 
            None
        if discharge_newpeaks is not None: 
            new_list_d = discharge_newpeaks.split(',')
            for i in new_list_d:
                int_list_d.append(float(i))
        else: 
            None
        new_df_mody, model_c_vals, model_d_vals, peak_heights_c, peak_heights_d = get_model_dfs(dff_data, datatype, selected_step, int_list_c, int_list_d, lenmax, peak_thresh)
        dff_mod = new_df_mody
        c_c0 = model_c_vals['c0']
        c_c1 = model_c_vals['c1']
        c_c2= model_c_vals['c2']
        c_c3 = model_c_vals['c3']
        c_c4 = model_c_vals['c4']
    else: 
    	# if user hasn't pushed the button, populate with original model from database
        modset_name = filename.split('.')[0] + '-ModPoints'
        df_model = dbexp.dbfs.get_file_from_database(modset_name, database)
        dff_mod = df_model[df_model[cycle_ind_col] == selected_step]
        #modvals = dbexp.dbfs.get_file_from_database(filename.split('.')[0] + 'ModParams', database)
        #modvals_selected = modvals[modvals['Cycle'] == selected_step]
        #modvals_selected = modvals_selected.reset_index(inplace = True)
        #model_c_vals = ast.literal_eval(modvals_selected.loc[0,('Model_Parameters_charge')])
        #model_d_vals = ast.literal_eval(modvals_selected.loc[0, ('Model_Parameters_discharge')])
        filtpeakvals = peak_vals_df[peak_vals_df['c_cycle_number'] == selected_step]
        filtpeakvals = filtpeakvals.reset_index(drop = True)
        c_c0 = filtpeakvals.loc[0,('c_poly_coef1')]
        c_c1 = filtpeakvals.loc[0, ('c_poly_coef2')]
        c_c2 = filtpeakvals.loc[0, ('c_poly_coef3')]
        c_c3 = filtpeakvals.loc[0, ('c_poly_coef4')]
        c_c4 = filtpeakvals.loc[0, ('c_poly_coef5')]
    #(charge, discharge) = dbexp.ccf.sep_char_dis(data, datatype)
    # grab datattype from file:
    #model_cd_vals are dictionaries - can refer to them with the key 
   
    

    #raw_filtered_data= raw_data[raw_data[cycle_ind_col]== selected_step]
    
    #filt_chargeloc = chargeloc_dict[selected_step] # this returns a list [] of peak indices
    #filt_disloc = dischloc_dict[selected_step]
    #for i in filtered_data[cycle_ind_col].unique():
    fig = plotly.tools.make_subplots(
        rows=1,cols=2,
        subplot_titles=('Descriptors','Smoothed Cycle'),
        shared_xaxes=True)
    marker = {'color': ['#0074D9']}
            #fig.append_trace({'x': [2.0, 2.0],'y': [0, 2.0], 'type': 'line', 'name': 'Peak Position'}, 1, 2
    fig.append_trace({
        'x': dff_data[volt_col],
        'y': dff_data['Smoothed_dQ/dV'],
        'type': 'scatter',
        'marker': marker,
        'name': 'Smoothed Data'
        }, 1, 2)
    for value in peaknum_to_plot: 
    	fig.append_trace({
            'x': peak_vals_df['c_cycle_number'],
            'y': peak_vals_df[desc_to_plot + cd_to_plot + value],
            'type': 'scatter',
            'marker': marker,
            'name': value 
            }, 1, 1)
       
    fig.append_trace({
        'x':dff_mod[volt_col], 
        'y':dff_mod['Model'] ,
        'type': 'scatter',
        'name': 'Model of One Cycle'
        }, 1,2)
   # add if checkbox is selected to show polynomial baseline 
    if 'show' in show_poly: 
	    fig.append_trace({
            'x': dff_mod[volt_col],
            'y': c_c0+c_c1*dff_mod[volt_col]+c_c2*(dff_mod[volt_col])**2+c_c3*(dff_mod[volt_col])**3+c_c4*(dff_mod[volt_col])**4,
            'type': 'scatter',
            'name':'Polynomial Baseline' # plot the poly
            }, 1,2)

    fig['layout']['showlegend'] = True
    #fig['layout']['shapes'] = shapes
    fig['layout']['xaxis1'].update(title = 'Cycle Number')
    fig['layout']['xaxis2'].update(title = 'Voltage (V)')
    fig['layout']['yaxis1'].update(title = 'Descriptor Value')
    fig['layout']['yaxis2'].update(title = 'dQ/dV', range = [dff_data['Smoothed_dQ/dV'].min(), dff_data['Smoothed_dQ/dV'].max()])
    #plotly_fig['layout']['yaxis1'].update({'range': [-0.3,0.3]})
    fig['layout']['height'] = 600
    fig['layout']['margin'] = {
        'l': 40,
        'r': 10,
        't': 60,
        'b': 200
        }
        #fig['layout']['yaxis'] = {'title': 'dQ/dV'}
    return fig

@app.callback( #update charge datatable
    Output('datatable', 'rows'),
    [Input('available-data', 'value'),
     #Input('upload-data', 'filename'),
     #Input('upload-data', 'last_modified')
     ])

def update_table1(filename):
    data, raw_data = pop_with_db(filename, database) 
    return data.to_dict('records')


#@app.callback(
#    Output('gen-desc-confirmation', 'children'),
#    [Input('update-model-button-button', 'n_clicks')])
#def update_output(n_clicks):
#    if n_clicks> 0:
#    	return 'Generating descriptors'
#    else:
#    	return 'Descriptors have not been generated yet.'

# #@app.callback( #decorator wrapper for plot
# #        Output('discharge-graph','figure'),
# #        [Input('cycle--slider','value'),
# #         Input('discharge-datatable','rows'),
# #         Input('discharge-datatable','selected_row_indices')]
# #        )

# @app.callback( #decorator wrapper for plot
#         Output('discharge-graph','figure'),
#         [Input('cycle--slider','value'),
#          #Input('charge-datatable','rows'),
#          Input('upload-data','contents'),
#          Input('upload-data','filename'),
#          Input('upload-data','last_modified'),
#          Input('discharge-datatable','selected_row_indices')]
#          #Input('upload-data','contents')]
#         )

# def update_figure2(selected_step,contents,filename,date,selected_row_indices):
#     data = parse_contents(contents, filename)
#     #(charge, discharge) = dbexp.ccf.sep_char_dis(data, datatype)
#     filtered_data = data[data['Cycle_Index'] == selected_step]
#     for i in filtered_data['Cycle_Index'].unique():
#         dff = filtered_data[filtered_data['Cycle_Index'] == i]
#         fig = plotly.tools.make_subplots(
#             rows=2,cols=1,
#             subplot_titles=('Smoothed dQ/dV Discharge Cycle','Cleaned dQ/dV Discharge Cycle'),
#             shared_xaxes=True)
#         marker = {'color': ['#0074D9']*len(dff)}
#         for i in (selected_row_indices or []):
#             marker['color'][i] = '#FF851B'
#         fig.append_trace({
#             'x': dff['Voltage(V)'],
#             'y': dff['Smoothed_dQ/dV'],
#             'type': 'scatter',
#             'marker': marker,
#             'name': 'Smoothed Data'
#             }, 1, 1)
#         fig.append_trace({
#             'x': dff['Voltage(V)'],
#             'y': dff['dQ/dV'],
#             'type': 'scatter',
#             'marker': marker,
#             'name': 'Raw Data'
#             }, 2, 1)
#         fig['layout']['showlegend'] = False
#         fig['layout']['height'] = 800
#         fig['layout']['margin'] = {
#             'l': 40,
#             'r': 10,
#             't': 60,
#             'b': 200
#             }
#         fig['layout']['yaxis2']
#     return fig


##########################################
#Customize CSS
##########################################
##TO DO: FORK THIS REPOSITORY (url) TO CUSTOMIZE CSS
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})


if __name__ == '__main__':
    app.run_server(debug=True)