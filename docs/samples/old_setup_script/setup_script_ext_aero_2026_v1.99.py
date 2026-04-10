# 
# ----------------------------------------------------------------------------------------------
#   Test script to produce the guideline setup with yaw angle
#   This is only for internal usage, so please use it on your own responsibility
# ----------------------------------------------------------------------------------------------
# Developed by: Yuta Kanemaru
# 20250722 ver.1.1
# Template exel version: v0.6
# Updates: Added variable option support for output. Added option for enable_ground_patch.

#Importing required libraries
import weakref
import re #Library for regex
from typing import List
import os
import json
import math
from hwx import inspire 
from hwx.inspire import vwt
from hwx.inspire.core.Sketch import Sketch
import hwfdmcore 
import hwfdmplugin 
import hwvwtCorePlugin 
from hwx.common.math import Matrix44
import pandas as pd
import ast
import sys
import os
import numpy as np

# ALWAYS START WITH AN EMPTY NEW MODEL
model=inspire.newModel()

# -----------------------------------------------------------------
# -----------    LOAD SETUP EXCEL SHEET    -----------------------------
# -----------------------------------------------------------------
# ----------------------
# Setting excel file
# ---------------------
if len(sys.argv) != 2:
    print('⚠️: Usage: please specify the path to setup excel file.')
else:
    setting_excel_file = sys.argv[1]
    print(f'✅: Specified setting excel file: {setting_excel_file}')


##################################################################
#
#                           INPUT
#
##################################################################

# -----------------------------------------------------------------
# -----------     START USER INPUT    -------------------------------
# -----------------------------------------------------------------
#Air Properties
heat_capacity_ratio = 1.4 #Cp/Cv
gas_constant = 8.3144 #J/mol*k
molecular_weight = 0.0289647
temperature = 20 #degrees
# inflow condition
density = 1.204
dynamic_viscosity = 1.8194e-5
# ground condition
cnt_turn_table = [0.0,0.0,0.0] # it has to be calculated by vwt in the future
FullSlip_VWT = False
match_inflow_belt_speed = True # option to match inflow velocity and driving speed = moving belt TBD: currently wheel rpm calculation doesn't work


# -----------------------------------------------------------------
# -----------     END USER INPUT    -------------------------------
# -----------------------------------------------------------------

# -----------------------------------------------------------------
# -----------   START SETUP GUIDELINE PARAMETERS ------------------
# -----------------------------------------------------------------
# --------------------------
# General guideline settings
# --------------------------
num_layers_rl7 = 8
num_layers_rl6 = 12
add_wheel_belt_refinement = False # currently supported only for 5-belt



# --------------------------
# parameters for refinements
# --------------------------
# factors based on the vehicle diementions
domain_size_factor=[-5, 10, -12, 12, 0, 20]
ref_box_factors=[]
ref_box_factors.append([-1, 3, -1, 1, -0.2, 1.5]) #RL1
ref_box_factors.append([-0.5, 1.5, -0.75, 0.75, -0.2,1]) #RL2
ref_box_factors.append([-0.3, 1, -0.5, 0.5, -0.2, 0.75]) #RL3 -- guideline 2024.0
ref_box_factors.append([-0.2, 0.6, -0.3, 0.3, -0.2, 0.5]) #RL4 -- guideline 2024.0
ref_box_factors.append([-0.1, 0.3, -0.15, 0.15, -0.2, 0.25]) #RL5 -- gsuideline 2024.0
 
#ref_box_factors.append([-0.15, 0.6, -0.25, 0.25, -0.2, 0.45]) #RL4 -- smaller than guideline 2024.0 
#ref_box_factors.append([-0.075, 0.3, -0.13, 0.13, -0.2, 0.225]) #RL5 -- smaller than guideline 2024.0


offset_ref_box = 0.02 # m (extend box from actually calculated box refinement size by factors)
offset_ref_box_ground = 0 # m(extend box from actually calculated box refinement size by factors)
offset_from_BL_suction = -0.01 #m, Offset from BL suction position.
offset_from_ground = -0.01 #m, offset from ground to make sure that ground is included in precision level.


# num_layers_rl5_ground = 30
# num_layers_rl6_ground = 12
num_layers_rl5_ground = 24
num_layers_rl6_ground = 8
ref_box_static_floor_inflation_factors=[1.4, 1.2, 1.1, 1.05] # based on static floor size and the height of RL5 layers on the ground




# -----------------------------
# parameters for static floor
# -----------------------------
# Options to specify the size of the static floor
belt_dimension_based_static = False #Specify the size of static floor based on the belt size (This yield more voxel counts)
body_dimension_based_static = True  #Specify the size of static floor based on the body size (This yield less voxel counts)

# Specify the scale factors
scale_factor_static_floor_belt_width = 1.25 #25% in setup guideline.

scale_factor_static_floor_body_length = 1.75 # Setup guideline
#scale_factor_static_floor_body_length = 1.5 # Scaled down
scale_factor_static_floor_body_width = 1.25

# ------------------------------------------
# parameters for tg
# ------------------------------------------
# body_tg
tg_body_num_eddies = 800
tg_body_intensity = 0.01
tg_body_rl = 6

# ground_tg
tg_ground_num_eddies = 800
tg_ground_intensity = 0.05
tg_ground_rl = 6
# ------------------------------------------
# parameters for tg in front of the body
# ------------------------------------------
tg_body_rls = 6
tg_body_turbulence_length_factor = 4
tg_body_x_pos_factor = 0.05
# ---------------------------------
# size must be further optimized
# ---------------------------------
tg_body_tg_size_factor = [-0.45, 0.45, 0.1, 0.65] #[-y, +y, -z, +z], preferably based on engine compartmet, but if naming is clear..

# ---------------------------------
# Recommended parameters
# ---------------------------------
mach_scaling = 2
max_mach_number = 0.4


# -----------------------------------------------------------------
# -----------   END SETUP GUIDELINE PARAMETERS ------------------
# -----------------------------------------------------------------


##################################################################
#
#                           MAIN
#
##################################################################

#####################################################################
# ### Loading settings from excel
#####################################################################
# Loading function
def excel_input_to_python_value(value):
    """
    Convert Excel cell input into a proper Python type.
    """

    # 1️⃣ NaN or None → []
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    
    # 3️⃣ 数値（int/float）はそのまま返す（1→Trueにならないよう注意）
    if isinstance(value, (int, float)):
        return value

    # 2️⃣ Bool型はそのまま返す（True/Falseセル専用）
    if isinstance(value, bool):
        if value == 1:
            return int(1)
        else:
            return value

    

    # 4️⃣ 文字列の場合
    if isinstance(value, str):
        val = value.strip()
        if val == "":
            return None

        val_lower = val.lower()
        # TRUE/FALSE文字列 → bool
        if val_lower == "true":
            return True
        elif val_lower == "false":
            return False

        # Pythonリスト形式（例: ["A", "B"]）
        if val.startswith("[") and val.endswith("]"):
            try:
                parsed = ast.literal_eval(val)
                return parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                return [v.strip() for v in val.strip("[]").split(",") if v.strip()]

        # カンマ区切り（例: A,B）
        elif "," in val:
            parts = [v.strip() for v in val.split(",") if v.strip()]
            # 全部が数値ならfloatに変換
            if all(p.replace('.', '', 1).replace('-', '', 1).isdigit() for p in parts):
                return [float(p) for p in parts]
            return parts

        # 単一の数値文字列なら float に変換
        if val.replace('.', '', 1).replace('-', '', 1).isdigit():
            return float(val)

        # 単一文字列
        return [val]

    # 5️⃣ その他（未知型）はそのまま
    return value


# --------------------------
# General settings 
# --------------------------
df = pd.read_excel(setting_excel_file, sheet_name='General')
df = df[df['Parameters'].notna()]
# Getting dictionary from excel
general_settings = {}
orig = {}
for index, row in df.iterrows():
    key = row['Parameters']
    value = row['Value']
    original_value_from_excel = value
    value = excel_input_to_python_value(value)

    orig[key] = original_value_from_excel
    general_settings[key] = value

#print(f"######{orig}")


#####################################################################
# ### Assigning variables
#####################################################################
simulationName = general_settings.get('simulationName')
simulationRunPath = general_settings.get('simulationRunPath')
inflow_velocity = general_settings.get('inflow_velocity')
simulation_time_with_flow_passes = general_settings.get('simulation_time_with_flow_passes')
simulation_time_num_flow_passes = general_settings.get('simulation_time_num_flow_passes')
start_averaging_time_num_flow_passes = general_settings.get('start_averaging_time_num_flow_passes')
simulation_time = general_settings.get('simulation_time')
start_averaging_time = general_settings.get('start_averaging_time')
avg_window_size_second=general_settings.get('avg_window_size_second')
yaw_angle_vehicle = general_settings.get('yaw_angle_vehicle')
ground_height = general_settings.get('ground_height')
calculate_ground_height_from_zMin = general_settings.get('calculate_ground_height_from_zMin')
opt_moving_floor = general_settings.get('opt_moving_floor')
bl_suction_pos_x_input = float(general_settings.get('bl_suction_pos_x_input'))
opt_belt_system = general_settings.get('opt_belt_system')
bl_suction_by_belt_x_min = general_settings.get('bl_suction_by_belt_x_min')
#num_belts = general_settings.get('num_belts')
osm_wheels = general_settings.get('osm_wheels')
include_wheel_belt_forces = general_settings.get('include_wheel_belt_forces')
wheel_belt_location_auto = general_settings.get('wheel_belt_location_auto')
enable_noslip_moving_ground_for_1belt = general_settings.get('enable_noslip_moving_ground_for_1belt')
bl_suction_by_belt_x_min_distance = general_settings.get('bl_suction_by_belt_x_min_distance')
HM_CFD_version = float(general_settings.get('HM_CFD_version'))
debug_mode = general_settings.get('debug_mode')
enable_ground_patch = general_settings.get('enable_ground_patch')
activate_body_tg = general_settings.get('activate_body_tg')
centre_belt_at_wheelbase_centre = general_settings.get('centre_belt_at_wheelbase_centre')
export_time_avg_partial_volume_outputs = general_settings.get('export_time_avg_partial_volume_outputs')
adjust_ride_height=general_settings.get("adjust_ride_height")
adjust_body_wheel_separately=general_settings.get("adjust_body_wheel_separately")
rotate_yaw_at_wheelbase_center = general_settings.get('rotate_yaw_at_wheelbase_center')
output_coarsening = general_settings.get('output_coarsening')
coarsest_target_refinement_level = general_settings.get('coarsest_target_refinement_level')
coarsen_by_num_refinement_levels = general_settings.get('coarsen_by_num_refinement_levels')
reference_length_auto = general_settings.get('reference_length_auto')
solution_type = general_settings.get('solution_type')
output_start_time = general_settings.get('output_start_time')
output_interval_time = general_settings.get('output_interval_time')
output_format = general_settings.get('output_format')
export_bounds_active = general_settings.get('export_bounds_active')

# Converting list to single value
solution_type = solution_type[0] 
output_format = output_format[0]

# Turning options off when wheel rotation is off.
if not opt_moving_floor:
    osm_wheels = False
    opt_belt_system = False
    bl_suction_by_belt_x_min = False
    enable_noslip_moving_ground_for_1belt = False
    wheel_belt_location_auto = False
    centre_belt_at_wheelbase_centre = False
    include_wheel_belt_forces = False






# --------------------------
# Belt settings 
# --------------------------
df = pd.read_excel(setting_excel_file, sheet_name='Belts')
df = df[df['Parameters'].notna()]
# Getting dictionary from excel
belt_settings = {}
for index, row in df.iterrows():
    key = row['Parameters']
    x = row['x']
    y = row['y']
    belt_settings[key] = [x,y]
# Assigning variables
belt_size_wheel = belt_settings.get('belt_size_wheel')
belt_size_center = belt_settings.get('belt_size_center')
belt_center_position_fr_lh = belt_settings.get('belt_center_position_fr_lh')
belt_center_position_fr_rh = belt_settings.get('belt_center_position_fr_rh')
belt_center_position_rr_lh = belt_settings.get('belt_center_position_rr_lh')
belt_center_position_rr_rh = belt_settings.get('belt_center_position_rr_rh')
belt_center_position_center = belt_settings.get('belt_center_position_center')

# --------------------------
# Wheels and baffles
# --------------------------
df = pd.read_excel(setting_excel_file, sheet_name='Wheels_baffles')
df = df[df['Parameters'].notna()]
Wheel_baffle_settings = {}
for index, row in df.iterrows():
    key = row['Parameters']
    value = row['Value']
    value = excel_input_to_python_value(value)
    Wheel_baffle_settings[key] = value

# Assigning variables
WheelPartsNames = Wheel_baffle_settings.get('WheelPartsNames')
RimPartsNames = Wheel_baffle_settings.get('RimPartsNames') or []
WheelTirePartsNames = []
WheelTirePartsNames.append(Wheel_baffle_settings.get('WheelTireParts_FR_LHS')[0])
WheelTirePartsNames.append(Wheel_baffle_settings.get('WheelTireParts_FR_RHS')[0])
WheelTirePartsNames.append(Wheel_baffle_settings.get('WheelTireParts_RR_LHS')[0])
WheelTirePartsNames.append(Wheel_baffle_settings.get('WheelTireParts_RR_RHS')[0])
TireSurfaceRoughness = Wheel_baffle_settings.get('TireSurfaceRoughness')
BafflePartsName = Wheel_baffle_settings.get('BafflePartsName')
windtunnel_parts = Wheel_baffle_settings.get('windtunnel_parts')

# OSM is not supported yet in v0.6. Please do not comment in.
WheelOSMPartsNames = []
if osm_wheels:
    WheelOSMPartsNames.append(Wheel_baffle_settings.get('OversetMeshPartsName_FR_LH')[0])
    WheelOSMPartsNames.append(Wheel_baffle_settings.get('OversetMeshPartsName_FR_RH')[0])
    WheelOSMPartsNames.append(Wheel_baffle_settings.get('OversetMeshPartsName_RR_LH')[0])
    WheelOSMPartsNames.append(Wheel_baffle_settings.get('OversetMeshPartsName_RR_RH')[0])
elif osm_wheels and not Wheel_baffle_settings.get('OversetMeshPartsName_FR_LH')[0]:
    raise ValueError("Please input OversetMeshPartsName in Wheel_baffle_settings.")
                                


# --------------------------
# Heat exchanger 
# --------------------------
Heat_exchangers=[]
df = pd.read_excel(setting_excel_file, sheet_name='Heat_exchangers')
df = df[df['name'].notna()]

for index, row in df.iterrows():
    Heat_exchangers.append({
        "name": row['name'],
        "inlet": row['inlet'],
        "frame": row['frame'],
        "outlet": row['outlet'],
        "coeffs_inertia": row['coeffs_inertia'],
        "coeffs_viscous": row['coeffs_viscous'],}
    )



# -------------------------
# additional offset refinement
# -------------------------
df = pd.read_excel(setting_excel_file, sheet_name='Additional_offset_refinement')
df = df[df['name'].notna()]

additional_part_offsets=[]
for index, row in df.iterrows():
    parts_include = excel_input_to_python_value(row['parts_include'])
    parts_exclude = excel_input_to_python_value(row['parts_exclude'])

    additional_part_offsets.append({
        'name': row['name'],
        "refinement_level": row['refinement_level'],
        "num_layers": row['num_layers'],
        'parts_include': parts_include,
        'parts_exclude': parts_exclude,}
    )

# -------------------------
# Custom refinement
# -------------------------
df = pd.read_excel(setting_excel_file, sheet_name='Custom_refinement')
df = df[df['name'].notna()]

custom_refinements=[]
for index, row in df.iterrows():
    custom_refinements.append({
        'name': row['name'],
        "refinement_level": row['refinement_level'],
        }
    )

# custom_refinementsの中から'name'の値だけを取り出してstrのリストを作成
custom_refinement_names = [refinement['name'] for refinement in custom_refinements]


# --------------------------
# Ride height settings 
# --------------------------
df = pd.read_excel(setting_excel_file, sheet_name='Ride_Height')
df = df[df['Parameters'].notna()]
# Getting dictionary from excel
ride_height_settings = {}
for index, row in df.iterrows():
    key = row['Parameters']
    value = row['Value']
    value = excel_input_to_python_value(value)
    ride_height_settings[key] = value

# Assigning variables
front_wheel_axis_RH = ride_height_settings.get('front_wheel_axis_RH')
rear_wheel_axis_RH = ride_height_settings.get('rear_wheel_axis_RH')
front_wheel_axis_height = ride_height_settings.get('front_wheel_axis_height')
rear_wheel_axis_height = ride_height_settings.get('rear_wheel_axis_height')
use_original_wheel_position = ride_height_settings.get("use_original_wheel_position")
front_wheel_parts_include = ride_height_settings.get("front_wheel_parts_include")
front_wheel_parts_exclude = ride_height_settings.get("front_wheel_parts_exclude")
rear_wheel_parts_include = ride_height_settings.get("rear_wheel_parts_include")
rear_wheel_parts_exclude = ride_height_settings.get("rear_wheel_parts_exclude")

# --------------------------
# Mesh Control settings 
# --------------------------
df = pd.read_excel(setting_excel_file, sheet_name='Mesh_Control')
df = df[df['Parameters'].notna()]
# Getting dictionary from excel
meshcontrol_settings = {}
for index, row in df.iterrows():
    key = row['Parameters']
    value = row['Value']
    value = excel_input_to_python_value(value)
    meshcontrol_settings[key] = value

#####################################################################
# ### Assigning variables
#####################################################################
trianglePlinth = meshcontrol_settings.get('trianglePlinth')
triangleSplitting = meshcontrol_settings.get('triangleSplitting')
maxRelativeEdgeLength = meshcontrol_settings.get('maxRelativeEdgeLength')
transitionLayers = meshcontrol_settings.get('transitionLayers')
coarsest_voxel_size = meshcontrol_settings.get('coarsest_voxel_size')

# --------------------------
# fullData Outputs
# --------------------------
df = pd.read_excel(setting_excel_file, sheet_name='fullData_Outputs')
df = df[df['Name'].notna()]
# Getting dictionary from excel
fullData_Outputs = {}
for index, row in df.iterrows():
    key = row['Name']
    value = row['Enable']
    value = excel_input_to_python_value(value)
    fullData_Outputs[key] = value

#####################################################################
# ### Assigning variables
#####################################################################
full_output_option = []
for key,value in fullData_Outputs.items():
    full_output_option.append((key,value))

# --------------------------
# Volume Outputs
# --------------------------
df = pd.read_excel(setting_excel_file, sheet_name='Full_Partial_Volume_Outputs')
df = df[df['Name'].notna()]
# Getting dictionary from excel
Full_Partial_Volume_Outputs = {}
for index, row in df.iterrows():
    key = row['Name']
    value = row['Enable']
    value = excel_input_to_python_value(value)
    Full_Partial_Volume_Outputs[key] = value

#####################################################################
# ### Assigning variables
#####################################################################
volume_output_option = []
for key,value in Full_Partial_Volume_Outputs.items():
    volume_output_option.append((key,value))

# --------------------------
# Surface Outputs
# --------------------------
df = pd.read_excel(setting_excel_file, sheet_name='FullData_Surface_Outputs')
df = df[df['Name'].notna()]
# Getting dictionary from excel
FullData_Surface_Outputs = {}
for index, row in df.iterrows():
    key = row['Name']
    value = row['Enable']
    value = excel_input_to_python_value(value)

    FullData_Surface_Outputs[key] = value

#####################################################################
# ### Assigning variables
#####################################################################
surface_output_option = []
for key,value in FullData_Surface_Outputs.items():
    surface_output_option.append((key,value))

# -------------------------
# Add partial surface outputs
# -------------------------
df = pd.read_excel(setting_excel_file, sheet_name='Partial_Surface_Outputs',header=1)
df = df[df['name'].notna()]

partial_surface_output=[]
for index, row in df.iterrows():
    # Converting str to list
    parts_include = excel_input_to_python_value(row['parts_include'])
    parts_exclude = excel_input_to_python_value(row['parts_exclude'])

    partial_surface_output.append({
        'name': row['name'],
        'parts_include': parts_include,
        'parts_exclude': parts_exclude,
        'Start_time[s]' : row['Start time[s]'],
        'Output_interval' : row['Output interval'],
        'Output_format' : row['Output_format'],
        'Merge_output': row['Merge output'],
        'Output_variables':{
            'Merge output' : row['Merge output'],
            'Pressure' : row['Pressure'],
            'Standard deviation' : row['Standard deviation'],
            'Variance' : row['Variance'],
            'Time average pressure' : row['Time average pressure'],
            'Window average pressure' : row['Window average pressure'],
            'Window average velocity' : row['Window average velocity'],
            'Mesh displacement' : row['Mesh displacement'],
            'Temperature' : row['Temperature'],
            'Time average temperature' : row['Time average temperature'],
            'Window average temperature' : row['Window average temperature'],
            'Velocity' : row['Velocity'],
            'Wall shear stress' : row['Wall shear stress'],
            'Time average wall shear stress' : row['Time average wall shear stress'],
            'Window average wall shear stress' : row['Window average wall shear stress'],
            'Surface normal' : row['Surface normal'],
            'Temperature' : row['Temperature'],
            'Time average temperature' : row['Time average temperature'],
            'Window average temperature' : row['Window average temperature'],
            'Mesh Data' : row['Mesh Data']
            },
        }
    )

# -------------------------
# Add partial volume outputs
# -------------------------
df = pd.read_excel(setting_excel_file, sheet_name='Partial_Volume_Outputs', header=1)
df = df[df['name'].notna()]
df = df.applymap(excel_input_to_python_value)

# 出力系のカラムを定義
output_keys = [
    'Pressure',
    'Pressure standard deviation',
    'Pressure variance',
    'Time average pressure',
    'Window average pressure',
    'Volume velocity',
    'Time average velocity',
    'Window average velocity',
    'Mesh displacement',
    'Vorticity',
    'Vorticity Magnitude',
    'Lamda 1',
    'Lamda 2',
    'Lamda 3',
    'Q Criterion',
    'Temperature',
    'Time average temperature',
    'Window average temperature',
]

partial_volume_output = []

for _, row in df.iterrows():
    record = row.to_dict()

    # ✅ 出力変数のみ抽出
    output_variables = {k: record[k] for k in output_keys if k in record}

    # ✅ 残りを main 辞書として保持
    main_dict = {k: v for k, v in record.items() if k not in output_keys}

    # ✅ 出力変数をまとめて格納
    main_dict['output_variables'] = output_variables
    partial_volume_output.append(main_dict)


# --------------------------
# Monitor surface Outputs
# --------------------------
df = pd.read_excel(setting_excel_file, sheet_name='Monitor_Surface_Outputs',header=1)
df = df[df['name'].notna()]
# Getting dictionary from excel
Monitor_Surface_Outputs = []
for index, row in df.iterrows():
    parts_include = excel_input_to_python_value(row['parts_include'])
    parts_exclude = excel_input_to_python_value(row['parts_exclude'])

    Monitor_Surface_Outputs.append({
        'name': row['name'],
        'parts_include': parts_include,
        'parts_exclude': parts_exclude,
        # Visual options
        'Visual Start time[s]': row['Visual Start time[s]'],
        'Visual Output interval': row['Visual Output interval'],
        'Visual Output format': row['Visual Output format'],
        'Visual Merge Output': row['Visual Merge Output'],
        # Summary options
        'Summary Start time[s]': row['Summary Start time[s]'],
        'Summary Output interval': row['Summary Output interval'],
        # Visual outputs
        'Visual_Outputs': {
        'Visual_Pressure': row['Visual_Pressure'],
        'Visual_Pressure standard deviation': row['Visual_Pressure standard deviation'],
        'Visual_Pressure variance': row['Visual_Pressure variance'],
        'Visual_Time average pressure': row['Visual_Time average pressure'],
        'Visual_Window average pressure': row['Visual_Window average pressure'],
        'Visual_Velocity': row['Visual_Velocity'],
        'Visual_Time average velocity': row['Visual_Time average velocity'],
        'Visual_Window average velocity': row['Visual_Window average velocity'],
        'Visual_Mass flow': row['Visual_Mass flow'],
        'Visual_Time average mass flow': row['Visual_Time average mass flow'],
        'Visual_Window average mass flow': row['Visual_Window average mass flow'],
        'Visual_Normal velocity': row['Visual_Normal velocity'],
        'Visual_Time average normal velocity': row['Visual_Time average normal velocity'],
        'Visual_Window average normal velocity': row['Visual_Window average normal velocity'],
        'Visual_Temperature': row['Visual_Temperature'],
        'Visual_Time average temperature': row['Visual_Time average temperature'],
        'Visual_Window average temperature': row['Visual_Window average temperature']},
        # Summary outputs
        'Summary_Outputs':{
        'Summary_Pressure': row['Summary_Pressure'],
        'Summary_Pressure standard deviation': row['Summary_Pressure standard deviation'],
        'Summary_Pressure variance': row['Summary_Pressure variance'],
        'Summary_Time average pressure': row['Summary_Time average pressure'],
        'Summary_Window average pressure': row['Summary_Window average pressure'],
        'Summary_Mass flow': row['Summary_Mass flow'],
        'Summary_Time average mass flow': row['Summary_Time average mass flow'],
        'Summary_Window average mass flow': row['Summary_Window average mass flow'],
        'Summary_Normal velocity': row['Summary_Normal velocity'],
        'Summary_Time average normal velocity': row['Summary_Time average normal velocity'],
        'Summary_Window average normal velocity': row['Summary_Window average normal velocity'],
        'Summary_Temperature': row['Summary_Temperature'],
        'Summary_Time average temperature': row['Summary_Time average temperature'],
        'Summary_Window average temperature': row['Summary_Window average temperature']}
        }

    )


#####################################################################
# ### Assigning variables
#####################################################################
surface_output_option = []
for key,value in FullData_Surface_Outputs.items():
    surface_output_option.append((key,value))

#####################################################################
# ### Export all inputs from excel if debug mode is activated.
#####################################################################
if debug_mode:
    print("Following Information is read from Excel")
    print(f"General: {general_settings}")
    print(f"Wheels_baffles: {Wheel_baffle_settings}")
    print(f"Belts: {belt_settings}")
    print(f"Heat Exchanger: {Heat_exchangers}")
    print(f'Additional offset refinements: {additional_part_offsets}')
    print(f'Custon refinement: {custom_refinements}')
    print(f'Ride Height Settings: {ride_height_settings}')
    print(f'Mesh control settings: {meshcontrol_settings}')
    print(f'FullData output variables: {full_output_option}')
    print(f'Partial volume output variables: {volume_output_option}')
    print(f'Partial surface output variables: {surface_output_option}')
    print(f'Partial surface output: {partial_surface_output}')
    print(f'partial_volume_output: {partial_volume_output}')
    # Write the same information to a JSON file for easier inspection
    try:
        debug_dump = {
            "General": general_settings,
            "Wheels_baffles": Wheel_baffle_settings,
            "Belts": belt_settings,
            "Heat Exchanger": Heat_exchangers,
            "Additional offset refinements": additional_part_offsets,
            "Custom refinement": custom_refinements,
            "Ride Height Settings": ride_height_settings,
            "Mesh control settings": meshcontrol_settings,
            "FullData output variables": full_output_option,
            "Partial volume output variables": volume_output_option,
            "Partial surface output variables": surface_output_option,
            "Partial surface output": partial_surface_output,
            "partial_volume_output": partial_volume_output,
        }

        # Derive a reasonable output path (same folder as Excel file)
        out_dir = os.path.dirname(setting_excel_file) if 'setting_excel_file' in locals() else os.getcwd()
        simname = general_settings.get('simulationName')
        if isinstance(simname, list):
            simname = simname[0] if simname else "simulation"
        elif not isinstance(simname, str) or not simname:
            simname = "simulation"
        out_path = os.path.join(out_dir, f"{simname}_input_from_excel.json")

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(debug_dump, f, ensure_ascii=False, indent=2)
        print(f"📝: Debug JSON exported to {out_path}")
    except Exception as e:
        print(f"⚠️: Failed to export debug JSON: {e}")



##################################################################
### Defining functions
##################################################################

def check_string_with_regex(text: str, include_pattern: str = None, exclude_pattern: str = None) -> bool:
    """
    Determines if the given string satisfies the regex 'include' condition and
    does not satisfy the 'exclude' condition.

    Args:
        text (str): The string to be checked.
        include_pattern (str, optional): The regex pattern the string must include.
                                         If None or an empty string, the include condition
                                         is always considered True. Defaults to None.
        exclude_pattern (str, optional): The regex pattern the string must not include.
                                         If None or an empty string, the exclude condition
                                         is always considered False (i.e., nothing is excluded).
                                         Defaults to None.

    Returns:
        bool: True if the string meets the include condition and does not meet the exclude condition.
              Returns False if regex compilation fails.
    """
    is_included = True
    is_excluded = False

    # Check 'include' pattern
    if include_pattern:
        try:
            is_included = bool(re.search(include_pattern, text))
        except re.error as e:
            print(f"⚠️ Warning: Invalid 'include' regex pattern '{include_pattern}': {e}")
            return False

    if not is_included:
        return False

    # Check 'exclude' pattern
    if exclude_pattern:
        try:
            is_excluded = bool(re.search(exclude_pattern, text))
        except re.error as e:
            print(f"⚠️ Warning: Invalid 'exclude' regex pattern '{exclude_pattern}': {e}")
            return False

    return is_included and not is_excluded

# This new function replaces the previous check_strings_with_regex_list
def check_string_against_multiple_patterns(
    text: str,
    include_patterns: List[str] = None,
    exclude_patterns: List[str] = None
) -> bool:
    """
    Checks a single string against a list of 'include' regex patterns and a list of 'exclude' regex patterns.
    The text passes if it matches AT LEAST ONE include pattern (if provided)
    AND does NOT match ANY exclude pattern (if provided).

    Args:
        text (str): The single string to be checked.
        include_patterns (List[str], optional): A list of regex patterns the string must include.
                                                 If None or empty, the include condition is always True.
                                                 The text passes if it matches ANY of these patterns.
        exclude_patterns (List[str], optional): A list of regex patterns the string must not include.
                                                 If None or empty, the exclude condition is always False.
                                                 The text fails if it matches ANY of these patterns.

    Returns:
        bool: True if the text meets the include condition AND does not meet the exclude condition.
              Returns False if any regex pattern is invalid.
    """
    # --- Check include patterns ---
    # If no include patterns are provided, the include condition is considered met by default.
    if not include_patterns:
        overall_included = True
    else:
        # The text must match at least one of the include patterns.
        overall_included = False
        for pattern in include_patterns:
            try:
                if re.search(pattern, text):
                    overall_included = True
                    break # Found a match, so the include condition is satisfied
            except re.error as e:
                print(f"⚠️ Warning: Invalid 'include' regex pattern '{pattern}': {e}")
                return False # An invalid pattern makes a reliable check impossible

    # If the include condition is not met, no need to check exclude patterns.
    if not overall_included:
        return False

    # --- Check exclude patterns ---
    # If no exclude patterns are provided, the exclude condition is considered not met by default.
    if not exclude_patterns:
        overall_excluded = False
    else:
        # The text must not match any of the exclude patterns.
        overall_excluded = False
        for pattern in exclude_patterns:
            try:
                if re.search(pattern, text):
                    overall_excluded = True
                    break # Found a match, so the exclude condition is violated
            except re.error as e:
                print(f"⚠️ Warning: Invalid 'exclude' regex pattern '{pattern}': {e}")
                return False # An invalid pattern makes a reliable check impossible

    # Final determination: True only if included condition is met AND exclude condition is NOT met
    return overall_included and not overall_excluded

def get_parts_with_regex(parts,include_patterns: List[str] = None,exclude_patterns: List[str] = None):
    '''
    Receive vwt parts and naming patterns, returns vwt parts that matches in patterns.
    '''
    matched_parts = []
    for part in parts:
        name = part.name
        if check_string_against_multiple_patterns(name,include_patterns,exclude_patterns):
            matched_parts.append(part)
    
    return matched_parts

def get_set_wheels(WheelPartsNames:List[str], exclude_patterns:List[str] = None):
    """
    Create vwt.Wheels object from wheel part names.
    
    Parameters:
        WheelPartsNames: List of part name patterns to include
        exclude_patterns: List of part name patterns to exclude (optional)
    
    Returns:
        Tuple of (wheels, wheelparts)
    """
    wheelparts = []
    for name in WheelPartsNames:
        for current_part in parts_vehicle:
            if name in current_part.name:
                # Check if part should be excluded
                should_exclude = False
                if exclude_patterns:
                    for exclude_name in exclude_patterns:
                        if exclude_name in current_part.name:
                            should_exclude = True
                            break
                if not should_exclude:
                    wheelparts.append(current_part)
    wheels = vwt.Wheels(wheelparts)
    return wheels, wheelparts

def get_set_rims(RimPartsNames:List[str]):
    rimparts = []
    for name in RimPartsNames:
        rimparts += [current_part for current_part in parts_vehicle if name in current_part.name]
    rims = vwt.Wheels(rimparts)
    return rims, rimparts


def set_osm_wheels(WheelOSMPartsNames:List[str]):
    osm_parts =[]
    for name in WheelOSMPartsNames:
        osm_parts += [current_part for current_part in parts_vehicle if name in current_part.name]
    return osm_parts

def classify_wheels_by_position(wheels):
    """
    Classify wheels into FR_LH, FR_RH, RR_LH, RR_RH based on wheel.center coordinates.
    Wheels with center=[0,1,0] (default/unset) are filtered out before classification.
    
    When multiple wheel parts belong to the same corner (e.g. two parts for FR_LH with
    slightly different centers), the average center is computed for each corner group and
    written back to every wheel in that group via wheel.center = avg_center.
    
    Parameters:
        wheels: List of vwt.Wheel objects
    
    Returns:
        dict: {"FR_LH": [wheels], "FR_RH": [wheels], "RR_LH": [wheels], "RR_RH": [wheels]}
              Each value is a list of all wheel objects belonging to that corner.
              All wheels in the same corner group share the same averaged center.
    """
    # 1. Filter out wheels with default/unset center [0,1,0]
    valid_wheels = []
    for wheel in wheels:
        c = wheel.center
        if c[0] == 0 and c[1] == 1 and c[2] == 0:
            print(f"⚠️: Skipping wheel with default center {c} (detected as unset).")
        else:
            valid_wheels.append(wheel)
    
    if len(valid_wheels) < 4:
        raise ValueError(f"Expected at least 4 valid wheels after filtering, got {len(valid_wheels)} "
                         f"(total input: {len(wheels)}, filtered out: {len(wheels) - len(valid_wheels)})")
    
    # 2. Calculate average X (front/rear boundary)
    centers = [wheel.center for wheel in valid_wheels]
    avg_x = sum(c[0] for c in centers) / len(centers)
    
    # 3. Separate front and rear
    front_wheels = [w for w in valid_wheels if w.center[0] < avg_x]
    rear_wheels = [w for w in valid_wheels if w.center[0] >= avg_x]
    
    if len(front_wheels) < 2 or len(rear_wheels) < 2:
        raise ValueError(f"Unexpected wheel distribution: {len(front_wheels)} front, {len(rear_wheels)} rear. "
                         f"Need at least 2 in each group.")
    
    # 4. Helper: separate left/right groups by Y coordinate median
    def split_left_right(wheel_list):
        """Split wheels into left (smaller Y) and right (larger Y) groups."""
        avg_y = sum(w.center[1] for w in wheel_list) / len(wheel_list)
        left_group = [w for w in wheel_list if w.center[1] < avg_y]
        right_group = [w for w in wheel_list if w.center[1] >= avg_y]
        return left_group, right_group
    
    front_left_group, front_right_group = split_left_right(front_wheels)
    rear_left_group, rear_right_group = split_left_right(rear_wheels)
    
    # 5. Helper: compute average center and write back to all wheels in group
    def average_and_assign_center(group, corner_name):
        """Compute average center of a wheel group, assign it to all wheels, return the group list."""
        if not group:
            raise ValueError(f"No wheels found for corner {corner_name}")
        
        n = len(group)
        avg_center = [
            sum(w.center[0] for w in group) / n,
            sum(w.center[1] for w in group) / n,
            sum(w.center[2] for w in group) / n,
        ]
        
        if n > 1:
            print(f"ℹ️: {corner_name} has {n} wheel parts with slightly different centers. "
                  f"Averaged center = [{avg_center[0]:.6f}, {avg_center[1]:.6f}, {avg_center[2]:.6f}]")
        
        for w in group:
            w.center = avg_center
        
        return group
    
    # 6. Apply averaging per corner and get wheel list per corner
    front_left  = average_and_assign_center(front_left_group,  "FR_LH")
    front_right = average_and_assign_center(front_right_group, "FR_RH")
    rear_left   = average_and_assign_center(rear_left_group,   "RR_LH")
    rear_right  = average_and_assign_center(rear_right_group,  "RR_RH")
    
    # 7. Return as dict (list of wheels per corner)
    return {
        "FR_LH": front_left,
        "FR_RH": front_right,
        "RR_LH": rear_left,
        "RR_RH": rear_right
    }

def get_wheel_center_position(vwtwheels):
    centers =[]
    for wheel in vwtwheels:
        current_center = wheel.center
        centers.append(current_center)
    return centers

def get_front_rear_wheel_center_position(centers):
    '''
    centers = [x,y,z]
    '''
    if not centers:
        raise ValueError("points list is empty")

    # 5つ以上渡された場合、x,y,z=0,1,0のアイテムを無視する
    if len(centers) >= 5:
        centers = [p for p in centers if not (p[0] == 0 and p[1] == 1 and p[2] == 0)]

    # 全体のx平均
    n = len(centers)
    mean_x = sum(p[0] for p in centers) / n

    # front / rear に分ける
    front = [p for p in centers if p[0] < mean_x]
    rear = [p for p in centers if p[0] >= mean_x]

    # 平均を計算する関数
    def mean_xyz(group):
        if not group:
            return [None, None, None]
        m = len(group)
        mean_x = sum(p[0] for p in group) / m
        mean_y = sum(p[1] for p in group) / m
        mean_z = sum(p[2] for p in group) / m
        return [mean_x, mean_y, mean_z]

    front_mean = mean_xyz(front)
    rear_mean = mean_xyz(rear)

    if debug_mode:
        print(f"Front mean: x={front_mean[0]:.4f}, y={front_mean[1]:.4f}, z={front_mean[2]:.4f}")
        print(f"Rear  mean: x={rear_mean[0]:.4f}, y={rear_mean[1]:.4f}, z={rear_mean[2]:.4f}")

    return {"front_mean": front_mean, "rear_mean": rear_mean}

def group_front_rear_wheel_parts(parts):
    if not parts:
        raise ValueError("Part is empty")
    
    # Get boundary of input parts
    part_boundary = get_boundarybox_of_parts(parts)
    part_center = get_parts_center_from_boundary_box(part_boundary)
    if debug_mode:
        print(f"Parts center of {parts} are {part_center}.")

    # Group parts into front and rear groups
    front_parts = []
    rear_parts = []

    for part in parts:
        part_bb = get_boundarybox_of_parts(part)
        part_center_x = get_parts_center_from_boundary_box(part_bb)[0]
        if part_center_x < part_center[0]:
            front_parts.append(part)
        else:
            rear_parts.append(part)
    
    if debug_mode:
        print(f"Front parts detected is: {front_parts}")
        print(f"Rear parts detected is: {rear_parts}")

    return front_parts, rear_parts

def separate_parts_with_part_names(parts, part_names: List[str]):
    """
    Get vehicle parts and separate custom refinement parts based on part names.

    Parameters
    ----------
    parts : list
        List of Part objects (each having a `.name` attribute)
    part_names : list of str
        List of part names to match against for custom refinements.
        If None, all parts are returned as parts_vehicle.

    Returns
    -------
    parts_vehicle : list
        Parts not matched with any custom refinement names.
    parts_custom_ref : list
        Parts matched with custom refinement names.
    """
    if not parts:
        raise ValueError("Part list is empty")
    
    # If part_names is None, return all parts as parts_vehicle
    if part_names is None:
        return parts, []
    
    if not isinstance(part_names, list):
        raise TypeError("part_names must be a list of strings")

    parts_vehicle = []
    parts_another = []

    for part in parts:
        matched = False
        for name in part_names:
            if not name:  # skip empty/None names
                continue
            if name in part.name:
                parts_another.append(part)
                matched = True
                break
        if not matched:
            parts_vehicle.append(part)

    return parts_vehicle, parts_another



def get_boundarybox_of_parts(parts):
    if not type(parts) == list:
        parts = [parts]
    elif not parts:
        raise ValueError("Failed to get boundary box of parts due to empty input.")
        
    part_zero = parts[0].axisAlignedBoundingBox.minMax
    xmin = part_zero[0][0]
    xmax = part_zero[1][0]
    ymin = part_zero[0][1]
    ymax = part_zero[1][1]
    zmin = part_zero[0][2]
    zmax = part_zero[1][2]
    for part in parts:
        box = part.axisAlignedBoundingBox.minMax
        if box[0][0] < xmin:
            xmin = box[0][0]
        if box[1][0] > xmax:
            xmax = box[1][0]
        if box[0][1] < ymin:
            ymin = box[0][1]
        if box[1][1] > ymax:
            ymax = box[1][1]
        if box[0][2] < zmin:
            zmin = box[0][2]
        if box[1][2] > zmax:
            zmax = box[1][2]
    return [xmin,xmax,ymin,ymax,zmin,zmax]

def get_parts_center_from_boundary_box(boundary_box:List):
    x_center = (boundary_box[0] + boundary_box[1]) /2 
    y_center = (boundary_box[2] + boundary_box[3]) /2 
    z_center = (boundary_box[4] + boundary_box[5]) /2 

    return [x_center,y_center,z_center]

def get_extended_boundarybox_of_parts_with_factor(parts,factors):
    '''
    Assuming factors are given in order of :
    [xmin, xmax, ymin, ymax, zmin, zmax]
    '''
    part_bb = get_boundarybox_of_parts(parts)
    x_length = part_bb[1]-part_bb[0]
    y_length = part_bb[3]-part_bb[2]
    z_length = part_bb[5]-part_bb[4]

    extended_boundary_box = []
    for index, bb in enumerate(part_bb):
        if index in [0,1]:
            extended_boundary_box.append(calculate_box_refinement_dimension(index, factors[index], x_length, bb))
        elif index in [2,3]:
            extended_boundary_box.append(calculate_box_refinement_dimension(index, factors[index], y_length, bb))
        elif index in [4,5]:
            extended_boundary_box.append(calculate_box_refinement_dimension(index, factors[index], z_length, bb))
    
    return extended_boundary_box


def calculate_box_refinement_dimension(self, factor, body_length, boundary_box): #Taking factor, body length, body boundary box to calculate ref box boundary. 
    return factor * body_length + boundary_box

    

def unsetParts(parts_list):
    for part in parts_list:
        hwvwtCorePlugin.hwvwtData.GetVWTData().SetAttribute(part, hwvwtCorePlugin.hwvwtWheelUtil.GetTagPrefix(), "BODY")

def generate_transition_matrix(translate):
    '''
    This function generates Matrix44 object with applied transition from the origin of the model,
    translate = [x,y,z]
    '''
    mtx = Matrix44()
    mtx = mtx.translate(translate)

    return mtx
    

def calculate_wheel_center(front_x,front_z,rear_x,rear_z):
    wheelbase_center = [(front_x+rear_x)/2,
                                 0,
                                 (front_z+rear_z)/2]
    return wheelbase_center

def calculate_wheelbase(front_x,rear_x):
    wheelbase = abs(front_x-rear_x)
    return wheelbase

def calculate_pitch_angle(wb: float, wb_z_difference: float, degree: bool = True) -> float:
    """
    直角三角形の2辺（直角をはさむ2辺）の長さ a, b から、
    その間の角度（小さい方、ラジアンまたは度）を返す。

    Parameters:
        a (float): 一方の直角辺の長さ
        b (float): もう一方の直角辺の長さ
        degree (bool): Trueなら度で返す（デフォルト）、Falseならラジアン

    Returns:
        float: 2辺の間の角度（小さい方）
    """
    # 2辺が直角を挟む → 直角なので角度は常に90°！
    # もし「その2辺ではなく斜辺と他の辺」なら以下の処理：
    hypotenuse = math.sqrt(wb**2 + wb_z_difference**2)
    angle = math.asin(min(wb, wb_z_difference) / hypotenuse)

    if degree:
        angle = math.degrees(angle)

    return angle

def apply_transition(parts,matrix44):
    for part in parts:
        part.position = matrix44

def apply_transition_by_system(parts,sys):
    for part in parts:
        part.position = sys.position


def rotateAboutAxis(x, y, z, theta, axis=[0, 0, 1], normalize=False):
    """
    Rotate point (x, y, z) around an arbitrary axis passing through the origin.

    Parameters
    ----------
    x, y, z : float
        Coordinates of the point to rotate
    theta : float
        Rotation angle in degrees
    axis : list or array-like of shape (3,)
        Rotation axis vector (e.g., [1, 0, 0] or [1, 1, 0])
    normalize : bool, optional
        If True, normalize the rotated vector to unit length

    Returns
    -------
    list of [x, y, z]
        Rotated point coordinates (rounded to 12 decimal places)
    """
    theta = np.radians(theta)
    point = np.array([x, y, z], dtype=float)
    axis = np.array(axis, dtype=float)

    # --- normalize axis ---
    axis_norm = np.linalg.norm(axis)
    if axis_norm == 0:
        raise ValueError("Rotation axis vector cannot be zero.")
    axis = axis / axis_norm

    # --- Rodrigues' rotation formula ---
    K = np.array([
        [0, -axis[2], axis[1]],
        [axis[2], 0, -axis[0]],
        [-axis[1], axis[0], 0]
    ])
    I = np.eye(3)
    R = I + np.sin(theta) * K + (1 - np.cos(theta)) * (K @ K)

    rotated = R.dot(point)

    if normalize:
        mag = np.linalg.norm(rotated)
        if mag != 0:
            rotated = rotated / mag

    return [round(rotated[0], 12), round(rotated[1], 12), round(rotated[2], 12)]

def apply_yaw_pitch_to_system(sys,center=[0,0,0],yaw_angle=0,pitch_angle=0):
    '''
    Apply yaw and pitch to the system at center applied.
    '''
    # --- Step 1: Yaw rotation first ---
    sys.position = sys.position.rotz(yaw_angle)
    axis_y_after_yaw = sys.position[1]
    axis_y_after_yaw.pop()

    # --- Step 2: Pitch rotation about Y-axis ---
    # Applying minus to the axis to follow rotate feature's spec.

    sys.position = sys.position.rotate(axis_y_after_yaw,-pitch_angle)

    # --- Step 3: Compute rotation around consistent center ---
    rotated_center = rotateAboutAxis(
        center[0],center[1],center[2],
        yaw_angle, axis=[0,0,1]
    )
    print(f"Rotated center by yaw: {rotated_center}")

    rotated_center = rotateAboutAxis(
        rotated_center[0], rotated_center[1], rotated_center[2],
        pitch_angle, axis=axis_y_after_yaw
    )
    print(f"Rotated center by pitch: {rotated_center}")

    # --- Step 4: Transition to bring WB center back to original ---
    collection_transition = [
        center[0] - rotated_center[0],
        center[1] - rotated_center[1],
        center[2] - rotated_center[2]
    ]

    print(f"Collection transition to position back to WB center: {collection_transition}")

    sys.location = collection_transition


def apply_translate_to_system(sys,transition:List):
    '''
    Input:
    sys: vwt.System
    transition: [x,y,z]
    '''
    sys.position = sys.position.translate(transition)



def check_wall_bc_setup():
    '''
    Apply appropriate wheel/ground boudnary condition setup according to user input
    '''
    # Getting global variables (not supposed to be changed in this script)
    global opt_moving_floor, opt_belt_system, osm_wheels,enable_noslip_moving_ground_for_1belt
    
    # No rotating wheel
    if not opt_moving_floor:
        if osm_wheels:
            print("⚠️: OSM is activated with non rotating wheel BC. Please review the setting.")
        elif opt_belt_system:
            print("⚠️: 5 belt system is activated with non rotating wheel BC. Please review the setting.")
        else:
            print("✅: No rotating wheels applied. OSM and belts are deactivated.")
            print("□: Rotating wheels with 5 belts applied with OSM.")
            print("□: Rotating wheels with 5 belts applied without OSM.")
            print("□: Rotating wheels with full moiving applied with OSM + Fullslip ground.")
            print("□: Rotating wheels with full moiving applied with OSM + moving no-slip ground.")
            print("□: Rotating wheels with full moiving applied without OSM + Fullslip ground.")
            print("□: Rotating wheels with full moiving applied without OSM + moving no-slip ground.")
    
    # Rotating wheel with 5 belts
    if opt_belt_system:
        if osm_wheels:
            print("□: No rotating wheels applied. OSM and belts are deactivated.")
            print("✅: Rotating wheels with 5 belts applied with OSM.")
            print("□: Rotating wheels with 5 belts applied without OSM.")
            print("□: Rotating wheels with full moiving applied with OSM + Fullslip ground.")
            print("□: Rotating wheels with full moiving applied with OSM + moving no-slip ground.")
            print("□: Rotating wheels with full moiving applied without OSM + Fullslip ground.")
            print("□: Rotating wheels with full moiving applied without OSM + moving no-slip ground.")
        else:
            print("□: No rotating wheels applied. OSM and belts are deactivated.")
            print("□: Rotating wheels with 5 belts applied with OSM.")
            print("✅: Rotating wheels with 5 belts applied without OSM.")
            print("□: Rotating wheels with full moiving applied with OSM + Fullslip ground.")
            print("□: Rotating wheels with full moiving applied with OSM + moving no-slip ground.")
            print("□: Rotating wheels with full moiving applied without OSM + Fullslip ground.")
            print("□: Rotating wheels with full moiving applied without OSM + moving no-slip ground.")

    # Rotating wheel with full moving + full slip
    if opt_moving_floor and not opt_belt_system:
        if osm_wheels:
            if enable_noslip_moving_ground_for_1belt:
                print("□: No rotating wheels applied. OSM and belts are deactivated.")
                print("□: Rotating wheels with 5 belts applied with OSM.")
                print("□: Rotating wheels with 5 belts applied without OSM.")
                print("□: Rotating wheels with full moiving applied with OSM + Fullslip ground.")
                print("✅: Rotating wheels with full moiving applied with OSM + moving no-slip ground.")
                print("□: Rotating wheels with full moiving applied without OSM + Fullslip ground.")
                print("□: Rotating wheels with full moiving applied without OSM + moving no-slip ground.")
            else:
                print("□: No rotating wheels applied. OSM and belts are deactivated.")
                print("□: Rotating wheels with 5 belts applied with OSM.")
                print("□: Rotating wheels with 5 belts applied without OSM.")
                print("✅: Rotating wheels with full moiving applied with OSM + Fullslip ground.")
                print("□: Rotating wheels with full moiving applied with OSM + moving no-slip ground.")
                print("□: Rotating wheels with full moiving applied without OSM + Fullslip ground.")
                print("□: Rotating wheels with full moiving applied without OSM + moving no-slip ground.")
        else:
            if enable_noslip_moving_ground_for_1belt:
                print("□: No rotating wheels applied. OSM and belts are deactivated.")
                print("□: Rotating wheels with 5 belts applied with OSM.")
                print("□: Rotating wheels with 5 belts applied without OSM.")
                print("□: Rotating wheels with full moiving applied with OSM + Fullslip ground.")
                print("□: Rotating wheels with full moiving applied with OSM + moving no-slip ground.")
                print("□: Rotating wheels with full moiving applied without OSM + Fullslip ground.")
                print("✅: Rotating wheels with full moiving applied without OSM + moving no-slip ground.")
            else:
                print("□: No rotating wheels applied. OSM and belts are deactivated.")
                print("□: Rotating wheels with 5 belts applied with OSM.")
                print("□: Rotating wheels with 5 belts applied without OSM.")
                print("□: Rotating wheels with full moiving applied with OSM + Fullslip ground.")
                print("□: Rotating wheels with full moiving applied with OSM + moving no-slip ground.")
                print("✅: Rotating wheels with full moiving applied without OSM + Fullslip ground.")
                print("□: Rotating wheels with full moiving applied without OSM + moving no-slip ground.")

def get_ground_position(parts,ground_height,calculate_ground_height_from_zMin):
    car_bb = get_boundarybox_of_parts(parts)
    if calculate_ground_height_from_zMin:
        ground_height_distance = ground_height
        ground_height = car_bb[4] + ground_height_distance
        print(f"✅: Ground height adjusted from zMin of input parts with distance of {ground_height_distance} m.")
        print(f"ℹ️: Ground height adjusted is at Z = {ground_height} m.")
    
    return ground_height

def get_wheel_belt_positions(parts,WheelTirePartsNames):
    print("✅: Wheel belt size was calculated automatically.")
    # Getting tire parts
    wheelTireparts = []
    boundary_box_wheel_parts = []
    for name in WheelTirePartsNames:
        wheelTireparts += [current_part for current_part in parts if name in current_part.name]
    # Getting boundary box.
    for part in wheelTireparts:
        current_dim = []
        current_dim.append(part.axisAlignedBoundingBox.minMax[0][0]) # xmin
        current_dim.append(part.axisAlignedBoundingBox.minMax[1][0]) # xmax
        current_dim.append(part.axisAlignedBoundingBox.minMax[0][1]) # ymin
        current_dim.append(part.axisAlignedBoundingBox.minMax[1][1]) # ymax
        boundary_box_wheel_parts.append(current_dim)
    # Over writing belt center positions using wheel boundary box.
    belt_center_position_fr_lh = [(boundary_box_wheel_parts[0][0] + boundary_box_wheel_parts[0][1])/2, (boundary_box_wheel_parts[0][2] + boundary_box_wheel_parts[0][3])/2]
    belt_center_position_fr_rh = [(boundary_box_wheel_parts[1][0] + boundary_box_wheel_parts[1][1])/2, (boundary_box_wheel_parts[1][2] + boundary_box_wheel_parts[1][3])/2]
    belt_center_position_rr_lh = [(boundary_box_wheel_parts[2][0] + boundary_box_wheel_parts[2][1])/2, (boundary_box_wheel_parts[2][2] + boundary_box_wheel_parts[2][3])/2]
    belt_center_position_rr_rh = [(boundary_box_wheel_parts[3][0] + boundary_box_wheel_parts[3][1])/2, (boundary_box_wheel_parts[3][2] + boundary_box_wheel_parts[3][3])/2]

    return belt_center_position_fr_lh, belt_center_position_fr_rh, belt_center_position_rr_lh, belt_center_position_rr_rh

def apply_output_formatting_settings(output_instance_vwt, output_format):
    '''
    Apply output formatting settings according to user input from excel.
    '''
    # Ensure output_format is a string and handle the format setting
    if isinstance(output_format, list):
        output_format = output_format[0] if output_format else "h3d"

    if output_format == "ensight":
        output_instance_vwt.ensight = True
        output_instance_vwt.h3d = False
    elif output_format == "h3d":
        output_instance_vwt.h3d = True
        output_instance_vwt.ensight = False
    elif output_format == "ensight_and_h3d":
        output_instance_vwt.h3d = True
        output_instance_vwt.ensight = True
    else:
        print(f"⚠️ Warning: Invalid output format '{output_format}'. Using default 'ensight'.")
        output_instance_vwt.ensight = True
        output_instance_vwt.h3d = False
        
    

#####################################################################
# ### Loading geometries
#####################################################################
# Loading stl file
DATA_FOLDER = general_settings.get('DATA_FOLDER')
# Assuming data folder is only given one.
temppath = ""
count=0
for item in DATA_FOLDER:
    if count == 0:
        temppath = temppath + item
        count += 1
    else:
        temppath = temppath + ', ' + item
DATA_FOLDER = temppath

# Normalize path separators for cross-platform compatibility (Windows \ → /)
DATA_FOLDER = DATA_FOLDER.replace('\\', '/')

list_stl_files = general_settings.get('list_stl_files')
# list_stl_files = [ "belt_0deg.stl"]
for tmp_stl_file in list_stl_files:
    tmp_file_path = os.path.join(DATA_FOLDER, tmp_stl_file)
    print(f"🕒: Loading file : {tmp_file_path}")
    inspire.importFile(tmp_file_path)
    
model_vehicle = inspire.getActiveModel()
parts_vehicle = inspire.getActiveModel().parts
#assembly_vehicle = model.assemblies


#####################################################################
# ### Exclude custom parts from parts_vehicle
#####################################################################
# Storing original parts set to apply mesh settings
parts_original = parts_vehicle
# Separate passive parts from vehicle parts
parts_vehicle, parts_windtunnel_parts = separate_parts_with_part_names(parts_vehicle,windtunnel_parts)
# Get total parts for ride height adjustment and yaw application
parts_total = parts_vehicle
# Separate custom refinement parts from vehicle parts
parts_vehicle, parts_custom_ref = separate_parts_with_part_names(parts_vehicle,custom_refinement_names)



#####################################################################
# ### Get ground position
#####################################################################
ground_height = get_ground_position(parts_vehicle,ground_height,calculate_ground_height_from_zMin)


#####################################################################
# ### Adjust ride height if adjust_ride_height option is true
#####################################################################
if adjust_ride_height:
    print("🕒: Adjusting Ride Height...")
    # Apply wheels to get heave feature in vwt run.
    # In 2026.0 build, even with static ground case this operation will be done anyway to calculate wheelbase.    
    # Get list of wheel parts
    if RimPartsNames:  # Use rims to define wheel axis/center
        # 1. Create wheels from rim parts
        rims, rimparts = get_set_rims(RimPartsNames)
        
        # 2. Classify rims by position (coordinate-based)
        rim_classified = classify_wheels_by_position(rims)
        
        # 3. Save axis and center from each rim (use first wheel in each corner group as reference)
        rim_properties = {
            corner: {"axis": rim_list[0].axis, "center": rim_list[0].center}
            for corner, rim_list in rim_classified.items()
        }
        
        if debug_mode:
            print("🔍 Rim positions detected:")
            for corner, rim_list in rim_classified.items():
                print(f"  {corner}: center={rim_list[0].center}, axis={rim_list[0].axis} ({len(rim_list)} parts)")

        #unset rim parts to avoid affecting wheel creation process
        unsetParts(rimparts)
        
        # 4. Create wheels from WheelPartsNames
        wheels, wheelparts = get_set_wheels(WheelPartsNames)
        
        # 5. Classify wheels by position (coordinate-based)
        wheel_classified = classify_wheels_by_position(wheels)
        
        if debug_mode:
            print("🔍 Wheel positions detected:")
            for corner, wheel_list in wheel_classified.items():
                print(f"  {corner}: center={wheel_list[0].center} ({len(wheel_list)} parts)")
        
        # 6. Override wheel axis and center with corresponding rim values for ALL wheels in each corner
        for corner in ["FR_LH", "FR_RH", "RR_LH", "RR_RH"]:
            for w in wheel_classified[corner]:
                w.axis = rim_properties[corner]["axis"]
                w.center = rim_properties[corner]["center"]
        
        print(f"✅: Wheel axis and center defined by rim parts (position-based matching)")
    else:
        # Standard behavior without rim parts
        wheels,wheelparts = get_set_wheels(WheelPartsNames)
    
    if osm_wheels:
        osm_parts = set_osm_wheels(WheelOSMPartsNames)
        
    # Keep original position of the wheel for belts
    if wheel_belt_location_auto:
        belt_center_position_fr_lh,belt_center_position_fr_rh,belt_center_position_rr_lh,belt_center_position_rr_rh = get_wheel_belt_positions(parts_vehicle,WheelTirePartsNames)


   
    # Keep original positions for check
    original_wheel_centers = get_wheel_center_position(wheels)
    original_front_rear_wheel_centers = get_front_rear_wheel_center_position(original_wheel_centers)

    # Get transition and rotation information
    # Get wheelbase center of original data: [x,y,z]
    wheelbase_center_original = calculate_wheel_center(original_front_rear_wheel_centers['front_mean'][0],original_front_rear_wheel_centers['front_mean'][2],original_front_rear_wheel_centers['rear_mean'][0],original_front_rear_wheel_centers['rear_mean'][2])
    wheelbase = calculate_wheelbase(original_front_rear_wheel_centers['front_mean'][0],original_front_rear_wheel_centers['rear_mean'][0])
    #print(f"wheelbase_center_original is {wheelbase_center_original}")
    #print(f"wheelbase is {wheelbase}")
    # Get wheelbase center of RH position
    # Calculate axle heights from z=0 plane reffering to user input
    front_wheel_axis_RH_from_z0 = front_wheel_axis_RH + ground_height
    rear_wheel_axis_RH_from_z0 = rear_wheel_axis_RH + ground_height  
    wheelbase_center_in_RH_pos = [wheelbase_center_original[0],0,(front_wheel_axis_RH_from_z0+rear_wheel_axis_RH_from_z0)/2]
    #print(f"wheelbase_center_in_RH_pos is {wheelbase_center_in_RH_pos}")

    # Get pitch angle:
    wheelbase_center_original_z_diff = original_front_rear_wheel_centers['front_mean'][2]-original_front_rear_wheel_centers['rear_mean'][2]
    #print(f"wheelbase_center_original_z_diff is {wheelbase_center_original_z_diff}")   
    wheelbase_center_RH_z_diff = front_wheel_axis_RH_from_z0-rear_wheel_axis_RH_from_z0
    #print(f"wheelbase_center_RH_z_diff is {wheelbase_center_RH_z_diff}")
    pitch_angle_original = calculate_pitch_angle(wheelbase,wheelbase_center_original_z_diff)
    pitch_angle_RH_pos = calculate_pitch_angle(wheelbase,wheelbase_center_RH_z_diff)
    
    # Get wheelbase center z transition
    wheelbase_center_z_transition = wheelbase_center_in_RH_pos[2] - wheelbase_center_original[2]
    #print(f"wheelbase_center_z_transition is {wheelbase_center_z_transition}")
    # Get wheelbase transition list
    wheelbase_center_transition = [0,0,wheelbase_center_z_transition]
    # Get rotation angle at wheelbase center
    wheelbase_center_rotation_angle = pitch_angle_RH_pos - pitch_angle_original
    #print(f"wheelbase_center_rotation_angle is {wheelbase_center_rotation_angle} deg.")

    # Apply rotation at origin first
    # Then apply transition to make sure that WB center is in the original pos and transition due to RH change is applied.
    cys_body = inspire.System()
    cys_body.name = "body"

    apply_yaw_pitch_to_system(cys_body,wheelbase_center_original,yaw_angle_vehicle,wheelbase_center_rotation_angle)
    apply_translate_to_system(cys_body,wheelbase_center_transition)
    apply_transition_by_system(parts_total,cys_body)

    
    print(f"✅: Ride height adjusted with Front: {front_wheel_axis_RH}m, Rear: {rear_wheel_axis_RH}m.")
    print(f"ℹ️: Front axis is now at Z= {front_wheel_axis_RH_from_z0}m.")
    print(f"ℹ️: Rear axis is now at Z= {rear_wheel_axis_RH_from_z0}m.")

    # if body and wheels are moved differently.
    if adjust_body_wheel_separately:
        
        # moving wheel position back to the original.
        if use_original_wheel_position:
            # Generate system for wheels
            cys_wheels = inspire.System()
            cys_wheels.name = "wheels"
            
            wheelbase_center_transition_to_original = []
            for transition in wheelbase_center_transition:
                transition_to_original = -transition
                wheelbase_center_transition_to_original.append(transition_to_original)
            # Tyre at original position should only have yaw angle. No pitch applied.
            apply_yaw_pitch_to_system(cys_wheels,wheelbase_center_original,yaw_angle=yaw_angle_vehicle,pitch_angle=0)
            # Applying transition by system
            apply_transition_by_system(wheelparts,cys_wheels)
            # Moving OSM parts
            if osm_wheels:
                # for osm in osm_parts:
                apply_transition_by_system(osm_parts,cys_wheels)
            print("✅: Wheel position has been shifted to the original position.")
        # If the option is false, calculate the wheel position
        else:
            # Generate system for wheels separately for front and rear
            cys_wheel_front = inspire.System()
            cys_wheel_front.name = "front_wheels"
            cys_wheel_rear = inspire.System()
            cys_wheel_rear.name = "rear_wheels"
            # Calculate the front and rear transition from the original position
            front_wheel_axis_from_z0 = front_wheel_axis_height + ground_height
            rear_wheel_axis_from_z0 = rear_wheel_axis_height + ground_height
            front_wheel_z_transition = front_wheel_axis_from_z0 - original_front_rear_wheel_centers["front_mean"][2]
            rear_wheel_z_transition = rear_wheel_axis_from_z0 - original_front_rear_wheel_centers["rear_mean"][2]

            # Get front and rear parts
            front_wheel_parts, rear_wheel_parts = group_front_rear_wheel_parts(wheelparts)
            if osm_wheels:
                front_osm_parts, rear_osm_parts = group_front_rear_wheel_parts(osm_parts)


            # Apply transition to the systems
            apply_yaw_pitch_to_system(cys_wheel_front,wheelbase_center_original,yaw_angle=yaw_angle_vehicle,pitch_angle=0)
            apply_yaw_pitch_to_system(cys_wheel_rear,wheelbase_center_original,yaw_angle=yaw_angle_vehicle,pitch_angle=0)
            apply_translate_to_system(cys_wheel_front,transition=[0,0,front_wheel_z_transition])
            apply_translate_to_system(cys_wheel_rear,transition=[0,0,rear_wheel_z_transition])

            # Apply transition using the system
            apply_transition_by_system(front_wheel_parts,cys_wheel_front)
            apply_transition_by_system(rear_wheel_parts,cys_wheel_rear)
            if osm_wheels:
                apply_transition_by_system(front_osm_parts,cys_wheel_front)
                apply_transition_by_system(rear_osm_parts,cys_wheel_rear)

            
            if debug_mode:
                print(f"FRONT WH RH BEFORE MOVE IS {original_front_rear_wheel_centers['front_mean']}")
                print(f"FRONT RH FROM GROUND IS {front_wheel_axis_height}")
            
            print("✅: Wheel heights are adjusted separately from Body.")
            if debug_mode:
                print(f"ℹ️: Front wheel parts are: {front_wheel_parts}.")
                print(f"ℹ️: Rear wheel parts are: {rear_wheel_parts}.")
            print(f"✅: Wheel Ride height updated with Front: {front_wheel_axis_height}m, Rear: {rear_wheel_axis_height}m.")
            print(f"✅: Wheel Front axis is now at Z= {front_wheel_axis_from_z0}m.")
            print(f"✅: Wheel Rear axis is now at Z= {rear_wheel_axis_from_z0}m.")
    print("✅: Ride height adjustment has been completed.")

    # Unset wheels
    unsetParts(wheelparts)


#####################################################################
# ### Derive dimensions (At STR condition)
#####################################################################
# --------------------------
# Derive dimensions for belts
# --------------------------

list_belt_name = []
if(opt_belt_system): #if 5 belt system is on.
    print("✅: Setup with 5 belt system on.")
    belt_dimensions_input = [] 
    # Getting belt center using wheel positions. When RH adjustment is on, this process will be run before RH change process.
    if not adjust_ride_height and wheel_belt_location_auto: 
        belt_center_position_fr_lh,belt_center_position_fr_rh,belt_center_position_rr_lh,belt_center_position_rr_rh = get_wheel_belt_positions(parts_vehicle,WheelTirePartsNames)
        
    # Getting belt dimensions using belt center posision and belt size.
    belt_dimensions_input.append([belt_center_position_fr_lh[0]-belt_size_wheel[0]/2, belt_center_position_fr_lh[0]+belt_size_wheel[0]/2, belt_center_position_fr_lh[1]-belt_size_wheel[1]/2, belt_center_position_fr_lh[1]+belt_size_wheel[1]/2])
    belt_dimensions_input.append([belt_center_position_fr_rh[0]-belt_size_wheel[0]/2, belt_center_position_fr_rh[0]+belt_size_wheel[0]/2, belt_center_position_fr_rh[1]-belt_size_wheel[1]/2, belt_center_position_fr_rh[1]+belt_size_wheel[1]/2])
    belt_dimensions_input.append([belt_center_position_rr_lh[0]-belt_size_wheel[0]/2, belt_center_position_rr_lh[0]+belt_size_wheel[0]/2, belt_center_position_rr_lh[1]-belt_size_wheel[1]/2, belt_center_position_rr_lh[1]+belt_size_wheel[1]/2])
    belt_dimensions_input.append([belt_center_position_rr_rh[0]-belt_size_wheel[0]/2, belt_center_position_rr_rh[0]+belt_size_wheel[0]/2, belt_center_position_rr_rh[1]-belt_size_wheel[1]/2, belt_center_position_rr_rh[1]+belt_size_wheel[1]/2])
    # Updates centre belt center position if the automated option is on.
    if centre_belt_at_wheelbase_centre:
        # Get wheelbase center position
        wheels,wheelparts = get_set_wheels(WheelPartsNames)
        original_wheel_centers = get_wheel_center_position(wheels)
        original_front_rear_wheel_centers = get_front_rear_wheel_center_position(original_wheel_centers)
        wheelbase_center_original = calculate_wheel_center(original_front_rear_wheel_centers['front_mean'][0],original_front_rear_wheel_centers['front_mean'][2],original_front_rear_wheel_centers['rear_mean'][0],original_front_rear_wheel_centers['rear_mean'][2])
        print(f"✅: Centre position of 5 Belt Centre belt has been adjusted to x:{wheelbase_center_original[0]}, y:{wheelbase_center_original[1]}")
        belt_center_position_center = wheelbase_center_original
        # Make sure unset wheels so that it does not affect the real wheel creation process.
        unsetParts(wheelparts)
    belt_dimensions_input.append([belt_center_position_center[0]-belt_size_center[0]/2, belt_center_position_center[0]+belt_size_center[0]/2, belt_center_position_center[1]-belt_size_center[1]/2, belt_center_position_center[1]+belt_size_center[1]/2])

    #Generating boundary box of the belt systems
    boundary_box_belts = []
    for indx in range(4):
        boundary_box_belts.append(belt_dimensions_input[0][indx])
        for current_belt in belt_dimensions_input:
            boundary_box_belts[indx]  = min(boundary_box_belts[indx],current_belt[indx])*(indx%2==0) + max(boundary_box_belts[indx],current_belt[indx])*(indx%2!=0)
            # if(indx in [0,2,4]):
            #     boundary_box_belts[indx] = min(boundary_box_belts[indx],current_belt[indx])
            # elif(indx in [1,3,5]):
            #     boundary_box_belts[indx] = max(boundary_box_belts[indx],current_belt[indx])

# --------------------------------
# Derive dimensions for vehicle body
# --------------------------------

# get vehicle dimension
boundary_box_body = []
body_parts_dimensions = []
for current_part in parts_vehicle:
    current_dim = []
    if(HM_CFD_version>=2024):
        current_dim.append(current_part.axisAlignedBoundingBox.minMax[0][0]) # xmin
        current_dim.append(current_part.axisAlignedBoundingBox.minMax[1][0]) # xmax
        current_dim.append(current_part.axisAlignedBoundingBox.minMax[0][1]) # ymin
        current_dim.append(current_part.axisAlignedBoundingBox.minMax[1][1]) # ymax    
        current_dim.append(current_part.axisAlignedBoundingBox.minMax[0][2]) # zmin
        current_dim.append(current_part.axisAlignedBoundingBox.minMax[1][2]) # zmax    

    else:
        current_dim.append(current_part.axisAlignedBoundingBox.GetMin()[0]) # xmin
        current_dim.append(current_part.axisAlignedBoundingBox.GetMax()[0]) # xmax
        current_dim.append(current_part.axisAlignedBoundingBox.GetMin()[1]) # ymin
        current_dim.append(current_part.axisAlignedBoundingBox.GetMax()[1]) # ymax
        current_dim.append(current_part.axisAlignedBoundingBox.GetMin()[2]) # zmin
        current_dim.append(current_part.axisAlignedBoundingBox.GetMax()[2]) # zmax
            
    body_parts_dimensions.append(current_dim)

# get boundary box in the format of:
# [xmin, xmax, ymin, ymax, zmin, zmax]
boundary_box_body = []
for indx in range(6):
    boundary_box_body.append(body_parts_dimensions[0][indx])
    for current_part in body_parts_dimensions:
        boundary_box_body[indx]  = min(boundary_box_body[indx],current_part[indx])*(indx%2==0) + max(boundary_box_body[indx],current_part[indx])*(indx%2!=0)
    if(indx==4):
        boundary_box_body[indx] = ground_height

print("ℹ️: boundary box body is")
print(boundary_box_body)

body_length_x = boundary_box_body[1] - boundary_box_body[0]
body_length_y = boundary_box_body[3] - boundary_box_body[2]
body_length_z = boundary_box_body[5] - boundary_box_body[4]

print("ℹ️: Body length in x, y, z are:")
print(body_length_x)
print(body_length_y)
print(body_length_z)



# --------------------------------
# Derive dimensions for heat exchangers for RL7 Offset
# --------------------------------
# Get list of names for heat exchangers
heat_exchanger_part_names = []
for heat_exchanger in Heat_exchangers:
    heat_exchanger_part_names.append(heat_exchanger["name"])

# Get part list of heat exchangers
heat_exchanger_parts = []
for name in heat_exchanger_part_names:
    current_part = []
    for part in parts_vehicle:
        if name in part.name:
            current_part.append(part)
    heat_exchanger_parts.append(current_part)   

# Get dimension list for heat exchangers
body_dimensions_heat_exchangers = []
for heat_exchanger in heat_exchanger_parts:
    current_dim = []
    for part in heat_exchanger:
        temp_list = []
        temp_list.append(part.axisAlignedBoundingBox.minMax[0][0]) # xmin
        temp_list.append(part.axisAlignedBoundingBox.minMax[1][0]) # xmax
        temp_list.append(part.axisAlignedBoundingBox.minMax[0][1]) # ymin
        temp_list.append(part.axisAlignedBoundingBox.minMax[1][1]) # ymax    
        temp_list.append(part.axisAlignedBoundingBox.minMax[0][2]) # zmin
        temp_list.append(part.axisAlignedBoundingBox.minMax[1][2]) # zmax
        current_dim.append(temp_list)
    body_dimensions_heat_exchangers.append(current_dim)

# Extracting min and max values for each heat exchangers
boundary_box_heat_exchangers = []
if not len(heat_exchanger_parts) == 0:
    for heat_exchanger in body_dimensions_heat_exchangers:
        current_min_max = heat_exchanger[0].copy() #Initialising with first list
        for part in heat_exchanger:
            for indx in range(len(part)):
                if indx % 2 == 0: #Even numbers, min values
                    current_min_max[indx] = min(current_min_max[indx],part[indx])
                else: #Odd numbers, max values
                    current_min_max[indx] = max(current_min_max[indx],part[indx])
        boundary_box_heat_exchangers.append(current_min_max)

# --------------------------------------
# define static floor dimensions
# --------------------------------------
if(bl_suction_by_belt_x_min & opt_belt_system):
    if bl_suction_by_belt_x_min_distance == 0:
        print("✅: BL suction position has been applied based on 5 belt x min.")
        bl_suction_pos_x = belt_dimensions_input[-1][0]
    else:
        print("✅: BL suction position has been applied based on 5 belt x min + Distance from xMin.")
        bl_suction_pos_x = belt_dimensions_input[-1][0] + bl_suction_by_belt_x_min_distance        

else:
    print("✅: BL suction position has been applied based on 'bl_suction_pos_x_input'.")
    bl_suction_pos_x = bl_suction_pos_x_input
# -- static floor dimension --> to be updated for yaw-angled cases

static_floor_dimensions = []
static_floor_dimensions.append(bl_suction_pos_x) # xmin: suction position (either belt xmin or user input)
if(belt_dimension_based_static & opt_belt_system):
    print("✅: Static floor has been defined based on belt dimensions.")
    static_floor_dimensions.append(belt_dimensions_input[-1][1]) # xmax = xmax of center belt
    static_floor_dimensions.append(scale_factor_static_floor_belt_width * boundary_box_belts[2]) # ymin
    static_floor_dimensions.append(scale_factor_static_floor_belt_width * boundary_box_belts[3]) # ymax

else:
    print("✅: Static floor has been defined based on body dimensions.")
    static_floor_dimensions.append(boundary_box_body[1] + body_length_x*(scale_factor_static_floor_body_length-1)) # xmax
    static_floor_dimensions.append(boundary_box_body[2] - body_length_y*(scale_factor_static_floor_body_width-1)) # ymin
    static_floor_dimensions.append(boundary_box_body[3] + body_length_y*(scale_factor_static_floor_body_width-1)) # ymax

#####################################################################
# ### Set domain size
#####################################################################

domain_dimension = []
for indx in range(len(boundary_box_body)):
    if indx == 0 or indx == 1:
        domain_dimension.append(body_length_x*domain_size_factor[indx] + boundary_box_body[indx])
    elif indx == 2 or indx == 3:
        domain_dimension.append(body_length_y*domain_size_factor[indx] + boundary_box_body[indx])
    elif indx == 4:
        domain_dimension.append(ground_height)
    else:
        domain_dimension.append(body_length_z*domain_size_factor[indx] + boundary_box_body[indx])

# - set wind tunnel
tunnel = vwt.Tunnel()  # WARNING: IT CAUSES CRASH IF VEHICLE IS NOT LOADED (meaning, only belt is loaded)
tunnel.length   = domain_dimension[1] - domain_dimension[0]
tunnel.width    = domain_dimension[3] - domain_dimension[2]
tunnel.height   = domain_dimension[5] - domain_dimension[4]
tunnel.xMin = domain_dimension[0]
tunnel.yMin = domain_dimension[2]
tunnel.zMin = ground_height
if enable_ground_patch:
    # 5 belt or static floor
    if opt_belt_system or not opt_moving_floor:
        tunnel.enableGroundPatch = True
        print("✅: Ground patch is activated.")
    # 1 belt
    else:
        print("✅: Ground patch is deactivated.")

# Specifying tunnel velocity
if(match_inflow_belt_speed or abs(yaw_angle_vehicle)==0):
    tunnel.velocity = inflow_velocity # m/s  # to be updated for yaw case
else:
    tunnel.velocity = inflow_velocity/Matrix44(angles=(0,0,yaw_angle_vehicle),degrees=True)[0][0]


# boundary condition --> full slip (static floor is added manually later) in 2024.0 or earlier
# Activating boundary layer suction for at any type of BC. Required for 1 belt system to apply full slip ground for the entire domain.
tunnel.boundaryLayerSuction = True
tunnel.boundaryLayerReference = "Origin"

# Applying full slip for full moving condition.
if opt_moving_floor and not opt_belt_system:
    if not enable_noslip_moving_ground_for_1belt:
        tunnel.boundaryLayerDistance = 1000
    else:
        tunnel.boundaryLayerSuction = False
else:
    tunnel.boundaryLayerDistance = bl_suction_pos_x

#####################################################################
# ### OPERATIONS FOR YAW CASES
#####################################################################
# Operations for yaw cases, only when yaw angle is set non zero.
if yaw_angle_vehicle != 0:
    print(f"ℹ️: This case has yaw angle of :{yaw_angle_vehicle} degrees.")

    # Creating sketches for each belts if 5 belt is activated
    if opt_belt_system:
        for belt in belt_dimensions_input:
            sketch = Sketch()
            rec = sketch.addRectangle2Vertex((belt[0], belt[2]), (belt[1], belt[3]))
            sketch.realize()
        # Extruding sketches created
        belt_parts = []
        for indx in range(len(belt_dimensions_input)): 
            sketch_part = model.getAllChildren('SketchPart')[indx]
            belt_name = "Belt_" + str(indx+1)
            #sketch_part.name = belt_name
            solid = inspire.geometry.extrude(sketch_part.getFeatures(type=inspire.FeatureArea),"BOTH", "NEW_PART", extrudeTo1=0.0001, extrudeTo2=0.0001)
            solid.name = belt_name
            belt_parts.append(solid)
            #sketch_part.deleteFaces2()
    

# - rotate around center of turn table
    # If rotate car at wheelbase center
    # When RH adjustment is on, this will be done by RH tool, so skipped.
    if rotate_yaw_at_wheelbase_center:
        if not adjust_ride_height:
            # Get wheelbase center position
            wheels,wheelparts = get_set_wheels(WheelPartsNames)
            original_wheel_centers = get_wheel_center_position(wheels)
            original_front_rear_wheel_centers = get_front_rear_wheel_center_position(original_wheel_centers)
            wheelbase_center_original = calculate_wheel_center(original_front_rear_wheel_centers['front_mean'][0],original_front_rear_wheel_centers['front_mean'][2],original_front_rear_wheel_centers['rear_mean'][0],original_front_rear_wheel_centers['rear_mean'][2])
            print(f"✅: Centre position of Yaw rotation has been adjusted to {wheelbase_center_original}")
            cnt_turn_table = wheelbase_center_original
            # Make sure unset wheels so that it does not affect the real wheel creation process.
            unsetParts(wheelparts)

            cys_body = inspire.System()
            cys_body.name = "body"
            apply_yaw_pitch_to_system(cys_body,wheelbase_center_original,yaw_angle_vehicle,0)
            apply_transition_by_system(parts_total,cys_body)
            # Belts need to be rotated here regardless RH adjustment is applied or not.
        if opt_belt_system:
            cys_belt = inspire.System()
            cys_belt.name = "belt"
            apply_yaw_pitch_to_system(cys_belt,wheelbase_center_original,yaw_angle_vehicle,0)
            apply_transition_by_system(belt_parts,cys_belt)
    # If you rotate car at Origin.
    else:
        mtx_yaw_angle = Matrix44(origin=cnt_turn_table, angles=( 0, 0, yaw_angle_vehicle), degrees=True)
        if not adjust_ride_height:
            # Ride height feature will adjust yaw, therefore not needed when it's on.
            for part in parts_vehicle:
                part.position = mtx_yaw_angle
        if opt_belt_system:
                for part in belt_parts:
                    part.position = mtx_yaw_angle

    # Passive Parts for belts
    if opt_belt_system:
        if include_wheel_belt_forces:
            passive_belts = belt_parts[4]
            vwt.setPassivePart(passive_belts, False)
        else:
            for belt in belt_parts:
                vwt.setPassivePart(belt, False)


else:
    print("ℹ️: This case is straight ahead condition (yaw angle = 0 degrees)")

#####################################################################
# ### Derive dimensions (Overwriting settings for Yaw)
#####################################################################
# --------------------------------
# Derive dimensions for vehicle body
# --------------------------------
# get vehicle dimension
if yaw_angle_vehicle != 0:
    boundary_box_body = []
    body_parts_dimensions= []
    for current_part in parts_vehicle:
        current_dim = []
        if(HM_CFD_version>=2024):
            current_dim.append(current_part.axisAlignedBoundingBox.minMax[0][0]) # xmin
            current_dim.append(current_part.axisAlignedBoundingBox.minMax[1][0]) # xmax
            current_dim.append(current_part.axisAlignedBoundingBox.minMax[0][1]) # ymin
            current_dim.append(current_part.axisAlignedBoundingBox.minMax[1][1]) # ymax    
            current_dim.append(current_part.axisAlignedBoundingBox.minMax[0][2]) # zmin
            current_dim.append(current_part.axisAlignedBoundingBox.minMax[1][2]) # zmax    

        else:
            current_dim.append(current_part.axisAlignedBoundingBox.GetMin()[0]) # xmin
            current_dim.append(current_part.axisAlignedBoundingBox.GetMax()[0]) # xmax
            current_dim.append(current_part.axisAlignedBoundingBox.GetMin()[1]) # ymin
            current_dim.append(current_part.axisAlignedBoundingBox.GetMax()[1]) # ymax
            current_dim.append(current_part.axisAlignedBoundingBox.GetMin()[2]) # zmin
            current_dim.append(current_part.axisAlignedBoundingBox.GetMax()[2]) # zmax
                
        body_parts_dimensions.append(current_dim)

    # get boundary box in the format of:
    # [xmin, xmax, ymin, ymax, zmin, zmax]
    boundary_box_body = []
    for indx in range(6):
        boundary_box_body.append(body_parts_dimensions[0][indx])
        for current_part in body_parts_dimensions:
            boundary_box_body[indx]  = min(boundary_box_body[indx],current_part[indx])*(indx%2==0) + max(boundary_box_body[indx],current_part[indx])*(indx%2!=0)
        if(indx==4):
            boundary_box_body[indx] = ground_height

    print("ℹ️: boundary box body is")
    print(boundary_box_body)

    body_length_x = boundary_box_body[1] - boundary_box_body[0]
    body_length_y = boundary_box_body[3] - boundary_box_body[2]
    body_length_z = boundary_box_body[5] - boundary_box_body[4]

    print("ℹ️: Body length in x, y, z are:")
    print(body_length_x)
    print(body_length_y)
    print(body_length_z)

    if debug_mode:
        print('✅: Body dimensions were re-calculated at yawed condition.')


    # --------------------------------
    # Derive dimensions for heat exchangers for RL7 Offset
    # --------------------------------
    # Get list of names for heat exchangers
    heat_exchanger_part_names = []
    for heat_exchanger in Heat_exchangers:
        heat_exchanger_part_names.append(heat_exchanger["name"])

    # Get part list of heat exchangers
    heat_exchanger_parts = []
    for name in heat_exchanger_part_names:
        current_part = []
        for part in parts_vehicle:
            if name in part.name:
                current_part.append(part)
        heat_exchanger_parts.append(current_part)   

    # Get dimension list for heat exchangers
    body_dimensions_heat_exchangers = []
    for heat_exchanger in heat_exchanger_parts:
        current_dim = []
        for part in heat_exchanger:
            temp_list = []
            temp_list.append(part.axisAlignedBoundingBox.minMax[0][0]) # xmin
            temp_list.append(part.axisAlignedBoundingBox.minMax[1][0]) # xmax
            temp_list.append(part.axisAlignedBoundingBox.minMax[0][1]) # ymin
            temp_list.append(part.axisAlignedBoundingBox.minMax[1][1]) # ymax    
            temp_list.append(part.axisAlignedBoundingBox.minMax[0][2]) # zmin
            temp_list.append(part.axisAlignedBoundingBox.minMax[1][2]) # zmax
            current_dim.append(temp_list)
        body_dimensions_heat_exchangers.append(current_dim)

    # Extracting min and max values for each heat exchangers
    boundary_box_heat_exchangers = []
    if not len(heat_exchanger_parts) == 0:
        for heat_exchanger in body_dimensions_heat_exchangers:
            current_min_max = heat_exchanger[0].copy() #Initialising with first list
            for part in heat_exchanger:
                for indx in range(len(part)):
                    if indx % 2 == 0: #Even numbers, min values
                        current_min_max[indx] = min(current_min_max[indx],part[indx])
                    else: #Odd numbers, max values
                        current_min_max[indx] = max(current_min_max[indx],part[indx])
            boundary_box_heat_exchangers.append(current_min_max)

    # --------------------------------------
    # define static floor dimensions
    # --------------------------------------
    if(bl_suction_by_belt_x_min & opt_belt_system):
        if bl_suction_by_belt_x_min_distance == 0:
            print("✅: BL suction position has been applied based on 5 belt x min.")
            bl_suction_pos_x = belt_dimensions_input[-1][0]
        else:
            print("✅: BL suction position has been applied based on 5 belt x min + Distance from xMin.")
            bl_suction_pos_x = belt_dimensions_input[-1][0] + bl_suction_by_belt_x_min_distance
            

    else:
        print("✅: BL suction position has been applied based on 'bl_suction_pos_x_input'.")
        bl_suction_pos_x = bl_suction_pos_x_input

        
    # -- static floor dimension --> to be updated for yaw-angled cases

    static_floor_dimensions = []
    static_floor_dimensions.append(bl_suction_pos_x) # xmin: suction position (either belt xmin or user input)
    if(belt_dimension_based_static & opt_belt_system):
        print("✅: Static floor has been defined based on belt dimensions.")
        static_floor_dimensions.append(belt_dimensions_input[-1][1]) # xmax = xmax of center belt
        static_floor_dimensions.append(scale_factor_static_floor_belt_width * boundary_box_belts[2]) # ymin
        static_floor_dimensions.append(scale_factor_static_floor_belt_width * boundary_box_belts[3]) # ymax

    else:
        print("✅: Static floor has been defined based on body dimensions.")
        static_floor_dimensions.append(boundary_box_body[1] + body_length_x*(scale_factor_static_floor_body_length-1)) # xmax
        static_floor_dimensions.append(boundary_box_body[2] - body_length_y*(scale_factor_static_floor_body_width-1)) # ymin
        static_floor_dimensions.append(boundary_box_body[3] + body_length_y*(scale_factor_static_floor_body_width-1)) # ymax



    
#####################################################################
# ### Create moving belts for Yaw = 0 (straight ahead) cases
#####################################################################
# - moving belts
if(opt_belt_system):
    if yaw_angle_vehicle == 0:
        belts = vwt.Belts()
        for belt in range(5):
            print(belt_dimensions_input[belt])
            if belt == 4:
                belts[belt].length = belt_size_center[0] #Length and Width must be specified before xMin/yMin
                belts[belt].width = belt_size_center[1] #Length and Width must be specified before xMin/yMin
            else:
                belts[belt].length = belt_size_wheel[0]
                belts[belt].width = belt_size_wheel[1]
            belts[belt].xMin = belt_dimensions_input[belt][0]
            belts[belt].yMin = belt_dimensions_input[belt][2]
                

        # Passive Parts for belts
        if include_wheel_belt_forces:
            passive_belts = belts[4]
            vwt.setPassivePart(passive_belts, False)
        else:
            for belt in belts:
                vwt.setPassivePart(belt, False)


#####################################################################
# ### Add moving velocity on belts
#####################################################################
belt_velocity = [inflow_velocity*Matrix44(angles=(0,0,yaw_angle_vehicle),degrees=True)[0][0],inflow_velocity*Matrix44(angles=(0,0,yaw_angle_vehicle),degrees=True)[0][1]]
print("ℹ️: Belt_velocity is:",belt_velocity)
print("ℹ️: Moment reference system roll:",Matrix44(angles=(0,0,yaw_angle_vehicle),degrees=True)[0][:3])
print("ℹ️: Moment reference system pitch:",Matrix44(angles=(0,0,yaw_angle_vehicle),degrees=True)[1][:3])
print("ℹ️: Moment reference system yaw:",Matrix44(angles=(0,0,yaw_angle_vehicle),degrees=True)[2][:3])


#####################################################################
# ### Set Sources and Boundary conditions 
#####################################################################

# set Heat exchangers

if not len(heat_exchanger_parts) == 0:
    for indx in range(len(Heat_exchangers)):
        hx = vwt.HeatExchanger()
        hx.name = Heat_exchangers[indx]["name"]
        
        if(bool(Heat_exchangers[indx]["outlet"]) & bool(Heat_exchangers[indx]["frame"])):
            # if(Heat_exchangers[indx]["baffle_frame"]): #This is unused.
            #     BafflePartsName.append(Heat_exchangers[indx]["frame"])
            print(f"ℹ️: Heat exchangers are : {Heat_exchangers[indx]}")
            rad_in     = model_vehicle.getChild(Heat_exchangers[indx]["inlet"],recursive=True)
            rad_out     = model_vehicle.getChild(Heat_exchangers[indx]["outlet"],recursive=True)
            rad_wall     = model_vehicle.getChild(Heat_exchangers[indx]["frame"],recursive=True)
            inlet   = hx.setInlets(rad_in)
            outlet  = hx.setOutlets(rad_out)
            wall    = hx.setWalls(rad_wall)
            
            
        else:
            rad_in = model_vehicle.getChild(Heat_exchangers[indx]["inlet"],recursive=True)
            inlet = hx.setInlets(rad_in)
            
        hx.inertialCoefficient  = Heat_exchangers[indx]["coeffs_inertia"]
        hx.viscousCoefficient   = Heat_exchangers[indx]["coeffs_viscous"]
        hx.permeabilityDirection


# set rotating wheels (boundary condition)
wheel_axles = []
wheel_centers = []
wheel_speed = []
wheelparts = []

if opt_moving_floor:
    if RimPartsNames:  # Use rims to define wheel axis/center
        # 1. Create wheels from rim parts
        rims, rimparts = get_set_rims(RimPartsNames)
        
        # 2. Classify rims by position (coordinate-based)
        rim_classified = classify_wheels_by_position(rims)
        
        # 3. Save axis and center from each rim (use first wheel in each corner group as reference)
        rim_properties = {
            corner: {"axis": rim_list[0].axis, "center": rim_list[0].center}
            for corner, rim_list in rim_classified.items()
        }
        
        if debug_mode:
            print("🔍 Rim positions detected:")
            for corner, rim_list in rim_classified.items():
                print(f"  {corner}: center={rim_list[0].center}, axis={rim_list[0].axis} ({len(rim_list)} parts)")

        #unset rim parts to avoid affecting wheel creation process
        unsetParts(rimparts)
        
        # 4. Create wheels from WheelPartsNames
        wheels, wheelparts = get_set_wheels(WheelPartsNames)
        
        # 5. Classify wheels by position (coordinate-based)
        wheel_classified = classify_wheels_by_position(wheels)
        
        if debug_mode:
            print("🔍 Wheel positions detected:")
            for corner, wheel_list in wheel_classified.items():
                print(f"  {corner}: center={wheel_list[0].center} ({len(wheel_list)} parts)")
        
        # 6. Override wheel axis and center with corresponding rim values for ALL wheels in each corner
        for corner in ["FR_LH", "FR_RH", "RR_LH", "RR_RH"]:
            for w in wheel_classified[corner]:
                w.axis = rim_properties[corner]["axis"]
                w.center = rim_properties[corner]["center"]
        # 7. Calculate wheel speed from rim center height (distance from ground)
        for corner in ["FR_LH", "FR_RH", "RR_LH", "RR_RH"]:
            rim_height_from_ground = rim_properties[corner]["center"][2] - ground_height
            rim_properties[corner]["speed"] = rim_height_from_ground
            for w in wheel_classified[corner]:
                w.speed = rim_properties[corner]["speed"]
        
        print(f"✅: Wheel axis and center defined by rim parts (position-based matching)")
    else:
        # Standard behavior without rim parts
        wheels, wheelparts = get_set_wheels(WheelPartsNames)
    
    print("ℹ️: Parts included in wheel are:", wheelparts)

    for wheel in wheels:
        wheel_axles.append(wheel.axis)
        wheel_centers.append(wheel.center)
        wheel_speed.append(wheel.speed)
        # auto calculate has to be disabled BEFORE updating inflow velocity, if inflow is different to vehicle speed
    print(f"ℹ️: Wheel axles are: {wheel_axles}")
    print(f"ℹ️: Wheel centers are: {wheel_centers}")
    print(f"ℹ️: Wheel speed are: {wheel_speed}")
# Setting up wheels even for static wheel for automatic reference length calculation.
else:
    if HM_CFD_version < 2027:
        if RimPartsNames:  # Use rims to define wheel axis/center
            # 1. Create wheels from rim parts
            rims, rimparts = get_set_rims(RimPartsNames)
            
            # 2. Classify rims by position (coordinate-based)
            rim_classified = classify_wheels_by_position(rims)
            
            # 3. Save axis and center from each rim (use first wheel in each corner group as reference)
            rim_properties = {
                corner: {"axis": rim_list[0].axis, "center": rim_list[0].center}
                for corner, rim_list in rim_classified.items()
            }
            
            if debug_mode:
                print("🔍 Rim positions detected:")
                for corner, rim_list in rim_classified.items():
                    print(f"  {corner}: center={rim_list[0].center}, axis={rim_list[0].axis} ({len(rim_list)} parts)")

            #unset rim parts to avoid affecting wheel creation process
            unsetParts(rimparts)
            
            # 4. Create wheels from WheelPartsNames
            wheels, wheelparts = get_set_wheels(WheelPartsNames)
            
            # 5. Classify wheels by position (coordinate-based)
            wheel_classified = classify_wheels_by_position(wheels)
            
            if debug_mode:
                print("🔍 Wheel positions detected:")
                for corner, wheel_list in wheel_classified.items():
                    print(f"  {corner}: center={wheel_list[0].center} ({len(wheel_list)} parts)")
            
            # 6. Override wheel axis and center with corresponding rim values for ALL wheels in each corner
            for corner in ["FR_LH", "FR_RH", "RR_LH", "RR_RH"]:
                for w in wheel_classified[corner]:
                    w.axis = rim_properties[corner]["axis"]
                    w.center = rim_properties[corner]["center"]
            
            print(f"✅: Wheel axis and center defined by rim parts (position-based matching)")
        else:
            # Standard behavior without rim parts
            wheels, wheelparts = get_set_wheels(WheelPartsNames)
        
        print("wheel parts:", wheelparts)

        for wheel in wheels:
            wheel_axles.append(wheel.axis)
            wheel_centers.append(wheel.center)
            wheel_speed.append(wheel.speed)
            # auto calculate has to be disabled BEFORE updating inflow velocity, if inflow is different to vehicle speed
        print(f"ℹ️: Wheel axles are: {wheel_axles}")
        print(f"ℹ️: Wheel centers are: {wheel_centers}")
        print(f"ℹ️: Wheel speed are: {wheel_speed}") 
    

# set OSM for rotating wheels - Not available in 2025.1 and 2026.0
# Specifying rule for regex
def add_pattern(text):
    return f"^{text}*"

# set baffle parts
baffle_parts = []
for name in BafflePartsName:
    baffle_parts += [current_part for current_part in parts_vehicle if name in current_part.name]
    
    if parts_windtunnel_parts:
        baffle_parts += [current_part for current_part in parts_windtunnel_parts if name in current_part.name]
print("ℹ️: Baffle parts are:", baffle_parts)

baffles=[]
for current_part in baffle_parts:
    baffles.append(vwt.setBaffle(current_part, True))

#####################################################################
# ### set mesh refinement zones
#####################################################################

# BOX REFINEMENT
# -- Defining the size of box refinement around the vehicle
ref_box_dim = [] #List of dimensions for box refinement



for current_ref in ref_box_factors: #Generating list of boundary box for box refinement.
    new_dim = []
    for indx, factor in enumerate(current_ref):
        if indx in [0,1]:
            new_dim.append(calculate_box_refinement_dimension(indx, factor, body_length_x, boundary_box_body[indx]))
        elif indx in [2,3]:
            new_dim.append(calculate_box_refinement_dimension(indx, factor, body_length_y, boundary_box_body[indx]))
        elif indx == 4:
            new_dim.append(ground_height)
        elif indx == 5:
            new_dim.append(calculate_box_refinement_dimension(indx, factor, body_length_z, boundary_box_body[indx]))
    ref_box_dim.append(new_dim)

print(f'ℹ️: Size of box refinement boxes are: {ref_box_dim}')



indx=0
for current_ref_box in ref_box_dim:
    indx = indx + 1
    bx = vwt.BoxRefinementZone()
    bx.name = "boxRL_" + str(indx)
    bx.refinementLevel = indx
    bx.length = current_ref_box[1] - current_ref_box[0]
    bx.width = current_ref_box[3] - current_ref_box[2]
    bx.height = current_ref_box[5] - current_ref_box[4]
    bx.xMin = current_ref_box[0]
    bx.yMin = current_ref_box[2] 
    bx.zMin = current_ref_box[4] + offset_from_ground



# Box refinement for porous media
# Not applied for GHN application
if not solution_type == "GHN":
    for indx, current_ref_box in enumerate(boundary_box_heat_exchangers):
        bx = vwt.BoxRefinementZone()
        bx.name = "box_porous_" + heat_exchanger_part_names[indx] + "_RL7"
        bx.refinementLevel = 7
        bx.length = current_ref_box[1] - current_ref_box[0]
        bx.width = current_ref_box[3] - current_ref_box[2]
        bx.height = current_ref_box[5] - current_ref_box[4]
        bx.xMin = current_ref_box[0]
        bx.yMin = current_ref_box[2]
        bx.zMin = current_ref_box[4]


# -- set refinement on the ground
# -- reference for the static floor
# Not applied for GHN application
if not solution_type == "GHN":
    ref_box_dim_ground = []
    # RL5 -- 30 layers
    thickness = coarsest_voxel_size * 0.5**5 * num_layers_rl5_ground
    ref_box_dim_ground.append([])
    for tmp in static_floor_dimensions:
        ref_box_dim_ground[-1].append(tmp)
    ref_box_dim_ground[-1].append(ground_height)
    ref_box_dim_ground[-1].append(ground_height + thickness)

    # RL6 -- 12 layers
    thickness = coarsest_voxel_size * 0.5**6 * num_layers_rl6_ground
    ref_box_dim_ground.append([])
    for tmp in static_floor_dimensions:
        ref_box_dim_ground[-1].append(tmp)
    ref_box_dim_ground[-1].append(ground_height)
    ref_box_dim_ground[-1].append(ground_height + thickness)



    indx = 4
    for current_ref_box in ref_box_dim_ground:
        indx = indx + 1
        bx = vwt.BoxRefinementZone()
        bx.name = "box_ground_RL" + str(indx)
        bx.refinementLevel = indx
        bx.length = (current_ref_box[1] - current_ref_box[0]) 
        bx.width = (current_ref_box[3] - current_ref_box[2]) 
        bx.height = (current_ref_box[5] - current_ref_box[4])
        bx.xMin = current_ref_box[0] + offset_from_BL_suction
        bx.yMin = current_ref_box[2] 
        bx.zMin = current_ref_box[4] + offset_from_ground




# RL4 to RL2 on the ground based on the factors
# This is enabled only when static ground is on
# Not applied for GHN application
if not solution_type == "GHN" and opt_moving_floor == False and opt_belt_system == False: #If there is no rotating wheels -> Static no-slip ground.
    ref_box_dim_ground_RL1to4=[]
    for currentRL in range(len(ref_box_static_floor_inflation_factors)):
        ref_box_dim_ground_RL1to4.append([])
        length_bb_ref_box_rl5 = ref_box_dim_ground[0][1] - ref_box_dim_ground[0][0]
        width_bb_ref_box_rl5 = ref_box_dim_ground[0][3] - ref_box_dim_ground[0][2]
        height_bb_ref_box_rl5 = coarsest_voxel_size * 0.5**5 * num_layers_rl5_ground
        for current_dim in range(len(ref_box_dim_ground[0])):
            operator_min_max = -1*(current_dim%2==0) + 1*(current_dim%2!=0) # even:negative, odd:positive
            ref_box_dim_ground_RL1to4[-1].append(ref_box_dim_ground[0][current_dim] + operator_min_max * length_bb_ref_box_rl5 * 0.5 * (ref_box_static_floor_inflation_factors[currentRL]-1))


    indx = 0
    for current_ref_box in ref_box_dim_ground_RL1to4:
        indx = indx + 1
        bx = vwt.BoxRefinementZone()
        bx.name = "box_ground_add_RL" + str(indx)
        bx.refinementLevel = indx
        bx.length = (current_ref_box[1] - current_ref_box[0]) 
        bx.width = (current_ref_box[3] - current_ref_box[2]) 
        bx.height = (current_ref_box[5] - current_ref_box[4]) 
        bx.xMin = current_ref_box[0] 
        bx.yMin = current_ref_box[2] 
        bx.zMin = current_ref_box[4] + offset_from_ground 


# OFFSET REFINEMENT

# set offset refinement
thickness_rl7 = coarsest_voxel_size * 0.5**7 * num_layers_rl7
thickness_rl6 = coarsest_voxel_size * 0.5**6 * num_layers_rl6
if (yaw_angle_vehicle == 0 or not opt_belt_system) and not parts_windtunnel_parts:
    offset_all_rl7 = {'name': "Body_Offset_ALL_RL7", 'level': 7, 'distance': thickness_rl7}
    offset_all_rl6 = {'name': "Body_Offset_ALL_RL6", 'level': 6, 'distance': thickness_rl6}       
else:
    offset_all_rl7 = {'name': "Part_Offset_ALL_RL7",'parts':parts_vehicle, 'level': 7, 'distance': thickness_rl7}
    offset_all_rl6 = {'name': "Part_Offset_ALL_RL6",'parts':parts_vehicle, 'level': 6, 'distance': thickness_rl6} 

if solution_type == "External_aerodynamics":
    offsets = [offset_all_rl7, offset_all_rl6]
else: #GHN does not need uniform RL7
    offsets = [offset_all_rl6]
    
for offset in offsets:
    if 'parts' in offset.keys():
        ofz = vwt.OffsetRefinementZone(offset['parts']) # part offset
    else:
        ofz = vwt.OffsetRefinementZone()
    ofz.refinementLevel = offset['level']
    ofz.name = offset['name']
    ofz.offsetDistance = offset['distance']
    
    
    
# set additional offset refinement on parts
part_offset_instance = []
for part_offset in additional_part_offsets:
    parts_include = part_offset['parts_include']
    parts_exclude = part_offset['parts_exclude']
    parts = get_parts_with_regex(parts_original,parts_include,parts_exclude)
    
    current_distance_offset = coarsest_voxel_size * 0.5**part_offset["refinement_level"]  * part_offset["num_layers"] 

    ofz = vwt.OffsetRefinementZone(parts)
    ofz.refinementLevel = part_offset['refinement_level']
    ofz.name = part_offset["name"]
    ofz.offsetDistance = current_distance_offset

    part_offset_instance.append(ofz)

    
    
# set refinement on wheel belts, NOT USED
if(add_wheel_belt_refinement):
    if(opt_belt_system):
        if yaw_angle_vehicle == 0:
            ref_box_dim_wheel_belts = []
            thickness_rl7 = coarsest_voxel_size * 0.5**7 * num_layers_rl7

            for current_belt_dim in belt_dimensions_input:
                ref_box_dim_wheel_belts.append([])
                for tmp in current_belt_dim:
                    ref_box_dim_wheel_belts[-1].append(tmp)    
                ref_box_dim_wheel_belts[-1].append(ground_height) 
                ref_box_dim_wheel_belts[-1].append(ground_height + thickness_rl7)
                
            offset_ref_box = 0.02
            indx = 7
            belt_num = 0
            for current_ref_box in ref_box_dim_wheel_belts:
                if(belt_num < 4):
                    belt_num = belt_num + 1
                    bx = vwt.BoxRefinementZone()
                    bx.name = "box_wheel_belts_RL" + str(indx) + "_belt_" +  str(belt_num)
                    bx.refinementLevel = indx
                    bx.length = (current_ref_box[1] - current_ref_box[0]) + offset_ref_box_ground
                    bx.width = (current_ref_box[3] - current_ref_box[2]) + offset_ref_box_ground
                    bx.height = (current_ref_box[5] - current_ref_box[4]) + offset_ref_box_ground*0.5
                    bx.xMin = current_ref_box[0] - offset_ref_box_ground*0.5
                    bx.yMin = current_ref_box[2] - offset_ref_box_ground*0.5
                    bx.zMin = current_ref_box[4] - offset_ref_box_ground*0.5
        
# CUSTOM REFINEMENT
custom_refinement_instances = []
count = 0
for part in parts_custom_ref:
    name = part.name
    for custom in custom_refinements:
        if name == custom['name']:
            crz = vwt.CustomRefinementZone(part)
            crz.refinementLevel = custom['refinement_level']
            custom_refinement_instances.append(crz)
            count += 1
if count == 0:
    print('⚠️: No parts matched with custom refinment part IDs.')
        


#####################################################################
# ### set turbulence generators
#####################################################################
# TODO: add if condition only for the case having static floor
# set ground turbulence generator 
# tg_ground = vwt.Turbulence(wheelparts) # turb gen creation requires parts, but not necessary
if solution_type == "External_aerodynamics": # Only apply TG for external aero.
    tg_ground = vwt.Turbulence(parts_vehicle) # turb gen creation requires parts, but not necessary

    # dimensions
    tg_ground.height = ref_box_dim_ground[1][5]-ref_box_dim_ground[1][4] # height of RL6
    tg_ground.width = static_floor_dimensions[3] - static_floor_dimensions[2]  # width of static floor
    tg_ground.yMin = static_floor_dimensions[2]
    tg_ground.zMin = ground_height

    #tg_ground.xMin = static_floor_dimensions[0] - 0.01 # it doesn't work as expected
    tg_ground.planePosition = static_floor_dimensions[0] - 0.01

    tg_ground.refineMesh = False

    # tg parameters
    tg_ground.name = "tg_ground"
    tg_ground.turbulenceIntensity = tg_ground_intensity
    tg_ground.numEddies = tg_ground_num_eddies



    if(activate_body_tg):

        # dimensions
        tg_width =  body_length_y * (tg_body_tg_size_factor[1] - tg_body_tg_size_factor[0])
        tg_height =  body_length_z * (tg_body_tg_size_factor[3] - tg_body_tg_size_factor[2])
        tg_y_min = 0.5*(boundary_box_body[2]+boundary_box_body[3]) - tg_width * 0.5
        tg_z_min = boundary_box_body[4] + body_length_z * tg_body_tg_size_factor[2]
        tg_x_pos = boundary_box_body[0] - body_length_x*tg_body_x_pos_factor


        # tg setting
        tg_body = vwt.Turbulence(parts_vehicle) # turb gen creation requires parts, but not necessary    
        tg_body.height = tg_height
        tg_body.width = tg_width
        
        # tg_body.xMin = tg_x_pos # it doesn't work as expected
        tg_body.planePosition = tg_x_pos 
        tg_body.yMin = tg_y_min
        tg_body.zMin = tg_z_min
        tg_body.refineMesh = False

        # tg parameters
        tg_body.name = "tg_body"
        tg_body.turbulenceIntensity = tg_body_intensity
        tg_body.numEddies = tg_body_num_eddies
        
        
        
        # add refinement box manually
        offset_ref_box_tg_x = body_length_x*0.08
        bx = vwt.BoxRefinementZone()
        bx.name = "boxRL_tg_body_" + str(indx)
        bx.refinementLevel = 6
        bx.length =  boundary_box_body[0] - tg_x_pos + offset_ref_box + offset_ref_box_tg_x
        bx.width = tg_width + offset_ref_box
        bx.height = tg_height  + offset_ref_box
        bx.xMin = tg_x_pos - offset_ref_box*0.5
        bx.yMin = tg_y_min - offset_ref_box*0.5
        bx.zMin = tg_z_min - offset_ref_box*0.5

#####################################################################
# ### set passive parts for wind tunnel parts
#####################################################################
if parts_windtunnel_parts:
    for part in parts_windtunnel_parts:
        vwt.setPassivePart(part, False)
        print(f"✅: Part {part.name} is set as passive part.")

    if enable_ground_patch:
        tunnel.groundPatchLength = 0.0001
        tunnel.groundPatchWidth = 0.0001



#####################################################################
# ### Run setup
#####################################################################
# Calculation
if simulation_time_with_flow_passes:
    runtime_applied = body_length_x * simulation_time_num_flow_passes / inflow_velocity
    start_averaging_time_applied = body_length_x * start_averaging_time_num_flow_passes / inflow_velocity
    print("✅: Simulation run time is applied by FLow Passes.")
else:
    runtime_applied = simulation_time
    start_averaging_time_applied = start_averaging_time
    print("✅: Simulation run time is applied by Second.")

if solution_type == "External_aerodynamics":
    mach_scaling = 2
else:
    mach_scaling = 1.5

print(f"ℹ️: Run time is :{runtime_applied} second.")
print(f"ℹ️: Averaging start time is :{start_averaging_time_applied} second. ")

Cs = (gas_constant*heat_capacity_ratio*(temperature+273)/molecular_weight)**0.5
print(f"ℹ️: Sound of speed is :{Cs} m/s")
print(f"ℹ️: Mach factor is: {mach_scaling}")

# Definition
# Run Parameters
run_param = vwt.RunParameters()
run_param.simulationName = simulationName[0]
if simulationRunPath:
    simulationRunPath = os.path.join(DATA_FOLDER, simulationRunPath[0]).replace('\\', '/')
else:
    simulationRunPath = DATA_FOLDER
run_param.simulationRunPath = simulationRunPath
run_param.runTime = runtime_applied # simulation time
# Running twice due vwt li
run_param.runTime = runtime_applied # simulation time
run_param.machFactor = mach_scaling
run_param.meshPreview = False
run_param.rotatingWheels = True if opt_moving_floor or opt_belt_system else False
run_param.movingGround = True if opt_moving_floor or opt_belt_system else False
print(f"✅: Moving ground and wheels are set {run_param.rotatingWheels}.")

# Mesh Controls > set far field element size
vwt.setMeshSize(coarsest_voxel_size)

# Mesh Controls
mc = vwt.MeshControls()
mc.trianglePlinth = trianglePlinth
mc.triangleSplitting = triangleSplitting
print(f"ℹ️: Triangle splitting is {mc.triangleSplitting}.")
mc.maxRelativeEdgeLength = maxRelativeEdgeLength
print(f"ℹ️: Max relative length for triangle splitting is {mc.maxRelativeEdgeLength}.")
mc.transitionLayers = transitionLayers
print(f"ℹ️: Num of mesh transition layer is {mc.transitionLayers}.")


# Output Controls
oc = vwt.OutputControls()
oc.timeAverageStartTime = start_averaging_time_applied
oc.windowAverageSize = avg_window_size_second
oc.probeOutputPrecision = 8
run_param.runTime = runtime_applied # simulation time
oc.resultsStartIteration = run_param.numTimeSteps * (output_start_time/runtime_applied)
oc.resultsOutputInterval = run_param.numTimeSteps * (output_interval_time/runtime_applied)
oc.sectionalUserDefinedCoefficientX = True
oc.sectionalCoefficientX = 100
oc.timeVaryingGoemOutput = False
oc.savedStatesValue
oc.savedOutputStates
oc.savedStatesValue = 1
apply_output_formatting_settings(oc,output_format)


# Set variables to export for both fluid and surface
for option in surface_output_option:
    oc.setSurfaceVariable(option[0],option[1])

for option in full_output_option:
    oc.setFieldVariable(option[0],option[1])

#####################################################################
# ### set default outputs
#####################################################################

### Set partial volume if option is true ###
if export_time_avg_partial_volume_outputs:

    ### Set partial volume ###
    avg_partial_volume = vwt.VolumeOutput(parts_vehicle)
    # avg_partial_volume.center = (ref_box_dim[3][1]-ref_box_dim[3][0])/2, (ref_box_dim[3][3]-ref_box_dim[3][2])/2, (ref_box_dim[3][5]-ref_box_dim[3][4])/2
    avg_partial_volume.width = ref_box_dim[3][3]-ref_box_dim[3][2]
    avg_partial_volume.length = ref_box_dim[3][1]-ref_box_dim[3][0]
    avg_partial_volume.height = ref_box_dim[3][5]-ref_box_dim[3][4]
    avg_partial_volume.xMin = ref_box_dim[3][0]
    avg_partial_volume.yMin = ref_box_dim[3][2]
    avg_partial_volume.zMin = ref_box_dim[3][4]

    # Set size of partial volume
    avg_partial_volume.name = "Partial_Volume_RL4_BOX"
    avg_partial_volume.samplingType = "Output Interval"
    avg_partial_volume.startType = "Time"
    avg_partial_volume.startTime = start_averaging_time_applied
    avg_partial_volume.outputInterval = run_param.numTimeSteps #Aiming to only export once.

    #Set variables to export
    #print(avg_partial_volume.properties())
    for option in volume_output_option:
        avg_partial_volume.setProperty(option[0],option[1])


### Set partial surface ###
partial_surface_output_instances = []
for partial in partial_surface_output:
    parts_include = partial['parts_include']
    parts_exclude = partial['parts_exclude']
    parts = get_parts_with_regex(parts_vehicle,parts_include,parts_exclude)

    output = vwt.SurfaceOutput(parts)
    output.name = partial['name']
    output.samplingType = "Output Interval"
    output.startType = "Time"
    output.startTime = partial['Start_time[s]']
    output.outputInterval = partial['Output_interval']
    #Output format
    apply_output_formatting_settings(output,partial['Output_format'])
    #Merge option
    if partial['Merge_output']:
        output.mergeOutputFiles = True
        output.mergeAndDeleteFiles = True
    else:
        output.mergeOutputFiles = False
        output.mergeAndDeleteFiles = False
    # Output variables
    for key,value in partial['Output_variables'].items():
        output.setProperty(key,value)

    partial_surface_output_instances.append(output)

### Set partial volume ###
partial_volume_output_instances = []
for partial in partial_volume_output:
    # Define bounding box
    xMin = partial['box_size'][0]
    xMax = partial['box_size'][1]
    yMin = partial['box_size'][2]
    yMax = partial['box_size'][3]
    zMin = partial['box_size'][4]
    zMax = partial['box_size'][5]

    # Overwrite it if set by factor option is true.
    if partial['box_size_with_parts_and_factors']:
        parts_include = partial['parts_include']
        parts_exclude = partial['parts_exclude']
        parts = get_parts_with_regex(parts_vehicle,parts_include,parts_exclude)
        extended_box_size = get_extended_boundarybox_of_parts_with_factor(parts,partial['box_size'])
        # Over write bounding box
        xMin = extended_box_size[0]
        xMax = extended_box_size[1]
        yMin = extended_box_size[2]
        yMax = extended_box_size[3]
        zMin = extended_box_size[4]
        zMax = extended_box_size[5]
    else:
        parts = parts_vehicle


    # Calculate size of box for vwt input
    length = xMax - xMin
    width = yMax - yMin
    height = zMax - zMin



    output = vwt.VolumeOutput(parts)
    output.length = length
    output.width = width
    output.height = height
    output.xMin = xMin
    output.yMin = yMin
    output.zMin = zMin

    output.name = partial['name'][0]
    output.samplingType = "Output_Interval"
    output.startType = "Time"
    output.startTime = partial['Start time[s]']
    output.outputInterval = partial['Output interval']
    #Output format
    apply_output_formatting_settings(output,partial['Output_format'][0])
    #Merge option
    if partial['Merge output']:
        output.mergeOutputFiles = True
        output.mergeAndDeleteFiles = True
    else:
        output.mergeOutputFiles = False
        output.mergeAndDeleteFiles = False
    # Output variables
    for key,value in partial['output_variables'].items():
        output.setProperty(key,value)

    # Coarsening options
    # Not supported in vwt 2026.0 properly.

    partial_volume_output_instances.append(output)


### Set Monitor surface ###
monitor_surface_output_instances = []
for monitor in Monitor_Surface_Outputs:
    parts_include = monitor['parts_include']
    parts_exclude = monitor['parts_exclude']
    parts = get_parts_with_regex(parts_vehicle,parts_include,parts_exclude)
    if parts:
        output = vwt.SurfaceMonitor(parts)
        output.name = monitor['name']
        # Visual
        output.visualSamplingType = "Output Interval"
        output.visualStartType = "Time"
        output.visualStartTime = monitor['Visual Start time[s]']
        output.visualOutputInterval = monitor['Visual Output interval']

        apply_output_formatting_settings(output,monitor['Visual Output format'])
        # Merge option
        if monitor['Visual Merge Output']:
            output.mergeOutputFiles = True
            output.mergeAndDeleteFiles = True
        else:
            output.mergeOutputFiles = False
            output.mergeAndDeleteFiles = False

        for key,value in monitor['Visual_Outputs'].items():
            k = "_".join(key.split("_")[1:])
            output.setVisualProperty(k,value)

        # Summary
        output.summaruSamplingType = "Output Interval"
        output.summaruStartType = "Time"
        output.summaryStartTime = monitor['Summary Start time[s]']
        output.summaryOutputInterval = monitor['Summary Output interval']

        for key,value in monitor['Summary_Outputs'].items():
            k = "_".join(key.split("_")[1:])
            output.setSummaryProperty(k,value)
        
        monitor_surface_output_instances.append(output)


#####################################################################
#
# ### CHECKS
#
#####################################################################

print('####################################')
print('### CHECKS')
print('####################################')

print('------------------------------------')
print('### GROUND/WHEEL BOUNDARY CONDITION')

check_wall_bc_setup()
print('------------------------------------')


print('✅: Completed')


