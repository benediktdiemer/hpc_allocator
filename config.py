###################################################################################################
#
# This file is part of the HPC allocator code for the UMD astronomy department
#
# (c) Benedikt Diemer
#
###################################################################################################

from collections import OrderedDict

###################################################################################################

# The pickle protocol should be fixed to make it exchangeable between machines
pickle_protocol = 5
pickle_dir = 'pickles/'
pickle_file_cfg = '%s/current_config.pkl' % (pickle_dir)
pickle_file_grps_cur = '%s/groups_current.pkl' % (pickle_dir)

###################################################################################################

# Set possible categories of HPC users and their allocation weights

people_types = {}
people_types['ttk'] = {'desc': 'TTK faculty',  'weight': 1.0}
people_types['ptk'] = {'desc': 'PTK faculty',  'weight': 0.3}
people_types['pd']  = {'desc': 'Postdoc',      'weight': 0.2}
people_types['gs']  = {'desc': 'Grad student', 'weight': 0.15}
people_types['ug']  = {'desc': 'Undergrad',    'weight': 0.05}
people_types['tbd'] = {'desc': 'Unknown',      'weight': 0.0}

weight_past_faculty = 0.5

###################################################################################################

# Set user data. First we pull users automatically from a number of astro lists (email exploders)
# and set their type. The data can be overwritten with the users_extra dictionary.

astro_lists = {}
astro_lists['graduates']          = {'people_type': 'gs'}
astro_lists['research-scientist'] = {'people_type': 'ptk'}
astro_lists['postdocs-all']       = {'people_type': 'pd'}
astro_lists['professorial']       = {'people_type': 'ttk'}

users_extra = {}

# Faculty who have left
users_extra['tkomacek']     = {'people_type': 'ttk', 'past_user': True, 'weight': weight_past_faculty}
users_extra['ekempton']     = {'people_type': 'ttk', 'past_user': True, 'weight': weight_past_faculty}

# Current grad students
users_extra['jdema']     = {'people_type': 'gs'}

# Current undergrads
users_extra['mlessard']     = {'people_type': 'ug'}

# Past undergrads
users_extra['zvladimi']     = {'people_type': 'ug',  'past_user': True}
users_extra['wenxi523']     = {'people_type': 'ug',  'past_user': True}

###################################################################################################

# Set group data; note that the username of the group leader does not necessarily match the name
# of the project.

groups = {}
groups['diemer-prj']   = {'lead': 'diemer'}
groups['dphamil-prj']  = {'lead': 'dphamil'}
groups['kempton-prj']  = {'lead': 'ekempton'}
groups['lkolokol-prj'] = {'lead': 'lkolokol'}
groups['komacek-prj']  = {'lead': 'diemer'}
groups['miller-prj']   = {'lead': 'mcmiller'}
groups['creynold-prj'] = {'lead': 'creynold'}
groups['dcr-prj']      = {'lead': 'dcr'}
groups['ricotti-prj']  = {'lead': 'ricotti'}
groups['jsunshin-prj'] = {'lead': 'jsunshin'}
groups['mwm-prj']      = {'lead': 'mwm'}
groups['qye-prj']      = {'lead': 'qye'}

###################################################################################################

# Allocation periods. The allocation fraction is the fraction of the total SUs remaining that is
# allocated to users, and it thus represents the product of the duration of the period and an
# oversubscription factor.

periods = OrderedDict()
periods[0] = {'start_day': 0,  'alloc_frac': 0.5}
periods[1] = {'start_day': 30, 'alloc_frac': 0.9}
periods[2] = {'start_day': 60, 'alloc_frac': 2.0}
periods[3] = {'start_day': 80, 'alloc_frac': None}

n_periods = len(periods)

###################################################################################################
