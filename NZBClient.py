#!/usr/bin/python3

###########################################################################
### NZBGET QUEUE/POST-PROCESSING SCRIPT
### QUEUE EVENTS: NZB_ADDED, NZB_DOWNLOADED, NZB_DELETED

# Official NZBClient Queue/Post-Processing script for sending push notifications.
#
# This script sends a NZBClient notification when an NZB is added/removed from your queue or the job is finished.
#
# Script Version 1.0.0
#
#
# NOTE: This script requires Python to be installed on your system.

##############################################################################
### OPTIONS                                                                ###

# NZBClient user key
#UserKey=

# Application token/key
#AppToken=

# Enable Message Encryption (yes, no).
#
# (Optional)
#EncryptionEnabled=no

# Encryption Private Key
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
POSTPROCESS_SUCCESS=93
POSTPROCESS_ERROR=94
POSTPROCESS_NONE=95

# Check if the script is called from nzbget 11.0 or later
if not 'NZBOP_SCRIPTDIR' in os.environ:
    print('*** NZBGet post-processing script ***')
    print('This script is supposed to be called from nzbget (11.0 or later).')
    sys.exit(POSTPROCESS_ERROR)

required_options = ('NZBPO_USERKEY', 'NZBPO_APPTOKEN')
for optname in required_options:
    if (not optname in os.environ):
        print('[ERROR] Option %s is missing in configuration file. Please check script settings' % optname[6:])
        sys.exit(POSTPROCESS_ERROR)

print('[DETAIL] Script successfully started')
sys.stdout.flush()

userkey = os.environ['NZBPO_USERKEY']
apptoken = os.environ['NZBPO_APPTOKEN']
device = '' #os.environ['NZBPO_DEVICE']
command = os.environ.get('NZBCP_COMMAND')
isEncrypted = os.environ['NZBPO_ENCRYPTIONENABLED'] == 'yes'

if (isEncrypted and os.environ['NZBPO_PRIVATEKEY'] is not None):
    from cryptography.fernet import Fernet


# Check par and unpack status for errors and set message

#  NZBPP_PARSTATUS    - result of par-check:
#                       0 = not checked: par-check is disabled or nzb-file does
#                           not contain any par-files;
#                       1 = checked and failed to repair;
#                       2 = checked and successfully repaired;
#                       3 = checked and can be repaired but repair is disabled.
#                       4 = par-check needed but skipped (option ParCheck=manual);

#  NZBPP_UNPACKSTATUS - result of unpack:
#                       0 = unpack is disabled or was skipped due to nzb-file
#                           properties or due to errors during par-check;
#                       1 = unpack failed;
#                       2 = unpack successful.

success=False

def encrypt_string(plaintext, password):
    return Fernet(password).encrypt(plaintext.encode())

def sendPushNotification(title, message, url=None, sound=None, priority=None):
    # Check if a parameter is None (not provided) and assign a default value if needed
    if url is None:
        url = ""
    if sound is None:
        sound = ""
    if priority is None:
        priority = "0"

    if (isEncrypted and os.environ['NZBPO_PRIVATEKEY'] is not None):
        privateKey = os.environ['NZBPO_PRIVATEKEY']
        message = encrypt_string(message, privateKey)

    print('[DETAIL] Sending Push notification')
    sys.stdout.flush()
    try:
        conn = http.client.HTTPSConnection("api.nzbclient.app:443")
        conn.request("POST", "/1/messages.json",
          urllib.parse.urlencode({
            "token": apptoken,
            "user": userkey,
            "device": device,
            "url": url,
            "sound": sound,
            "priority": priority,
            "isEncrypted": isEncrypted,
            "title": title,
            "message": message,
          }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()
        sys.exit(POSTPROCESS_SUCCESS)
    except Exception as err:
        print('[ERROR] %s' % err)
        sys.exit(POSTPROCESS_ERROR)


def startPostProcessingScript():
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
        success=True

    #Set requested success or failure sound
    if not success and 'NZBPO_FAILURESOUND' in os.environ:
        sound = os.environ['NZBPO_FAILURESOUND']
    elif success and 'NZBPO_SUCCESSSOUND' in os.environ:
        sound = os.environ['NZBPO_SUCCESSSOUND']
    else:
        sound=""

    #Set success priority
    if os.environ['NZBPO_SUCCESSPRIORITY'] == 'low':
        successpriority = "-1"
    elif os.environ['NZBPO_SUCCESSPRIORITY'] == 'normal':
        successpriority = "0"
    elif os.environ['NZBPO_SUCCESSPRIORITY'] == 'high':
        successpriority = "1"

    #set failure priority
    if os.environ['NZBPO_FAILUREPRIORITY'] == 'low':
        failurepriority = "-1"
    elif os.environ['NZBPO_FAILUREPRIORITY'] == 'normal':
        failurepriority = "0"
    elif os.environ['NZBPO_FAILUREPRIORITY'] == 'high':
        failurepriority = "1"

    #set priority to success or failure priority
    if success:
        priority = successpriority
    else:
        priority = failurepriority

    # add par and unpack status to the message
    if os.environ['NZBPO_APPENDPARUNPACK'] == 'yes':
        parStatus = { '0': 'skipped', '1': 'failed', '2': 'repaired', '3': 'repairable', '4': 'manual' }
        message += '\nPar-Status: %s' % parStatus[os.environ['NZBPP_PARSTATUS']]

        unpackStatus = { '0': 'skipped', '1': 'failed', '2': 'success' }
        message += '\nUnpack-Status: %s' % unpackStatus[os.environ['NZBPP_UNPACKSTATUS']]

    # add list of downloaded files to the message
    if os.environ['NZBPO_FILELIST'] == 'yes':
        message += '\n\nFiles:'
        for dirname, dirnames, filenames in os.walk(os.environ['NZBPP_DIRECTORY']):
            for filename in filenames:
                message += '\n' + os.path.join(dirname, filename)[len(os.environ['NZBPP_DIRECTORY']) + 1:]

    sendMessage = False
    if os.environ['NZBPO_NOTIFYSUCCESS'] == 'yes' and success:
        sendMessage = True
    elif os.environ['NZBPO_NOTIFYFAILURE'] == 'yes' and not success:
        sendMessage = True

    if "NZBPP_NZBID" in os.environ:
        url = 'nzbclient://history/' + os.environ['NZBPP_NZBID']
    else:
        url = 'nzbclient://history'

    if sendMessage:
        # Send message
        print('[DETAIL] Sending Push notification')
        sendPushNotification(title=title, message=message, url=url, sound=sound, priority=priority)
    else:
        # Send message
        print('[DETAIL] Skipping Push notification')
        sys.stdout.flush()

        # All OK, returning exit status 'POSTPROCESS_NONE' (int <95>) to let NZBGet know
        # that our script has successfully completed without action.
        sys.exit(POSTPROCESS_NONE)

def startQueueScript():
    print('[DETAIL] Script starting queue...')
    if os.environ.get('NZBNA_EVENT') not in ['NZB_ADDED', 'NZB_DOWNLOADED', 'NZB_DELETED']:
        sys.exit(0)

    if os.environ['NZBPO_NZBADDED'] == 'yes' and os.environ['NZBNA_EVENT'] == 'NZB_ADDED':
        #set added priority
        if os.environ['NZBPO_ADDEDPRIORITY'] == 'low':
            priority = "-1"
        elif os.environ['NZBPO_ADDEDPRIORITY'] == 'normal':
            priority = "0"
        elif os.environ['NZBPO_ADDEDPRIORITY'] == 'high':
            priority = "1"

        if "NZBNA_NZBID" in os.environ:
            url = 'nzbclient://downloads/' + os.environ['NZBNA_NZBID']
        else:
            url = 'nzbclient://downloads'
        sendPushNotification(title='NZB Added To Queue', message=os.environ['NZBNA_NZBNAME'], url=url, priority=priority)

    elif os.environ['NZBPO_NZBDOWNLOADED'] == 'yes' and os.environ['NZBNA_EVENT'] == 'NZB_DOWNLOADED':
        #set downloaded priority
        if os.environ['NZBPO_DOWNLOADEDPRIORITY'] == 'low':
            priority = "-1"
        elif os.environ['NZBPO_DOWNLOADEDPRIORITY'] == 'normal':
            priority = "0"
        elif os.environ['NZBPO_DOWNLOADEDPRIORITY'] == 'high':
            priority = "1"

        if "NZBNA_NZBID" in os.environ:
            url = 'nzbclient://history/' + os.environ['NZBNA_NZBID']
        else:
            url = 'nzbclient://history'
        sendPushNotification(title='NZB Downloaded', message=os.environ['NZBNA_NZBNAME'], url=url, priority=priority)

    elif os.environ['NZBPO_NZBDELETED'] == 'yes' and os.environ['NZBNA_EVENT'] == 'NZB_DELETED':
        if "NZBNA_NZBID" in os.environ:
            url = 'nzbclient://history/' + os.environ['NZBNA_NZBID']
        else:
            url = 'nzbclient://history'
        #set failure priority
        if os.environ['NZBPO_DELETEDPRIORITY'] == 'low':
            priority = "-1"
        elif os.environ['NZBPO_DELETEDPRIORITY'] == 'normal':
            priority = "0"
        elif os.environ['NZBPO_DELETEDPRIORITY'] == 'high':
            priority = "1"

        if os.environ['NZBNA_DELETESTATUS'] == 'MANUAL':
            title = 'NZB Manually Deleted'
        elif os.environ['NZBNA_DELETESTATUS'] == 'DUPE':
            title = 'Duplicate NZB Deleted'
        elif os.environ['NZBNA_DELETESTATUS'] == 'BAD':
            title = 'Bad NZB Deleted'
        elif os.environ['NZBNA_DELETESTATUS'] == 'GOOD':
            title = 'Good NZB Deleted'
        elif os.environ['NZBNA_DELETESTATUS'] == 'COPY':
            title = 'NZB Copy Deleted'
        elif os.environ['NZBNA_DELETESTATUS'] == 'SCAN':
            title = 'NZB Scan Deleted'

        sendPushNotification(title=title, message=os.environ['NZBNA_NZBNAME'], url=url, priority=priority)

def testsettings():
    """
    Execute the TestSettings Test Action
    """
    print('[DETAIL] Execute the TestSettings Test Action')
    sendPushNotification(title='Test Notification', message='Success! Push Notifications are working.', url='nzbclient://test')

if "NZBNA_EVENT" in os.environ:
    startQueueScript()
elif "NZBPP_TOTALSTATUS" in os.environ:
    startPostProcessingScript()
elif command == 'TestSettings':
    testsettings()

