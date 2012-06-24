"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Quick versions to shotgun from Nuke

"""

import tank
from tank import TankError
import sys
import nuke
import os
import tempfile
import datetime

class NukeQuickDailies(tank.platform.Application):
    
    def init_app(self):
        """
        Called as the application is being initialized
        """
        
        # assign this app to nuke handle so that the node
        # callback finds it
        nuke.tk_nuke_quickdailies = self
        
        self._movie_template = self.get_template("movie_template")
        
        
        
        # add to tank menu
        icon = os.path.join(self.disk_location, "resources", "node_icon.png")
        self.engine.register_command("Tank Quick Dailies", 
                                      self.create_node, 
                                      {"type": "node", "icon": icon})
                      
    def create_node(self):
        """
        Creates a tank quick dailies node
        """
        nk_file = os.path.join(self.disk_location, "resources", "quickdailynode.nk")
        nk_file = nk_file.replace(os.sep, "/")
        nuke.nodePaste(nk_file)

    # callbacks! note that if the behaviour changes, we need to version up these methods
    # we must support all older versions of nodes that may remain inside of scenes.

    def _get_first_frame(self):
        """
        returns the first frame for this session
        """
        return int(nuke.root()["first_frame"].value())
        
    def _get_last_frame(self):
        """
        returns the last frame for this session
        """
        return int(nuke.root()["last_frame"].value())

    def _setup_formatting(self, group_node, name, iteration):
        """
        Sets up slates and burnins
        """
        
        # set the fonts for all text fields
        font = os.path.join(self.disk_location, "resources", "liberationsans_regular.ttf")
        font = font.replace(os.sep, "/")
        group_node.node("top_left_text")["font"].setValue(font)
        group_node.node("top_right_text")["font"].setValue(font)
        group_node.node("bottom_left_text")["font"].setValue(font)
        group_node.node("framecounter")["font"].setValue(font)
        group_node.node("slate_info")["font"].setValue(font)
        
        # format the burnins  
        
        # top-left says 
        # Project XYZ
        # Shot ABC
        top_left = "%s\n%s %s" % (self.context.project["name"], 
                                  self.context.entity["type"], 
                                  self.context.entity["name"])
        group_node.node("top_left_text")["message"].setValue(top_left)
        
        # top-right has date
        # format '23 Jan 2012' is universally understood.
        today = datetime.date.today()
        top_right = today.strftime("%d %b %Y")
        group_node.node("top_right_text")["message"].setValue(top_right)
        
        # bottom left says
        # Name#increment
        # User
        bottom_left = "%s#%d\n" % (name, iteration)
        user = tank.util.get_shotgun_user(self.tank.shotgun)
        if user is None:
            bottom_left += "Unknown User"
        else:
            bottom_left += user.get("name", "Unknown User")
        group_node.node("bottom_left_text")["message"].setValue(bottom_left)
                
        # and the slate
        slate_str =  "Project: %s\n" % self.context.project["name"]
        slate_str += "%s: %s\n" % (self.context.entity["type"], self.context.entity["name"])
        slate_str += "Name: %s\n" % name
        slate_str += "Iteration: %d\n" % iteration
        
        if self.context.task:
            slate_str += "Task: %s\n" % self.context.task["name"]
        elif self.context.step:
            slate_str += "Step: %s\n" % self.context.step["name"]
        
        slate_str += "Frames: %s - %s\n" % (self._get_first_frame(), self._get_last_frame())
        
        group_node.node("slate_info")["message"].setValue(slate_str)



    def _render(self, group_node, mov_path, png_path):
        """
        Renders quickdaily node
        """

        # setup quicktime output resolution
        width = self.get_setting("width", 1024)
        height = self.get_setting("height", 540)        
        mov_reformat_node = group_node.node("mov_reformat")
        mov_reformat_node["box_width"].setValue(width)
        mov_reformat_node["box_height"].setValue(height)
        
        # setup output png path
        png_out = group_node.node("png_writer")
        png_path = png_path.replace(os.sep, "/")
        png_out["file"].setValue(png_path)
        
        # setup output quicktime path
        mov_out = group_node.node("mov_writer")
        mov_path = mov_path.replace(os.sep, "/")
        mov_out["file"].setValue(mov_path)
        
        # on the mac and windows, we use the quicktime codec
        # on linux, use ffmpeg
        if sys.platform == "win32" or sys.platform == "darwin":
            
            # apple photo-jpeg movie
            mov_out["file_type"].setValue('mov')
            mov_out["codec"].setValue('jpeg')
            mov_out["fps"].setValue(23.97599983)
            mov_out["settings"].setValue("000000000000000000000000000019a7365616e0000000100000001000000000000018676696465000000010000000e00000000000000227370746c0000000100000000000000006a706567000000000018000003ff000000207470726c000000010000000000000000000000000017f9db00000000000000246472617400000001000000000000000000000000000000530000010000000100000000156d70736f00000001000000000000000000000000186d66726100000001000000000000000000000000000000187073667200000001000000000000000000000000000000156266726100000001000000000000000000000000166d70657300000001000000000000000000000000002868617264000000010000000000000000000000000000000000000000000000000000000000000016656e647300000001000000000000000000000000001663666c67000000010000000000000000004400000018636d66720000000100000000000000006170706c00000014636c75740000000100000000000000000000001c766572730000000100000000000000000003001c00010000")

        elif sys.platform == "linux2":
            mov_out["file_type"].setValue("ffmpeg")
            mov_out["codec"].setValue("MOV format (mov)")

        # turn on the nodes        
        mov_out.knob('disable').setValue(False)
        png_out.knob('disable').setValue(False)

        # finally render everything!
        # default to using the first view on stereo
        
        try:
            first_view = nuke.views()[0]        
            nuke.executeMultiple( [mov_out, png_out], 
                                  ([ self._get_first_frame()-1, self._get_last_frame(), 1 ],),
                                  [first_view]
                                  )
        finally:            
            # turn off the nodes again
            mov_out.knob('disable').setValue(True)
            png_out.knob('disable').setValue(True)


    def _get_comments(self):
        """
        Get name and comments from user via UI
        """
        return ("test", "comments hello")


    def create_daily_v1(self, group_node):
        """
        Create daily. Version 1 of implementation.
        """

        # get inputs
        (name, message) = self._get_comments()

        # calculate the increment
        fields = self.context.as_template_fields(self._movie_template)
        fields["name"] = name
        fields["iteration"] = 1
        
        # get all files
        files = self.tank.paths_from_template(self._movie_template, fields, ["iteration"])
        
        # get all iteration numbers
        iterations = [self._movie_template.get_fields(f).get("iteration") for f in files]
        if len(iterations) == 0:
            new_iteration = 1
        else:
            new_iteration = max(iterations)
        
        # compute new file path
        fields["iteration"] = new_iteration
        mov_path = self._movie_template.apply_fields(fields)
        
        # set metadata
        self._setup_formatting(group_node, name, new_iteration)
        
        # make sure folders exist for mov
        mov_folder = os.path.dirname(mov_path)
        if not os.path.exists(mov_folder):
            self.tank.execute_hook("create_folder", path=mov_folder)
        
        # generate temp file for png sequence
        png_tmp_folder = tempfile.mkdtemp()
        png_path = os.path.join(png_tmp_folder, "thumb_seq.%08d.png")
        
        # and render!
        self._render(group_node, mov_path, png_path)

        # post process


        

        
        # execute post hook
        
        
        
        
        
    def destroy_app(self):
        self.log_debug("Destroying tk-nuke-publish")
                       

