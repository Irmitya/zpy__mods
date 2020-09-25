bl_info = {
    "name": "SpacingSculptor",
    "author": "jasm",
    "description": "f-curves no more",
    "blender": (2, 82, 0),
    "version": (1, 1, 9),
    "location": "View3D > pose Mode > toolbar",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Animation"
}


import bpy
import math
import mathutils
from bpy.props import BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator, Menu, WorkSpaceTool
from threading import Timer
from zpy import Is, keyframe


class OpTemplate:
    @classmethod
    def poll(cls, context):
        if Is.animation_playing(context):
            return False
        # if len(context.selected_pose_bones) == 1:
            # return True
        return bool(context.selected_pose_bones)

    autokeying = None

    def toggle_autokeying(self):
        ts = bpy.context.tool_settings
        if self.autokeying is None:
            # First Check

            self.autokeying = ts.use_keyframe_insert_auto
            if (ts.use_keyframe_insert_auto):
                # op.report({'WARNING'}, 'Auto Insert Keyframe turned off')
                ts.use_keyframe_insert_auto = False
        elif self.autokeying:
            # Enable if it was auto disabled
            ts.use_keyframe_insert_auto = True

    mode: EnumProperty(
        items=[
            ('all', "All Transforms", ""),
            ('location', "Location", ""),
            ('rotation', "Rotation", ""),
            ('scale', "Scale", ""),
        ],
        name="Mode",
        description="Transformation operation type",
        default=None,
        options={'SKIP_SAVE'},
    )


class SPACING_OT_Transform(Operator, OpTemplate):
    """گازی هندەک تشتێن دی دکەت پشتی ترانسفورمینگێ """
    bl_idname = "pose.transformfacade"
    bl_label = "Transform On Curve"

    bl_options = {'UNDO'}

    def __init__(self):
        self.bones = list()

    def execute(self, context):
        poll_any = False
        for bone in context.selected_pose_bones:
            poll_loc = (keyframe.poll_unlock(bone, 'location') and not Is.connected(bone))
            poll_rot = keyframe.poll_unlock(bone, 'rotation')
            poll_scale = keyframe.poll_unlock(bone, 'scale')

            polls = {'location': poll_loc, 'rotation': poll_rot, 'scale': poll_scale}
            if not poll_any and not polls.pop(self.mode):
                for poll in polls:
                    if polls[poll]:
                        self.mode = poll
                        break
                else:
                    continue
            polls = {'location': poll_loc, 'rotation': poll_rot, 'scale': poll_scale}
            if polls[self.mode]:
                self.bones.append(bone)
            poll_any = True

        if not poll_any:
            self.report({'INFO'}, "All transforms locked on selected bones")
            return {'CANCELLED'}

        if (self.mode == 'location'):
            bpy.ops.transform.translate('INVOKE_DEFAULT', True)
        elif (self.mode == 'rotation'):
            bpy.ops.transform.rotate('INVOKE_DEFAULT', True)
        elif (self.mode == 'scale'):
            bpy.ops.transform.resize('INVOKE_DEFAULT', True)
        else:
            """can't use the "all" value"""
            return {'CANCELLED'}
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'LEFTMOUSE', 'RET', 'SPACE'}:
            bpy.ops.pose.transformfacade_exit(dict(selected_pose_bones=self.bones), mode=self.mode)
            return {'FINISHED', 'PASS_THROUGH'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED', 'PASS_THROUGH'}

        return {'PASS_THROUGH'}
        return {'RUNNING_MODAL'}


class SPACING_OT_Transform_exit(Operator, OpTemplate):
    """گازی هندەک تشتێن دی دکەت پشتی ترانسفورمینگێ """
    bl_idname = "pose.transformfacade_exit"
    bl_label = "Transform On Curve"

    def execute(self, context):
        self.toggle_autokeying()
        self.bones = context.selected_pose_bones
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        """In modal to execute after the builtin transform operator"""
        # if (self.mode == 'location'):
            # ks = 'Location'
        # elif (self.mode == 'rotation'):
            # ks = 'Rotation'
        # elif (self.mode == 'scale'):
            # ks = 'Scaling'

        # bpy.ops.anim.keyframe_insert(type=ks, confirm_success=False)

        break_curves = dict()
        for bone in self.bones:
            break_curves[bone] = list()
            curves = {fc: len(fc.keyframe_points) for fc in get_bone_curve(bone, self.mode)}
            getattr(keyframe, self.mode)(context, bone, insert_key=True)
            for fc in get_bone_curve(bone, self.mode):
                if len(fc.keyframe_points) <= 2:
                    continue
                if len(fc.keyframe_points) != curves.get(fc):
                    break_curves[bone].append(fc)
                    # Only remove new keyframes; never old keyframes

        if break_curves:
            global _bone_curves
            _bone_curves = dict()
            for bone, data in break_curves.items():
                _bone_curves[repr(bone)] = data
            bpy.ops.pose.frame_ot_operation(dict(bone_curves=list(break_curves)), adjust=False, mode=self.mode)

        self.toggle_autokeying()
        return {'FINISHED'}


class SPACING_OT_TransformOffset(Operator, OpTemplate):
    bl_idname = "pose.transformoffset"
    bl_label = "TransformOffset"
    bl_description = "Tranform bone and offset values for all keys in action"

    def __init__(self):
        self.bones = dict()

    def execute(self, context):
        current_frame = context.scene.frame_current

        poll_any = False
        for bone in context.selected_pose_bones:
            poll_loc = (keyframe.poll_unlock(bone, 'location') and not Is.connected(bone))
            poll_rot = keyframe.poll_unlock(bone, 'rotation')
            poll_scale = keyframe.poll_unlock(bone, 'scale')

            polls = {'location': poll_loc, 'rotation': poll_rot, 'scale': poll_scale}
            if not poll_any and not polls.pop(self.mode):
                for poll in polls:
                    if polls[poll]:
                        self.mode = poll
                        break
                else:
                    continue
            polls = {'location': poll_loc, 'rotation': poll_rot, 'scale': poll_scale}
            if polls[self.mode]:
                self.bones[bone] = type('', (), {})
            poll_any = True

        if not poll_any:
            self.report({'INFO'}, "All transforms locked on selected bones")
            return {'CANCELLED'}

        for bone in self.bones:
            self.bones[bone].curves = get_bone_curve(bone, self.mode)

            if (self.mode == 'location'):
                self.bones[bone].current_values = bone.matrix_basis.to_translation()
            elif (self.mode == 'rotation'):
                self.bones[bone].current_values = get_bone_rotation(bone)
                if self.bones[bone].current_values is None:
                    del self.bones[bone]
            elif (self.mode == 'scale'):
                self.bones[bone].current_values = bone.matrix_basis.to_scale()

        if (self.mode == 'location'):
            bpy.ops.transform.translate('INVOKE_DEFAULT')
        elif (self.mode == 'rotation'):
            if not self.bones:
                self.report({'INFO'}, "Cancelled Rotation (can't use Axis Angle)")
                return {'CANCELLED'}

            bpy.ops.transform.rotate('INVOKE_DEFAULT')
        elif (self.mode == 'scale'):
            bpy.ops.transform.resize('INVOKE_DEFAULT')
        else:
            """can't use the "all" value"""
            return {'CANCELLED'}

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'LEFTMOUSE', 'RET', 'SPACE'}:
            global _bones
            _bones = dict()
            for bone in self.bones:
                _bones[repr(bone)] = self.bones[bone]

            bpy.ops.pose.transformoffset_exit(dict(selected_pose_bones=list(self.bones)), mode=self.mode)
            return {'FINISHED', 'PASS_THROUGH'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED', 'PASS_THROUGH'}

        return {'PASS_THROUGH'}
        return {'RUNNING_MODAL'}


class SPACING_OT_TransformOffsetExit(Operator, OpTemplate):
    bl_idname = "pose.transformoffset_exit"
    bl_label = "TransformOffset"
    bl_description = "Tranform bone and offset values for all keys in action"

    def __init__(self):
        self.bones = dict()

    def execute(self, context):
        global _bones
        for bone in context.selected_pose_bones:
            data = _bones.get(repr(bone))
            if data:
                self.bones[bone] = data
        del _bones

        self.toggle_autokeying()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        """In modal to execute after the builtin transform operator"""
        current_frame = context.scene.frame_current

        for bone in self.bones:
            if (self.mode == 'location'):
                now_value = bone.matrix_basis.to_translation()
            elif (self.mode == 'rotation'):
                now_value = get_bone_rotation(bone)
            elif (self.mode == 'scale'):
                now_value = bone.matrix_basis.to_scale()

            delta_values = now_value - self.bones[bone].current_values

            for curve in self.bones[bone].curves:
                delta = delta_values[curve.array_index]
                for key in curve.keyframe_points:
                    # # blender wont allow you change it when they are selected
                    # key.select_control_point = False
                    # key.select_left_handle = False
                    # key.select_right_handle = False

                    # TODO: make it run only in frame range, or on selected keys

                    # using index and not iterator makes it easier (هەر بەرەک جهێ خی یێ بقەرە)
                    key.co.y += delta
                    key.handle_right.y += delta
                    # vector and free need this statement otherwise changing right handle is enough
                    key.handle_left.y += delta

                curve.update()

        self.toggle_autokeying()
        return {'FINISHED'}

    current_values: bpy.props.FloatVectorProperty(size=4)


class SPACING_OT_SmoothCurves(Operator, OpTemplate):
    """پاقشکەرێ کرڤی """
    bl_idname = "pose.smoothingcurves"
    bl_label = "Smooth Curves"

    def __init__(self):
        self.bones = dict()
        self.update_curves = False
        self.easing = True
        self.left_toggle = True
        self.right_toggle = True

    def execute(self, context):
        has_curves = False
        start_frame = end_frame = None

        for bone in context.selected_pose_bones:
            self.bones[bone] = type('', (), {})
            self.bones[bone].prev_frames = []
            self.bones[bone].handles_right_start = []
            self.bones[bone].right_smooth = []

            self.bones[bone].next_frames = []
            self.bones[bone].handles_left_start = []
            self.bones[bone].left_smooth = []

            self.bones[bone].curves = get_bone_curve(bone, self.mode)

            for curve in self.bones[bone].curves:

                cg = get_curve_geographic(curve)
                if ((cg & 4) != 0) or ((cg & 2) != 0):
                    continue

                prev_frame, next_frame = get_pn_frames(curve)
                if None in (next_frame, prev_frame):
                    continue

                if (start_frame is None) or (prev_frame.co.x < start_frame):
                    start_frame = prev_frame.co.x
                if (end_frame is None) or (end_frame < next_frame.co.x):
                    end_frame = next_frame.co.x

                # ma points
                self.bones[bone].next_frames.append(next_frame)
                self.bones[bone].prev_frames.append(prev_frame)

                # intial point
                start_right = (prev_frame.handle_right.x, prev_frame.handle_right.y)
                start_left = (next_frame.handle_left.x, next_frame.handle_left.y)

                self.bones[bone].handles_left_start.append(start_left)
                self.bones[bone].handles_right_start.append(start_right)

                length = (next_frame.co.x - prev_frame.co.x) * self.strength

                left, right = calculate_easing_point(prev_frame.co, next_frame.co, curve, length)

                prev_frame.handle_right = mix(right, start_right, self.transition)
                next_frame.handle_left = mix(left, start_left, self.transition)

                self.bones[bone].left_smooth.append(left)
                self.bones[bone].right_smooth.append(right)

                has_curves = True

        if not has_curves:
            return {'CANCELLED'}

        bpy.ops.zpy.update_motion_paths(start_frame=start_frame, end_frame=end_frame + 1, use_start_end=True)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        update_curves = False
        recalculate = False
        event_input = event.type

        if event.value == 'PRESS':
            if event_input in {'LEFTMOUSE', 'RET', 'SPACE'}:
                bpy.ops.zpy.clear_motion_paths()
                return {'FINISHED'}
            elif event_input in {'RIGHTMOUSE', 'ESC'}:
                for bone in self.bones:
                    for i in range(len(self.bones[bone].next_frames)):
                        self.bones[bone].next_frames[i].handle_left = self.bones[bone].handles_left_start[i]
                        self.bones[bone].prev_frames[i].handle_right = self.bones[bone].handles_right_start[i]
                bpy.ops.zpy.clear_motion_paths()
                return {'CANCELLED'}
            elif event_input == "MIDDLEMOUSE":
                self.easing = not self.easing
                recalculate = True
            elif event_input == "LEFT_ARROW":
                update_curves = True
                self.left_toggle = not self.left_toggle
                for bone in self.bones:
                    for i in range(len(self.bones[bone].next_frames)):
                        self.bones[bone].next_frames[i].handle_left = self.bones[bone].handles_left_start[i]
            elif event_input == "RIGHT_ARROW":
                update_curves = True
                self.right_toggle = not self.right_toggle
                for bone in self.bones:
                    for i in range(len(self.bones[bone].next_frames)):
                        self.bones[bone].prev_frames[i].handle_right = self.bones[bone].handles_right_start[i]

        if (event_input in {'WHEELDOWNMOUSE', 'DOWN_ARROW'}):
            update_curves = True
            if event.ctrl and self.strength > 0.1:
                recalculate = True
                self.strength -= 0.1

            elif self.transition > 0.1:
                if event.shift:
                    self.transition -= 0.01
                else:
                    self.transition -= 0.1
        elif event_input in {'WHEELUPMOUSE', 'UP_ARROW'}:
            update_curves = True
            if event.ctrl and self.strength < 0.9:
                recalculate = True
                self.strength += 0.1

            elif self.transition < 0.9:
                if event.shift:
                    self.transition += 0.01
                else:
                    self.transition += 0.1

        if recalculate:
            update_curves = True

            for bone in self.bones:
                self.bones[bone].right_smooth = []
                self.bones[bone].left_smooth = []

                for i in range(len(self.next_frames)):
                    length = (self.bones[bone].next_frames[i].co.x -
                            self.bones[bone].prev_frames[i].co.x) * self.strength

                    if self.easing:
                        left, right = calculate_easing_point(
                            self.bones[bone].prev_frames[i].co, self.bones[bone].next_frames[i].co, self.bones[bone].curves[i], length)
                    else:
                        left, right = calculate_linear_points(
                            self.bones[bone].prev_frames[i].co, self.bones[bone].next_frames[i].co, length)

                    self.bones[bone].right_smooth.append(right)
                    self.bones[bone].left_smooth.append(left)

        if update_curves:
            for bone in self.bones:
                for i in range(len(self.bones[bone].next_frames)):
                    if self.left_toggle:
                        self.bones[bone].next_frames[i].handle_left = mix(
                            self.bones[bone].handles_left_start[i], self.bones[bone].left_smooth[i], self.transition)
                    if self.right_toggle:
                        self.bones[bone].prev_frames[i].handle_right = mix(
                            self.bones[bone].handles_right_start[i], self.bones[bone].right_smooth[i], self.transition)

            if not self.update_curves:
                self.update_curves = True

        if event.type == 'MOUSEMOVE' and self.update_curves:
            # don't constantly update motion path; it's slow
            bpy.ops.pose.paths_update()
            self.update_curves = False

        return {'RUNNING_MODAL'}

    strength: FloatProperty(name="strength", default=0.5, min=0, max=1)
    transition: FloatProperty(name="transition", default=0.5, min=0, max=1)


class SPACING_OT_RemoveKeyframe(Operator, OpTemplate):
    """کرڤا دبەتە خالا دیار کری """
    bl_idname = "pose.frame_ot_operation"
    bl_label = "Wipe Keyframe from Curve"

    bl_options = {'UNDO'}

    def __init__(self):
        self.bones = dict()
        self.update_curves = False

    def execute(self, context):
        current_frame = context.scene.frame_current
        has_curves = False

        start_frame = end_frame = None

        bone_curves = dict()
        if hasattr(context, 'bone_curves'):
            global _bone_curves

            for bone in context.bone_curves:
                bone_curves[bone] = _bone_curves[repr(bone)]
            del _bone_curves
        else:
            for bone in context.selected_pose_bones:
                bone_curves[bone] = get_bone_curve(bone, self.mode)

        for (bone, curves) in bone_curves.items():
            self.bones[bone] = type('', (), {})
            self.bones[bone].base_keys = dict()

            self.bones[bone].handles_right = []
            self.bones[bone].handles_left = []
            self.bones[bone].scaler = []
            self.bones[bone].mid = []

            for curve in curves:
                cg = get_curve_geographic(curve)
                if ((cg & 4) != 0) or ((cg & 2) != 0):
                    continue

                yc = None

                next_index = math.inf
                prev_index = -1

                next_frame = None
                prev_frame = None

                # ڤی فرەیمی ژێ ببە و خالێ خەزن کە
                for keyframe in curve.keyframe_points:
                    if (keyframe.co.x == current_frame):
                        yc = keyframe.co.y
                        curve.keyframe_points.remove(keyframe, fast=False)

                # هە کەر چ کیفرەیم نەبن ڤێ خالێ بکە خال کو تێ دا دەرباز بیت
                if yc is None:
                    yc = curve.evaluate(current_frame)

                # فرەیمێ پشتی هنگێ و بەریهنگێ بینە
                for keyframe in curve.keyframe_points:
                    frame = keyframe.co.x

                    if frame < current_frame and prev_index < frame:
                        prev_index = frame
                        prev_frame = keyframe

                    elif current_frame < frame and next_index > frame:
                        next_frame = keyframe
                        next_index = frame

                # بیرا من ب ڤێ ناهێت
                if None in (next_frame, prev_frame):
                    continue

                if (start_frame is None) or (prev_frame.co.x < start_frame):
                    start_frame = prev_frame.co.x
                if (end_frame is None) or (end_frame < next_frame.co.x):
                    end_frame = next_frame.co.x

                for base in (prev_frame, next_frame):
                    if base in self.bones[bone].base_keys:
                        continue
                    self.bones[bone].base_keys[base] = type('', (), dict(
                        interpolation=base.interpolation,
                        handle_right_type=base.handle_right_type,
                        handle_right=base.handle_right.copy(),
                        handle_left_type=base.handle_left_type,
                        handle_left=base.handle_left.copy(),
                    ))

                # ١٠٠٪ دێ دڤێ خالا دیراکریرا بوریت
                mid, scaler = Calculate_mid_point(
                    prev_frame, next_frame, mathutils.Vector((current_frame, yc)))

                next_frame.interpolation = 'BEZIER'
                prev_frame.interpolation = 'BEZIER'

                next_frame.handle_left_type = 'FREE'
                prev_frame.handle_right_type = 'FREE'

                # کرڤێ دەسپێکی
                next_frame.handle_left += mid + \
                    (self.strength * scaler) - next_frame.handle_left
                prev_frame.handle_right += mid - \
                    (self.strength * scaler) - prev_frame.handle_right

                # ڤانا ببە مودال دا کارئینەر بشێت سەیترێ سەر قوەتا وی بکەت
                self.bones[bone].handles_left.append(next_frame.handle_left)
                self.bones[bone].handles_right.append(prev_frame.handle_right)

                self.bones[bone].scaler.append(scaler)
                self.bones[bone].mid.append(mid)

                has_curves = True

        if not has_curves:
            return {'CANCELLED'}

        if self.adjust:
            bpy.ops.zpy.update_motion_paths(start_frame=start_frame, end_frame=end_frame + 1, use_start_end=True)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        return {'FINISHED'}

    def modal(self, context, event):

        update_curves = False
        event_input = event.type

        if event_input in {'LEFTMOUSE', 'RET', 'SPACE'} and event.value == 'PRESS':
            bpy.ops.zpy.clear_motion_paths()
            return {'FINISHED'}
        elif event_input == "MIDDLEMOUSE" and event.value == 'PRESS':
            update_curves = True

            for bone in self.bones:
                for s in self.bones[bone].scaler:
                    s.y *= -1
        elif event_input in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            for bone in self.bones:
                for (key, base) in self.bones[bone].base_keys.items():
                    key.interpolation = base.interpolation
                    key.handle_left_type = base.handle_left_type
                    key.handle_left = base.handle_left
                    key.handle_right_type = base.handle_right_type
                    key.handle_right = base.handle_right

            bpy.ops.zpy.clear_motion_paths()
            return {'CANCELLED'}
        # elif event_input == 'MOUSEMOVE':
            # update_curves = True
        elif (event_input in {'WHEELDOWNMOUSE', 'DOWN_ARROW'}):
            update_curves = True
            for bone in self.bones:
                if event.shift:
                    self.strength -= 0.1
                else:
                    self.strength -= 1
        elif event_input in {'WHEELUPMOUSE', 'UP_ARROW'}:
            update_curves = True
            for bone in self.bones:
                if event.shift:
                    self.strength += 0.1
                else:
                    self.strength += 1

        if update_curves:
            for bone in self.bones:
                for i in range(len(self.bones[bone].mid)):
                    self.bones[bone].handles_left[i] += self.bones[bone].mid[i] + \
                        (self.strength * self.bones[bone].scaler[i]) - self.bones[bone].handles_left[i]
                    self.bones[bone].handles_right[i] += self.bones[bone].mid[i] - \
                        (self.strength * self.bones[bone].scaler[i]) - self.bones[bone].handles_right[i]
            if not self.update_curves:
                self.update_curves = True

        if event.type == 'MOUSEMOVE' and self.update_curves:
            # don't constantly update motion path; it's slow
            bpy.ops.pose.paths_update()
            self.update_curves = False

        return {'RUNNING_MODAL'}

    adjust: BoolProperty(default=True)
    strength: FloatProperty(name="strength", default=1, min=0.001, max=10)


class SPACING_OT_RemoveKeyframePieMenu(Operator):
    bl_idname = "pose.spacing_remove_keyframe_pie_menu"
    bl_label = "Show_Pie_Menu"

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="SPACING_MT_RemoveKeyframe")
        return {'FINISHED'}


class SPACING_MT_RemoveKeyframe(Menu):
    bl_label = "select transformation"

    def draw(self, context):
        layout = self.layout

        # using inset key frame 'names'
        pie = layout.menu_pie()
        op = SPACING_OT_RemoveKeyframe.bl_idname
        pie.operator(op, text="Location").mode = "location"
        pie.operator(op, text="Rotation").mode = "rotation"
        pie.operator(op, text="Scaling").mode = "scale"
        pie.operator(op, text="All").mode = "all"


class TweakCurve_Tool(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'POSE'

    bl_idname = "SpacingSculptor.tweckcurve"
    bl_label = "Spacing sculptor"

    bl_description = (
        # "handful set of tool that \n"
        # "makes animating more efficient"
        "G/R/S = Grab/Rotate/Scale"
        # "\nShift + G/R/S = Offset Tranforms for all keys in action"
        "\nCtrl + R = Smooth Curves"
        "\nShift X = Wipe/Convert and current keyframes"
    )

    bl_icon = "ops.generic.select"
    bl_widget = None
    bl_keymap = (
        # tranform facede
        (SPACING_OT_Transform.bl_idname, {"type": 'G', "value": 'PRESS'}, {"properties": [("mode", 'location')]}),
        (SPACING_OT_Transform.bl_idname, {"type": 'R', "value": 'PRESS'}, {"properties": [("mode", 'rotation')]}),
        (SPACING_OT_Transform.bl_idname, {"type": 'S', "value": 'PRESS'}, {"properties": [("mode", 'scale')]}),

        (SPACING_OT_RemoveKeyframePieMenu.bl_idname, {"type": 'X', "value": 'PRESS', 'ctrl': True}, None),
        (SPACING_OT_RemoveKeyframe.bl_idname, {"type": 'X', "value": 'PRESS', 'shift': True}, {'properties': [('adjust', False)]}),
        (SPACING_OT_SmoothCurves.bl_idname, {"type": 'R', "value": 'PRESS', "ctrl": True}, None),

        # # transform offset hotkeys
        # (SPACING_OT_TransformOffset.bl_idname, {"type": 'G', "value": 'PRESS', "shift": True}, {"properties": [("mode", 'location')]}),
        # (SPACING_OT_TransformOffset.bl_idname, {"type": 'R', "value": 'PRESS', "shift": True}, {"properties": [("mode", 'rotation')]}),
        # (SPACING_OT_TransformOffset.bl_idname, {"type": 'S', "value": 'PRESS', "shift": True}, {"properties": [("mode", 'scale')]})
    )

    def draw_settings(context, layout, tool):
        mid_props = tool.operator_properties(
            SPACING_OT_RemoveKeyframe.bl_idname)
        layout.prop(mid_props, "strength", text="break strength")
        layout.separator()

        row = layout.row(align=True)
        smo_props = tool.operator_properties("pose.smoothingcurves")
        row.prop(smo_props, "strength", text="smooth strength")
        row.prop(smo_props, "transition", text="smooth transaction")


def set_angle(piv, angle, length):
    new_X = math.cos(angle) * length
    new_y = math.sin(angle) * length
    return (new_X + piv.x, new_y + piv.y)


def get_rotation(vec):
    return math.atan2(vec.y, vec.x)


def get_bone_rotation(bone):
    mode = bone.rotation_mode
    rotations = []
    if mode == 'AXIS_ANGLE':
        return None
    elif(mode == 'QUATERNION'):
        rotations = bone.matrix_basis.to_quaternion()[:]
    else:
        rotations = bone.matrix_basis.to_euler(mode)[:]

    return mathutils.Vector(rotations)


def get_pn_frames(curve):
    current_frame = bpy.context.scene.frame_current

    next_index = math.inf
    prev_index = -1

    next_frame = None
    prev_frame = None

    for keyframe in curve.keyframe_points:
        frame = keyframe.co.x

        if frame < current_frame and prev_index < frame:
            prev_index = frame
            prev_frame = keyframe

        elif current_frame < frame and next_index > frame:
            next_frame = keyframe
            next_index = frame

    return (prev_frame, next_frame)


def get_bone_curve(bone, requre_path="all"):
    curves = []
    anim = bone.id_data.animation_data

    if anim is not None and anim.action is not None:
        for curve in anim.action.fcurves:

            curve_name = curve.data_path.split('"')[1]
            curve_data_path = curve.data_path.split('.')[-1].split('_')[0]

            if curve.lock or curve_name != bone.name or (requre_path != "all" and curve_data_path != requre_path):
                continue

            curves.append(curve)

    return curves


def get_curve_geographic(curve):
    # 0 is default ,1 there is keyframe here , 4 curser at last keyframe  , 2 curser at starting keyframe
    r = 0
    current_frame = bpy.context.scene.frame_current
    maxkey = 0
    minkey = math.inf
    x = None
    for keyframe in curve.keyframe_points:
        x = keyframe.co.x
        if x == current_frame:
            r |= 1
        if x > maxkey:
            maxkey = x
        if x < minkey:
            minkey = x

    if current_frame < minkey + 1:
        r |= 2

    elif current_frame > maxkey - 1:
        r |= 4

    return r


def Calculate_mid_point(prev_frame, next_frame, mid_point):

    mid = mathutils.Vector(
        (mid_point - (prev_frame.co * 0.125) - (next_frame.co * 0.125))) / 0.75

    prev_frame.handle_right = mid.x, mid.y
    next_frame.handle_left = mid.x, mid.y

    # ڤێ خالێ ئاسایێ بکە
    tx, ty = prev_frame.co - next_frame.co
    total = tx + ty
    return mid, mathutils.Vector((tx / total, ty / total))


def calculate_easing_point(prev_co, next_co, curve, weight):
    x = next_co.x + 1
    vec = mathutils.Vector((x, curve.evaluate(x)))
    angle = get_rotation(next_co - vec)
    length = set_angle(next_co, angle, weight)

    x = prev_co.x - 1
    vec = mathutils.Vector((x, curve.evaluate(x)))
    angle = get_rotation(prev_co - vec)
    rotation = set_angle(prev_co, angle, weight)
    return length, rotation


def calculate_linear_points(prev_co, next_co, weight):
    angle = get_rotation(next_co - prev_co)
    length = set_angle(next_co, angle + math.pi, weight)
    rotation = set_angle(prev_co, angle, weight)
    return length, rotation


def mix(veca, vecb, t=0.5):
    x = (t * vecb[0]) + ((1 - t) * veca[0])
    y = (t * vecb[1]) + ((1 - t) * veca[1])
    return (x, y)


def register():
    bpy.utils.register_tool(TweakCurve_Tool, separator=True)


def unregister():
    bpy.utils.unregister_tool(TweakCurve_Tool)
