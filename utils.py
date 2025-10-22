###################################################################################################
#
# This file is part of the HPC allocator code for the UMD astronomy department
#
# (c) Benedikt Diemer
#
###################################################################################################

import datetime

import config

###################################################################################################

# Quarter counter starts in 2025/4; this is hard-coded and cannot be changed later
first_quarter_year = 2025
first_quarter_idx = 4

###################################################################################################

def printLine():

    print('--------------------------------------------------------------------------------')

    return

###################################################################################################

def getTotalWeight(groups):

    w_tot = 0.0
    for grp in groups.keys():
        w_tot += groups[grp]['weight']
    
    return w_tot

###################################################################################################

def printGroupData(groups, w_tot = None,
                   show_pos = True, show_weight = True, show_su = True, show_scratch = True,
                   only_grp = None,
                   do_print = True):

    if w_tot is None:
        w_tot = getTotalWeight(groups)
        
    ll = []
    for grp in groups.keys():
        if (only_grp is not None) and (grp != only_grp):
            continue
        ll.append('%-20s' % (grp))
        s1 = '    | User        |'
        s2 = '    ---------------'
        if show_pos:
            s1 += ' Pos  Ex |'
            s2 += '----------'
        if show_weight:
            s1 += ' Weight |'
            s2 += '---------'
        if show_su:
            s1 += '      kSU |'
            s2 += '-----------'
        if show_scratch:
            s1 += '  Scratch |'
            s2 += '-----------'
        ll.append(s1)
        ll.append(s2)
        for usr in sorted(list(groups[grp]['users'].keys())):
            s1 = '    | %-12s|' % (usr)
            if show_pos:
                if ('past_user' in groups[grp]['users'][usr]) and (groups[grp]['users'][usr]['past_user']):
                    str_previous = 'x'
                elif ('past_user' in groups[grp]['users'][usr]) and (not groups[grp]['users'][usr]['active']):
                    str_previous = 'i'
                else:
                    str_previous = ' '
                s1 += ' %-3s  %s  |' % (groups[grp]['users'][usr]['people_type'], str_previous)
            if show_weight:
                s1 += '  %5.2f |' % (groups[grp]['users'][usr]['weight'])
            if show_su:
                s1 += ' %8.1f |' % (groups[grp]['users'][usr]['su_usage'] / 1000.0)
            if show_scratch:
                s1 += ' %8.1f |' % (groups[grp]['users'][usr]['scratch_usage'])
            ll.append(s1)

        ll.append(s2)
        s1 = '    | TOTAL       |'
        s2 = '    | AVAILABLE   |'
        s3 = '    | FRACTION    |'
        if show_pos:
            s1 += '         |'
            s2 += '         |'
            s3 += '         |'
        if show_weight:
            s1 += '  %5.2f |' % (groups[grp]['weight'])
            s2 += '  %5.2f |' % (w_tot)
            s3 += '  %4.1f%% |' % (100.0 * groups[grp]['weight'] / w_tot)
        if show_su:
            s1 += ' %8.1f |' % (groups[grp]['su_usage'] / 1000.0)
            if 'alloc' in groups[grp]:
                s2 += ' %8.1f |' % (groups[grp]['alloc'] / 1000.0)
                s3 += '   %5.1f%% |' % (100.0 * groups[grp]['su_usage'] / groups[grp]['alloc'])
            else:
                s2 += '             |'
                s3 += '             |'
        if show_scratch:
            s1 += ' %8.1f |' % (groups[grp]['scratch_usage'])
            s2 += ' %8.1f |' % (groups[grp]['scratch_quota'])
            s3 += '   %5.1f%% |' % (100.0 * groups[grp]['scratch_usage'] / groups[grp]['scratch_quota'])
        ll.append(s1)
        ll.append(s2)
        ll.append(s3)
        ll.append('')
        
    if do_print:
        for l in ll:
            print(l)
        return
    else:
        return ll

###################################################################################################

def getTimes(days_future = 0):

    def quarterStartDate(year, quarter):
        
        return datetime.date.fromisoformat('%4d-%02d-01' % (year, ((quarter - 1) * 3 + 1)))

    cfg = config.getConfig()

    # Get current year and month
    date_today = datetime.date.today()
    if days_future != 0:
        time_delta = datetime.timedelta(days = days_future)
        date_today += time_delta
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
    q_start = quarterStartDate(yr, q_yr)
    q_all = (yr - first_quarter_year) * 4 + (q_yr - first_quarter_idx)

    # Determine days since beginning of quarter
    delta = date_today - q_start
    d = delta.days
    
    # Determine period from days
    p = cfg['n_periods'] - 1
    while cfg['periods'][p]['start_day'] > d:
        p -= 1
        
    # Determine first and last date of period
    time_delta = datetime.timedelta(days = cfg['periods'][p]['start_day'])
    p_start = q_start + time_delta
    if p == len(cfg['periods']) - 1:
        if q_yr == 4:
            q_start_next = quarterStartDate(yr + 1, 1)
        else:
            q_start_next = quarterStartDate(yr, q_yr + 1)
        time_delta = datetime.timedelta(days = -1)
        p_end = q_start_next + time_delta
    else:
        time_delta = datetime.timedelta(days = cfg['periods'][p + 1]['start_day'] - cfg['periods'][p]['start_day'] - 1)
        p_end = p_start + time_delta
    
    return yr, q_yr, q_all, p, d, p_start, p_end

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

def getYamlNameQuarter(q_all, yr, q_yr, previous = False):

    cfg = config.getConfig()
    
    if previous:
       
        if q_yr == 0:
            yr_use = yr - 1
            q_yr_use = 4
        else:
            yr_use = yr
            q_yr_use = q_yr - 1
        yaml_file_quarter = '%s/quarter_%02d_%04d_%d.yaml' % (cfg['yaml_dir'], q_all - 1, yr_use, q_yr_use)
    else:
        yaml_file_quarter = '%s/quarter_%02d_%04d_%d.yaml' % (cfg['yaml_dir'], q_all, yr, q_yr)
    
    return yaml_file_quarter

###################################################################################################
