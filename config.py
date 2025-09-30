###################################################################################################
#
# This file is part of the HPC allocator code for the UMD astronomy department
#
# (c) Benedikt Diemer
#
###################################################################################################

# Set possible categories of HPC users and their allocation weights

people_types = {}
people_types['ttk'] = {'desc': 'TTK faculty',  'weight': 1.0}
people_types['ptk'] = {'desc': 'PTK faculty',  'weight': 0.3}
people_types['pd']  = {'desc': 'Postdoc',      'weight': 0.2}
people_types['gs']  = {'desc': 'Grad student', 'weight': 0.15}
people_types['ug']  = {'desc': 'Undergrad',    'weight': 0.05}
people_types['tbd'] = {'desc': 'Unknown',      'weight': 0.0}

###################################################################################################

# Set user data. First we pull users automatically from a number of astro lists (email exploders)
# and set their type. The data can be overwritten with the users_extra dictionary.

astro_lists = {}
astro_lists['graduates']          = {'people_type': 'gs'}
astro_lists['research-scientist'] = {'people_type': 'ptk'}
astro_lists['postdocs-all']       = {'people_type': 'pd'}
astro_lists['professorial']       = {'people_type': 'ttk'}

users_extra = {}

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
