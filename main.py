#
# Official NZBClient Queue/Post-Processing script for sending push notifications.
#
# Copyright (C) 2025 Digital Tools Ltd <andrew@digitaltools.nz>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import os
import sys
import http.client
import urllib

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    Fernet = None
    CRYPTO_AVAILABLE = False


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
        print(f'[ERROR] Option {opt_name[6:]} is missing in the configuration file. Please check script settings.')
        sys.exit(POSTPROCESS_ERROR)

print('[DETAIL] Script successfully started')
sys.stdout.flush()

user_key = os.environ['NZBPO_USERKEY']
app_token = os.environ['NZBPO_APPTOKEN']
command = os.environ.get('NZBCP_COMMAND')

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

    if os.environ['NZBPO_ENCRYPTIONENABLED'] == 'yes' and os.environ['NZBPO_PRIVATEKEY'] is not None and CRYPTO_AVAILABLE:
        private_key = os.environ['NZBPO_PRIVATEKEY']
        message = encrypt_string(message, private_key)
        is_encrypted = True

    nzb_id = os.environ.get("NZBNA_NZBID") or os.environ.get("NZBPP_NZBID") or ""

    print('[DETAIL] Sending Push notification')

    sys.stdout.flush()
    try:
        body = urllib.parse.urlencode({
            "token": app_token,
            "user": user_key,
            "url": url,
            "priority": priority,
            "isEncrypted": is_encrypted,
            "title": title,
            "message": message,
            "app": "nzbget",
            "nzbID": nzb_id,
        })

        conn = http.client.HTTPSConnection("api.nzbclient.app:443")
        conn.request("POST", "/1/messages.json", body, {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()

        print('[DETAIL] Sent Push notification')

        sys.exit(POSTPROCESS_SUCCESS)
    except Exception as err:
        print(f'[ERROR] {err}')
        sys.exit(POSTPROCESS_ERROR)

def start_post_processing_script():
    global success
    
    print('[DETAIL] Script starting post-processing...')

    if os.environ['NZBPP_TOTALSTATUS'] == 'FAILURE':
        title = 'Download Failed'
        message = f'Download of "{os.environ["NZBPP_NZBNAME"]}" has failed: {os.environ["NZBPP_STATUS"]}'
    elif os.environ['NZBPP_TOTALSTATUS'] == 'WARNING':
        title = 'Action Needed'
        message = f'User intervention required for download of "{os.environ["NZBPP_NZBNAME"]}": {os.environ["NZBPP_STATUS"]}'
    else:
        title = 'Download Successful'
        message = f'Download of "{os.environ["NZBPP_NZBNAME"]}" has successfully completed: {os.environ["NZBPP_STATUS"]}'
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
        message += f'\nPar-Status: {par_status[os.environ["NZBPP_PARSTATUS"]]}'

        unpack_status = { '0': 'skipped', '1': 'failed', '2': 'success' }
        message += f'\nUnpack-Status: {unpack_status[os.environ["NZBPP_UNPACKSTATUS"]]}'

    # Add a list of downloaded files to the message
    if os.environ['NZBPO_FILELIST'] == 'yes':
        message += '\n\nFiles:'
        for dirname, _, filenames in os.walk(os.environ['NZBPP_DIRECTORY']):
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
    print('[DETAIL] Execute the TestSettings Test Action')
    send_push_notification(
        title='Test Notification',
        message='Success! Push Notifications are working.',
        url='nzbclient://test'
    )


if "NZBNA_EVENT" in os.environ:
    start_queue_script()
elif "NZBPP_TOTALSTATUS" in os.environ:
    start_post_processing_script()
elif command == 'Test':
    test_settings()