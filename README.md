# NZBClient Notifier

Official post-processing and queue script for sending push notifications to [NZBClient](https://nzbclient.app) app on iOS. Works with NZBGet **v23+**.

## Features

* Sends notifications when NZBs are **added, deleted, or finished** in your queue.
* Supports **success** and **failure** notifications during post-processing.
* Optional **encryption** of notification messages for enhanced privacy.
* Configurable notification **priority** (quiet, normal, or time-sensitive).

## Requirements

* Python **3.8+**
* NZBClient app installed on your iPhone or iPad
* **Ultra subscription** in NZBClient
* The following NZBClient credentials:

  * **User Key** (found in NZBClient → Settings → NZBClient Ultra → Notifications)
  * **App Token** (found in NZBClient → Settings → NZBClient Ultra → Notifications)

If you enable encryption, you must also provide:

* **Private Key** (can be generated in NZBClient → Settings → NZBClient Ultra → Notifications)

More info about encryption can be found [here](https://nzbclient.app/faq/encryption)

## NZBGet Versions

* **v23+**: Use the latest release of this extension
* **v22 or below**: Download the [legacy v1.0 version](https://github.com/handya/nzbclient-script/tree/legacy) or from [NZBClient.app](https://nzbclient.app/download)

## Installation

1. Download in the NZBGet Extension Manager
2. Add setup extension by adding:
   * Your **User Key**
   * Your **App Token**
   * Optionally enable **encryption** and paste your Private Key
    These can be found in the app → Settings → NZBClient Ultra → Notifications
4. Save settings and restart NZBGet.

## Example Usage

Once configured, the script will automatically send push notifications for queue events and post-processing results. For example:

* **Download Successful** → "Download of Example.Movie completed successfully."
* **Download Failed** → "Download of Example.Movie has failed."

## License

GNU General Public License (GPL)
