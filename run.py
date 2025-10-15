###################################################################################################
#
# This file is part of the HPC allocator code for the UMD astronomy department
#
# (c) Benedikt Diemer
#
###################################################################################################

import sys
import argparse
import subprocess
import copy
import os
import yaml

import config as cfg
import utils
import messaging

###################################################################################################
# MODES
###################################################################################################

# In test mode, the code can be executed on a machine other than an HPC cluster. The command-line
# queries are replaced by previously loaded data.
global test_mode 
test_mode = False

# If dry_run == True, the function runs but does not set the config to the new dates and saves 
# emails for review instead of sending them.
global dry_run
dry_run = True

###################################################################################################

def main():
    
    global test_mode
    global dry_run
    
    if len(sys.argv) == 1:
        
        checkStatus(verbose = True)
    
    else:
    
        parser = argparse.ArgumentParser(description = 'Welcome to the HPC allocator.')
    
        helpstr = 'The operation to execute'
        parser.add_argument('op_type', type = str, help = helpstr)
        parser.add_argument('mode', type = str, help = helpstr)
    
        args = parser.parse_args()
    
        utils.printLine()
        print('Welcome to the HPC Allocator')
        utils.printLine()
        print('Settings: operation = %s, mode = %s, test_mode = %s, dry_run = %s.' \
              % (args.op_type, args.mode, str(test_mode), str(dry_run)))

        if args.mode == 'test':
            test_mode = True
            dry_run = True
        elif args.mode == 'dry':
            dry_run = True
        elif args.mode == 'action':
            dry_run = False
        
        if args.op_type == 'check':
            checkStatus()
        elif args.op_type == 'groupinfo':
            printCurrentGroups(show_weight = True, show_su = False, show_scratch = False)
        elif args.op_type == 'emailtest':
            messaging.testMessage(do_send = True)
        else:
            raise Exception('Unknown operation, "%s". Allowed are [config, check].' % (args.op_type))
        
    return

###################################################################################################

# This function should be executed regularly. It:
# 
# - Load the base config (last quarter/period, group allocations for this quarter)
# - Compute the current quarter, period, and day from the date
# - If date differs from previous, re-load current group data (members and usage)
# - Check whether a new quarter has started by comparing to the last known quarter. If so:
#   - Compute new allocation weights for each group and save them to the config
#   - Send out email with new allocation details to group leads
# - Check whether a new period has started by comparing to the last known period, or if a new
#   quarter has started. If so:
#   - Compute allocations (SUs) for this period
#   - Send out allocations for this period to all group members
# - If not new quarter / period, check for usage close to allocation

def checkStatus(verbose = False):

    # ---------------------------------------------------------------------------------------------
    # Date config: Compute date, quarter, period; check for changes
    
    print('Setting overall config...')
    if os.path.exists(cfg.yaml_file_cfg):
        pFile = open(cfg.yaml_file_cfg, 'r')
        dic_cfg = yaml.safe_load(pFile)
        pFile.close()
        prev_q_all = dic_cfg['prev_q_all']
        prev_p = dic_cfg['prev_p']
        prev_d = dic_cfg['prev_d']
    else:
        prev_q_all = -1
        prev_p = -1
        prev_d = -1
        print('    WARNING: found no previous config. Re-setting variables.')
        
    yr, q_yr, q_all, p, d, p_start, p_end = utils.getTimes()
    new_quarter = (prev_q_all != q_all)
    new_period = (prev_p != p)
    new_day = (prev_d != d)
    print('    Quarter = %d (prev. %d), period = %d (prev. %d), day = %d (prev. %d).' \
          % (q_all, prev_q_all, p, prev_p, d, prev_d))
    
    # ---------------------------------------------------------------------------------------------
    # Group data

    print('Setting group data...')
    grp_file_found = os.path.exists(cfg.yaml_file_grps_cur)

    if (new_period or new_day or (not grp_file_found)):
        if grp_file_found:
            print('    Updating current group data...')
            pFile = open(cfg.yaml_file_grps_cur, 'r')
            dic_grps_prev = yaml.safe_load(pFile)
            pFile.close()
            grps_prev = dic_grps_prev['grps_cur']               
        else:
            print('    WARNING: could not find file with current group data. Will create from scratch.')
            grps_prev = {}
        
        grps_cur = collectGroupData(verbose = False)
        print('    Saving current group data to file...')
        dic_grps = {}
        dic_grps['grps_cur'] = grps_cur
        output_file = open(cfg.yaml_file_grps_cur, 'w')
        yaml.dump(dic_grps, output_file)
        output_file.close()
        if verbose:
            utils.printLine()
            print('    Current group data')
            utils.printLine()
            utils.printGroupData(grps_cur)
            utils.printLine()
    else:
        print('    Current group data already up to date, loading from file...')
        pFile = open(cfg.yaml_file_grps_cur, 'r')
        dic_grps = yaml.safe_load(pFile)
        pFile.close()
        grps_cur = dic_grps['grps_cur']

    # ---------------------------------------------------------------------------------------------
    # Quarter data

    print('Setting quarter data...')
    yaml_file_quarter = utils.getYamlNameQuarter(q_all, yr, q_yr)
    found_yaml_q = os.path.exists(yaml_file_quarter)
    
    if new_quarter or not found_yaml_q:
        
        if (not new_quarter) and (not found_yaml_q):
            print('    WARNING: could not find file with quarter data. Will create from scratch.')
        
        q_su_quota_astr, q_su_avail_astr = collectAllocation()
        print('    Found overall quarter allocation of %.1f kSU, %.1f kSU remaining.' \
              % (q_su_quota_astr / 1000.0, q_su_avail_astr / 1000.0))
        
        dic_q = {}
        dic_q['q_su_quota_astr'] = q_su_quota_astr
        dic_q['q_su_avail_astr'] = q_su_avail_astr
        prds = {}
        dic_q['periods'] = prds
        
        # Load previous file
        yaml_file_quarter_prev = utils.getYamlNameQuarter(q_all, yr, q_yr, previous = True)
        found_yaml_q_prev = os.path.exists(yaml_file_quarter_prev)
        if found_yaml_q_prev:
            pFile = open(yaml_file_quarter_prev, 'r')
            dic_q_prev = yaml.safe_load(pFile)
            pFile.close()
        else:
            print('    WARNING: Could not find data from previous quarter. Will assume this is first quarter.')
            dic_q_prev = None  

    # ---------------------------------------------------------------------------------------------
    # Period changes
    
    if new_period:

        # Create new period dataset
        print('Starting new period...')
        prds[p] = {}
        
        print('    Period runs from %s to %s.' % (p_start.strftime('%Y/%m/%d'), p_end.strftime('%Y/%m/%d')))
        prds[p]['start_date'] = p_start
        prds[p]['end_date'] = p_end
        prds[p]['groups'] = {}
        
        # Set shortcuts for new and previous period
        prd_new = prds[p]
        if p > 0:
            prd_old = prds[p - 1]
        else:
            if dic_q_prev is not None:
                prd_old = dic_q_prev['periods'][cfg.n_periods - 1]
            else:
                prd_old = {}
                prd_old['groups'] = {}
        
        # Compute total weight
        for grp in grps_cur:
            prd_new['groups'][grp] = {}
            prd_new['groups'][grp]['weight'] = grps_cur[grp]['weight']
        w_tot_cur = utils.getTotalWeight(grps_cur)
        prd_new['w_tot'] = w_tot_cur

        # Compute available allocation
        if p < cfg.n_periods - 1:
            alloc_period = q_su_avail_astr * cfg.periods[p]['alloc_frac']
        else:
            alloc_period = q_su_avail_astr
        prd_new['su_avail'] = q_su_avail_astr
        prd_new['su_alloc'] = alloc_period
        
        # Go through groups to assign allocations and notify
        for grp in grps_cur:
            
            # Compute weight
            w_frac = prd_new['groups'][grp]['weight'] / prd_new['w_tot']
            prd_new['groups'][grp]['weight_frac'] = w_frac

            # Add current users
            prd_new['groups'][grp]['users'] = {}
            for usr in grps_cur[grp]['users']:
                prd_new['groups'][grp]['users'][usr] = {}
                prd_new['groups'][grp]['users'][usr]['people_type'] = grps_cur[grp]['users'][usr]['people_type']
                prd_new['groups'][grp]['users'][usr]['past_user'] = grps_cur[grp]['users'][usr]['past_user']  

            # Compute cumulative usage in the previous period. If this is a new quarter, the usage 
            # has been reset to zero and we need to use the previous group data. This technically 
            # misses any usage between the last run of the script and this run, but that is 
            # inevitable; this info is simply lost.
            if new_quarter:
                if grp in grps_prev:
                    grp_su_usage_cum = grps_prev[grp]['su_usage']
                else:
                    grp_su_usage_cum = 0.0
                prd_new['groups'][grp]['su_usage_start'] = 0.0
            else:
                grp_su_usage_cum = grps_cur[grp]['su_usage']
                prd_new['groups'][grp]['su_usage_start'] = grp_su_usage_cum
            prd_new['groups'][grp]['su_usage'] = 0.0
            
            # Update old period with final usage
            if grp in prd_old['groups']:
                prd_old['groups'][grp]['su_usage'] = grp_su_usage_cum - prd_old['groups'][grp]['su_usage_start']
            
            # Now repeat the process for individual users. Users could be only in the old or only 
            # in the new dataset, so we need to consider a superset of possible users and check
            # whether they are in each set.
            all_users = []
            if grp in prd_old['groups']:
                all_users += list(prd_old['groups'][grp]['users'].keys())
            all_users += list(prd_new['groups'][grp]['users'].keys())
            all_users = list(set(all_users))
            for usr in all_users:
                if new_quarter:
                    if (grp in grps_prev) and (usr in grps_prev[grp]['users']):
                        usr_su_usage_cum = grps_prev[grp]['users'][usr]['su_usage']
                    else:
                        usr_su_usage_cum = 0.0
                    if usr in prd_new['groups'][grp]['users']:
                        prd_new['groups'][grp]['users'][usr]['su_usage_start'] = 0.0
                else:
                    usr_su_usage_cum = grps_cur[grp]['users'][usr]['su_usage']
                    prd_new['groups'][grp]['users'][usr]['su_usage_start'] = usr_su_usage_cum
                if (grp in prd_old['groups']) and (usr in prd_old['groups'][grp]['users']):
                    prd_old['groups'][grp]['users'][usr]['su_usage'] = usr_su_usage_cum - prd_old['groups'][grp]['users'][usr]['su_usage_start']
                prd_new['groups'][grp]['users'][usr]['su_usage'] = 0.0
                
            # Try to find previous penalty if any
            if grp in prd_old['groups']:
                penalty_old = prd_old['groups'][grp]['penalty_new']
            else:
                penalty_old = 0.0
                
            # Multiply penalty by penalty factor
            penalty_old *= cfg.penalty_factor
            
            # Distinguish the last period in each quarter
            if p < cfg.n_periods - 1:
                alloc_grp = alloc_period * w_frac
                if penalty_old <= alloc_grp:
                    alloc_grp_final = alloc_grp - penalty_old
                    penalty_new = 0.0
                else:
                    alloc_grp_final = 0.0
                    penalty_new = penalty_old - alloc_grp
                print('    Group %-15s fractional weight %.4f, allocation %6.1f kSU, penalty %6.1f kSU, final %6.1f kSU.' \
                      % (grp, w_frac, alloc_grp / 1000.0, penalty_old / 1000.0, alloc_grp_final / 1000.0))
            else:
                alloc_grp_final = q_su_avail_astr
                penalty_new = penalty_old
                print('    Assigned full remaining allocation to all groups.')

            # Store new data
            prd_new['groups'][grp]['alloc'] = alloc_grp_final
            prd_new['groups'][grp]['penalty_old'] = penalty_old
            prd_new['groups'][grp]['penalty_new'] = penalty_new

            # Write changes to previous period to file
            if (p == 0) and (dic_q_prev is not None):
                output_file = open(yaml_file_quarter_prev, 'w')
                yaml.dump(dic_q_prev, output_file)
                output_file.close()

            # Send out email with allocation details, oversubscription warning, usage in previous 
            # period, penalties if applicable, and so on to the lead. The members receive a 
            # simplified version that does not state how the allocation was computed.
            messaging.messageNewPeriod(prd_new, p, grps_cur, grp, do_send = (not dry_run))

    # ---------------------------------------------------------------------------------------------
    # If there is no new period: Usage warnings

    # For dry runs, we execute the following part since any new period data will not be stored in 
    # the yaml files.
    if (not new_period) or dry_run:
        
        print('Checking usage against allocations...')
        prd_cur = prds[p]
        for grp in grps_cur:
            
            # The group could have been added after the period was created.
            if not grp in prd_cur['groups']:
                print('WARNING: Could not find group "%s" in current period.' % (grp))
                continue
        
            # Update SU usage from cumulative
            su_usage_old = prd_cur['groups'][grp]['su_usage']
            su_usage_new = grps_cur[grp]['su_usage'] - prd_cur['groups'][grp]['su_usage_start']
            prd_cur['groups'][grp]['su_usage'] = su_usage_new
            
            # Update individual user data
            
            # TODO
            
            # Compute fraction of allocation and warn users if necessary. In the case where a 
            # group has a finite allocation, we check for fractions that exceed a warning level 
            # but did not exceed it given the old usage (so that emails are only sent once).
            #          
            # If a group got an allocation of zero (presumably due to a penalty), we send out an
            # email every time the absolute usage has changed.
            su_alloc = prd_cur['groups'][grp]['alloc']
            if su_alloc > 0.0:
                usage_prct_old = su_usage_old / su_alloc * 100.0
                usage_prct_new = su_usage_new / su_alloc * 100.0
                warned_level = -1
                if su_usage_new > 0.0:
                    for ii in range(len(cfg.warning_levels)):
                        i = len(cfg.warning_levels) - ii - 1
                        if (usage_prct_new > cfg.warning_levels[i]) and (usage_prct_old <= cfg.warning_levels[i]):
                            messaging.messageUsageWarning(prd_cur, grps_cur, grp, i, do_send = (not dry_run))
                            warned_level = i
                            break
                s = '    Group %-15s allocation %6.1f kSU, usage %6.1f -> %6.1f kSU, fraction %5.1f -> %5.1f%%' \
                      % (grp, su_alloc / 1000.0, su_usage_old / 1000.0, su_usage_new / 1000.0, 
                         usage_prct_old, usage_prct_new)
                if warned_level >= 0:
                    s += ' (%d%% warning)' % (cfg.warning_levels[warned_level])
                print(s)
            else:
                if su_usage_new > su_usage_old + 1.0:
                    messaging.messageUsageWarning(prd_cur, grps_cur, grp, None, do_send = (not dry_run))

    # ---------------------------------------------------------------------------------------------
    # Store changes to current quarter/period data and status

    # Write quarter file
    output_file = open(yaml_file_quarter, 'w')
    yaml.dump(dic_q, output_file)
    output_file.close()

    # Write config (after function has successfully run)
    if not dry_run:
        print('Updating config yaml...')
        dic = {}
        dic['prev_q_all'] = q_all
        dic['prev_p'] = p
        dic['prev_d'] = d
        output_file = open(cfg.yaml_file_cfg, 'w')
        yaml.dump(dic, output_file)
        output_file.close()
    
    return
        
###################################################################################################

# Check the allocation for astronomy for the quarter

def collectAllocation():

    if test_mode:
        alloc_guess = 8333.2 * 1000.0
        return alloc_guess, alloc_guess * 0.5

    ret = subprocess.run(['sbalance', '-account', 'astr'], 
                         capture_output = True, text = True, check = True)
    rettxt = ret.stdout
    ll = rettxt.splitlines()
    w = ll[1].split()
    q_su_quota_astr = float(w[1]) * 1000.0
    w = ll[2].split()
    q_su_avail_astr = float(w[1]) * 1000.0
    
    return q_su_quota_astr, q_su_avail_astr
        
###################################################################################################

# Collect user data from a) email exploders and b) the users_extra dictionary in config, which can
# be used to overwrite the former.

def collectUserData(verbose = False):
    
    users = {}
    
    for lname in cfg.astro_lists.keys():
        ptype = cfg.astro_lists[lname]['people_type']
        f = open('astro_lists/' + lname, 'r')
        ll = f.readlines()
        f.close()
        for l in ll:
            uid = (l.split('@')[0]).lower()
            users[uid] = {'people_type': ptype, 'past_user': False}
    
    users.update(cfg.users_extra)
    
    if verbose:
        utils.printLine()
        print('User data')
        utils.printLine()
        usrs = sorted(list(users.keys()))
        for i in range(len(usrs)):
            usr = usrs[i]
            s ='%-10s  %s' % (usr, users[usr]['people_type'])
            if 'past_user' in users[usr]:
                s += '  past user'
            if 'weight' in users[usr]:
                s += '  weight %.2f' % (users[usr]['weight'])
            print(s)
            
    return users

###################################################################################################

def collectGroupData(verbose = False):
    
    # In test mode, we just load a previously determined set of group data
    if test_mode:
        pFile = open(cfg.yaml_file_grps_cur, 'r')
        dic_grps = yaml.safe_load(pFile)
        pFile.close()
        grps_cur = dic_grps['grps_cur']
        return grps_cur
    
    # Get user data
    known_users = collectUserData(verbose = False)
    
    # Get group users
    groups = copy.copy(cfg.groups)
    for grp in groups.keys():
        
        groups[grp]['users'] = {}
        
        # Analyze scratch_quota to get full user list
        ret = subprocess.run(['scratch_quota', '--group', 'zt-%s' % (grp), '--users'], 
                             capture_output = True, text = True, check = True)
        rettxt = ret.stdout
        ll = rettxt.splitlines()
        i = 2
        w = ll[i].split()
        if w[0] != 'zt-%s' % (grp):
            raise Exception('Expected "zt-%s" in third line of output.' % (grp))
        groups[grp]['scratch_quota'] = utils.getSizeFromString(w[3], w[4])
        groups[grp]['scratch_usage'] = utils.getSizeFromString(w[1], w[2])
        i += 1
        if ll[i].strip() != '# User quotas':
            raise Exception('Expected "# User quotas" in line 4 of output.')
        i += 2
        
        # Find users in list
        w_grp = 0.0
        while i < len(ll):
            w = ll[i].split()
            usr = w[0]
            groups[grp]['users'][usr] = {}
            groups[grp]['users'][usr]['scratch_usage'] = utils.getSizeFromString(w[1], w[2])
            
            # Get user details from known users if possible. Weight may or may not have been set.
            weight = None
            if usr in known_users:
                ptype = known_users[usr]['people_type']
                past_user = known_users[usr]['past_user']
                if 'weight' in known_users[usr]:
                    weight = known_users[usr]['weight']
            else:
                print('WARNING: Could not find group %-12s user %-12s in user list. Setting weight to default.' % (grp, usr))
                ptype = 'tbd'
                past_user = False
            
            # If weight has not been set explicitly, make it zero for past users and dependent on 
            # people type otherwise.
            if weight is None:
                if past_user:
                    weight = 0.0
                else:
                    weight = cfg.people_types[ptype]['weight']
            groups[grp]['users'][usr]['people_type'] = ptype
            groups[grp]['users'][usr]['past_user'] = past_user
            groups[grp]['users'][usr]['weight'] = weight
            groups[grp]['users'][usr]['su_usage'] = 0.0
            
            # Sum group weight from users
            w_grp += groups[grp]['users'][usr]['weight']
            i += 1

        # Set group weight and add to total
        groups[grp]['weight'] = w_grp

        # Analyze s_balance to get SU usage
        ret = subprocess.run(['sbalance', '-account', '%s-astr' % (grp), '--all'], 
                             capture_output = True, text = True, check = True)
        rettxt = ret.stdout
        ll = rettxt.splitlines()
        i = 1
        w = ll[i].split()
        groups[grp]['su_quota'] = float(w[1]) * 1000.0
        i += 2
        w = ll[i].split()
        groups[grp]['su_usage'] = float(w[1]) * 1000.0
        i += 1
        while i < len(ll):
            w = ll[i].split()
            if w[0] != 'User':
                raise Exception('Expected "User" in sbalance return, found "%s".' % (w[0]))
            usr = w[1].strip()
            if not usr in groups[grp]['users']:
                raise Exception('Found user "%s" in sbalance return but not in group users.' % (usr))
            groups[grp]['users'][usr]['su_usage'] = float(w[3]) * 1000.0
            i += 1
    
    if verbose:
        utils.printLine()
        print('Group data')
        utils.printLine()
        utils.printGroupData(groups)
        utils.printLine()
        
    return groups

###################################################################################################

def printCurrentGroups(show_weight = True, show_su = True, show_scratch = True):

    if not os.path.exists(cfg.yaml_file_grps_cur):
        raise Exception('Could not find yaml file for current groups.')

    pFile = open(cfg.yaml_file_grps_cur, 'r')
    dic_grps_prev = yaml.safe_load(pFile)
    pFile.close()

    utils.printGroupData(dic_grps_prev['grps_cur'], show_weight = show_weight, 
                   show_su = show_su, show_scratch = show_scratch)
               
    return

###################################################################################################
# Trigger
###################################################################################################

if __name__ == "__main__":
    main()
