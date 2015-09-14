# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys

from tank import Hook
import nuke

class NukeQuickdailiesGetQuicktimeSettings(Hook):
    """
    Allows modifying default settings for Quicktime generation.
    """
    def execute(self, **kwargs):
        """
        Returns a dictionary of settings to be used for the Write Node that generates
        the Quicktime in Nuke.
        """
        settings = {}
        if sys.platform in ["darwin", "win32"]:
            # On Mac and Windows, we use the Quicktime codec
            settings["file_type"] = "mov"
            # Nuke 9.0v1 changed the codec knob name to meta_codec and added an encoder knob
            # (which defaults to the new mov64 encoder/decoder).  
            if nuke.NUKE_VERSION_MAJOR > 8:
                settings["meta_codec"] = "jpeg"
            else:
                settings["codec"] = "jpeg"
            settings["fps"] = 23.97599983
            settings["settings"] = "000000000000000000000000000019a7365616e0000000100000001000000000000018676696465000000010000000e00000000000000227370746c0000000100000000000000006a706567000000000018000003ff000000207470726c000000010000000000000000000000000017f9db00000000000000246472617400000001000000000000000000000000000000530000010000000100000000156d70736f00000001000000000000000000000000186d66726100000001000000000000000000000000000000187073667200000001000000000000000000000000000000156266726100000001000000000000000000000000166d70657300000001000000000000000000000000002868617264000000010000000000000000000000000000000000000000000000000000000000000016656e647300000001000000000000000000000000001663666c67000000010000000000000000004400000018636d66720000000100000000000000006170706c00000014636c75740000000100000000000000000000001c766572730000000100000000000000000003001c00010000"

        elif sys.platform == "linux2":
            # On linux, use ffmpeg
            settings["file_type"] = "ffmpeg"
            settings["format"] = "MOV format (mov)"

        return settings
