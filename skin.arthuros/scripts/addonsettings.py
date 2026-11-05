# ArthurOS: open the settings of the add-on that is playing.
#
# Run by the Add-on settings button on the video and music OSD.
#
# Which add-on? A plugin:// path names it (plugin://plugin.video.youtube/...),
# and Player.FilenameAndPath still holds that path when playback was started
# from a favourite, a desktop tile or music played from an add-on. When the
# add-on handed Kodi a resolved stream (an http:// URL), the path no longer
# says; then the media browser it was started from has recorded it in
# Window(Home).Property(arthuros.plugin) as it closed.
from urllib.parse import urlparse

import xbmc


def playing_addon():
    path = xbmc.getInfoLabel("Player.FilenameAndPath")
    if path.startswith("plugin://"):
        aid = urlparse(path).netloc
        if aid:
            return aid
    return xbmc.getInfoLabel("Window(Home).Property(arthuros.plugin)")


aid = playing_addon()
if aid and xbmc.getCondVisibility("System.HasAddon(%s)" % aid):
    xbmc.executebuiltin("Addon.OpenSettings(%s)" % aid)
