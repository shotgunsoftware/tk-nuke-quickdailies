# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Quick versions to shotgun from Nuke

"""

import tank
from tank import TankError
import sys
import nuke
import os
import tempfile
import datetime

PNG_THUMB_SEQUENCE_MARKER = "%08d"





class NukeQuickDailies(tank.platform.Application):
    
    def init_app(self):
        """
        Called as the application is being initialized
        """
        
        # assign this app to nuke handle so that the node
        # callback finds it
        nuke.tk_nuke_quickdailies = self
        
        self._movie_template = self.get_template("movie_template")
        self._snapshot_template = self.get_template("current_scene_template")
        self._version_template = self.get_template("sg_version_name_template")
        
        # add to tank menu
        icon = os.path.join(self.disk_location, "resources", "node_icon.png")
        self.engine.register_command("Shotgun Quick Dailies", 
                                      self.create_node, 
                                      {"type": "node", "icon": icon})

    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.
        """
        return True
                      
    def create_node(self):
        """
        Creates a quick dailies node
        """
        nk_file = os.path.join(self.disk_location, "resources", "quickdailynode.nk")
        nk_file = nk_file.replace(os.sep, "/")
        nuke.nodePaste(nk_file)

    def post_context_change(self, old_context, new_context):
        """
        Runs after a context change has completed.

        :param old_context: The sgtk.context.Context being switched from.
        :param new_context: The sgtk.context.Context being switched to.
        """
        self._movie_template = self.get_template("movie_template")
        self._snapshot_template = self.get_template("current_scene_template")
        self._version_template = self.get_template("sg_version_name_template")

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
        
        # get some useful data
        
        # date -- format '23 Jan 2012' is universally understood.
        today = datetime.date.today()
        date_formatted = today.strftime("%d %b %Y")
        
        # current user
        user_data = tank.util.get_current_user(self.tank)
        if user_data is None:
            user_name = "Unknown User"
        else:
            user_name = user_data.get("name", "Unknown User")        
                
        # format the burnins  
        
        # top-left says 
        # Project XYZ
        # Shot ABC
        top_left = "%s\n%s %s" % (self.context.project["name"], 
                                  self.context.entity["type"], 
                                  self.context.entity["name"])
        group_node.node("top_left_text")["message"].setValue(top_left)
        
        # top-right has date
        group_node.node("top_right_text")["message"].setValue(date_formatted)
        
        # bottom left says
        # Name#increment
        # User
        bottom_left = "%s " % name.capitalize() if name else ""
        bottom_left += ("Iteration %d\n" % (iteration))
        bottom_left += user_name
        group_node.node("bottom_left_text")["message"].setValue(bottom_left)
                
        # and the slate
        slate_str =  "Project: %s\n" % self.context.project["name"]
        slate_str += "%s: %s\n" % (self.context.entity["type"], self.context.entity["name"])
        if name:
            slate_str += "Name: %s\n" % name
        slate_str += "Iteration: %d\n" % iteration
        
        if self.context.task:
            slate_str += "Task: %s\n" % self.context.task["name"]
        elif self.context.step:
            slate_str += "Step: %s\n" % self.context.step["name"]
        
        slate_str += "Frames: %s - %s\n" % (self._get_first_frame(), self._get_last_frame())
        slate_str += "Date: %s\n" % date_formatted
        slate_str += "User: %s\n" % user_name
        
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
        
        # apply the Write node codec settings we'll use for generating the Quicktime
        self.execute_hook_method("codec_settings_hook", 
                                 "get_quicktime_settings",
                                 write_node=mov_out)

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


    def _get_comments(self, sg_version_name):
        """
        Get name and comments from user via UI
        """
        # deferred import so that this app runs in batch mode
        tk_nuke_quickdailies = self.import_module("tk_nuke_quickdailies")
        d = tk_nuke_quickdailies.CommentsPanel(sg_version_name)        
        result = d.showModalDialog()
        if result:
            return d.get_comments()
        else:
            return None

    def _produce_thumbnails(self, png_path):
        """
        Makes filmstrip thumbs and thumb.
        Assumes that png_path has a PNG_THUMB_SEQUENCE_MARKER 
        sequence indicator in the path (like %08d)
        
        returns (thumb_path, filmstrip_path)
        """
        start_frame = self._get_first_frame()
        end_frame = self._get_last_frame()
        
        # first get static thumbnail
        # middle frame is thumb
        thumb_frame = (end_frame-start_frame) / 2 + start_frame
        single_thumb_path = png_path.replace(PNG_THUMB_SEQUENCE_MARKER, PNG_THUMB_SEQUENCE_MARKER % thumb_frame)
        if not os.path.exists(single_thumb_path):
            single_thumb_path = None
        
        # now try to build film strip using the convert command
        # convert img1.png img2.png img3.png +append output.png
        filmstrip_thumb_path = tempfile.NamedTemporaryFile(suffix=".png", prefix="tankthumb", delete=False).name
        
        cmdline = ["convert"]
        for x in range(start_frame, end_frame+1):
            cmdline.append("\"%s\"" %  png_path.replace(PNG_THUMB_SEQUENCE_MARKER, PNG_THUMB_SEQUENCE_MARKER % x) )
        cmdline.append("+append")
        cmdline.append("\"%s\"" % filmstrip_thumb_path)
        
        cmd = " ".join(cmdline)
        
        if os.system(cmd) != 0:  
            filmstrip_thumb_path = None
        
        return (single_thumb_path, filmstrip_thumb_path)
        

    def create_daily_v1(self, group_node):
        """
        Create daily. Version 1 of implementation.
        """
        name = "Quickdaily"
        
        # now try to see if we are in a normal work file
        # in that case deduce the name from it
        curr_filename = nuke.root().name().replace("/", os.path.sep)
        version = 0
        name = "Quickdaily"
        if self._snapshot_template.validate(curr_filename):
            fields = self._snapshot_template.get_fields(curr_filename)
            name = fields.get("name")
            version = fields.get("version")

        # calculate the increment
        fields = self.context.as_template_fields(self._movie_template)
        if name:
            fields["name"] = name
        if version != None:
            fields["version"] = version
        fields["iteration"] = 1
        
        # get all files
        files = self.tank.paths_from_template(self._movie_template, fields, ["iteration"])
        
        # get all iteration numbers
        iterations = [self._movie_template.get_fields(f).get("iteration") for f in files]
        if len(iterations) == 0:
            new_iteration = 1
        else:
            new_iteration = max(iterations) + 1
        
        # compute new file path
        fields["iteration"] = new_iteration
        mov_path = self._movie_template.apply_fields(fields)
        
        # compute shotgun version name
        sg_version_name = self._version_template.apply_fields(fields)
        
        # get inputs
        message = self._get_comments(sg_version_name)
        if message is None:
            # user pressed cancel!
            return
        
        # set metadata
        self._setup_formatting(group_node, name, new_iteration)
        
        # make sure folders exist for mov
        mov_folder = os.path.dirname(mov_path)
        self.ensure_folder_exists(mov_folder)
        
        # generate temp file for png sequence
        png_tmp_folder = tempfile.mkdtemp()
        png_path = os.path.join(png_tmp_folder, "thumb_seq.%s.png" % PNG_THUMB_SEQUENCE_MARKER)
        
        # and render!
        self._render(group_node, mov_path, png_path)

        # make thumbnails
        (thumb, filmstrip) = self._produce_thumbnails(png_path)

        # create sg version        
        data = {
            "code": sg_version_name,
            "description": message,
            "project": self.context.project,
            "entity": self.context.entity,
            "sg_task": self.context.task,
            "created_by": tank.util.get_current_user(self.tank),
            "user": tank.util.get_current_user(self.tank),
            "sg_path_to_movie": mov_path,
            "sg_first_frame": self._get_first_frame(),
            "sg_last_frame": self._get_last_frame(),
            "frame_count": (self._get_last_frame() - self._get_first_frame()) + 1,
            "frame_range": "%d-%d" % (self._get_first_frame(), self._get_last_frame()),
            "sg_movie_has_slate": True
        }

        # thumbnails and filmstrip thumbnails can be added at creation time to save time
        if thumb:
            data["image"] = thumb
        if filmstrip:
            data["filmstrip_image"] = filmstrip

        entity = self.shotgun.create("Version", data)
        self.log_debug("Version created in ShotgunL %s" % entity)
        
        # upload the movie to Shotgun if desired
        if self.get_setting("upload_movie", False):
            self.log_debug("Uploading movie to Shotgun")
            self.shotgun.upload("Version", entity["id"], mov_path, "sg_uploaded_movie")

        # execute post hook
        for h in self.get_setting("post_hooks", []):
            self.execute_hook_by_name(h, mov_path=mov_path, version_id=entity["id"], comments=message)
        
        # status message!
        sg_url = "%s/detail/Version/%s" % (self.shotgun.base_url, entity["id"]) 
        nuke.message("Your submission was successfully sent to review.")
        
        
    def destroy_app(self):
        self.log_debug("Destroying tk-nuke-quickdailies")
                       




