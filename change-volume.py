#!/usr/bin/python3
#
# Authors:
#   1. Garrett Holbrook - 27 August 2015
#   2. Abdulbaki Eren Bilir - 14 July 2020
#
# Changes the system volume through amixer and then
# makes a dbus method call to the gnome shell to get the
# gnome volume OSD (On Screen Display)
#
# Usage: 
# python3 volume-change.py increase <percentage to increase>
# python3 volume-change.py decrease <percentage to decrease>
# python3 volume-change.py increase toggle
#
# Requires: python3 and python-dbus (on Arch) or python3-dbus
#           (on Debian) or equivalent

import dbus
import sys
from subprocess import getoutput, call

# Getting the dbus interface to communicate with gnome's OSD
session_bus = dbus.SessionBus()
proxy = session_bus.get_object('org.gnome.Shell', '/org/gnome/Shell')
interface = dbus.Interface(proxy, 'org.gnome.Shell')

# Interpreting how to affect the volume and by what percentage and
# then creating a bash command that will reduce the stdout to the
# new percentage volume. Vol = volume
vol_action = sys.argv[1]

comm_get_mute_status = 'amixer -D pulse get Master | grep -oP "(?<=\[)(on|off)(?=\])"'

# Get the volumes for all the channels
comm_get_volume = 'amixer -D pulse get Master | grep -oP "\[\d*%\]" | sed s:[][%]::g'
vol_percentages = list(map(int, getoutput(comm_get_volume).split()))
    
# Average them into a single value
vol_percent = int(sum(vol_percentages)/len(vol_percentages)) 

# Add/subtract the value of volume, limit it to 0-100
if vol_action == 'toggle':
    mute_status = getoutput(comm_get_mute_status).split()[0]
    if mute_status == 'on':
        toggle = 'mute'
    else:
        toggle = 'unmute'
    command = 'amixer -qD pulse set Master ' + toggle
else:
    vol_percent_change = int(sys.argv[2])
    if vol_action == 'increase':
        # If increasing, unmute the audio
        call('amixer -qD pulse set Master unmute', shell=True)
        vol_percent = min(100, (vol_percent + vol_percent_change))
    elif vol_action == 'decrease':
        vol_percent = max(0, (vol_percent - vol_percent_change))
    
    command = 'amixer -qD pulse sset Master ' + str(vol_percent) + '%'

# Run the specified command
call(command, shell=True)

# If volume is 0% then mute
if vol_percent == 0:
	call('amixer -qD pulse set Master mute', shell=True)

# Determining which logo to use
logo = 'audio-volume-'
mute_status = getoutput(comm_get_mute_status).split()[0]
if mute_status == 'off':
    logo += 'muted'
elif vol_percent < 30:
    logo += 'low'
elif vol_percent < 70:
    logo += 'medium'
else:
    logo += 'high'
logo += '-symbolic'

# Make the dbus method call
interface.ShowOSD({"icon":logo, "level":vol_percent/100, "label":f"{vol_percent}%"})