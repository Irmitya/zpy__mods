import bpy
from math import pi
from bpy.props import *
from bpy.types import AddonPreferences, PropertyGroup
from zpy import utils


class Mod_Preferences(AddonPreferences, utils.Preferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        self.draw_keymaps(context)

        #####################################
        # Cenda Tools >> Change Frame / Frame Drag
        layout.prop(self.change_frame, 'boolSmoothDrag')

        if(self.change_frame.boolSmoothDrag):
            layout.prop(self.change_frame, 'boolSmoothSnap')
        layout.prop(self.change_frame, 'boolLoopTimeline')
        ######################################

        ######################################
        # boneWidget
        row = layout.row()
        col = row.column()
        col.prop(self.bone_widgets, "widget_prefix", text="Widget Prefix")
        #add symmetry suffix later
        #col.prop(self, "symmetry_suffix", text="Symmetry suffix")
        col.prop(self.bone_widgets, "bonewidget_collection_name", text="Collection name")
        ######################################

    class bone_widgets(PropertyGroup):
        keep_settings: BoolProperty(
            name="Keep Settings",
            description="Keep settings from operator tweaks",
            default=True,
            options={'SKIP_SAVE'},
        )
        relative_size: BoolProperty(
            name="Relative size",
            description="Widget size proportionnal to Bone size",
            default=True,
        )
        global_size: FloatProperty(
            name="Global Size",
            default=1.0,
            description="",
            options={'SKIP_SAVE'},
        )
        slide: FloatVectorProperty(
            name="Slide",
            description="",
            default=(0.0, 0.0, 0.0),
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
        scale: FloatVectorProperty(
            name="Scale",
            description="scale",
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
        mirror: BoolProperty(
            name="Mirror",
            description="Mirror X values when selecting Left and Right bones",
            default=True,
        )

        # widget prefix
        widget_prefix: StringProperty(
            name="Bone Widget prefix",
            description="Choose a prefix for the widget objects",
            default="WGT-",    # Rigify
            # default="WDGT_",  # Original
        )
        '''
        #symmetry suffix (will try to implement this later)
        symmetry_suffix: EnumProperty(
            name="Bone Widget symmetry suffix",
            description="Choose a naming convention for the symmetrical widgets",
            default=".L",
        )
        '''
        # collection name
        bonewidget_collection_name: StringProperty(
            name="Bone Widget collection name",
            description="Choose a name for the collection the widgets will appear",
            default="Widgets",  # Rigify
            # default="WDGT_shapes",
        )
    bone_widgets: utils.register_pointer(bone_widgets)

    class change_frame(PropertyGroup):
        boolSmoothDrag: BoolProperty(
            name="Smooth Drag",
            default=True,
        )
        boolSmoothSnap: BoolProperty(
            name="Snap after drag",
            default=True,
        )
        boolLoopTimeline: BoolProperty(
            name="Loop Timeline",
            default=True,
            description="Loop start/end of timeline",
        )
    change_frame: utils.register_pointer(change_frame)
