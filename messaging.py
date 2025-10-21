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
import utils

###################################################################################################

subject_prefix = '[Astro HPC]'
email_ext = '@umd.edu'

email_start = 'Dear HPC user,\n\n'
email_end = " For any other questions regarding our allocation system or Zaratan in general, please see the astro wiki at https://wiki.astro.umd.edu/computing/zaratan."
email_end += '\n\nHappy computing!\n\nYour friendly HPC allocation robot'

###################################################################################################

def testMessage(do_send = False):

    subject = 'Test message'
    content = 'This is a test message.\nThe date and time is %s.\n\nThe HPC admin' \
                        % (str(datetime.datetime.now()))
    
    sendMessage(cfg.test_email, subject, content, do_send = do_send, verbose = True)

    return

###################################################################################################

# This message is sent to the lead and all members at the beginning of a new period. Only the lead
# sees how the weight is computed.

def messageNewPeriod(prd_data, prd_data_prev, p, grp, do_send = False):
    
    subject = '%s New allocation period' % (subject_prefix)

    content = email_start
    content += 'You are receiving this email because you are a member of the user group %s.' % (grp)
    content += " We are beginning this quarter's %s allocation period, which runs from %s to %s." \
        % (cfg.periods[p]['label'], prd_data['start_date'].strftime('%Y/%m/%d'), prd_data['end_date'].strftime('%Y/%m/%d'))

    if grp in prd_data_prev['groups']:
        content += " The following table shows your group's usage over the previous period (in kSU), as well as your current scratch usage (in GB):"
        content += '\n'
        content += '\n'
        ll = utils.printGroupData(prd_data_prev['groups'], w_tot = prd_data_prev['w_tot'],
                                      only_grp = grp, show_weight = False, show_pos = False, do_print = False)
        for i in range(len(ll)):
            if i == 0:
                continue
            content += ll[i] + '\n'
    
    content += 'The following table details the allocation that your group has received for the new period according to our distribution key.'
    content += ' An "x" means that a user is marked as being a former member of UMD astronomy.'
    content += ' If that is incorrect, or if members not marked with an "x" have left your group, please let the HPC admin know.'
    content += '\n'
    content += '\n'
    ll = utils.printGroupData(prd_data['groups'], w_tot = prd_data['w_tot'],
                                  only_grp = grp, show_su = False, show_scratch = False, do_print = False)
    for i in range(len(ll)):
        if i == 0:
            continue
        content += ll[i] + '\n'
    content += "Your group's total allocation for this period is %.1f kSU. This is calculated as follows:" \
        % (prd_data['groups'][grp]['alloc'] / 1000.0)
    content += '\n'
    content += '\n'
    content += 'Remaining quarterly allocation for astronomy:   %7.1f kSU\n' % (prd_data['su_avail'] / 1000.0)
    content += 'Over/under-subscription factor for period:      %7.1f\n' % (cfg.periods[p]['alloc_frac'])
    content += 'Total allocation for this period:               %7.1f kSU\n' % (prd_data['su_alloc'] / 1000.0)
    content += "Your group's fractional allocation:             %7.1f %%\n" % (prd_data['groups'][grp]['weight_frac'] * 100.0)
    content += "Your group's allocation before penalties:       %7.1f kSU\n" % (prd_data['groups'][grp]['weight_frac'] * prd_data['su_alloc'] / 1000.0)
    content += "Penalty from previous period(s):                %7.1f kSU\n" % (prd_data['groups'][grp]['penalty_old'] / 1000.0)
    content += "Your group's allocation:                        %7.1f kSU\n" % (prd_data['groups'][grp]['alloc'] / 1000.0)
    content += '\n'
    content += "It is the responsibility of all group members to keep track of your group's usage."
    content += " You will receive a warning email when your group's usage exceeds %d percent of this period's allocation." \
        % (cfg.warning_levels[0])
    content += email_end
    
    # Send
    recipients = ''
    for usr in prd_data['groups'][grp]['users'].keys():
        recipients += '%s@umd.edu, ' % (usr)
    recipients = recipients[:-2]
    sendMessage(recipients, subject, content, do_send = do_send, verbose = False, recipient_label = grp)

    return

###################################################################################################

def messageUsageWarning(prd_data, grp, warn_idx, do_send = False):

    zero_alloc = (prd_data['groups'][grp]['alloc'] <= 0.0)
    if not zero_alloc:
        used_frac = prd_data['groups'][grp]['su_usage'] / prd_data['groups'][grp]['alloc']

    content = email_start

    if zero_alloc or (used_frac >= 1.0):
        subject = '%s Warning: allocation exceeded!' % (subject_prefix)
        content += "Your group %s's allocation has been exceeded." % (grp)
    else:
        subject = '%s Warning: %.0f%% of allocation used up' % (subject_prefix, used_frac * 100.0)
        content += "As of today, %.0f%% of your group %s's allocation has been used up." % (used_frac * 100.0, grp)

    content += '\n'
    content += '\n'
    content += "Your group's allocation for this period:     %7.1f kSU\n" % (prd_data['groups'][grp]['alloc'] / 1000.0)
    content += "Used:                                        %7.1f kSU\n" % (prd_data['groups'][grp]['su_usage'] / 1000.0)
    content += "Remaining:                                   %7.1f kSU\n" \
        % (prd_data['groups'][grp]['alloc'] / 1000.0 - prd_data['groups'][grp]['su_usage'] / 1000.0)
    content += '\n'
    content += 'The following table shows the consumption of SUs (and scratch space) by user:'
    content += '\n'
    content += '\n'

    ll = utils.printGroupData(prd_data['groups'], w_tot = prd_data['w_tot'],
                                  only_grp = grp, show_weight = False, do_print = False)
    for i in range(len(ll)):
        if i == 0:
            continue
        content += ll[i] + '\n'
    
    content += "The current allocation period runs from %s to %s." \
        % (prd_data['start_date'].strftime('%Y/%m/%d'), prd_data['end_date'].strftime('%Y/%m/%d'))
    
    if zero_alloc or (used_frac >= 1.0):
        content += " Please stop all running jobs and wait until the next allocation period."
        content += " Any additional usage will be multiplied by a penalty factor and subtracted from your next allocation."
    else:
        content += " Please carefully keep track of your group's usage."
        content += " You will receive another warning email when your group's usage exceeds %d percent of this period's allocation." \
            % (cfg.warning_levels[warn_idx + 1])
    
    content += email_end
    
    # Send
    recipients = ''
    for usr in prd_data['groups'][grp]['users'].keys():
        recipients += '%s@umd.edu, ' % (usr)
    recipients = recipients[:-2]
    sendMessage(recipients, subject, content, do_send = do_send, verbose = False, recipient_label = grp)

    return

###################################################################################################

# This function saves messages to text file and, if do_send is True, attempts to send them via
# email.

def sendMessage(recipients, subject, content, recipient_label = None, 
                do_send = False, safe_mode = False, verbose = False):
    
    do_send = do_send and ((not safe_mode) or (recipient_label == 'diemer-prj'))
        
    if do_send:
        email_dir = cfg.email_dir_sent
    else:
        email_dir = cfg.email_dir_draft
    
    if recipient_label is None:
        recipient_label = recipients
    
    time_str = str(datetime.datetime.now())[:-2]
    time_str = time_str.replace(' ', '_').replace('-', '_').replace(':', '_')
    fname = email_dir + time_str + '_' + recipient_label + '.txt'
    f = open(fname, 'w')
    f.write('From:    %s\n' % (cfg.sender_email))
    f.write('To:      %s\n' % (recipients))
    f.write('Subject: %s\n' % (subject))
    f.write('\n\n')
    f.write(content)
    f.close()
    
    if do_send:

        msg = EmailMessage()
        msg['From'] = cfg.sender_email
        msg['To'] = recipients
        msg['Subject'] = subject
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
