# ----------------------------------------------------------------------------------------------
#   Test script to correct xml file comply to guideline setting
#   This is only for internal usage, so please use it on your own responsibility
# ----------------------------------------------------------------------------------------------
# Developed by: Yuta Kanemaru
# 20250722 ver.0.1
# Template exel version: v0.7
# Updates: Added variable option support for output. Added option for enable_ground_patch.

import os
import re
from typing import List
import sys
import numpy as np
import pandas as pd
import ast
from pprint import pprint
import math


import xml.etree.ElementTree as ET
import xml.dom.minidom


# -----------------------------------------------------------------
# -----------    LOAD SETUP EXCEL SHEET    -----------------------------
# -----------------------------------------------------------------
# ----------------------
# Setting excel file
# ---------------------
if len(sys.argv) != 3:
    print('Usage: please specify the path to setup excel file and xml file to correct.')
else:
    setting_excel_file = sys.argv[1]
    xml_file = sys.argv[2]
    print(f'Specified setting excel file: {setting_excel_file}')
    print(f'Specified xml file: {xml_file}')


#####################################################################
# ### Expert parameters
#####################################################################

# Full data bouding box size
bounding_box_fullData_boxRL = 2


heat_capacity_ratio = 1.4 #Cp/Cv
gas_constant = 8.3144 #J/mol*k
molecular_weight = 0.0289647
temperature = 20 #degrees
mach_scaling = 2

#####################################################################
# ### END OF USER UNPUT #####
#####################################################################

#####################################################################
# ### Loading settings from excel
#####################################################################
# Loading function
def excel_input_to_python_value(value):
    """
    Convert Excel cell input into a proper Python type.

    Examples:
    - ["A", "B"] → ["A", "B"]
    - A,B → ["A", "B"]
    - A → "A"
    - 123 → 123
    - TRUE/FALSE → True/False
    - NaN, None, "" → None
    """

    # 1️⃣ NaN or None → None
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []

    # 2️⃣ Boolean string
    if isinstance(value, str) and value.lower() == 'true':
        return True
    elif isinstance(value, str) and value.lower() == 'false':
        return False

    # 3️⃣ String processing
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None

        # Pythonリスト形式（例: ["A","B"]）
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = ast.literal_eval(value)
                return parsed if isinstance(parsed, list) else parsed
            except Exception:
                # カンマで区切ってリスト化
                return [v.strip() for v in value.strip("[]").split(",") if v.strip()]

        # カンマ区切り（例: A,B）
        elif "," in value:
            return [v.strip() for v in value.split(",") if v.strip()]

        # 単一文字列
        else:
            return [value]

    # 4️⃣ 数値などはそのまま返す
    return value


# --------------------------
# General settings 
# --------------------------
df = pd.read_excel(setting_excel_file, sheet_name='General')
df = df[df['Parameters'].notna()]
# Getting dictionary from excel
general_settings = {}
for index, row in df.iterrows():
    key = row['Parameters']
    value = row['Value']
    value = excel_input_to_python_value(value)
    
    general_settings[key] = value

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
solution_type = general_settings.get('solution_type')[0]
output_start_time = general_settings.get('output_start_time')
output_interval_time = general_settings.get('output_interval_time')
output_format = general_settings.get('output_format')[0]
export_bounds_active = general_settings.get('export_bounds_active')
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
WheelTirePartsNames = []
WheelTirePartsNames.append(Wheel_baffle_settings.get('WheelTireParts_FR_LHS')[0])
WheelTirePartsNames.append(Wheel_baffle_settings.get('WheelTireParts_FR_RHS')[0])
WheelTirePartsNames.append(Wheel_baffle_settings.get('WheelTireParts_RR_LHS')[0])
WheelTirePartsNames.append(Wheel_baffle_settings.get('WheelTireParts_RR_RHS')[0])
TireSurfaceRoughness = Wheel_baffle_settings.get('TireSurfaceRoughness')
BafflePartsName = Wheel_baffle_settings.get('BafflePartsName')

WheelOSMPartsNames = []
if general_settings.get('osm_wheels'):
    WheelOSMPartsNames.append(Wheel_baffle_settings.get('OversetMeshPartsName_FR_LH')[0])
    WheelOSMPartsNames.append(Wheel_baffle_settings.get('OversetMeshPartsName_FR_RH')[0])
    WheelOSMPartsNames.append(Wheel_baffle_settings.get('OversetMeshPartsName_RR_LH')[0])
    WheelOSMPartsNames.append(Wheel_baffle_settings.get('OversetMeshPartsName_RR_RH')[0])


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
        'Baffle_export_option': row['Baffle_export_option'],
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





#####################################################################
# ### Defining functions
#####################################################################

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

def get_parts_with_regex_no_vwt(parts,include_patterns: List[str] = None,exclude_patterns: List[str] = None):
    '''
    Receive parts and naming patterns, returns vwt parts that matches in patterns.
    '''
    matched_parts = []
    for part in parts:
        if check_string_against_multiple_patterns(part,include_patterns,exclude_patterns):
            matched_parts.append(part)
    
    return matched_parts

def ufx_deck_parser(elem):
    """
    任意のElementTree要素をネストされた辞書に変換（再帰）
    - 同じタグが複数あるとリストで返す
    - テキストがあればそれを優先
    - 空タグは無視
    """
    tag = elem.tag.split('}', 1)[-1]  # 名前空間除去
    children = list(elem)

    # 子要素がない場合：テキストを返す
    if not children:
        return {tag: elem.text.strip() if elem.text else ''}

    # 子要素がある場合：再帰的に辞書を構築
    result = {}
    for child in children:
        child_dict = ufx_deck_parser(child)
        child_tag = list(child_dict.keys())[0]
        child_val = child_dict[child_tag]

        if child_tag in result:
            # 既に同じタグが存在する場合 → リスト化
            if not isinstance(result[child_tag], list):
                result[child_tag] = [result[child_tag]]
            result[child_tag].append(child_val)
        else:
            result[child_tag] = child_val

    return {tag: result}

def dict_to_element(tag, value):
    """
    Converts a nested dictionary or list into an ElementTree Element.
    Lists are not wrapped in an extra parent tag.
    """
    if isinstance(value, dict):
        elem = ET.Element(tag)
        for k, v in value.items():
            children = dict_to_element(k, v)
            if isinstance(children, list):
                elem.extend(children)
            else:
                elem.append(children)
        return elem

    elif isinstance(value, list):
        # Do not wrap list with tag; return list of Elements
        return [dict_to_element(tag, item) for item in value]

    else:
        elem = ET.Element(tag)
        elem.text = str(value)
        return elem

def save_dict_as_pretty_xml(parsed_xml_file, input_xml_path):
    # Extract base dict and convert to XML Element
    ufx_dict = parsed_xml_file.get("uFX_solver_deck", {})
    ufx_elem_result = dict_to_element("uFX_solver_deck", ufx_dict)

    # Ensure root is a single Element
    if isinstance(ufx_elem_result, list):
        raise ValueError("Root element cannot be a list. Invalid XML structure.")

    # Convert to string
    rough_string = ET.tostring(ufx_elem_result, encoding='utf-8')
    reparsed = xml.dom.minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")

    # Create output path
    input_dir = os.path.dirname(input_xml_path)
    input_base = os.path.splitext(os.path.basename(input_xml_path))[0]
    output_filename = os.path.join(input_dir, f"{input_base}_corrected.xml")

    # Save with indentation
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    return output_filename

def configure_osm_wheels(parsed_xml_file, WheelOSMPartsNames, WheelTirePartsNames, osm_wheels):
    if not osm_wheels:
        print("❌ OSM for wheels is False, skipping OSM wheel setup.")
        return

    ufx = parsed_xml_file.get("uFX_solver_deck", {})

    # --- Validation ---
    if not isinstance(WheelOSMPartsNames, list) or len(WheelOSMPartsNames) != 4:
        raise ValueError("WheelOSMPartsNames must contain exactly 4 items.")
    if not isinstance(WheelTirePartsNames, list) or len(WheelTirePartsNames) != 4:
        raise ValueError("WheelTirePartsNames must contain exactly 4 items.")

    # --- Ensure meshing > overset > rotating structure exists ---
    meshing = ufx.setdefault("meshing", {})
    if not isinstance(meshing.get("overset"), dict):
        meshing["overset"] = {}
    overset = meshing["overset"]
    if not isinstance(overset.get("rotating"), dict):
        overset["rotating"] = {}
    rotating = overset["rotating"]
    rotating_instances = rotating.setdefault("rotating_instance", [])

    if isinstance(rotating_instances, dict):
        rotating["rotating_instance"] = [rotating_instances]
        rotating_instances = rotating["rotating_instance"]
    elif isinstance(rotating_instances, str):
        rotating["rotating_instance"] = [rotating_instances]
        rotating_instances = rotating["rotating_instance"]

    # --- Get wall_instance list ---
    wall_instances = (
        ufx.get("boundary_conditions", {})
           .get("wall", {})
           .get("wall_instance", [])
    )
    if isinstance(wall_instances, dict):
        wall_instances = [wall_instances]
    elif not isinstance(wall_instances, list):
        wall_instances = []

    # --- Loop and copy matched instances ---
    for tire_part, osm_name in zip(WheelTirePartsNames, WheelOSMPartsNames):
        matched = False
        for instance in wall_instances:
            part_name = instance.get("parts", {}).get("name", "")
            if tire_part in part_name:
                # fluid_bc_settings 取得
                fbc = instance.get("fluid_bc_settings", {})
                new_instance = {
                    'name': osm_name,
                    'rpm': fbc.get('rpm'),
                    'center': fbc.get('center'),
                    'axis': fbc.get('axis'),
                    'parts': {'name': osm_name}
                }
                rotating_instances.append(new_instance)
                matched = True
                break

        if not matched:
            available_names = [inst.get("parts", {}).get("name") for inst in wall_instances]
            raise ValueError(
                f"❌ No wall_instance with parts:name containing '{tire_part}' found.\nAvailable: {available_names}"
            )

    print("✅ Overset mesh settings applied in meshing section.")

def modify_geometry_section(parsed_xml_file, triangleSplitting, maxRelativeEdgeLength):
    ufx = parsed_xml_file.get("uFX_solver_deck", {})

    # triangle_splittingの設定（必要ならsurface_mesh_optimizationを作成）
    if triangleSplitting:
        geometry = ufx['geometry']
        smo = geometry.setdefault('surface_mesh_optimization', {})
        smo['triangle_splitting'] = {
            'active': 'true',
            'max_absolute_edge_length': '3',
            'max_relative_edge_length': str(maxRelativeEdgeLength)
        }

    # triangle_plinthは常にfalseに（推奨設定）
    geometry = ufx['geometry']
    geometry['triangle_plinth'] = 'false'

    print("✅ Geometry section corrected.")

def modify_output_section(parsed_xml_file, bounding_box_fullData_boxRL, coarsen_output_options,reference_length_auto,WheelTirePartsNames,yaw_angle_vehicle,export_bounds_active):
    ufx = parsed_xml_file.get("uFX_solver_deck", {})

    # --- output/generalの参照 ---
    output = ufx.get('output', {})
    general = output.get('general', {})

    # --- Output coarsening の適用 ---
    if coarsen_output_options.get('output_coarsening') is True:
        general['output_coarsening'] = {
            'active': 'true',
            'coarsen_by_num_refinement_levels': str(coarsen_output_options.get('coarsen_by_num_refinement_levels')),
            'coarsest_target_refinement_level': str(coarsen_output_options.get('coarsest_target_refinement_level')),
            'export_uncoarsened_voxels': 'false'
        }
        print("✅ Output coarsening applied.")

    # --- bounding_box_fullData_boxRL に対応する bounding_box を抽出 ---
    bounding_box_fulldata = None
    box_instances = (
        ufx.get('meshing', {})
           .get('refinement', {})
           .get('box', {})
           .get('box_instance', [])
    )

    if isinstance(box_instances, dict):
        box_instances = [box_instances]

    for instance in box_instances:
        if instance.get('refinement_level') == str(bounding_box_fullData_boxRL):
            bounding_box_fulldata = instance.get('bounding_box')
            break

    if bounding_box_fulldata:
        general['bounding_box'] = bounding_box_fulldata
        print(f"✅ Bounding box for full data output set from refinement_level={bounding_box_fullData_boxRL}")
    else:
        raise ValueError(f"❌ refinement_level '{bounding_box_fullData_boxRL}' not found in box_instance.")
    

    #Getting reference length and moment center

    if not isinstance(WheelTirePartsNames, list) or len(WheelTirePartsNames) != 4:
        raise ValueError("WheelTirePartsNames must contain exactly 4 items.")
    
    wall_instances = (
        ufx.get("boundary_conditions", {})
           .get("wall", {})
           .get("wall_instance", [])
    )
    if isinstance(wall_instances, dict):
        wall_instances = [wall_instances]
    elif not isinstance(wall_instances, list):
        wall_instances = []

    wheel_center = []
    
    # Calculate wheelbase only for external aerodynamics
    if solution_type == "External_aerodynamics":
        for tire_part in WheelTirePartsNames:
            matched = False
            for instance in wall_instances:
                part_name = instance.get("parts", {}).get("name", "")
                if tire_part in part_name:
                    matched = True
                    # fluid_bc_settings 取得
                    fbc = instance.get("fluid_bc_settings", {})
                    name = instance.get('name')
                    center = fbc.get('center')
                    x_value = center.get('x_pos')
                    y_value = center.get('y_pos')
                    xy = {
                        'name':name,
                        'x':float(x_value),
                        'y':float(y_value)
                        }
                    wheel_center.append(xy)
        if not matched:
            raise ValueError("WheelTirePartsNames are not valid and unable to calculate reference length. Please check WheelTireParts setting.")

        #print(f"Wheel center info is {wheel_center}")

        # Extract front and rear groups
        # 1. x の値を抽出
        x_values = [item["x"] for item in wheel_center]

        # 2. 平均値を計算
        x_avg = sum(x_values) / len(x_values)

        # 3. Front / Rear に分割
        front_wheels = [item for item in wheel_center if item["x"] <= x_avg]
        rear_wheels  = [item for item in wheel_center if item["x"] > x_avg]

        # 前輪中心
        front_center_x = sum(w['x'] for w in front_wheels) / 2
        front_center_y = sum(w['y'] for w in front_wheels) / 2

        # 後輪中心
        rear_center_x = sum(w['x'] for w in rear_wheels) / 2
        rear_center_y = sum(w['y'] for w in rear_wheels) / 2

        # ホイールベース長（前後中心間の距離）
        wheel_base = math.hypot(rear_center_x - front_center_x, rear_center_y - front_center_y)

        # 全体の重心（x, y平均）
        center_x = sum(w['x'] for w in wheel_center) / len(wheel_center)
        center_y = sum(w['y'] for w in wheel_center) / len(wheel_center)

        
        # Calculating axis for roll, pitch, and yaw
        axes = {
            "roll_axis": np.array([1, 0, 0]),   # X
            "pitch_axis": np.array([0, 1, 0]),  # Y
            "yaw_axis": np.array([0, 0, 1])     # Z
        }

        # Z軸に+10度回転
        theta_deg = yaw_angle_vehicle
        theta_rad = math.radians(theta_deg)

        # Z軸回転行列
        Rz = np.array([
            [math.cos(theta_rad), -math.sin(theta_rad), 0],
            [math.sin(theta_rad),  math.cos(theta_rad), 0],
            [0,                   0,                    1]
        ])

        # 回転適用（yaw_axisは変化なし）
        rotated_axes = {
            name: Rz.dot(vec) if name != "yaw_axis" else vec
            for name, vec in axes.items()
        }

        # 小数点3桁で丸めて表示

        # 結果表示
        if reference_length_auto:
            print(f"✅ Wheel base length: {wheel_base:.6f} calculated automatically.")
            aero_coefficients =  output.get('aero_coefficients', {})
            aero_coefficients['reference_length'] = f"{wheel_base:.6f}"

        if yaw_angle_vehicle != 0:
            print(f"✅ Center of wheelbase (x, y) is corrected for yaw simulation: ({center_x:.6f}, {center_y:.6f})")
            moment_reference_system = output.get('moment_reference_system',{})
            
            for name, vec in rotated_axes.items():
                rounded = [round(v, 3) for v in vec]
                moment_reference_system[name]['x_dir'] = rounded[0]
                moment_reference_system[name]['y_dir'] = rounded[1]

    # Applying export_bounds_active if it's set true
    if export_bounds_active:
        aero_coefficients =  output.get('aero_coefficients', {})
        coefficients_along_axis = aero_coefficients.get('coefficients_along_axis', {})
        export_bounds = coefficients_along_axis.setdefault('export_bounds', {})
        export_bounds['active'] = 'true'
        export_bounds['exclude_domain_parts'] = 'true'
        print(f"✅ Export bounds with aero coefficient along axis is activated.")


def modify_partial_volume_output_section(parsed_xml_file, partial_volume_output,coarsen_output_options):
    ufx = parsed_xml_file.get("uFX_solver_deck", {})

    # --- outputの参照 ---
    output = ufx.get('output', {})
    partial_volume = output.get('partial_volume',{})
    if isinstance(partial_volume,dict):
        partial_volume_instances = partial_volume['partial_volume_instance']
        if not isinstance(partial_volume_instances,list):
            partial_volume_instances = [partial_volume_instances]
    else:
        print(f"⚠️: Partial volume output is not defined in this setup.")

    


    #print(f'Partial volume output setting from excel is {partial_volume_output}')

    for partial in partial_volume_output:
        if partial.get('output_coarsening') is True:
            for instance in partial_volume_instances:
                if instance['name'] == partial['name'][0]:
                    print(f"✅ Coarsen output for {instance['name']} has been modified.")
                    instance['output_coarsening'] = {
                    'active': 'true',
                    'coarsen_by_num_refinement_levels': str(partial.get('coarsen_by_num_refinement_levels')),
                    'coarsest_target_refinement_level': str(partial.get('coarsest_target_refinement_level')),
                    'export_uncoarsened_voxels': 'false'
                }
        else:
            for instance in partial_volume_instances:
                if instance['name'] == partial['name'][0]:
                    instance['output_coarsening'] = {
                    'active': 'false',
                    'coarsen_by_num_refinement_levels': str(partial.get('coarsen_by_num_refinement_levels')),
                    'coarsest_target_refinement_level': str(partial.get('coarsest_target_refinement_level')),
                    'export_uncoarsened_voxels': 'false'
                }

    
    if export_time_avg_partial_volume_outputs:
        #with this option, full partial volume output should be exported with the name of :Partial_Volume_RL4_BOX
        if coarsen_output_options['output_coarsening']:
            for instance in partial_volume_instances:
                if instance['name'] == "Partial_Volume_RL4_BOX":
                    print(f"✅: Coarsen output for {instance['name']} has been modified.")
                    instance['output_coarsening'] = {
                    'active': 'true',
                    'coarsen_by_num_refinement_levels': str(coarsen_output_options.get('coarsen_by_num_refinement_levels')),
                    'coarsest_target_refinement_level': str(coarsen_output_options.get('coarsest_target_refinement_level')),
                    'export_uncoarsened_voxels': 'false'
                }        

                    
    print("✅ Output coarsening applied.")


    
def delete_wheel_rotating_bc_for_static(parsed_xml_file, WheelPartsNames):
    if not opt_moving_floor:
        ufx = parsed_xml_file.get("uFX_solver_deck", {})
        wall_instance = ufx["boundary_conditions"]["wall"]["wall_instance"]

        updated_wall_instance = [
            instance
            for instance in wall_instance
            if not any(name in instance.get("name", "") for name in WheelPartsNames)
        ]

        ufx["boundary_conditions"]["wall"]["wall_instance"] = updated_wall_instance
        print(f"✅ Static floor condition has been applied. Rotating boundary condition for wheels has been deleted.")


        


def set_surface_roughness_for_wheels(parsed_xml_file, WheelTirePartsNames, TireSurfaceRoughness):
    if TireSurfaceRoughness in [0,float('nan'),False]:
        print("❎ Tire surface roughness is deactivated or set as 0. Nothing applied.")
        return

    ufx = parsed_xml_file.get("uFX_solver_deck", {})
    wall_instance = ufx["boundary_conditions"]["wall"]["wall_instance"]

    for instance in wall_instance:
        for name in WheelTirePartsNames:
            if name in instance.get("name"):
                instance["roughness"] = str(TireSurfaceRoughness)

    print(f"✅ Surface roughness '{TireSurfaceRoughness}' set for wheels: {WheelPartsNames}")

def set_belts_for_yaw(parsed_xml_file,yaw_angle_vehicle,inflow_velocity):
    if yaw_angle_vehicle == 0:
        print("❎ Simulation is stread ahead condition and nothing applied.")
        return

    ufx = parsed_xml_file.get("uFX_solver_deck", {})
    wall_instance = ufx["boundary_conditions"]["wall"]["wall_instance"]

    # Getting velocity for belts
    angle_rad = math.radians(yaw_angle_vehicle)
    x_velocity = inflow_velocity*math.cos(angle_rad)
    y_velocity = inflow_velocity*math.sin(angle_rad)

    for index in range(5):
        current_belt_name = "Belt_" + str(index+1)
        #print(f'Current belt name is {current_belt_name}')
        belt = {
            'name': current_belt_name,
            'parts' : {
                'name': current_belt_name
            },
            'fluid_bc_settings':{
                'type':'moving',
                'velocity':{
                    'x_dir':str(x_velocity),
                    'y_dir':str(y_velocity),
                    'z_dir':'0'
                },
                'roughness': '0',
            }
        }
        wall_instance.append(belt)

    print("✅ Moving BCs for Belts are applied for yaw + 5 belts setup.")

def calculate_delta_t():
    
    # inflow condition
    Cs = (gas_constant*heat_capacity_ratio*(temperature+273)/molecular_weight)**0.5
    delta_t=mach_scaling*(coarsest_voxel_size/(Cs*3**(1/2)))
    return delta_t

def apply_partial_surface_baffle_export_option(parsed_xml_file, partial_surface_output, BafflePartsName):
    ufx = parsed_xml_file.get("uFX_solver_deck", {})
    output = ufx.get('output', {})
    partial_surface = output.get('partial_surface', {})
    
    if isinstance(partial_surface, dict):
        partial_surface_instances = partial_surface.get('partial_surface_instance', [])
        if not isinstance(partial_surface_instances, list):
            partial_surface_instances = [partial_surface_instances]
    else:
        print(f"⚠️: Partial surface output is not defined in this setup.")
        return  # Exit early if no partial surface output is defined

    for partial in partial_surface_output:
        count = 0
        if partial.get('Baffle_export_option') == "baffle_front_only":
            suffix_to_add = ".uFX_baffle_front"
            count += 1
        elif partial.get('Baffle_export_option') == "baffle_back_only":
            suffix_to_add = ".uFX_baffle_back"
            count += 1
        else:
            continue
            
        for instance in partial_surface_instances:
            if partial['name'] == instance['name']:
                parts = instance.get('parts', {})
                names = parts.get('name', '')
                
                # Ensure names is always a list
                if not isinstance(names, list):
                    names = [names]
                
                # Create a new list to store modified names
                modified_names = []
                for name in names:
                    if check_string_against_multiple_patterns(name, include_patterns=BafflePartsName):
                        modified_name = name + suffix_to_add
                        modified_names.append(modified_name)
                        print(f"✅ Baffle export option '{partial.get('Baffle_export_option')}' applied for baffle part: {modified_name}")
                    else:
                        modified_names.append(name)
                
                # Update the parts name with modified list
                parts['name'] = modified_names if len(modified_names) > 1 else modified_names[0]

    if count == 0:
        print("❎ No baffle export options were specified in the excel settings.")
    else:             
        print("✅ Baffle export options applied where specified.")


def add_transitional_bl_detection_for_ghn(parsed_xml_file, HM_CFD_version, solution_type):
    """
    Add <transitional_bl_detection>true</transitional_bl_detection> to <simulation><wall_modeling>
    when HM_CFD_version <= 2027 and solution_type == "GHN"
    """
    # Check conditions
    if HM_CFD_version > 2027 or solution_type != "GHN":
        return
    
    ufx = parsed_xml_file.get("uFX_solver_deck", {})
    
    # Ensure simulation section exists
    simulation = ufx.setdefault("simulation", {})
    
    # Ensure wall_modeling section exists
    wall_modeling = simulation.setdefault("wall_modeling", {})
    
    # Add transitional_bl_detection
    wall_modeling["transitional_bl_detection"] = "true"
    
    print(f"✅ Added transitional_bl_detection to apply alpha/beta wall model for GHN case.")


                    

            

            

#####################################################################
# ### Parsing xml file
#####################################################################

tree = ET.parse(xml_file)
root = tree.getroot()

parsed_xml_file = ufx_deck_parser(root)

print("### Correcting xml files.......")




#####################################################################
# ### Modifying OSM section
#####################################################################
configure_osm_wheels(parsed_xml_file,WheelOSMPartsNames,WheelTirePartsNames,osm_wheels)

#####################################################################
# ### Modifying OSM section
#####################################################################
modify_geometry_section(parsed_xml_file,triangleSplitting,maxRelativeEdgeLength)


#####################################################################
# ### Modifying Surface roughness for wheels
#####################################################################
set_surface_roughness_for_wheels(parsed_xml_file,WheelTirePartsNames,TireSurfaceRoughness)

#####################################################################
# ### Modifying output section
#####################################################################\
if not coarsen_by_num_refinement_levels == 2:
    coarsen_by_num_refinement_levels = 1
    

coarsen_output_options = {
    'output_coarsening': output_coarsening,
    'coarsest_target_refinement_level': coarsest_target_refinement_level,
    'coarsen_by_num_refinement_levels': coarsen_by_num_refinement_levels
}
modify_output_section(parsed_xml_file,bounding_box_fullData_boxRL,coarsen_output_options,reference_length_auto,WheelTirePartsNames,yaw_angle_vehicle,export_bounds_active)

#####################################################################
# ### Modifying partial output section
#####################################################################\

modify_partial_volume_output_section(parsed_xml_file,partial_volume_output,coarsen_output_options)

#####################################################################
# ### Modifying partial surface output section
#####################################################################\

apply_partial_surface_baffle_export_option(parsed_xml_file,partial_surface_output,BafflePartsName)

#####################################################################
# ### Deleting rotating bc (rpm=0) for static ground
#####################################################################\
delete_wheel_rotating_bc_for_static(parsed_xml_file,WheelPartsNames)

#####################################################################
# ### Adding transitional BL detection for GHN cases
#####################################################################
add_transitional_bl_detection_for_ghn(parsed_xml_file, HM_CFD_version, solution_type)

#####################################################################
# ### Applying moving wall boundary condition on belts for yaw cases
#####################################################################
if not yaw_angle_vehicle == 0 and opt_belt_system:
    set_belts_for_yaw(parsed_xml_file,yaw_angle_vehicle,inflow_velocity)

#####################################################################
# ### Exporting modified xml file
#####################################################################\

output_path = save_dict_as_pretty_xml(parsed_xml_file, xml_file)
print(f"✅ XML was saved to: {output_path}")

if debug_mode:
    pprint(parsed_xml_file)