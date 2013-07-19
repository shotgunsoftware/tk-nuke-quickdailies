# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import nukescripts
import nuke
import os
import shutil
import datetime

from tank import TankError


class CommentsPanel(nukescripts.PythonPanel):
    
    def __init__(self, sg_version_name):
        super(CommentsPanel, self).__init__("Shotgun: Quick Dailies" )

        self.addKnob(nuke.Text_Knob("info1", "", "This will render a quicktime and send it to Shotgun for review."))
        
        self.addKnob(nuke.Text_Knob("div1", ""))

        self.addKnob(nuke.Text_Knob("info1", "<b>Shotgun Name:</b>", "%s" % sg_version_name))
        
        self.addKnob(nuke.Text_Knob("div1", ""))
        self._comments = nuke.Multiline_Eval_String_Knob("comment", "<b>Comments:</b>", "")
        self.addKnob(self._comments)
        
        self.addKnob(nuke.Text_Knob("div1", ""))
                
        # finally some buttons
        self.okButton = nuke.Script_Knob("Create Daily")
        self.addKnob(self.okButton)
        self.cancelButton = nuke.Script_Knob("Cancel")
        self.addKnob(self.cancelButton)

    def get_comments(self):
        return self._comments.value()

    def knobChanged(self, knob):
        
        if knob == self.okButton:
            # make sure the file doesn't already exist
            self.finishModalDialog(True)
        elif knob == self.cancelButton:
            self.finishModalDialog(False)
