# system_project_folder.py (c) 2010 Dany Lebel (Axon_D)
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

from zpy import is27, is28
from platform import system as currentOS
import os
import bpy
bl_info = {
    "name": "Project Folder",
    "author": "Dany Lebel (Axon_D), Spirou4D",
    "version": (0, 3, 1),
    "blender": (2, 61, 0),
    "location": "Info -> File Menu -> Project Folder",
    "description": "Open the project folder in a file browser",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/System/Project_Folder",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "System"}


class SYS_OT_ProjectFolder(bpy.types.Operator):
    """Open the Project Folder in a file Browser"""
    bl_idname = "file.project_folder"
    bl_label = "Project Folder"

    @classmethod
    def poll(cls, context):
        return bpy.data.filepath

    def execute(self, context):
        try:
            path = self.path()
        except ValueError:
            self.report({'INFO'}, "No project folder yet")
            return {'FINISHED'}

        bpy.ops.wm.path_open(filepath=path)

        return {'FINISHED'}

    def path(self):
        filepath = bpy.data.filepath
        relpath = bpy.path.relpath(filepath)
        path = filepath[0: -1 * (relpath.__len__() - 2)]
        return path


# Registration

def menu_func(self, context):
    self.layout.operator(
        SYS_OT_ProjectFolder.bl_idname,
        text="Project Folder",
        icon=('FILEBROWSER', "FILESEL")[is27])


if is28: cls = bpy.types.TOPBAR_MT_file
if is28: cls = bpy.types.TOPBAR_MT_app
if is27: cls = bpy.types.INFO_MT_file


def register():
    cls.prepend(menu_func)


def unregister():
    cls.remove(menu_func)
