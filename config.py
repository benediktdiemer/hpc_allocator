###################################################################################################
#
# This file is part of the HPC allocator code for the UMD astronomy department
#
# (c) Benedikt Diemer
#
###################################################################################################

import os
import yaml

###################################################################################################

config_path = 'config/config.yaml'
config_path_email = 'config/config_email.yaml'

cfg = None

###################################################################################################

def getConfig():
    
    global cfg
    
    if cfg is None:
       
        if not os.path.exists(config_path):
            raise Exception('Could not find config file %s.' % (config_path))
        pFile = open(config_path, 'r')
        cfg = yaml.safe_load(pFile)
        pFile.close()        
    
        if not os.path.exists(config_path_email):
            raise Exception('Could not find config file %s.' % (config_path_email))
        pFile = open(config_path_email, 'r')
        cfg_email = yaml.safe_load(pFile)
        pFile.close() 
        
        cfg.update(cfg_email)
        
        cfg['n_periods'] = len(cfg['periods'])
        cfg['admin_user'] = cfg['email']['sender_email'].split('@')[0]    
    
    return cfg

###################################################################################################
