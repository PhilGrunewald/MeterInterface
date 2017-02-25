Configuring a Master Device
===========================


Prepare phone for root/flash
----------------------------

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

`adb reboot recovery`

- BACKUP
- tick all
- > Options > enable compression
- swipe to backup (392s)

Copy backup folder to local machine

`adb pull /sdcard/TWRP ./TWRP`


Setting up a eMeter (Pixi 3 - Android 4.2.2)
--------------------------------------------

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

Setting up an aMeter (Pixi 4 - Android 6)
-----------------------------------------

Start device > Settings 
--> developer options 
--> OEM unlocking (allow bootloader unlock)

From shell with USB connected (you may need to reconnect the USB cable between each step):

.. code:: bash

    adb reboot bootloader
    fastboot oem unlock

Confirm with <VOL UP>

.. code:: bash

    fastboot flash recovery recoverypixi4.img
    fastboot format userdata
    fastboot reboot

