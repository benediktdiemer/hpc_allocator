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

import config as cfg

###################################################################################################

def main():
    
    if len(sys.argv) == 1:
        main_local()
    else:
        main_script()
    
    return

###################################################################################################

def main_local():
    
    printConfig()
    
    return

###################################################################################################

def main_script():

    parser = argparse.ArgumentParser(description = 'Welcome to the HPC allocator.')

    helpstr = 'The operation to execute'
    parser.add_argument('op_type', type = str, help = helpstr)

    args = parser.parse_args()
    
    if args.op_type == 'config':
        
        printConfig()
        
    elif args.op_type == 'check':
        
        checkUsage()
        
    else:
        raise Exception('Unknown operation, "%s". Allowed are [config, check].' % (args.op_type))
    
    return

###################################################################################################

def printConfig():
    
    collectGroupData()
    
    return

###################################################################################################

# Collect user data from a) email exploders and b) the users_extra dictionary in config, which can
# be used to overwrite the former.

def collectUserData(verbose = True):
    
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
        user_names = sorted(list(users.keys()))
        for i in range(len(user_names)):
            print('%-10s  %s' % (user_names[i], users[user_names[i]]['people_type']))
    
    return users

###################################################################################################

def collectGroupData():
    
    # Get user data
    users = collectUserData()
    
    # Get group users
    for grp in cfg.groups.keys():
        cfg.groups[grp]['users'] = []
        
        ret = subprocess.run(['scratch_quota', '--group' 'zt-%s' % (grp), '--users'], 
                             capture_output = True, text = True, check = True)
        
        print(ret)
    
    return

###################################################################################################

def checkUsage(send_emails = False):
    
    return

###################################################################################################
# Trigger
###################################################################################################

if __name__ == "__main__":
    main()
