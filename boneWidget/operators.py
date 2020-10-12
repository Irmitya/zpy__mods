from zpy import Get, New, utils
from math import *
from mathutils import *
from .. import __package__ as __addon__


# # main
# from .functions.mainFunctions import boneMatrix
# from .functions.mainFunctions import fromWidgetFindBone
# from .functions.mainFunctions import createWidget
# from .functions.mainFunctions import symmetrizeWidget
# from .functions.mainFunctions import editWidget
# from .functions.mainFunctions import returnToArmature
# from .functions.mainFunctions import findMirrorObject
# from .functions.mainFunctions import findMatchBones
# from .functions.mainFunctions import get_collection
# # json
# from .functions.jsonFunctions import addRemoveWidgets
# from .functions.jsonFunctions import readWidgets
# from .functions.jsonFunctions import objectDataToDico


import bpy

from .functions import (
    findMatchBones,
    fromWidgetFindBone,
    findMirrorObject,
    symmetrizeWidget,
    boneMatrix,
    createWidget,
    editWidget,
    returnToArmature,
    addRemoveWidgets,
    readWidgets,
    objectDataToDico,
    get_collection,
)
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty, FloatVectorProperty, StringProperty


class BONEWIDGET_OT_createWidget(Operator):
    """Creates a widget for selected bone"""
    bl_idname = "bonewidget.create_widget"
    bl_label = "Create"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.ops.object.editmode_toggle.poll(context.copy()):
            return (context.object and context.object.mode == 'POSE')

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Slide:", icon='ORIENTATION_GLOBAL')
        row.prop(self, 'mirror')
        layout.row().prop(self, 'slide', text="")

        layout.label(text="Rotation:", icon='ORIENTATION_LOCAL')
        layout.row().prop(self, 'rotate', text="")

        row = layout.row()
        row.label(text="Scale", icon='ORIENTATION_VIEW')
        row.prop(self, 'relative_size')
        layout.prop(self, 'global_size', expand=False)
        layout.row().prop(self, 'scale', text="")

    def execute(self, context):
        if self.bones:
            bones = eval(self.bones)
        else:
            bones = Get.selected_pose_bones(context)

        if not bones:
            return {'CANCELLED'}

        wgts = readWidgets()
        if self.widget:
            widget = wgts[self.widget]
        else:
            widget = wgts[context.scene.widget_list]

        for bone in bones:
            if bone.id_data.proxy:
                continue
            slide = list(self.slide)
            rotate = list(self.rotate)
            if self.mirror:
                mirror = findMirrorObject(bone)
                if mirror and mirror in bones and bone.name.endswith(('L', 'l')):
                    slide[0] *= -1
                    rotate[1] *= -1
                    rotate[2] *= -1

            createWidget(context,
                bone,
                widget,
                self.relative_size,
                self.global_size,
                [*self.scale],
                slide,
                rotate,
                get_collection(context),
            )

        utils.update(context)

        pr = utils.prefs(__addon__).bone_widgets
        # pr = prefs.prefs().bone_widgets
        if pr.keep_settings:
            pr.slide = self.slide
            pr.rotate = self.rotate
            pr.relative_size = self.relative_size
            pr.global_size = self.global_size
            pr.scale = self.scale
            pr.mirror = self.mirror

        # Create new object then delete it.
        # When creating multiple widgets, if the last one tries to enter edit
        # mode before a particular update occurs, Blender will crash.
        # If the last object created (I.E. this empty) is not the widget,
        # Blender can enter edit mode without crash
        Get.objects(context, link=True).unlink(New.object(context))

        return {'FINISHED'}

    slide: FloatVectorProperty(
        name="Slide",
        description="Slide widget along x/y/z axis",
        default=(0.0, 0.0, 0.0),
        # min=nan,
        # max=nan,
        # soft_min=-(pi+pi)/2,
        # soft_max=(pi+pi)/2,
        # step=100,
        # precision=2,
        options={'SKIP_SAVE'},
        subtype='TRANSLATION',  # 'DISTANCE',
        unit='LENGTH',
        size=3,
    )
    rotate: FloatVectorProperty(
        name="Rotation",
        description="",
        default=(0.0, 0.0, 0.0),
        # min=nan,
        # max=nan,
        soft_min=-(pi + pi) / 2,
        soft_max=(pi + pi) / 2,
        step=100,
        precision=2,
        options={'SKIP_SAVE'},
        subtype='XYZ',
        unit='ROTATION',
        size=3,
    )
    relative_size: BoolProperty(
        name="Relative size",
        description="Widget size proportionnal to bone size",
        default=True,
    )
    global_size: FloatProperty(
        name="Global Size",
        description="Global Size",
        default=1.0,
        options={'SKIP_SAVE'},
    )
    scale: FloatVectorProperty(
        name="Scale",
        description="",
        default=(1.0, 1.0, 1.0),
        # min=nan,
        # max=nan,
        # soft_min=-(pi+pi)/2,
        # soft_max=(pi+pi)/2,
        # step=100,
        # precision=2,
        options={'SKIP_SAVE'},
        subtype='TRANSLATION',
        unit='LENGTH',
        size=3,
    )
    mirror: BoolProperty(
        name="Mirror",
        description="Mirror X values when selecting Left and Right bones",
        default=True,
    )

    bones: StringProperty(
        name="",
        description="List of bones to use, in string format "
                    "(for running without button)",
        default="",
        options={'HIDDEN', 'SKIP_SAVE'},
        subtype='NONE',
    )
    widget: StringProperty(
        name="",
        description="Widget to use force creation"
                    ".\nOr default to item selected for scene",
        default="",
        options={'HIDDEN', 'SKIP_SAVE'},
        subtype='NONE',
    )


class BONEWIDGET_OT_editWidget(Operator):
    """Edit the widget for selected bone"""
    bl_idname = "bonewidget.edit_widget"
    bl_label = "Edit"

    @classmethod
    def poll(cls, context):
        # if not all((context.object and context.object.type == 'ARMATURE' and context.object.pose)):
        # if bpy.ops.object.editmode_toggle.poll(context.copy()):
        for b in Get.selected_pose_bones(context):
            if b.custom_shape and not b.id_data.proxy:
                return True

    def execute(self, context):
        # editWidget(context, context.active_pose_bone)

        bones = Get.selected_pose_bones(context)
        # bpy.ops.object.mode_set(mode='OBJECT')

        for bone in bones:
            if (bone.custom_shape) and (not bone.id_data.proxy):
                editWidget(context, bone)

        return {'FINISHED'}


class BONEWIDGET_OT_removeWidget(Operator):
    """Remove the widget for selected bone"""
    bl_idname = "bonewidget.remove_widget"
    bl_label = "Remove"

    @classmethod
    def poll(cls, context):
        # if not all((context.object and context.object.type == 'ARMATURE' and context.object.pose)):
        # if bpy.ops.object.editmode_toggle.poll(context.copy()):
        for b in Get.selected_pose_bones(context):
            if b.custom_shape and not b.id_data.proxy:
                return True

    def execute(self, context):
        # editWidget(context, context.active_pose_bone)

        bones = Get.selected_pose_bones(context)
        # bpy.ops.object.mode_set(mode='OBJECT')

        for bone in bones:
            wgt = bone.custom_shape
            if wgt and (not bone.id_data.proxy):
                bone.custom_shape = None
                if wgt.users < 2:
                    # only used by widget collection now, so delete it
                    bpy.data.objects.remove(wgt)

        return {'FINISHED'}


class BONEWIDGET_OT_returnToArmature(Operator):
    """Switch back to the armature"""
    bl_idname = "bonewidget.return_to_armature"
    bl_label = "Return to armature"

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            for o in context.selected_objects:
                if o and o.type == 'MESH':
                    return True
        elif context.mode == 'EDIT_MESH':
            for o in Get.in_view(context):
                if o and o.type == 'MESH' and o.mode == 'EDIT':
                    return True

    def execute(self, context):
        if context.mode == 'OBJECT':
            for o in Get.selected_objects(context):
                if o.type == 'MESH':
                    if fromWidgetFindBone(o):
                        returnToArmature(context, o)
                    # else:
                        # self.report({'INFO'}, 'Object is not a bone widget' + repr(o))
        else:
            for o in Get.in_view(context):
                if o.type == 'MESH' and o.mode == 'EDIT':
                    if fromWidgetFindBone(o):
                        returnToArmature(context, o)

        return {'FINISHED'}


class BONEWIDGET_OT_matchBoneTransforms(Operator):
    """Match the widget to the bone transforms"""
    bl_idname = "bonewidget.match_bone_transforms"
    bl_label = "Match bone transforms"

    def execute(self, context):
        if context.mode == "POSE":
            for bone in Get.selected_pose_bones(context):
                if bone.custom_shape_transform and bone.custom_shape:
                    boneMatrix(bone.custom_shape, bone.custom_shape_transform)
                elif bone.custom_shape:
                    boneMatrix(bone.custom_shape, bone)
        else:
            for ob in Get.selected_objects(context):
                if ob.type == 'MESH':
                    matchBone = fromWidgetFindBone(ob)
                    if matchBone:
                        if matchBone.custom_shape_transform:
                            boneMatrix(ob, matchBone.custom_shape_transform)
                        else:
                            boneMatrix(ob, matchBone)

        return {'FINISHED'}


class BONEWIDGET_OT_matchSymmetrizeShape(Operator):
    """Symmetrize to the opposite side, if it is named with a .L or .R"""
    bl_idname = "bonewidget.symmetrize_shape"
    bl_label = "Symmetrize"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        collection = get_collection(context)
        (widgetsAndBones, activeObject, armature) = findMatchBones(context)

        if not activeObject:
            self.report({"INFO"}, "No active bone or object")
            return {'FINISHED'}

        for bone in widgetsAndBones:
            if activeObject.name.endswith("L"):
                if bone.name.endswith("L") and widgetsAndBones[bone]:
                    symmetrizeWidget(context, bone, collection)
            elif activeObject.name.endswith("R"):
                if bone.name.endswith("R") and widgetsAndBones[bone]:
                    symmetrizeWidget(context, bone, collection)

        return {'FINISHED'}


class BONEWIDGET_OT_addWidgets(Operator):
    """Add selected mesh object to Bone Widget Library"""
    bl_idname = "bonewidget.add_widgets"
    bl_label = "Add Widgets"

    def execute(self, context):
        objects = []
        if context.mode == "POSE":
            for bone in Get.selected_pose_bones(context):
                objects.append(bone.custom_shape)
        else:
            for ob in Get.selected_objects(context):
                if ob.type == 'MESH':
                    objects.append(ob)

        if not objects:
            self.report({'INFO'}, 'Select Meshes or Pose_bones')

        addRemoveWidgets(context, "add", bpy.types.Scene.widget_list[1]['items'], objects)

        return {'FINISHED'}


class BONEWIDGET_OT_removeWidgets(Operator):
    """Remove selected widget object from the Bone Widget Library"""
    bl_idname = "bonewidget.remove_widgets"
    bl_label = "Remove Widgets"

    def execute(self, context):
        objects = context.scene.widget_list
        addRemoveWidgets(context, "remove", bpy.types.Scene.widget_list[1]['items'], objects)
        return {'FINISHED'}
