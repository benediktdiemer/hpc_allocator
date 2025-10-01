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
import pickle
import os

import config as cfg
import utils

###################################################################################################

# The pickle protocol should be fixed to make it exchangeable between machines
pickle_protocol = 5
pickle_dir = 'pickles/'

###################################################################################################

def main():
    
    if len(sys.argv) == 1:
        
        checkStatus(dry_run = True, verbose = True)
    
    else:
    
        parser = argparse.ArgumentParser(description = 'Welcome to the HPC allocator.')
    
        helpstr = 'The operation to execute'
        parser.add_argument('op_type', type = str, help = helpstr)
    
        args = parser.parse_args()
        
        if args.op_type == 'config':
            
            printConfig()
            
        elif args.op_type == 'check':
            
            checkStatus()
            
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
#
# If dry_run == True, the function runs but does not set the config to the new dates and saves emails
# for review instead of sending them.

def checkStatus(force_load = False, dry_run = True, verbose = False):

    utils.printLine()
    print('HPC Allocator: Checking status')
    utils.printLine()
    
    # Load config (dates)
    pickle_file_cfg = '%s/current_config.pkl' % (pickle_dir)
    if os.path.exists(pickle_file_cfg):
        pFile = open(pickle_file_cfg, 'rb')
        dic = pickle.load(pFile)
        pFile.close()
        prev_q_all = dic['prev_q_all']
        prev_p = dic['prev_p']
        prev_d = dic['prev_d']
    else:
        prev_q_all = -1
        prev_p = -1
        prev_d = -1
        print('WARNING: found no previous config. Re-setting variables.')
        
    # Compute date, quarter, period; check for changes
    yr, q_yr, q_all, p, d = utils.getTimes()
    new_quarter = (prev_q_all != q_all)
    new_period = (prev_p != p)
    new_day = (prev_d != d)
    print('Quarter = %d (prev. %d), period = %d (prev. %d), day = %d (prev. %d).' \
          % (q_all, prev_q_all, p, prev_p, d, prev_d))

    # Check if we need new to update group/user data
    pickle_file_grps_cur = '%s/groups_current.pkl' % (pickle_dir)
    must_update_grp_cur = False
    if new_quarter or new_day or force_load:
        print('Updating current group data...')
        must_update_grp_cur = True
    else:
        if not os.path.exists(pickle_file_grps_cur):
            print('WARNING: could not find file with current group data. Creating from scratch...')
            must_update_grp_cur = True
        else:
            print('Current group data already up to date, loading from file...')
            pFile = open(pickle_file_grps_cur, 'rb')
            dic = pickle.load(pFile)
            pFile.close()
            grps_cur = dic['grps_cur']
    if must_update_grp_cur:
        grps_cur = collectGroupData(verbose = verbose)
        print('Saving current group data to file...')
        dic = {}
        dic['grps_cur'] = grps_cur
        output_file = open(pickle_file_grps_cur, 'wb')
        pickle.dump(dic, output_file, pickle_protocol)
        output_file.close()
    
        if verbose:
            utils.printLine()
            print('Current group data')
            utils.printLine()
            printGroupData(grps_cur)
            utils.printLine()

    # Load or update the group data to be used for computing quarterly allocations
    pickle_file_grps_q = '%s/groups_quarter_%02d_%04d_%d.pkl' % (pickle_dir, q_all, yr, q_yr)
    must_update_grp_q = False
    if new_quarter:
        print('Updating quarter group data...')
        must_update_grp_q = True
    else:
        if os.path.exists(pickle_file_grps_q):
            print('Quarter group data already up to date, loading from file...')
            pFile = open(pickle_file_grps_q, 'rb')
            dic = pickle.load(pFile)
            pFile.close()
            grps_q = dic['grps_q']
        else:
            print('WARNING: Could not find file with quarter group data, using current...')
            must_update_grp_q = True
    if must_update_grp_q:
        print('Saving quarter group data to file...')
        grps_q = copy.copy(grps_cur)    
        dic = {}
        dic['grps_q'] = grps_q
        output_file = open(pickle_file_grps_q, 'wb')
        pickle.dump(dic, output_file, pickle_protocol)
        output_file.close()
    
        utils.printLine()
        print('Quarter group data')
        utils.printLine()
        printGroupData(grps_cur)
        utils.printLine()

    # Check for a new quarter and if it has changed, send out allocation details
    
    # Check for a new period
    
    # Write config (after function has successfully run)
    if not dry_run:
        print('Updating config pickle...')
        dic = {}
        dic['prev_q_all'] = q_all
        dic['prev_p'] = p
        dic['prev_d'] = d
        output_file = open(pickle_file_cfg, 'wb')
        pickle.dump(dic, output_file, pickle_protocol)
        output_file.close()
    
    return

###################################################################################################

def printConfig(verbose = False):
    
    collectGroupData(verbose = verbose)
    
    return

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
            users[uid] = {'people_type': ptype}
    
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
    
    # Get user data
    users = collectUserData(verbose = False)
    
    # Get group users
    w_tot = 0.0
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
        w_grp = 0.0
        while i < len(ll):
            w = ll[i].split()
            usr = w[0]
            groups[grp]['users'][usr] = {}
            groups[grp]['users'][usr]['scratch_usage'] = utils.getSizeFromString(w[1], w[2])
            if usr in users:
                ptype = users[usr]['people_type']
            else:
                print('WARNING: Could not find group %-12s user %-12s in user list. Setting weight to default.' % (grp, usr))
                ptype = 'tbd'
            groups[grp]['users'][usr]['people_type'] = ptype
            if (usr in users) and ('weight' in users[usr]):
                groups[grp]['users'][usr]['weight'] = users[usr]['weight']
            else:
                groups[grp]['users'][usr]['weight'] = cfg.people_types[ptype]['weight']
            groups[grp]['users'][usr]['su_used'] = 0.0
            w_grp += groups[grp]['users'][usr]['weight']
            i += 1

        # Set group weight and add to total
        groups[grp]['weight'] = w_grp
        w_tot += w_grp

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
        groups[grp]['su_used'] = float(w[1]) * 1000.0
        i += 1
        while i < len(ll):
            w = ll[i].split()
            if w[0] != 'User':
                raise Exception('Expected "User" in sbalance return, found "%s".' % (w[0]))
            usr = w[1].trim()
            if not usr in groups[grp]['users']:
                raise Exception('Found user "%s" in sbalance return but not in group users.' % (usr))
            groups[grp]['users'][usr]['su_used'] = float(w[3]) * 1000.0
            
    if verbose:
        utils.printLine()
        print('Group data')
        utils.printLine()
        printGroupData(groups)
        utils.printLine()
        
    return groups

###################################################################################################

def printGroupData(groups):

    w_tot = 0.0
    for grp in groups.keys():
        w_tot += groups[grp]['weight']
        
    for grp in groups.keys():
        print('%-20s   weight   scratch' % (grp))
        for usr in sorted(list(groups[grp]['users'].keys())):
            print('    %-12s %-3s   %.2f     %8.2e     %8.2e' % (usr, 
                        groups[grp]['users'][usr]['people_type'], groups[grp]['users'][usr]['weight'], 
                        groups[grp]['users'][usr]['su_usage'], groups[grp]['users'][usr]['scratch_usage']))
        print('    -------------------------------------')
        print('    TOTAL              %.2f     %8.2e     %8.2e' % (groups[grp]['weight'], groups[grp]['su_usage'], groups[grp]['scratch_usage']))
        print('    AVAILABLE         %5.2f     %8.2e     %8.2e' % (w_tot, groups[grp]['su_quota'], groups[grp]['scratch_quota']))
        print('    FRACTION          %4.1f%%       %5.2f%%       %5.2f%%' % (100.0 * groups[grp]['weight'] / w_tot, 
                        100.0 * groups[grp]['su_usage'] / groups[grp]['su_quota'],
                        100.0 * groups[grp]['scratch_usage'] / groups[grp]['scratch_quota']))
        print()
    
    return

###################################################################################################
# Trigger
###################################################################################################

if __name__ == "__main__":
    main()
