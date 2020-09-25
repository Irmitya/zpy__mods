import traceback
# from . import constraint_operator
import bpy
'''
Copyright (C) 2016 Andreas Esau
andreasesau@gmail.com

Created by Andreas Esau

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "Driver to Bone Constraint",
    "description": "This Operator lets you create a shape driver constraint to a bone with one single dialog operator. Quick and easy.",
    "author": "Andreas Esau",
    "version": (2, 0, 0, "Alpha"),
    "blender": (2, 80, 0),
    "location": "Operator Search -> Driver Constraint",
    "warning": "This addon is still in development.",
    "wiki_url": "https://github.com/ndee85/Driver-Constraint-Addon",
    "category": "Rigging"}


# load and reload submodules
##################################


# register
##################################


# classes = (
#     constraint_operator.DRIVER_CONSTRAINT_OT_create,
# )


def add_to_specials(self, context):
    if context.selected_objects:
        layout = self.layout.column()
        layout.operator_context = "INVOKE_DEFAULT"
        layout.separator()
        op = layout.operator(
            "object.create_driver_constraint", text="Driver Constraint", icon="DRIVER")
        op.mode = "DRIVER"
        # if getattr(context.active_object, 'type', None) == "ARMATURE" and \
        #         context.selected_pose_bones:
        ar = layout.row()
        ar.enabled = bool(bpy.data.actions)
        op = ar.operator(
            "object.create_driver_constraint", text="Action Constraint", icon="ACTION")
        op.mode = "ACTION"


def add_pose_tools(self, context):
    if context.selected_objects:
        layout = self.layout.column()
        layout.operator_context = "INVOKE_DEFAULT"
        layout.separator()
        layout.label(text="Driver Tools:")
        op = layout.operator(
            "object.create_driver_constraint", text="Driver Constraint", icon="DRIVER")
        op.mode = "DRIVER"
        if getattr(context.active_object, 'type', None) == "ARMATURE" and \
                context.selected_pose_bones:
            ar = layout.row()
            ar.enabled = bool(bpy.data.actions)
            op = ar.operator(
                "object.create_driver_constraint", text="Action Constraint", icon="ACTION")
            op.mode = "ACTION"


def register():
    # for cls in classes:
    #     bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_pose.append(add_to_specials)
    bpy.types.VIEW3D_MT_object.append(add_to_specials)
    bpy.types.VIEW3D_PT_context_properties.append(add_pose_tools)
    # bpy.types.VIEW3D_PT_tools_object.append(add_pose_tools)

    bpy.types.VIEW3D_MT_pose_context_menu.append(add_to_specials)
    bpy.types.VIEW3D_MT_object_context_menu.append(add_to_specials)


def unregister():
    # for cls in classes:
    #     bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_pose.remove(add_to_specials)
    bpy.types.VIEW3D_MT_object.remove(add_to_specials)
    bpy.types.VIEW3D_PT_context_properties.remove(add_pose_tools)
    # bpy.types.VIEW3D_PT_tools_object.remove(add_pose_tools)

    bpy.types.VIEW3D_MT_pose_context_menu.remove(add_to_specials)
    bpy.types.VIEW3D_MT_object_context_menu.remove(add_to_specials)
