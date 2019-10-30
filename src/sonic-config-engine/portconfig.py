
#!/usr/bin/env python
try:
    import os
    import sys
    import json
    import ast
    import re
    from collections import OrderedDict
    from swsssdk import ConfigDBConnector
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

# Global Variable
PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
PLATFORM_ROOT_PATH_DOCKER = '/usr/share/sonic/platform'
SONIC_ROOT_PATH = '/usr/share/sonic'
HWSKU_ROOT_PATH = '/usr/share/sonic/hwsku'

PLATFORM_JSON = 'platform.json'
PORT_CONFIG_INI = 'portconfig.ini'

PORT_STR = "Ethernet"
BRKOUT_MODE = "default_brkout_mode"

BRKOUT_PATTERN = r'(\d{1,3})x(\d{1,3}G)(\[\d{1,3}G\])?(\((\d{1,3})\))?'

def db_connect_configdb():
    """
    Connect to configdb
    """
    config_db = ConfigDBConnector()
    if config_db is None:
        return None
    config_db.connect()
    return config_db

def get_port_config_file_name(hwsku=None, platform=None):

    # check 'platform.json' file presence
    port_config_candidates_Json = []
    port_config_candidates_Json.append(os.path.join(HWSKU_ROOT_PATH, PLATFORM_JSON))
    if platform and hwsku:
        port_config_candidates_Json.append(os.path.join(PLATFORM_ROOT_PATH, platform, hwsku, PLATFORM_JSON))
    elif platform and not hwsku:
        port_config_candidates_Json.append(os.path.join(PLATFORM_ROOT_PATH, platform, PLATFORM_JSON))
    elif hwsku and not platform:
        port_config_candidates_Json.append(os.path.join(PLATFORM_ROOT_PATH_DOCKER, hwsku, PLATFORM_JSON))
        port_config_candidates_Json.append(os.path.join(SONIC_ROOT_PATH, hwsku, PLATFORM_JSON))

    # check 'portconfig.ini' file presence
    port_config_candidates = []
    port_config_candidates.append(os.path.join(HWSKU_ROOT_PATH, PORT_CONFIG_INI))
    if platform and hwsku:
        port_config_candidates.append(os.path.join(PLATFORM_ROOT_PATH, platform, hwsku, PORT_CONFIG_INI))
    elif platform and not hwsku:
        port_config_candidates.append(os.path.join(PLATFORM_ROOT_PATH, platform, PORT_CONFIG_INI))
    elif hwsku and not platform:
        port_config_candidates.append(os.path.join(PLATFORM_ROOT_PATH_DOCKER, hwsku, PORT_CONFIG_INI))
        port_config_candidates.append(os.path.join(SONIC_ROOT_PATH, hwsku, PORT_CONFIG_INI))

    for candidate in port_config_candidates_Json + port_config_candidates:
        if os.path.isfile(candidate):
            return candidate
    return None

def get_port_config(hwsku=None, platform=None, port_config_file=None):
    config_db = db_connect_configdb()

    # If available, Read from CONFIG DB first
    if config_db is not None:

        port_data = config_db.get_table("PORT")
        if port_data is not None:
            ports = ast.literal_eval(json.dumps(port_data))
            port_alias_map = {}
            for intf_name in ports.keys():
                port_alias_map[ports[intf_name]["alias"]]= intf_name
            return (ports, port_alias_map)

    if not port_config_file:
        port_config_file = get_port_config_file_name(hwsku, platform)
        if not port_config_file:
            return ({}, {})

    # Read from 'platform.json' file
    if port_config_file.endswith('.json'):
        return parse_platform_json_file(port_config_file)

    # If 'platform.json' file is not available, read from 'port_config.ini'
    else:
        return parse_port_config_file(port_config_file)

def parse_port_config_file(port_config_file):
    ports = {}
    port_alias_map = {}
    # Default column definition
    titles = ['name', 'lanes', 'alias', 'index']
    with open(port_config_file) as data:
        for line in data:
            if line.startswith('#'):
                if "name" in line:
                    titles = line.strip('#').split()
                continue;
            tokens = line.split()
            if len(tokens) < 2:
                continue
            name_index = titles.index('name')
            name = tokens[name_index]
            data = {}
            for i, item in enumerate(tokens):
                if i == name_index:
                    continue
                data[titles[i]] = item
            data.setdefault('alias', name)
            ports[name] = data
            port_alias_map[data['alias']] = name
    return (ports, port_alias_map)

# Generate configs (i.e. alias, lanes, speed, index) for port
def gen_port_config(ports, intf, match_list, index, alias_at_lanes, lanes):
    parent_interface_index = int(re.search("Ethernet(\d+)", intf).group(1))
    alias_start = 0
    """
    Example of match_list for some breakout_mode using regex
        Breakout Mode -------> Match_list
        -----------------------------
        2x25G(2)+1x50G(2) ---> [('2', '25G', None, '(2)', '2'), ('1', '50G', None, '(2)', '2')]
        1x50G(2)+2x25G(2) ---> [('1', '50G', None, '(2)', '2'), ('2', '25G', None, '(2)', '2')]
        1x100G[40G] ---------> [('1', '100G', '[40G]', None, None)]
        2x50G ---------------> [('2', '50G', None, None, None)]
    """
    for k in match_list:
        num_lane_used, speed, alt_speed, _ , assigned_lane = k[0], k[1], k[2], k[3], k[4]

        # Logic for ASYMMETRIC breakout mode
        if assigned_lane:
            if num_lane_used:
                step = int(assigned_lane)/int(num_lane_used)
                for i in range(0,int(assigned_lane), step):
                    intf_name = PORT_STR + str(parent_interface_index)

                    ports[intf_name] = {}
                    ports[intf_name]['alias'] = alias_at_lanes.split(",")[alias_start]
                    ports[intf_name]['lanes'] = ','.join(lanes.split(",")[alias_start:alias_start+step])
                    if speed:
                        ports[intf_name]['speed'] = speed
                    else:
                        raise Exception('Regex return for speed is None...')
                    ports[intf_name]['index'] = index.split(",")[alias_start]
                    ports[intf_name]['admin_status'] = "up"

                    parent_interface_index += step
                    alias_start += step
            else:
                raise Exception('Regex return for num_lane_used is None...')

        # Logic for SYMMETRIC breakout mode
        else:
            lane_len = len(lanes.split(","))
            if num_lane_used:
                step = lane_len/int(num_lane_used)
                lane_end = step
                for i in range(0,lane_len, step):
                    intf_name = PORT_STR + str(parent_interface_index)

                    ports[intf_name] = {}
                    ports[intf_name]['alias'] = alias_at_lanes.split(",")[alias_start]
                    ports[intf_name]['lanes'] = ','.join(lanes.split(",")[alias_start:lane_end])
                    if speed:
                        ports[intf_name]['speed'] = speed
                    else:
                        raise Exception('Regex return for speed is None...')
                    ports[intf_name]['index'] = index.split(",")[alias_start]
                    ports[intf_name]['admin_status'] = "up"

                    parent_interface_index += step
                    alias_start += step
                    lane_end += step
            else:
                raise Exception('Regex return for num_lane_used is None...')

def parse_platform_json_file(port_config_file, brkout_mode=None):
    ports = {}
    port_alias_map = {}

    # Read 'platform.json' file
    try:
        with open(port_config_file) as fp:
            try:
                data = json.load(fp)
            except json.JSONDecodeError:
                print("Json file does not exist")
        global port_dict
        port_dict = ast.literal_eval(json.dumps(data))
    except:
        print("error occurred while parsing json:", sys.exc_info()[1])

    for intf in port_dict:
        index = port_dict[intf]['index']
        alias_at_lanes = port_dict[intf]['alias_at_lanes']
        lanes = port_dict[intf]['lanes']

        # if User does not specify brkout_mode, take default_brkout_mode from platform.json
        if brkout_mode is None:
            brkout_mode = port_dict[intf][BRKOUT_MODE]

        # Get match_list for Asymmetric breakout mode
        if re.search("\+",brkout_mode) is not None:
            brkout_parts = brkout_mode.split("+")
            match_list = [re.match(BRKOUT_PATTERN, i).groups() for i in brkout_parts]

        # Get match_list for Symmetric breakout mode
        else:
            match_list = [re.match(BRKOUT_PATTERN, brkout_mode).groups()]

        if match_list is not None:
            gen_port_config(ports, intf, match_list, index, alias_at_lanes, lanes)
            brkout_mode = None
        else:
            raise Exception("match_list should not be None.")
    if not ports:
        raise Exception("Ports dictionary is empty")

    for i in ports.keys():
        port_alias_map[ports[i]["alias"]]= i
    return (ports, port_alias_map)
