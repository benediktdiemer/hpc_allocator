###################################################################################################
#
# This file is part of the HPC allocator code for the UMD astronomy department
#
# (c) Benedikt Diemer
#
###################################################################################################

import smtplib
from email.message import EmailMessage
import datetime

import config as cfg

###################################################################################################

def testMessage(do_send = False):

    subject = f'Test message'
    content = 'This is a test message.\nThe date and time is %s.\n\nThe HPC admin' \
                        % (str(datetime.datetime.now()))
    
    sendMessage(cfg.test_email, subject, content, do_send = do_send, verbose = True)
 
    return

###################################################################################################

def messageNewPeriodLead(prd_grp_data):
    
    # TODO
    
    return

###################################################################################################

def messageNewPeriodMembers(prd_grp_data):
     
    # TODO
       
    return

###################################################################################################

def messageUsageWarning(prd_grp_data):
     
    # TODO
       
    return

###################################################################################################

def messageUsageWarningZeroAlloc(prd_grp_data):
     
    # TODO
       
    return

###################################################################################################

# This function saves messages to text file and, if do_send is True, attempts to send them via
# email.

def sendMessage(recipient, subject, content, do_send = False, verbose = False):
    
    if do_send:
        email_dir = cfg.email_dir_sent
    else:
        email_dir = cfg.email_dir_draft
    
    time_str = str(datetime.datetime.now())[:-4]
    time_str = time_str.replace(' ', '_').replace('-', '_').replace(':', '_')
    fname = email_dir + time_str + '_' + recipient + '.txt'
    f = open(fname, 'w')
    f.write('Subject: %s' % (subject))
    f.write('\n\n')
    f.write(content)
    f.close()
        
    if do_send:

        msg = EmailMessage()
        msg['From'] = cfg.sender_email 
        msg['To'] = cfg.test_email
        msg['Subject'] = f'Test message'
        msg.set_content(content)

        if verbose:
            print('Sending email "%s"...' % (msg['Subject']))
            print('    Connecting to server...')
        s = smtplib.SMTP('smtp.gmail.com')
        
        # Identify yourself to an ESMTP server using EHLO
        if verbose:
            print('    Sending EHLO...')
        s.ehlo()
        
        # Secure the SMTP connection
        if verbose:
            print('    Starting TLS...')
        s.starttls()
        
        # Login to the server (if required)
        if verbose:
            print('    Logging in...')
        s.login(cfg.sender_email , cfg.sender_password)
        
        # Send message
        if verbose:
            print('    Sending message...')
        s.send_message(msg)
        
        s.quit()

    return

###################################################################################################
