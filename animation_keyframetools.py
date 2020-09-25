# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import FloatProperty, FloatVectorProperty
from bpy.types import Operator, Menu
from copy import deepcopy
from mathutils import Vector
from zpy import Get, Is, register_keymaps, utils
km = register_keymaps()

bl_info = {
    "name": "Keyframe Tools",
    "author": "quollism",
    "version": (0, 6, 1),
    "blender": (2, 80, 0),
    "description": "Some helpful tools for working with keyframes. Inspired by Alan Camilo's animBot toolset.",
    "warning": "Pre-release software. Only armature animation is supported so far. Working on it!",
    "category": "Animation",
    'wiki_url': "https://github.com/quollism/blender-keyframetools/tree/2.8compatible",
}

addon_keymaps = []


def get_selected_keys_and_extents():
    context = bpy.context
    pbones = context.selected_pose_bones
    if pbones is None:
        pbones = []
    curve_datas = []
    selected = []
    objects = []
    bones = []
    fcurves = []

    try:
        only_selected = context.space_data.dopesheet.show_only_selected
        show_hidden = context.space_data.dopesheet.show_hidden
    except:
        only_selected = True
        show_hidden = False

    def add_obj(obj):
        if show_hidden is False and not Is.visible(context, obj):
            return None
        if obj not in selected:
            selected.append(obj)

    def add_bone(b):
        if only_selected and not b.bone.select:
            return None
        add_obj(b.id_data)
        bones.append(b)

    for obj in Get.objects(context):
        if show_hidden is False and not Is.visible(context, obj):
            continue

        # Add object and bones
        if not (only_selected and not Is.selected(obj)):
            add_obj(obj)
        if obj.pose is not None:
            for (name, pbone) in obj.pose.bones.items():
                if any((only_selected is False, Is.selected(obj), pbone in pbones,)):
                    add_bone(pbone)

    # Add fcurves from objects
    for obj in selected:
        anim = obj.animation_data
        if anim and anim.action:
            fcurves.extend([(obj, fc) for fc in anim.action.fcurves])

    # Scan fcurves for keyframes
    for obj, curve in fcurves:
        if curve.hide or curve.lock or not curve.select:
            continue
        first_co = None
        points = None
        last_co = None
        path = curve.data_path

        # Read path to get target's name
        if (path.startswith('pose.bones')):
            # btype =   'BONE'
            # bpath =   path.split('"]', 1)[1]      ## Transforms and custom prop
            # if (bpath.startswith('.')):       ## constraints?
                # bpath =   bpath.split('.', 1)[1]
            bname = (path.split('["', 1)[1].split('"]', 1)[0])
            bone = obj.pose.bones.get(bname)
        elif (path.startswith('bones')):  # data.bones
            # btype = 'BONE'
            # bpath = path.split('"].', 1)[1]
            bname = (path.split('["', 1)[1].split('"]', 1)[0])
            bone = obj.bones.get(bname)
        else:
            # btype = 'OBJECT'
            # bpath = path
            bname = obj.name
            bone = obj

        if (bone is None and curve.is_valid is True) or (bone is not None and bone != obj and bone not in bones):
            # Bone not selected
            continue

        keyframes_referenced = []
        keyframes_data = []
        for keyframe in curve.keyframe_points:
            if keyframe.select_control_point:
                if first_co is None:
                    first_co = keyframe.co
                else:
                    last_co = keyframe.co
                keyframes_referenced.append(keyframe)
                keyframes_data.append({
                    'co': deepcopy(keyframe.co),
                    'handle_left': deepcopy(keyframe.handle_left),
                    'handle_right': deepcopy(keyframe.handle_right)
                })  # needs to be all three data points!
        if last_co is not None:
            curve_datas.append([keyframes_referenced, first_co, last_co, keyframes_data, curve])
    return curve_datas


class GRAPH_OT_flatten_keyframes(Operator):
    bl_description = "Converges keys and handles to a linear fit between the first and last keyframe of the selection"
    bl_idname = "graph.flatten_keyframes"
    bl_label = "Flatten Keyframes"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'NONE'
    bl_context = 'EDIT_CURVE'
    bl_options = {'UNDO'}
    add_to_menu = True

    def execute(self, context):
        utils.update_keyframe_points(context)
        curve_datas = get_selected_keys_and_extents()
        for curve_data in curve_datas:
            slopeMaker = keyframe_calculator(curve_data[1], curve_data[2])
            for i, keyframe in enumerate(curve_data[0]):
                keyframe.co[1] = slopeMaker.linear_fit(keyframe.co[0])
                keyframe.handle_left[1] = slopeMaker.linear_fit(keyframe.handle_left[0])
                keyframe.handle_right[1] = slopeMaker.linear_fit(keyframe.handle_right[0])
        return {'FINISHED'}


class keyframe_calculator():
    def __init__(self, first_co, last_co):
        self.start_frame = first_co[0]
        self.start_value = first_co[1]
        self.finish_frame = last_co[0]
        self.finish_value = last_co[1]
        self.length = last_co[0] - first_co[0]
        self.height = last_co[1] - first_co[1]

    def linear_fit(self, frame):
        position = (frame - self.start_frame) / self.length
        unadjusted_value = position * self.height
        final_value = self.start_value + unadjusted_value
        # print("value for "+str(frame)+" calculated at "+str(final_value)+" from unadjusted value "+str(unadjusted_value))
        return final_value

    def flatten_exaggerate(self, frame, orig_value, factor):
        linear_value = self.linear_fit(frame)
        final_value = (orig_value - linear_value) * factor + linear_value
        # print("value for "+str(frame)+" calculated at "+str(final_value))
        return final_value

    # TODO: a nicer way to handle out-of-bounds frames
    def ease(self, frame, exponent, orig_value):
        position = (frame - self.start_frame) / self.length
        if position < 0 or position > 1:
            return orig_value  # do nothing for now
        # if exponent is 0.0 then we can just calculate the linear case and go home for the day
        if exponent != 0.0:
            # ensure exponent never drifts beyond anything usable
            safe_exponent = max(1, min(10, (abs(exponent) + 1)))
            # invert the position to get an inverse curve
            if exponent < 0:
                position = 1 - position
            position = pow(position, safe_exponent)
        # invert the position back again so we don't get an upside-down curve
        if exponent < 0:
            position = 1 - position
        final_value = self.start_value + (position * self.height)
        return final_value


class GRAPH_OT_ease_keyframes(Operator):
    bl_description = "Puts keys and handles along an eased curve between the first and last keyframe of the selection"
    bl_idname = "graph.ease_keyframes"
    bl_label = "Ease Keyframes"
    bl_options = {'UNDO', 'GRAB_CURSOR', 'BLOCKING'}
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'NONE'
    bl_context = 'EDIT_CURVE'
    add_to_menu = True

    def invoke(self, context, event):
        utils.update_keyframe_points(context)
        if context.space_data.type == 'GRAPH_EDITOR':
            self._auto_normalize = context.space_data.use_auto_normalization
            self._initial_mouse = event.mouse_x  # self._initial_mouse = Vector((event.mouse_x, event.mouse_y, 0.0))
            self._curve_datas = get_selected_keys_and_extents()
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be graph editor")
            return {'CANCELLED'}

    def execute(self, context):
        factor = self.offset
        for curve_data in self._curve_datas:
            slopeMaker = keyframe_calculator(curve_data[1], curve_data[2])
            for i, keyframe in enumerate(curve_data[0]):
                keyframe.co[1] = slopeMaker.ease(keyframe.co[0], factor, curve_data[3][i]['co'][1])
                keyframe.handle_left[0] = keyframe.co[0] - 2
                keyframe.handle_left[1] = slopeMaker.ease(keyframe.handle_left[0], factor, curve_data[3][i]['handle_left'][1])
                keyframe.handle_right[0] = keyframe.co[0] + 2
                keyframe.handle_right[1] = slopeMaker.ease(keyframe.handle_right[0], factor, curve_data[3][i]['handle_right'][1])

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            context.space_data.use_auto_normalization = False
            self.offset = (self._initial_mouse - event.mouse_x) * -0.02  # (self._initial_mouse - Vector((event.mouse_x, event.mouse_y, 0.0))) * -0.02
            self.execute(context)
            context.area.header_text_set("Ease Factor %.4f" % (self.offset))  # ("Ease Factor %.4f" % (self.offset[0]))

        elif event.type == 'LEFTMOUSE':
            context.space_data.use_auto_normalization = self._auto_normalize
            for curve_data in self._curve_datas:
                for i, keyframe in enumerate(curve_data[0]):
                    keyframe.handle_left_type = 'FREE'
                    keyframe.handle_right_type = 'FREE'
            context.area.header_text_set(None)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.space_data.use_auto_normalization = self._auto_normalize
            for curve_data in self._curve_datas:
                for i, keyframe in enumerate(curve_data[0]):
                    keyframe.co[1] = curve_data[3][i]['co'][1]
                    keyframe.handle_left[1] = curve_data[3][i]['handle_left'][1]
                    keyframe.handle_right[1] = curve_data[3][i]['handle_right'][1]
                curve_data[4].update()
            context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    offset: FloatProperty(name="Offset")  # FloatVectorProperty( name="Offset", size=3 )


class GRAPH_OT_flatten_exaggerate_keyframes(Operator):
    bl_description = "Scales keys and handles to/from a linear fit between the first and last keyframe of the selection"
    bl_idname = "graph.flatten_exaggerate_keyframes"
    bl_label = "Flatten/Exaggerate Keyframes"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'NONE'
    bl_context = 'EDIT_CURVE'
    bl_options = {'UNDO', 'GRAB_CURSOR', 'BLOCKING'}
    add_to_menu = True

    def invoke(self, context, event):
        utils.update_keyframe_points(context)
        if context.space_data.type == 'GRAPH_EDITOR':
            self._auto_normalize = context.space_data.use_auto_normalization
            self._initial_mouse = event.mouse_x  # Vector((event.mouse_x, event.mouse_y, 0.0))
            self._curve_datas = get_selected_keys_and_extents()
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be graph editor")
            return {'CANCELLED'}

    def execute(self, context):
        for curve_data in self._curve_datas:
            slopeMaker = keyframe_calculator(curve_data[1], curve_data[2])
            shifted_offset = self.offset + 1  # self.offset[0] + 1
            for i, keyframe in enumerate(curve_data[0]):
                keyframe.co[1] = slopeMaker.flatten_exaggerate(
                    keyframe.co[0], curve_data[3][i]['co'][1], shifted_offset)
                keyframe.handle_left[1] = slopeMaker.flatten_exaggerate(
                    keyframe.handle_left[0], curve_data[3][i]['handle_left'][1], shifted_offset)
                keyframe.handle_right[1] = slopeMaker.flatten_exaggerate(
                    keyframe.handle_right[0], curve_data[3][i]['handle_right'][1], shifted_offset)

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            context.space_data.use_auto_normalization = False
            self.offset = (self._initial_mouse - event.mouse_x) * -0.01  # (self._initial_mouse - Vector((event.mouse_x, event.mouse_y, 0.0))) * -0.01
            self.execute(context)
            context.area.header_text_set("Flatten/Exaggerate Factor %.4f" % (self.offset + 1))  # ("Flatten/Exaggerate Factor %.4f" % (self.offset[0] + 1))

        elif event.type == 'LEFTMOUSE':
            context.space_data.use_auto_normalization = self._auto_normalize
            context.area.header_text_set(None)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.space_data.use_auto_normalization = self._auto_normalize
            for curve_data in self._curve_datas:
                for i, keyframe in enumerate(curve_data[0]):
                    keyframe.co[1] = curve_data[3][i]['co'][1]
                    keyframe.handle_left[1] = curve_data[3][i]['handle_left'][1]
                    keyframe.handle_right[1] = curve_data[3][i]['handle_right'][1]
                curve_data[4].update()
            context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    offset: FloatProperty(name="Offset")  # FloatVectorProperty( name="Offset", size=3 )


# BUGGY
class keyframetools_ShareKeys:  # (Operator):
    bl_description = "Shares keys between visisble animation channels in dope sheet"
    bl_idname = "action.share_keyframes"
    bl_label = "Share Keyframes"
    bl_options = {'UNDO'}
    add_to_menu = True

    def execute(self, context):
        # so the vague problem with this
        # is that it overwrites keys from the original
        # which is not what we want
        # but hey better than nothing
        # store current frame from this scene in return_frame
        start_frame = context.scene.frame_current
        context.scene.frame_current = 1
        last_keyed_frame = 0
        bpy.ops.screen.keyframe_jump(next=True)
        #   if current keyframe same as last_keyed frame, break loop
        while last_keyed_frame != context.scene.frame_current:
                # go to "first key"
                # loop:
            #   insert keyframe: bpy.ops.action.keyframe_insert
            bpy.ops.action.keyframe_insert(type='ALL')
            #   record current frame in last_keyed_frame
            last_keyed_frame = context.scene.frame_current
            #   advance to next keyframe: bpy.ops.action.
            bpy.ops.screen.keyframe_jump(next=True)
        # set frame back to return_frame
        context.scene.frame_current = start_frame
        return {'FINISHED'}


class GRAPH_OT_place_cursor_and_pivot(Operator):
    bl_description = "Places 2D cursor at selection and sets pivot mode to 2D cursor"
    bl_idname = "graph.place_cursor_and_pivot"
    bl_label = "Place Cursor and Pivot"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'NONE'
    bl_context = 'EDIT_CURVE'
    bl_options = {'REGISTER', 'UNDO_GROUPED'}
    # bl_undo_group = ""
    add_to_menu = True

    def execute(self, context):
        bpy.ops.graph.frame_jump()
        context.space_data.pivot_point = 'CURSOR'
        # now deselect everything
        bpy.ops.graph.select_all(action='DESELECT')
        return {'FINISHED'}


# def keyframetools_dopesheet_extra_controls(self, context):
    # if context.space_data.mode in ('DOPESHEET', 'ACTION'):
    #     layout = self.layout
    #     layout.operator("action.share_keys", text="Share Keys")


# class GRAPH_MT_keyframetools_menu(bpy.types.Menu):
    # bl_label = "Keyframe Tools"
    # # just graph editor for now
    # bl_idname = "GRAPH_MT_keyframetools_menu"
    # add_to_menu = False

    # def draw(self, context):
    #     if context.space_data.type == 'GRAPH_EDITOR':
    #         layout = self.layout
    #         for c in classes:
    #             if c.add_to_menu:
    #                 layout.operator(c.bl_idname)
    #     # else nothing


class GRAPH_MT_PIE_keyframetools_piemenu(Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "Keyframe Tools"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'NONE'
    bl_context = 'EDIT_CURVE'
    add_to_menu = False

    def draw(self, context):
        layout = self.layout
        if context.space_data.type == 'GRAPH_EDITOR':
            pie = layout.menu_pie()
            pie.operator("graph.place_cursor_and_pivot", text="Place Cursor and Pivot", icon='CURSOR')
            icon = 'ARROW_LEFTRIGHT'
            pie.operator("graph.flatten_keyframes", text="Flatten Keys", icon=icon)
            pie.operator("graph.flatten_exaggerate_keyframes", text="Flatten/Exaggerate Keys", icon=icon)
            pie.operator("graph.ease_keyframes", text="Ease Keys", icon=icon)


# classes = (
    # # below operator is buggy mcbugbugs
    # # keyframetools_ShareKeys,
    # GRAPH_OT_flatten_keyframes,
    # GRAPH_OT_flatten_exaggerate_keyframes,
    # GRAPH_OT_ease_keyframes,
    # GRAPH_OT_place_cursor_and_pivot,
    # # GRAPH_MT_keyframetools_menu,
    # GRAPH_MT_PIE_keyframetools_piemenu,
    # )


def register():
    args = dict(name='Graph Editor')
    # km.add('graph.flatten_keyframes', type='A', ctrl=True, **args)
    km.add('graph.ease_keyframes', type='A', shift=True, **args)
    km.add('graph.flatten_exaggerate_keyframes', type='D', **args)
    # km.add('graph.place_cursor_and_pivot', type='G', shift=True, ctrl=True, **args)

    # # for c in classes:
    # #     bpy.utils.register_class(c)
    # # bpy.types.DOPESHEET_HT_header.append(keyframetools_dopesheet_extra_controls)
    # wm = bpy.context.window_manager
    # km = wm.keyconfigs.addon.keymaps.new(name='Graph Editor', space_type='GRAPH_EDITOR')
    # # pie menu!
    #     # kmi = km.keymap_items.new('wm.call_menu_pie', 'Z', 'PRESS', shift=True)
    #     # kmi.properties.name = 'GRAPH_MT_PIE_keyframetools_piemenu'
    #     # addon_keymaps.append((km, kmi))
    # # shortcuts for graph editor
    # kmi = km.keymap_items.new('graph.flatten_keyframes', 'A', 'PRESS', ctrl=True)
    # addon_keymaps.append((km, kmi))
    # kmi = km.keymap_items.new('graph.flatten_exaggerate_keyframes', 'D', 'PRESS')
    # addon_keymaps.append((km, kmi))
    # kmi = km.keymap_items.new('graph.ease_keyframes', 'A', 'PRESS', shift=True)
    # addon_keymaps.append((km, kmi))
    # kmi = km.keymap_items.new('graph.place_cursor_and_pivot', 'G', 'PRESS', shift=True, ctrl=True)
    # addon_keymaps.append((km, kmi))


def unregister():
    km.remove()
    # # for c in classes:
    # #     bpy.utils.unregister_class(c)
    # # bpy.types.DOPESHEET_HT_header.remove(keyframetools_dopesheet_extra_controls)
    # for km, kmi in addon_keymaps:
    #     km.keymap_items.remove(kmi)
    #     addon_keymaps.clear()
