###################################################################################################
#
# This file is part of the HPC allocator code for the UMD astronomy department
#
# (c) Benedikt Diemer
#
###################################################################################################

from collections import OrderedDict
import configparser
import os

###################################################################################################
# EMAIL CONFIG
###################################################################################################

# The email module relies on sensitive info such as an app password and should thus not be stored
# in the code. Instead, create a email.cfg file in the directory where the code is run. The file
# should look like this:
#
# [login]
# email = <admin's UMD email>
# password = <admin's app password (created in Google account)>
# test_email = <another email to which a test can be sent>

parser = configparser.ConfigParser()
if not os.path.exists('email.cfg'):
    raise Exception('Could not find email.cfg file.')
parser.read('email.cfg')
sender_email = parser['login']['email']
sender_password = parser['login']['password']
test_email = parser['login']['test_email']
admin_user = sender_email.split('@')[0]

# If we are in dry run mode, output emails as text files into this directory

email_dir_draft = 'emails_draft/'
email_dir_sent = 'emails_sent/'

###################################################################################################
# STORAGE
###################################################################################################

yaml_dir = 'yaml'
yaml_file_cfg = '%s/current_config.yaml' % (yaml_dir)
yaml_file_grps_cur = '%s/groups_current.yaml' % (yaml_dir)

###################################################################################################
# USER CATEGORIES
###################################################################################################

people_types = {}
people_types['ttk'] = {'desc': 'TTK faculty',  'weight': 1.0}
people_types['ptk'] = {'desc': 'PTK faculty',  'weight': 0.4}
people_types['pd']  = {'desc': 'Postdoc',      'weight': 0.3}
people_types['gs']  = {'desc': 'Grad student', 'weight': 0.2}
people_types['ug']  = {'desc': 'Undergrad',    'weight': 0.1}
people_types['tbd'] = {'desc': 'Unknown',      'weight': 0.0}

weight_past_faculty = 0.5

###################################################################################################
# USER DATA
###################################################################################################

# Set user data. First we pull users automatically from a number of astro lists (email exploders)
# and set their type. The data can be overwritten with the users_extra dictionary.

astro_lists = {}
astro_lists['graduates']          = {'people_type': 'gs'}
astro_lists['research-scientist'] = {'people_type': 'ptk'}
astro_lists['postdocs-all']       = {'people_type': 'pd'}
astro_lists['professorial']       = {'people_type': 'ttk'}

users_extra = {}

# Past faculty
users_extra['ekempton']     = {'people_type': 'ttk', 'past_user': True, 'weight': weight_past_faculty}
users_extra['tkomacek']     = {'people_type': 'ttk', 'past_user': True, 'weight': weight_past_faculty}

# Past grad students
users_extra['dittmann']     = {'people_type': 'gs',  'past_user': True}
users_extra['jdema']        = {'people_type': 'gs',  'past_user': True}

# Current undergrads
users_extra['adayal']       = {'people_type': 'ug',  'past_user': False}
users_extra['bnowicki']     = {'people_type': 'ug',  'past_user': False}

# Past undergrads
users_extra['fgarcia4']     = {'people_type': 'ug',  'past_user': True}
users_extra['mlessard']     = {'people_type': 'ug',  'past_user': True}
users_extra['wenxi523']     = {'people_type': 'ug',  'past_user': True}
users_extra['zvladimi']     = {'people_type': 'ug',  'past_user': True}

###################################################################################################
# GROUPS
###################################################################################################

# Set group data; note that the username of the group leader does not necessarily match the name
# of the project.

groups = {}
groups['diemer-prj']   = {'lead': 'diemer'}
groups['dphamil-prj']  = {'lead': 'dphamil'}
groups['kempton-prj']  = {'lead': 'ekempton'}
groups['lkolokol-prj'] = {'lead': 'lkolokol'}
groups['komacek-prj']  = {'lead': 'tkomacek'}
groups['miller-prj']   = {'lead': 'mcmiller'}
groups['creynold-prj'] = {'lead': 'creynold'}
groups['dcr-prj']      = {'lead': 'dcr'}
groups['ricotti-prj']  = {'lead': 'ricotti'}
groups['jsunshin-prj'] = {'lead': 'jsunshin'}
groups['mwm-prj']      = {'lead': 'mwm'}
groups['qye-prj']      = {'lead': 'qye'}

###################################################################################################
# ALLOCATION PERIODS WITHIN EACH QUARTER
###################################################################################################

# Allocation periods. The allocation fraction is the fraction of the total SUs remaining that is
# allocated to users, and it thus represents the product of the duration of the period and an
# oversubscription factor.

periods = OrderedDict()
periods[0] = {'start_day': 0,  'alloc_frac': 0.9,  'label': '1st'}
periods[1] = {'start_day': 30, 'alloc_frac': 1.5,  'label': '2nd'}
periods[2] = {'start_day': 60, 'alloc_frac': 2.0,  'label': '3rd'}
periods[3] = {'start_day': 80, 'alloc_frac': None, 'label': 'final'}

n_periods = len(periods)

###################################################################################################
# PENALTY SETTINGS
###################################################################################################

# If there is no additional penalty for exceeding allocations, that would create a perverse 
# incentive to do so since time earlier in the quarter is "more valuable" than time later, when the
# oversubscription factors are larger.

penalty_factor = 1.0

###################################################################################################
# LEVELS WHEN WARNINGS ARE SENT OUT
###################################################################################################

# When the usage of a group exceeds the following ratios with their total allocation for the first
# time, an email is sent. The fractions are expressed as percent so that they are integers.

warning_levels = [80, 100]

###################################################################################################
