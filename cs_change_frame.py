from zpy import utils, register_keymaps, is27, is28
from bpy.types import Operator
from bpy.props import BoolProperty, FloatProperty, IntProperty
import bpy
km = register_keymaps()


bl_info = {
    "name": "Change Frame",
    "author": "Cenek Strichel",
    "version": (1, 0, 5),
    "blender": (2, 80, 0),
    "location": "Add 'view3d.change_frame_drag' to Input Preferences under 3D View (Global)",
    "description": "Change frame by dragging",
    "category": "Cenda Tools",
    "wiki_url": "https://github.com/CenekStrichel/CendaTools/wiki",
    "tracker_url": "https://github.com/CenekStrichel/CendaTools/issues"
}


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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****


class CENDA_OT_ChangeFrame(Operator):
    bl_description = "Change frame with dragging"
    bl_idname = "view3d.change_frame_drag"
    bl_label = "Change Frame Drag"
    bl_options = {'UNDO_GROUPED', 'INTERNAL', 'GRAB_CURSOR', 'BLOCKING'}

    autoSensitivity: BoolProperty(name="Auto Sensitivity")
    defaultSensitivity: FloatProperty(name="Sensitivity", default=5)
    renderOnly: BoolProperty(name="Render Only", default=False)
    sensitivity_factor: IntProperty(default=0)

    global frameOffset
    global mouseOffset
    global sensitivity
    global previousManipulator
    global previousOnlyRender
    global StartButton

    @classmethod
    def poll(self, context):
        return True

    def draw_status(SELF, self, context):
        layout = self.layout
        for (icon, text) in SELF.text:
            layout.label(icon=icon, text=text)
            layout.separator_spacer()

    def modal(self, context, event):
        addon_prefs = utils.prefs(__package__).change_frame
        scene = context.scene
        space_data = context.space_data

        def set_text(items=None):
            if is27:
                if items is None:
                    context.area.header_text_set()
                else:
                    string = ""
                    for (icon, text) in items:
                        string += f"{text}    "
                    context.area.header_text_set(string)
            if is28:
                if items is None:
                    bpy.types.STATUSBAR_HT_header.remove(self.draw_status)
                    context.window.workspace.status_text_set(None)
                else:
                    context.window.workspace.status_text_set("")
                    self.text = items

        if scene.use_preview_range:
            start = scene.frame_preview_start
            end = scene.frame_preview_end
        else:
            start = scene.frame_start
            end = scene.frame_end

        scrolled = False
        if event.value == 'PRESS':
            if event.type == 'WHEELUPMOUSE':
                self.sensitivity_factor -= 1
                scrolled = True
            if event.type == 'WHEELDOWNMOUSE':
                self.sensitivity_factor += 1
                scrolled = True

        sensitivity = self.sensitivity
        for i in range(abs(self.sensitivity_factor)):
            if self.sensitivity_factor < 0:
                # sensitivity += sensitivity * 0.1  # faster
                sensitivity *= 1.1  # faster
            else:
                # sensitivity -= sensitivity * 0.1  # slower
                sensitivity *= 0.9  # slower

        looping = addon_prefs.boolLoopTimeline
        # if (event.value == 'PRESS' and event.type == 'CTRL'):
        if (event.value == 'PRESS' and event.type == 'LEFT_CTRL'):
            addon_prefs.boolLoopTimeline = not looping

        # change frame
        if (event.type == 'MOUSEMOVE') or scrolled:

            delta = self.mouseOffset - event.mouse_x
            offset = (-delta * sensitivity) + self.frameOffset

            if looping:

                dist = abs(start - end)

                if (start != end):  # prevent loop freeze/crash
                    if offset > end:
                        while offset > end:
                            offset -= dist
                    elif offset < start:
                        while offset < start:
                            offset += dist

            if (addon_prefs.boolSmoothDrag):
                current = int(offset)
                subframe = offset - int(offset)
                if (current < 0 and subframe) or subframe < 0:
                    # Negative numbers have to offset a little for frame_set
                    current -= 1
                    subframe = 1 - abs(subframe)
                scene.frame_current = current
                scene.frame_subframe = subframe
            else:
                scene.frame_current = offset

        # end of modal
        elif (event.type == self.startButton and event.value == 'RELEASE'):
            set_text()

            # previous viewport setting
            if (context.area.type == 'VIEW_3D'):
                if is27:
                    space_data.show_manipulator = self.previousManipulator

                    if (self.renderOnly):
                        space_data.show_only_render = self.previousOnlyRender
                if is28:
                    space_data.show_gizmo = self.previousManipulator

                    if (self.renderOnly):
                        space_data.overlay.show_overlays = self.previousOnlyRender

            # cursor back
            context.window.cursor_set("DEFAULT")

            # snap back
            if (addon_prefs.boolSmoothSnap):
                scene.frame_subframe = 0

            return {'FINISHED'}

        set_text([
            (('REW'), f"<{start :02}>"),
            (('NONE'), f"({scene.frame_current :05.2f})"),
            (('FF'), f"<{end :02}>"),
            (('MOUSE_MMB_DRAG'), F"Sensitivity: {((sensitivity / self.sensitivity) * 100) :.1f}%"),
            (('PLAY', 'FILE_REFRESH')[looping], f"""{("", "(Loop Animation) Left Ctrl to Disable")[looping]}"""),
            ])

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        addon_prefs = utils.prefs(__package__).change_frame
        scene = context.scene
        space_data = context.space_data

        # hide viewport helpers
        if (context.area.type == 'VIEW_3D'):
            if is27:
                self.previousManipulator = space_data.show_manipulator
                # space_data.show_manipulator = False
            if is28:
                self.previousManipulator = space_data.show_gizmo
                # space_data.show_gizmo = False

            if (self.renderOnly):
                if is27:
                    self.previousOnlyRender = space_data.show_only_render
                    space_data.show_only_render = True
                if is28:
                    self.previousOnlyRender = space_data.overlay.show_overlays
                    space_data.overlay.show_overlays = False

        # start modal
        if (addon_prefs.boolSmoothDrag):
            self.frameOffset = scene.frame_current_final
        else:
            self.frameOffset = scene.frame_current

        self.mouseOffset = event.mouse_x
        self.startButton = event.type

        # cursor
        context.window.cursor_set("SCROLL_X")

        self.text = []
        if is28: bpy.types.STATUSBAR_HT_header.prepend(self.draw_status)
        context.window_manager.modal_handler_add(self)

        found = False

        # auto sensitivity
        if (self.autoSensitivity):

            ratio = (1024 / context.area.width)
            self.sensitivity = (ratio / 10)

            # finding end of frame range
            if (scene.use_preview_range):
                endFrame = scene.frame_preview_end
            else:
                endFrame = scene.frame_end

            self.sensitivity *= (endFrame / 100)

            found = True

        # default
        if (not found):
            self.sensitivity = self.defaultSensitivity / 100

        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)

        return {'RUNNING_MODAL'}


def register():
    args = dict(name='Frames', type='SPACE')
    km.add('view3d.change_frame_drag', **args, value='CLICK_DRAG')
    km.toggle('screen.animation_play', **args, value='PRESS', addon=is27)
    km.add('screen.animation_play', **args, value='CLICK')


def unregister():
    km.remove()
