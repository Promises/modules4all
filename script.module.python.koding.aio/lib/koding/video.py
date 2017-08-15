# -*- coding: utf-8 -*-

# script.module.python.koding.aio
# Python Koding AIO (c) by whufclee (info@totalrevolution.tv)

# Python Koding AIO is licensed under a
# Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License.

# You should have received a copy of the license along with this
# work. If not, see http://creativecommons.org/licenses/by-nc-nd/4.0.

# IMPORTANT: If you choose to use the special noobsandnerds features which hook into their server
# please make sure you give approptiate credit in your add-on description (noobsandnerds.com)
# 
# Please make sure you've read and understood the license, this code can NOT be used commercially
# and it can NOT be modified and redistributed. If you're found to be in breach of this license
# then any affected add-ons will be blacklisted and will not be able to work on the same system
# as any other add-ons which use this code. Thank you for your cooperation.

import os
import shutil
import xbmc
import xbmcgui

from __init__    import dolog
from guitools    import Show_Busy
from systemtools import Last_Error

dp            = xbmcgui.DialogProgress()
check_started = xbmc.translatePath('special://profile/addon_data/script.module.python.koding.aio/temp/playback_in_progress')
#----------------------------------------------------------------    
# TUTORIAL #
def Check_Playback(ignore_dp=False,timeout=10):
    """
This function will return true or false based on video playback. Simply start a stream
(whether via an add-on, direct link to URL or local storage doesn't matter), the code will
then work out if playback is successful. This uses a number of checks and should take into
account all potential glitches which can occur during playback. The return should happen
within a second or two of playback being successful (or not).

CODE: Check_Playback()

AVAILABLE PARAMS:
    
    ignore_dp  -  By default this is set to True but if set to False
    this will ignore the DialogProgress window. If you use a DP while
    waiting for the stream to start then you'll want to set this True.
    Please bare in mind the reason this check is in place and enabled
    by default is because some streams do bring up a DialogProgress
    when initiated (such as f4m proxy links) and disabling this check
    in those circumstances can cause false positives.

    timeout  -  This is the amount of time you want to allow for playback
    to start before sending back a response of False. Please note if
    ignore_dp is set to True then it will also add a potential 10s extra
    to this amount if a DialogProgress window is open. The default setting
    for this is 10s.

EXAMPLE CODE:
xbmc.Player().play('http://totalrevolution.tv/videos/python_koding/Browse_To_Folder.mov')
isplaying = koding.Check_Playback()
if isplaying:
    dialog.ok('PLAYBACK SUCCESSFUL','Congratulations, playback was successful')
    xbmc.Player().stop()
else:
    dialog.ok('PLAYBACK FAILED','Sorry, playback failed :(')
~"""    
    if not ignore_dp:
        isdialog = True
        counter = 1

# Check if the progress window is active and wait for playback
        while isdialog:
            if xbmc.getCondVisibility('Window.IsActive(progressdialog)'):
                if dp.iscanceled():
                    dp.close()
                    break
            dolog('### Current Window: %s' % xbmc.getInfoLabel('System.CurrentWindow'))
            dolog('### Current XML: %s' % xbmc.getInfoLabel('Window.Property(xmlfile)'))
            dolog('### Progress Dialog active, sleeping for %s seconds' % counter)
            xbmc.sleep(1000)
            if xbmc.getCondVisibility('Window.IsActive(progressdialog)') or (xbmc.getInfoLabel('Window.Property(xmlfile)') == 'DialogProgress.xml'):
                isdialog = True
            else:
                isdialog = False
            counter += 1
            dolog('counter: %s' % counter)

# Given the DialogProgress 10 seconds to finish and it's still up - time to close it
            if counter == 10:
                try:
                    dolog('attempting to send click to close dp')
                    xbmc.executebuiltin('SendClick()')
                    if dp.iscanceled():
                        dp.close()
                except:
                    dolog('### FAILED TO CLOSE DP')

    isplaying = xbmc.Player().isPlaying()
    counter   = 1
    if xbmc.Player().isPlayingAudio():
        return True
# If xbmc player is not yet active give it some time to initialise
    while not isplaying and counter < timeout:
        xbmc.sleep(1000)
        isplaying = xbmc.Player().isPlaying()
        dolog('### XBMC Player not yet active, sleeping for %s seconds' % counter)
        counter += 1

    success = 0
    counter = 0

# If it's playing give it time to physically start streaming then attempt to pull some info
    if isplaying:
        xbmc.sleep(1000)
        while not success and counter < 5:
            try:
                if xbmc.Player().isPlayingVideo():
                    infotag = xbmc.Player().getVideoInfoTag()
                vidtime = xbmc.Player().getTime()
                if vidtime > 0:
                    success = 1

# If playback doesn't start automatically (buffering) we force it to play
                else:
                    dolog('### Playback active but time at zero, trying to unpause')
                    xbmc.executebuiltin('PlayerControl(Play)')
                    xbmc.sleep(2000)
                    vidtime = xbmc.Player().getTime()
                    if vidtime > 0:
                        success = 1

# If no infotag or time could be pulled then we assume playback failed, try and stop the xbmc.player
            except:
                counter += 1
                xbmc.sleep(1000)

# Check if the busy dialog is still active from previous locked up playback attempt
    isbusy  = xbmc.getCondVisibility('Window.IsActive(busydialog)')
    counter   = 1
    while isbusy:
        dolog('### Busy dialog active, sleeping for %ss' % counter)
        xbmc.sleep(1000)
        isbusy  = xbmc.getCondVisibility('Window.IsActive(busydialog)')
        counter += 1
        if counter == 5:
            xbmc.executebuiltin('Dialog.Close(busydialog)')

    if not success:
        xbmc.executebuiltin('PlayerControl(Stop)')
        dolog('### Failed playback, stopped stream')
        return False

    else:
        return True
#----------------------------------------------------------------    
# TUTORIAL #
def M3U_Selector(url,post_type='get',header='Stream Selection'):
    """
Send through an m3u/m3u8 playlist and have the contents displayed via a dialog select.
The return will be a dictionary of 'name' and 'url'. You can send through either
a locally stored filepath or an online URL.

This function will try it's best to pull out the relevant playlist details even if the
web page isn't a correctly formatted m3u playlist (e.g. an m3u playlist embedded into
a blog page).

CODE: M3U_Selector(url, [post_type, header])

AVAILABLE PARAMS:
    (*) url  -  The location of your m3u file, this can be local or online

    post_type  -  If you need to use POST rather than a standard query string
    in your url set this to 'post', by default it's set to 'get'.

    header  -  This is the header you want to appear at the top of your dialog
    selection window, by default it's set to "Stream Selection"

EXAMPLE CODE:
# This example uses YouTube plugin paths but any playable paths will work
vid = koding.M3U_Selector(url='http://totalrevolution.tv/videos/playlists/youtube.m3u')

# Make sure there is a valid link returned
if vid:
    playback = koding.Play_Video(video=vid['url'], showbusy=False)
    if playback:
        dialog.ok('SUCCESS!','Congratulations the playback was successful!')
        xbmc.Player().stop()
    else:
        dialog.ok('OOPS!','Looks like something went wrong there, the playback failed. Check the links are still valid.')
~"""
    from web import Open_URL
    from systemtools import Cleanup_String
    from filetools import Text_File, Find_In_Text
    success = False
    if url.startswith('http'):
        content = Open_URL(url=url, post_type=post_type, timeout=10)
    else:
        try:
            url = xbmc.translatePath(url)
        except:
            pass
        content = Text_File(url,'r')
    if content:
        newcontent = content.splitlines()
        name_array = []
        url_array  = []
        name = ''
        for line in newcontent:
            line = line.strip()
        # Grab the name of the stream
            if line.startswith('#EXT'):
                name = line.split(',')
                name.pop(0)
                name = ''.join(name)
        # Grab the url(s) of the stream
            if name != '' and line != '' and not line.startswith('#EXT'):
                name_array.append(Cleanup_String(name))
                line = line.replace('<br>','').replace('<br />','').replace('<br/>','')
                line = line.replace('</p>','').replace('</div>','').replace('</class>','')
                dolog('line: %s'%line)
                if 'm3u' in line or 'm3u8' in line:
                    line = 'LIST~'+line
                if 'src="' in line:
                    line = Find_In_Text(content=line, start='src="', end='"')[0]
                url_array.append(line)
                name = ''
                line = ''
        # If there is only one entry with no names/comments just return as unknown with the link
            if not '#EXT' in content:
                return {'name' : 'Unknown', 'url' : line}

    # If there's a list we show a dialog select of the available links
        if len(name_array) > 0:
            choice = xbmcgui.Dialog().select(header, name_array)
            if choice >= 0:

            # If the selection is a final url and not a list of multiple links
                if not url_array[choice].startswith('LIST~'):
                    success = True
                    return {'name' : name_array[choice], 'url' : url_array[choice]}

            # List of multiple links detected, give option of which link to play
                else:
                    clean_link = url_array[choice].replace('LIST~','')
                    content = Open_URL(url=clean_link, timeout=10)
                    if content:
                        newcontent = content.splitlines()
                        name_array = []
                        url_array  = []
                        name = ''
                        counter = 1
                        for line in newcontent:
                        # Show name as link 1,2,3,4 etc.
                            if line.startswith('#EXT'):
                                name = 'LINK '+str(counter)
                        # Grab the link(s) to the video
                            if name != '' and line != '' and not line.startswith('#EXT'):
                                name_array.append(name)
                                line = line.replace('<br>','').replace('<br />','').replace('<br/>','')
                                line = line.replace('</p>','').replace('</div>','').replace('</class>','')
                                url_array.append(line)
                                name = ''
                                line = ''
                                counter += 1
                        # If there is only one entry with no names/comments just return as unknown with the link
                            if not '#EXT' in content:
                                return {'name' : 'Unknown', 'url' : line}

                    # Give option of which link to play in case of multiple links available
                        if len(name_array) > 0:
                            choice = xbmcgui.Dialog().select(header, name_array)
                            if choice >= 0:
                                success = True
                                return {'name' : name_array[choice], 'url' : url_array[choice]}
    if not success:
        xbmcgui.Dialog().ok('NO LINKS FOUND','Sorry no valid links could be found for this stream.')
        return False
#----------------------------------------------------------------    
# TUTORIAL #
def Play_Video(video,showbusy=True,content='video',ignore_dp=False,timeout=10, item=None):
    """
This will attempt to play a video and return True or False on
whether or not playback was successful. This function is similar
to Check_Playback but this actually tries a number of methods to
play the video whereas Check_Playback does not actually try to
play a video - it will just return True/False on whether or not
a video is currently playing.

If you have m3u or m3u8 playlist links please use the M3U_Selector
function to get the final resolved url.

CODE: Play_Video(video, [showbusy, content, ignore_dp, timeout, item])

AVAILABLE PARAMS:

    (*) video  -  This is the path to the video, this can be a local
    path, online path or a channel number from the PVR.

    showbusy  -  By default this is set to True which means while the
    function is attempting to playback the video the user will see the
    busy dialog. Set to False if you prefer this not to appear but do
    bare in mind a user may navigate to another section and try playing
    something else if they think this isn't doing anything.

    content  -  By default this is set to 'video', however if you're
    passing through audio you may want to set this to 'music' so the
    system can correctly set the tags for artist, song etc.

    ignore_dp  -  By default this is set to True but if set to False
    this will ignore the DialogProgress window. If you use a DP while
    waiting for the stream to start then you'll want to set this True.
    Please bare in mind the reason this check is in place and enabled
    by default is because some streams do bring up a DialogProgress
    when initiated (such as f4m proxy links) and disabling this check
    in those circumstances can cause false positives.

    timeout  -  This is the amount of time you want to allow for playback
    to start before sending back a response of False. Please note if
    ignore_dp is set to True then it will also add a potential 10s extra
    to this amount if a DialogProgress window is open. The default setting
    for this is 10s.

    item  -  By default this is set to None and in this case the metadata
    will be auto-populated from the previous Add_Dir so you'll just get the
    basics like title, thumb and description. If you want to send through your
    own metadata in the form of a dictionary you can do so and it will override
    the auto-generation. If anything else sent through no metadata will be set,
    you would use this option if you've already set metadata in a previous function.


EXAMPLE CODE:
isplaying = koding.Play_Video('http://totalrevolution.tv/videos/python_koding/Browse_To_Folder.mov')
if isplaying:
    dialog.ok('PLAYBACK SUCCESSFUL','Congratulations, playback was successful')
    xbmc.Player().stop()
else:
    dialog.ok('PLAYBACK FAILED','Sorry, playback failed :(')
~"""

    dolog('### ORIGINAL VIDEO: %s'%video)
    import urlresolver
    try:    import simplejson as json
    except: import json

    if not item:
        meta = {}
        for i in ['title', 'originaltitle', 'tvshowtitle', 'year', 'season', 'episode', 'genre', 'rating', 'votes',
                  'director', 'writer', 'plot', 'tagline']:
            try:
                meta[i] = xbmc.getInfoLabel('listitem.%s' % i)
            except:
                pass
        meta = dict((k, v) for k, v in meta.iteritems() if not v == '')
        if 'title' not in meta:
            meta['title'] = xbmc.getInfoLabel('listitem.label')
        icon = xbmc.getInfoLabel('listitem.icon')
        item = xbmcgui.ListItem(path=video, iconImage =icon, thumbnailImage=icon)
        if content == "music":
            try:
                meta['artist'] = xbmc.getInfoLabel('listitem.artist')
                item.setInfo(type='Music', infoLabels={'title': meta['title'], 'artist': meta['artist']})
            except:
                item.setInfo(type='Video', infoLabels=meta)
        else:
            item.setInfo(type='Video', infoLabels=meta)

    elif type(item).__name__ == 'dict':
        item.setInfo(type='Video', infoLabels=meta)

    else:
        pass

    playback = False
    if showbusy:
        Show_Busy()


# if a plugin path is sent we try activate window
    if video.startswith('plugin://'):
        try:
            dolog('Attempting to play via xbmc.Player().play() method')
            xbmc.Player().play(video)
            playback = Check_Playback(ignore_dp,timeout)
        except:
            dolog(Last_Error())

# If an XBMC action has been sent through we do an executebuiltin command
    elif video.startswith('ActivateWindow') or video.startswith('RunAddon') or video.startswith('RunScript') or video.startswith('PlayMedia'):
        try:
            dolog('Attempting to play via xbmc.executebuiltin method')
            xbmc.executebuiltin('%s'%video)
            playback = Check_Playback(ignore_dp,timeout)
        except:
            dolog(Last_Error())

    elif ',' in video:
# Standard xbmc.player method (a comma in url seems to throw urlresolver off)
        try:
            dolog('Attempting to play via xbmc.Player.play() method')
            xbmc.Player().play('%s'%video, item)
            playback = Check_Playback(ignore_dp,timeout)

# Attempt to resolve via urlresolver
        except:
            try:
                dolog('Attempting to resolve via urlresolver module')
                dolog('video = %s'%video)
                hmf = urlresolver.HostedMediaFile(url=video, include_disabled=False, include_universal=True)
                if hmf.valid_url() == True:
                    video = hmf.resolve()
                    dolog('### VALID URL, RESOLVED: %s'%video)
                xbmc.Player().play('%s' % video, item)
                playback = Check_Playback(ignore_dp,timeout)
            except:
                dolog(Last_Error())

# Play from a db entry - untested
    elif video.isdigit():
        dolog('### Video is digit, presuming it\'s a db item')
        command = ('{"jsonrpc": "2.0", "id":"1", "method": "Player.Open","params":{"item":{"channelid":%s}}}' % url)
        xbmc.executeJSONRPC(command)
        playback = Check_Playback(ignore_dp,timeout)

    else:
# Attempt to resolve via urlresolver
        try:
            dolog('Attempting to resolve via urlresolver module')
            dolog('video = %s'%video)
            hmf = urlresolver.HostedMediaFile(url=video, include_disabled=False, include_universal=True)
            if hmf.valid_url() == True:
                video = hmf.resolve()
                dolog('### VALID URL, RESOLVED: %s'%video)
            xbmc.Player().play('%s' % video, item)
            playback = Check_Playback(ignore_dp,timeout)

# Standard xbmc.player method
        except:
            try:
                dolog('Attempting to play via xbmc.Player.play() method')
                xbmc.Player().play('%s' % video, item)
                playback = Check_Playback(ignore_dp,timeout)
            except:
                dolog(Last_Error())

    dolog('Playback status: %s' % playback)
    Show_Busy(False)
    counter = 1
    dialogprogress = xbmc.getCondVisibility('Window.IsActive(progressdialog)')
    while dialogprogress:
        dp.create('Playback Good','Closing dialog...')
        dolog('Attempting to close dp #%s'%counter)
        dp.close()
        xbmc.sleep(1000)
        counter += 1
        dialogprogress = xbmc.getCondVisibility('Window.IsActive(progressdialog)')

    return playback
#----------------------------------------------------------------    
# TUTORIAL #
def Sleep_If_Playback_Active():
    """
This will allow you to pause code while kodi is playing audio or video

CODE: Sleep_If_Playback_Active()

EXAMPLE CODE:
dialog.ok('PLAY A VIDEO','We will now attempt to play a video, once you stop this video you should see a dialog.ok message.')
xbmc.Player().play('http://download.blender.org/peach/bigbuckbunny_movies/big_buck_bunny_720p_stereo.avi')
xbmc.sleep(3000) # Give kodi enough time to load up the video
koding.Sleep_If_Playback_Active()
dialog.ok('PLAYBACK FINISHED','The playback has now been finished so this dialog code has now been initiated')
~"""
    isplaying = xbmc.Player().isPlaying()
    while isplaying:
        xbmc.sleep(500)
        isplaying = xbmc.Player().isPlaying()
