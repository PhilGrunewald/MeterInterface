% Configure aMeter 


Master
======

Prepare phone for root/flash
----------------------------

Install

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

NEW PHONE
=========

assume rooted, Insecured

`adb push recovery.img /sdcard/recovery.img`

`adb install Flashify.apk`
`adb push ./TWRP /sdcard/TWRP`

Open "Flashify"

- OK, OK, OK
- Recovery image
- select /sdcard/recovery.img
- Flashing (some time)


`adb reboot recovery`

- RESTORE , select, swipe

- create /sdcard/METER/
- push id.txt
