# S-57 Attribute Dictionaries

# NOAA ENC Scale Bands
scale_band_dic = {
    '1': 'Overview (1:10M - 1:3.5M)',
    '2': 'General (1:1.5M - 1:700k)',
    '3': 'Coastal (1:350k - 1:180k)',
    '4': 'Approach (1:90k - 1:45k)',
    '5': 'Harbor (1:22k - 1:12k)',
    '6': 'Berthing (1:4k - 1:2k)'
}

boyshp_dic = {
    '1': 'conical', '2': 'can', '3': 'spherical', '4': 'pillar',
    '5': 'spar', '6': 'barrel', '7': 'superbuoy', '8': 'ice_buoy'
}

bcnshp_dic = {
    '1': 'stake', '2': 'with_symbol', '3': 'beacon_tower',
    '4': 'lattice_beacon', '5': 'pile_beacon', '6': 'cairn', '7': 'buoyant_beacon'
}

catcam_dic = {
    '1': 'north', '2': 'east', '3': 'south', '4': 'west'
}

colour_dic = {
    '1': 'white', '2': 'black', '3': 'red', '4': 'green',
    '5': 'blue', '6': 'yellow', '7': 'grey', '8': 'brown',
    '9': 'amber', '10': 'violet', '11': 'orange', '12': 'magenta', '13': 'pink'
}

colpat_dic = {
    '1': 'horizontal_stripes', '2': 'vertical_stripes', 
    '3': 'diagonal_stripes', '4': 'squared', 
    '5': 'stripes', '6': 'border_stripe'
}

def colour_builder(colour_raw):
    try:
        if hasattr(colour_raw, '__iter__') and not isinstance(colour_raw, str):
            c_str = ",".join(map(str, colour_raw))
        else:
            c_str = str(colour_raw)
    except Exception:
        c_str = str(colour_raw)
        
    c_str = c_str.lower().strip()
    
    if c_str in ['nan', 'none', '', '[]', '<na>', 'nan,nan']: 
        return 'unknown'
    
    clean_str = c_str.replace('.0', '').replace('[', '').replace(']', '').replace("'", "").replace(' ', '')
    colors = [colour_dic.get(c, 'unknown') for c in clean_str.split(',')]
    return '_'.join(colors)

def colpat_builder(colpat_raw):
    try:
        if hasattr(colpat_raw, '__iter__') and not isinstance(colpat_raw, str):
            c_str = ",".join(map(str, colpat_raw))
        else:
            c_str = str(colpat_raw)
    except Exception:
        c_str = str(colpat_raw)

    c_str = c_str.lower().strip()
    
    if c_str in ['nan', 'none', '', '[]', '<na>', 'nan,nan']:
        return ''

    clean_str = c_str.replace('.0', '').replace('[', '').replace(']', '').replace("'", "").replace(' ', '')
    patterns = [colpat_dic.get(p) for p in clean_str.split(',') if p in colpat_dic]

    if patterns:
        return '_'.join(patterns)
    return ''

def parse_light_sequence(sigseq):
    if not sigseq or str(sigseq) == 'nan': return "0.0,0.0"
    seq = str(sigseq).replace('(', '').replace(')', '')
    parts = seq.split(',')
    parsed = []
    for p in parts:
        try:
            parsed.append(f"{float(p):.1f}")
        except ValueError:
            parsed.append("0.0")
    return ','.join(parsed)

def get_rgb(color_name):
    rgb_map = {
        'white': (255, 255, 255), 'red': (255, 0, 0),
        'green': (0, 255, 0), 'yellow': (255, 255, 0),
        'blue': (0, 0, 255), 'orange': (255, 165, 0)
    }
    return rgb_map.get(color_name, (255, 255, 255))
