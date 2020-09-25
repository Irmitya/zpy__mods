import bpy
from .functions import readWidgets
from .. import __package__ as __addon__
from zpy import is27, is28, utils


class BONEWIDGET_PT_posemode_panel(bpy.types.Panel):
    bl_label = "Bone Widget"
    bl_category = "Tool"  # "RIG Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_idname = 'VIEW3D_PT_bw_posemode_panel'

    @classmethod
    def poll(cls, context):
        return context.mode in ('POSE', 'OBJECT', 'EDIT_MESH')

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        if len(bpy.types.Scene.widget_list[1]['items']) < 6:
            row.prop(context.scene, 'widget_list', expand=True)
        else:
            row.prop(context.scene, 'widget_list', expand=False, text="")

        row = layout.row(align=True)
        row.menu('BONEWIDGET_MT_bw_specials', icon='DOWNARROW_HLT', text="")
        create = row.operator('bonewidget.create_widget', icon='OBJECT_DATAMODE')

        if context.mode == "POSE":
            row.operator('bonewidget.edit_widget', icon='OUTLINER_DATA_MESH')
            row.operator('bonewidget.remove_widget', text="", icon='X')
        else:
            row.operator('bonewidget.return_to_armature', icon='LOOP_BACK', text='To bone')

        if bpy.ops.bonewidget.create_widget.poll():
            pr = utils.prefs(__addon__).bone_widgets

            row = layout.row()
            row.label(text="Slide:", icon=('ORIENTATION_GLOBAL', 'MAN_TRANS')[is27])
            row.prop(pr, 'mirror')
            layout.row().prop(pr, 'slide', text="")
            create.slide = pr.slide

            layout.label(text="Rotation:", icon=('ORIENTATION_LOCAL', 'MAN_ROT')[is27])
            layout.row().prop(pr, 'rotate', text="")
            create.rotate = pr.rotate

            row = layout.row()
            row.label(text="Scale", icon=('ORIENTATION_VIEW', 'MAN_SCALE')[is27])
            row.prop(pr, 'relative_size')
            layout.prop(pr, 'global_size', expand=False)
            layout.row().prop(pr, 'scale', text="")
            create.relative_size = pr.relative_size
            create.global_size = pr.global_size
            create.scale = pr.scale


class BONEWIDGET_MT_bw_specials(bpy.types.Menu):
    bl_label = "Bone Widget Specials"

    def draw(self, context):
        layout = self.layout

        if is28: i = ('MOD_MIRROR', 'ADD', 'REMOVE')
        if is27: i = ('MOD_MULTIRES', 'ZOOMIN', 'ZOOMOUT')

        layout.operator('bonewidget.symmetrize_shape', icon=i[0])
        layout.operator('bonewidget.match_bone_transforms', icon='GROUP_BONE')

        layout.operator('bonewidget.add_widgets', icon=i[1], text="Add Widgets")
        layout.operator('bonewidget.remove_widgets', icon=i[2], text="Remove Widgets")

        pr = utils.prefs(__addon__).bone_widgets
        layout.prop(pr, 'keep_settings')


def register():
    items = []
    for (key, value) in readWidgets().items():
        items.append(key)

    itemsSort = []
    for key in sorted(items):
        # itemsSort.append((key.replace(' ', '_'), key, ""))
        itemsSort.append((key, key, ""))

    bpy.types.Scene.widget_list = bpy.props.EnumProperty(
        name="Shape", items=itemsSort, description="Shape")


def unregister():
    del bpy.types.Scene.widget_list
