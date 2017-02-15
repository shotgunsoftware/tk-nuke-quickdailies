# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook that controls codec settings when generating quick dailies for review
"""
import sgtk
import os
import sys

import nuke

HookBaseClass = sgtk.get_hook_baseclass()

class CodecSettings(HookBaseClass):

    def get_quicktime_settings(self, write_node, **kwargs):
        """
        Allows modifying default settings for Quicktime generation.
        Returns a dictionary of settings to be used for the Write Node that generates
        the Quicktime in Nuke.

        :param write_node: Nuke Write node 
        """
        settings = {}

        if sys.platform == "linux2":
            if nuke.NUKE_VERSION_MAJOR >= 9:
                # Nuke 9.0v1 removed ffmpeg and replaced it with the mov64 writer
                # http://help.thefoundry.co.uk/nuke/9.0/#appendices/appendixc/supported_file_formats.html
                write_node["file_type"].setValue("mov64")
                write_node["mov64_codec"].setValue("jpeg")
                write_node["mov64_quality_max"].setValue("3")
            else:
                # the 'codec' knob name was changed to 'format' in Nuke 7
                write_node["file_type"].setValue("ffmpeg")
                write_node["format"].setValue("MOV format (mov)")
        elif nuke.NUKE_VERSION_MAJOR >= 10 and (nuke.NUKE_VERSION_MINOR > 1 or nuke.NUKE_VERSION_RELEASE > 1):
            # In Nuke 10.0v2, the dependency on the Quicktime desktop application was removed. Because of
            # that, we have to account for changes in the .mov encoding settings in the Write node.
            write_node["file_type"].setValue("mov64")
            write_node["meta_codec"].setValue("jpeg")
            write_node["mov64_quality_max"].setValue("3")    
        else:
            write_node["file_type"].setValue("mov")
            if nuke.NUKE_VERSION_MAJOR >= 9:
                # Nuke 9.0v1 changed the codec knob name to meta_codec and added an encoder knob
                # (which defaults to the new mov64 encoder/decoder).                  
                write_node["meta_codec"].setValue("jpeg")
                write_node["mov64_quality_max"].setValue("3")
            else:
                write_node["codec"].setValue("jpeg")
            write_node["fps"].setValue(23.97599983)
            write_node["settings"].setValue("000000000000000000000000000019a7365616e0000000100000001000000000000018676696465000000010000000e00000000000000227370746c0000000100000000000000006a706567000000000018000003ff000000207470726c000000010000000000000000000000000017f9db00000000000000246472617400000001000000000000000000000000000000530000010000000100000000156d70736f00000001000000000000000000000000186d66726100000001000000000000000000000000000000187073667200000001000000000000000000000000000000156266726100000001000000000000000000000000166d70657300000001000000000000000000000000002868617264000000010000000000000000000000000000000000000000000000000000000000000016656e647300000001000000000000000000000000001663666c67000000010000000000000000004400000018636d66720000000100000000000000006170706c00000014636c75740000000100000000000000000000001c766572730000000100000000000000000003001c00010000")
