"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

"""
import nukescripts
import nuke
import os
import shutil
import datetime

from tank import TankError


class CommentsPanel(nukescripts.PythonPanel):
    
    def __init__(self, name):
        super(CommentsPanel, self).__init__("Tank Quick Dailies" )
        
        # build UI        
        self.addKnob(nuke.Text_Knob("info1", "", "Submission Name:"))
        self._name = nuke.String_Knob("name", "", name)
        self.addKnob(self._name)

        self.addKnob(nuke.Text_Knob("info1", "", "Comments:"))
        self._comments = nuke.Multiline_Eval_String_Knob("comment", "", "")
        self.addKnob(self._comments)
        
        self.addKnob(nuke.Text_Knob("div1", ""))
                
        # finally some buttons
        self.okButton = nuke.Script_Knob("Create Daily")
        self.addKnob(self.okButton)
        self.cancelButton = nuke.Script_Knob("Cancel")
        self.addKnob(self.cancelButton)

    def get_name(self):
        return self._name.value()

    def get_comments(self):
        return self._comments.value()

    def knobChanged(self, knob):
        
        if knob == self.okButton:
            # make sure the file doesn't already exist
            self.finishModalDialog(True)
        elif knob == self.cancelButton:
            self.finishModalDialog(False)
