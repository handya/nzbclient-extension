#!/usr/bin/python3

###########################################################################
### NZBGET QUEUE/POST-PROCESSING SCRIPT
### QUEUE EVENTS: NZB_ADDED, NZB_DOWNLOADED, NZB_DELETED

# Official NZBClient Queue/Post-Processing script for sending push notifications.
#
# This script sends a NZBClient notification when an NZB is added/removed from your queue or the job is finished.
#
# Script Version 1.1.0
#
#
# NOTE: This script requires Python to be installed on your system and a minimum app version of 2023.3.

##############################################################################
### OPTIONS                                                                ###

# NZBClient user key
#
# To find your User Key open NZBClient then Settings tab -> NZBClient Ultra -> Notifications.
#
#UserKey=

# Application token/key
#
# To find your App Token open NZBClient then Settings tab -> NZBClient Ultra -> Notifications.
#
#AppToken=

# Enable Message Encryption (yes, no).
# 
# (Optional)
#EncryptionEnabled=no

# Encryption Private Key
#
# Key can be generated in NZBClient Settings tab -> NZBClient Ultra -> Notifications.
#
# (Optional)
#PrivateKey=

# Send NZB added notification (yes, no).
#
# Send NZB added notification
#
#
# (queue only)
#NZBAdded=yes

# Priority of NZB's added queue notification (low, normal, high).
#
# Low priority (quiet notification)
#
# Normal priority
#
# High priority (Sends notification as time sensitive)
#
#
# (queue only)
#AddedPriority=normal

# Send NZB downloaded notification (yes, no).
#
# Send NZB downloaded notification (not need of using post-processing script)
#
#
# (queue only)
#NZBDownloaded=no

# Priority of NZB downloaded notification (low, normal, high).
#
# Low priority (quiet notification)
#
# Normal priority
#
# High priority (Sends notification as time sensitive)
#
#
# (queue only)
#DownloadedPriority=normal

# Send NZB deleted notification (yes, no).
#
# Send NZB deleted notification.
#
#
# (queue only)
#NZBDeleted=yes

# Priority of deleted notification (low, normal, high).
#
# Low priority (quiet notification)
#
# Normal priority
#
# High priority (Sends notification as time sensitive)
#
#
# (queue only)
#DeletedPriority=normal

# Send success notification (yes, no).
#
# Send the success notification
#
#
# (post-processing only)
#NotifySuccess=yes

# Priority of success notification (low, normal, high).
#
# Low priority (quiet notification)
#
# Normal priority
#
# High priority (Sends notification as time sensitive)
#
#
# (post-processing only)
#SuccessPriority=normal

# Send failure notification (yes, no).
#
# Send the failure notification
#
#
# (post-processing only)
#NotifyFailure=yes

# Priority of failure notification (low, normal, high).
#
# Low priority (quiet notification)
#
# Normal priority
#
# High priority (Sends notification as time sensitive)
#
#
# (post-processing only)
#FailurePriority=normal

# Append Par-Status and Unpack-Status to the message (yes, no).
#
# Add the Par and Unpack status.
#
#
# (post-processing only)
#AppendParUnpack=no

# Append list of files to the message (yes, no).
#
# Add the list of downloaded files (the content of destination directory).
#
#
# (post-processing only)
#FileList=no

# You can test your configuration here.
#
# If tests fail, try saving and reloading NZBGet and trying again.
#TestSettings@Test Push Notifications

### NZBGET QUEUE/POST-PROCESSING SCRIPT
###########################################################################

import os
import sys
import http.client
import urllib

# Exit codes used by NZBGet
POSTPROCESS_SUCCESS = 93
POSTPROCESS_ERROR = 94
POSTPROCESS_NONE = 95

# Check if the script is called from NZBGet 11.0 or later
if 'NZBOP_SCRIPTDIR' not in os.environ:
    print('*** NZBGet post-processing script ***')
    print('This script is supposed to be called from NZBGet (11.0 or later).')
    sys.exit(POSTPROCESS_ERROR)

required_options = ('NZBPO_USERKEY', 'NZBPO_APPTOKEN')
for opt_name in required_options:
    if opt_name not in os.environ:
        print('[ERROR] Option %s is missing in the configuration file. Please check script settings.' % opt_name[6:])
        sys.exit(POSTPROCESS_ERROR)

print('[DETAIL] Script successfully started')
sys.stdout.flush()

user_key = os.environ['NZBPO_USERKEY']
app_token = os.environ['NZBPO_APPTOKEN']
command = os.environ.get('NZBCP_COMMAND')

if os.environ['NZBPO_ENCRYPTIONENABLED'] == 'yes' and os.environ['NZBPO_PRIVATEKEY'] is not None:
    from cryptography.fernet import Fernet

# Check PAR and unpack status for errors and set message
# - NZBPP_PARSTATUS:
#   0 = not checked (par-check is disabled or NZB-file does not contain par-files)
#   1 = checked and failed to repair
#   2 = checked and successfully repaired
#   3 = checked and can be repaired but repair is disabled
#   4 = par-check needed but skipped (option ParCheck=manual)
#
# - NZBPP_UNPACKSTATUS:
#   0 = unpack is disabled or was skipped due to NZB-file properties or due to errors during par-check
#   1 = unpack failed
#   2 = unpack successful
success = False

def encrypt_string(plaintext, password):
    return Fernet(password).encrypt(plaintext.encode())

def send_push_notification(title, message, url=None, priority=None):
    # Check if a parameter is None (not provided) and assign a default value if needed
    if url is None:
        url = ""
    if priority is None:
        priority = "0"

    message = message.replace(".", " ")

    is_encrypted = False

    if os.environ['NZBPO_ENCRYPTIONENABLED'] == 'yes' and os.environ['NZBPO_PRIVATEKEY'] is not None:
        private_key = os.environ['NZBPO_PRIVATEKEY']
        message = encrypt_string(message, private_key)
        is_encrypted = True

    nzb_id = os.environ.get("NZBNA_NZBID") or os.environ.get("NZBPP_NZBID") or ""

    print('[DETAIL] Sending Push notification')

    sys.stdout.flush()
    try:
        conn = http.client.HTTPSConnection("api.nzbclient.app:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": app_token,
                         "user": user_key,
                         "url": url,
                         "priority": priority,
                         "isEncrypted": is_encrypted,
                         "title": title,
                         "message": message,
                         "app": "nzbget",
                         "nzbID": nzb_id,
                     }), {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()
        sys.exit(POSTPROCESS_SUCCESS)
    except Exception as err:
        print('[ERROR] %s' % err)
        sys.exit(POSTPROCESS_ERROR)

def start_post_processing_script():
    global success
    
    print('[DETAIL] Script starting post-processing...')

    if os.environ['NZBPP_TOTALSTATUS'] == 'FAILURE':
        title = 'Download Failed'
        message = 'Download of "%s" has failed: %s' % (os.environ['NZBPP_NZBNAME'], os.environ['NZBPP_STATUS'])
    elif os.environ['NZBPP_TOTALSTATUS'] == 'WARNING':
        title = 'Action Needed'
        message = 'User intervention required for download of "%s": %s' % (os.environ['NZBPP_NZBNAME'], os.environ['NZBPP_STATUS'])
    else:
        title = 'Download Successful'
        message = 'Download of "%s" has successfully completed: %s' % (os.environ['NZBPP_NZBNAME'], os.environ['NZBPP_STATUS'])
        success = True

    # Set success priority
    success_priority_map = {'low': "-1", 'normal': "0", 'high': "1"}
    success_priority = success_priority_map.get(os.environ['NZBPO_SUCCESSPRIORITY'], "0")

    # Set failure priority
    failure_priority_map = {'low': "-1", 'normal': "0", 'high': "1"}
    failure_priority = failure_priority_map.get(os.environ['NZBPO_FAILUREPRIORITY'], "0")

    # Set priority to success or failure priority
    priority = success_priority if success else failure_priority

    # Add par and unpack status to the message
    if os.environ['NZBPO_APPENDPARUNPACK'] == 'yes':
        par_status = { '0': 'skipped', '1': 'failed', '2': 'repaired', '3': 'repairable', '4': 'manual' }
        message += '\nPar-Status: %s' % par_status[os.environ['NZBPP_PARSTATUS']]

        unpack_status = { '0': 'skipped', '1': 'failed', '2': 'success' }
        message += '\nUnpack-Status: %s' % unpack_status[os.environ['NZBPP_UNPACKSTATUS']]

    # Add a list of downloaded files to the message
    if os.environ['NZBPO_FILELIST'] == 'yes':
        message += '\n\nFiles:'
        for dirname, dirnames, filenames in os.walk(os.environ['NZBPP_DIRECTORY']):
            for filename in filenames:
                message += '\n' + os.path.join(dirname, filename)[len(os.environ['NZBPP_DIRECTORY']) + 1:]

    send_message = False
    if os.environ['NZBPO_NOTIFYSUCCESS'] == 'yes' and success:
        send_message = True
    elif os.environ['NZBPO_NOTIFYFAILURE'] == 'yes' and not success:
        send_message = True

    if "NZBPP_NZBID" in os.environ:
        url = 'nzbclient://history?nzbid=' + os.environ['NZBPP_NZBID']
    else:
        url = 'nzbclient://history'

    if send_message:
        # Send message
        print('[DETAIL] Sending Push notification')
        send_push_notification(title=title, message=message, url=url, priority=priority)
    else:
        # Send message
        print('[DETAIL] Skipping Push notification')
        sys.stdout.flush()

        # All OK, returning exit status 'POSTPROCESS_NONE' (int <95>) to let NZBGet know
        # that our script has successfully completed without action.
        sys.exit(POSTPROCESS_NONE)

def start_queue_script():
    print('[DETAIL] Script starting queue...')
    nzbna_event = os.environ.get('NZBNA_EVENT')
    if nzbna_event not in ['NZB_ADDED', 'NZB_DOWNLOADED', 'NZB_DELETED']:
        sys.exit(0)

    if os.environ['NZBPO_NZBADDED'] == 'yes' and nzbna_event == 'NZB_ADDED':
        # Set added priority
        added_priority_map = {'low': "-1", 'normal': "0", 'high': "1"}
        priority = added_priority_map.get(os.environ['NZBPO_ADDEDPRIORITY'], "0")

        if "NZBNA_NZBID" in os.environ:
            url = 'nzbclient://downloads?nzbid=' + os.environ['NZBNA_NZBID']
        else:
            url = 'nzbclient://downloads'

        send_push_notification(title='NZB Added To Queue', message=os.environ['NZBNA_NZBNAME'], url=url, priority=priority)

    elif os.environ['NZBPO_NZBDOWNLOADED'] == 'yes' and nzbna_event == 'NZB_DOWNLOADED':
        # Set downloaded priority
        downloaded_priority_map = {'low': "-1", 'normal': "0", 'high': "1"}
        priority = downloaded_priority_map.get(os.environ['NZBPO_DOWNLOADEDPRIORITY'], "0")

        if "NZBNA_NZBID" in os.environ:
            url = 'nzbclient://history?nzbid=' + os.environ['NZBNA_NZBID']
        else:
            url = 'nzbclient://history'

        send_push_notification(title='NZB Downloaded', message=os.environ['NZBNA_NZBNAME'], url=url, priority=priority)

    elif os.environ['NZBPO_NZBDELETED'] == 'yes' and nzbna_event == 'NZB_DELETED':
        if "NZBNA_NZBID" in os.environ:
            url = 'nzbclient://history?nzbid=' + os.environ['NZBNA_NZBID']
        else:
            url = 'nzbclient://history'
        # Set failure priority
        deleted_priority_map = {'low': "-1", 'normal': "0", 'high': "1"}
        priority = deleted_priority_map.get(os.environ['NZBPO_DELETEDPRIORITY'], "0")

        delete_status_map = {
            'MANUAL': 'NZB Manually Deleted',
            'DUPE': 'Duplicate NZB Deleted',
            'BAD': 'Bad NZB Deleted',
            'GOOD': 'Good NZB Deleted',
            'COPY': 'NZB Copy Deleted',
            'SCAN': 'NZB Scan Deleted'
        }
        title = delete_status_map.get(os.environ['NZBNA_DELETESTATUS'], 'Unknown Deletion')

        send_push_notification(title=title, message=os.environ['NZBNA_NZBNAME'], url=url, priority=priority)

def test_settings():
    """
    Execute the TestSettings Test Action
    """
    print('[DETAIL] Execute the TestSettings Test Action')
    send_push_notification(title='Test Notification', message='Success! Push Notifications are working.', url='nzbclient://test')

if "NZBNA_EVENT" in os.environ:
    start_queue_script()
elif "NZBPP_TOTALSTATUS" in os.environ:
    start_post_processing_script()
elif command == 'TestSettings':
    test_settings()