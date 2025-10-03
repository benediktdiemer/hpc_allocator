###################################################################################################
#
# This file is part of the HPC allocator code for the UMD astronomy department
#
# (c) Benedikt Diemer
#
###################################################################################################

from datetime import date 

import config as cfg

###################################################################################################

# Quarter counter starts in 2025/4; this is hard-coded and cannot be changed later
first_quarter_year = 2025
first_quarter_idx = 4

###################################################################################################

# Outputs are like "5.02 TB" and such, which needs to be parsed to a number in GB.

def getSizeFromString(num_str, unit_str):

    num = float(num_str)
    if unit_str.upper() == 'B':
        fac = 1024.0**-3
    elif unit_str.upper() == 'KB':
        fac = 1024.0**-2
    elif unit_str.upper() == 'MB':
        fac = 1024.0**-1
    elif unit_str.upper() == 'GB':
        fac = 1.0
    elif unit_str.upper() == 'TB':
        fac = 1024.0
    else:
        raise Exception('Unknown file size unit, "%s".' % (unit_str))
    sze = num * fac
    
    return sze

###################################################################################################

def printLine():

    print('--------------------------------------------------------------------------------')

    return

###################################################################################################

def getTimes():

    # Get current year and month    
    date_today = date.today()
    yr = date_today.year
    mth = date_today.month
    
    # Determine quarter 
    if mth >= 10:
        q_yr = 4
    elif mth >= 7:
        q_yr = 3
    elif mth >= 4:
        q_yr = 2
    else:
        q_yr = 1
    q_start = date.fromisoformat('%4d-%02d-01' % (yr, ((q_yr - 1) * 3 + 1)))
    q_all = (yr - first_quarter_year) * 4 + (q_yr - first_quarter_idx)

    # Determine days since beginning of quarter
    delta = date_today - q_start
    d = delta.days
    
    # Determine period from days
    p = len(cfg.periods) - 1
    while cfg.periods[p]['start_day'] > d:
        p -= 1
    
    return yr, q_yr, q_all, p, d

###################################################################################################

def getPickleNameQuarter(q_all, yr, q_yr, previous = False):

    if previous:
       
        if q_yr == 0:
            yr_use = yr - 1
            q_yr_use = 4
        else:
            yr_use = yr
            q_yr_use = q_yr - 1
        pickle_file_quarter = '%s/quarter_%02d_%04d_%d.pkl' % (cfg.pickle_dir, q_all - 1, yr_use, q_yr_use)
    else:
        pickle_file_quarter = '%s/quarter_%02d_%04d_%d.pkl' % (cfg.pickle_dir, q_all, yr, q_yr)
    
    return pickle_file_quarter

###################################################################################################
