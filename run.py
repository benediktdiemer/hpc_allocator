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
    
    printConfig(verbose = True)
    
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
        printLine()
        print('User data')
        printLine()
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
        
        ret = subprocess.run(['scratch_quota', '--group', 'zt-%s' % (grp), '--users'], 
                             capture_output = True, text = True, check = True)
        rettxt = ret.stdout
        ll = rettxt.splitlines()

        i = 2
        w = ll[i].split()
        if w[0] != 'zt-%s' % (grp):
            raise Exception('Expected "zt-%s" in third line of output.' % (grp))
        groups[grp]['scratch_quota'] = getSizeFromString(w[3], w[4])
        groups[grp]['scratch_usage'] = getSizeFromString(w[1], w[2])

        i += 1
        if ll[i].strip() != '# User quotas':
            raise Exception('Expected "# User quotas" in line 4 of output.')

        i += 2
        w_grp = 0.0
        while i < len(ll):
            w = ll[i].split()
            usr = w[0]
            groups[grp]['users'][usr] = {}
            groups[grp]['users'][usr]['scratch_usage'] = getSizeFromString(w[1], w[2])
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
            w_grp += groups[grp]['users'][usr]['weight']
            i += 1

        groups[grp]['weight'] = w_grp
        w_tot += w_grp

    if verbose:
        printLine()
        print('Group data')
        printLine()
        for grp in groups.keys():
            print('%-20s   weight   scratch' % (grp))
            for usr in sorted(list(groups[grp]['users'].keys())):
                print('    %-12s %-3s   %.2f     %8.2e' % (usr, groups[grp]['users'][usr]['people_type'], groups[grp]['users'][usr]['weight'], groups[grp]['users'][usr]['scratch_usage']))
            print('    -------------------------------------')
            print('    TOTAL              %.2f     %8.2e' % (groups[grp]['weight'], groups[grp]['scratch_usage']))
            print('    AVAILABLE         %5.2f     %8.2e' % (w_tot, groups[grp]['scratch_quota']))
            print('    FRACTION          %4.1f%%       %5.2f%%' % (100.0 * groups[grp]['weight'] / w_tot, 100.0 * groups[grp]['scratch_usage'] / groups[grp]['scratch_quota']))
            print()
        printLine()
                      
    return

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

def checkUsage(send_emails = False):
    
    return

###################################################################################################
# Trigger
###################################################################################################

if __name__ == "__main__":
    main()
