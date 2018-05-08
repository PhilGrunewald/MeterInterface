Configuring Devices
===================


Prepare root/flash
------------------

Install packages (.apk)

- root
- Insecure
- Flashify
- AppRemover
- AppHider
- AppLock
- ButtonRemap
- Tasker

Copy 

- recovery.img

Settings

- Lock settings
- Select Lock screen
- None

Open "Uninstall" (AppRemover)

- System app
- delete about 43 apps

- User app > remove:
- MyEE
- SuperBattery
- Twitter
- WhatsApp

Open "AppHider"

- hide all but the downloaded apps
- hide Settings
- Pin Code -> Never Show

Open "Tasker"

- Profile > [+] > Event > Display > Off
- [+] task
- App > Launch > Meter

Open "Button Remapper"

- enable service > OK
- [+] Short and long press
- BACK > do nothing
- Home > do nothing

Open "AppLock"

- lock all but Meter

Create Backup
-------------

.. code:: bash

    adb reboot recovery

- BACKUP
- tick all
- > Options > enable compression
- swipe to backup (392s)

Copy backup folder to local machine

.. code:: bash

    adb pull /sdcard/TWRP ./TWRP


eMeter setup
------------

Requires: Pixi 3 - Android 4.2.2

Assume device is rooted, Insecured

From bash with USB connected: 

.. code:: bash

    adb push recovery.img /sdcard/recovery.img
    adb install Flashify.apk
    adb push ./TWRP /sdcard/TWRP

Open "Flashify"

- OK, OK, OK
- Recovery image
- select /sdcard/recovery.img
- Flashing (2 min)

.. code:: bash

    adb reboot recovery

- RESTORE , select, swipe

.. code:: bash

    adb shell
    mkdir /sdcard/METER/
    exit
    adb push id.txt /sdcard/METER

aMeter setup
------------

Requires: Pixi 4 - Android 6

Start device (Skip or ignore of offered options)

> Settings > About Phone

- tap `Build Number` 5 times to enable Developer options

> Settings > Developer Options

- enable `OEM unlocking` (allow bootloader unlock)
- enable `USB debugging` (allow to connect via USB)

- Connect device via USB
- Tick `trust this device` on device
- on computer, open terminal in the folder where recoverypixi4.img resides (this file can be found in this repository under `flash_aMeter/`)

*NOTE* you may need to reconnect the USB cable between each step

.. code:: bash

    adb reboot bootloader
    fastboot oem unlock

Confirm with <VOL UP>

.. code:: bash

    fastboot flash recovery recoverypixi4.img
    fastboot format userdata

- remove the battery (tough but quick way to switch off)
- insert the SD card with the backup (see `flash_aMeter/TWRP/`)
- insert battery
- start phone with `Power` + `VOL UK` (this is equivalent to `fastboot reboot`)
- select <Restore>
- select <Storage location>
- select <SD card>
- pick directory and swipe to restore
- when done, remove battery and SD card
- insert battery and start with `Power` button

Set Time
^^^^^^^^

Use this command to set the time (also available in Meter Interface > Menu > Device > Set time)

.. code:: bash

    'adb shell date -s `date "+%Y%m%d.%H%M%S"`'

- on device, go to > Settings > Time and Date

It may be necessary to set the time manually to the right time zone first.

To make the time 'stick' it is necessary to manually confirm it. For this open either `time` or `date` and tap `OK`.

