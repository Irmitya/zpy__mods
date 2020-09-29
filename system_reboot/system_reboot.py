# Add-on information
import sys
import os
import subprocess
import bpy

bl_info = {
    "name": "Reboot",
    "author": "(saidenka) meta-androcto",
    "version": (0, 1),
    "blender": (2, 7),
    "location": "File Menu",
                "description": "Reboot Blender without save",
                "warning": "",
                "wiki_url": "",
                "tracker_url": "",
                "category": "System"
}


class SYS_OT_RestartBlender(bpy.types.Operator):
    bl_idname = "wm.restart_blender"
    bl_label = "Reboot Blender"
    bl_description = "Blender Restart"
    bl_options = {'REGISTER'}

    def execute(self, context):
        py = os.path.join(os.path.dirname(__file__), "console_toggle.py")
        filepath = bpy.data.filepath
        if (filepath != ""):
            subprocess.Popen([sys.argv[0], filepath, '-P', py])
            # subprocess.Popen(
            #     # [sys.argv[0], '--enable-new-depsgraph', '-P', py, filepath])
            #     [sys.argv[0], '', '-P', py, filepath])
            # # ???###subprocess.Popen([sys.argv[0], '', '-P', py, filepath])
            # # subprocess.Popen([sys.argv[0], filepath, '-P', py])
        else:
            subprocess.Popen([sys.argv[0], '-P', py])
            # # subprocess.Popen([sys.argv[0], '--enable-new-depsgraph', '-P', py])
            # subprocess.Popen([sys.argv[0], '', '-P', py])
            # # ???###subprocess.Popen([sys.argv[0], '', '-P', py])
            # # subprocess.Popen([sys.argv[0],'-P', py])
        bpy.ops.wm.quit_blender()
        return {'FINISHED'}


def menu_func(self, context):
    layout = self.layout
    # layout.separator()
    layout.operator(SYS_OT_RestartBlender.bl_idname, icon="PLUGIN")
    # layout.separator()


cls = bpy.types.TOPBAR_MT_file
cls = bpy.types.TOPBAR_MT_app


def register():
    cls.prepend(menu_func)


def unregister():
    cls.remove(menu_func)


if __name__ == "__main__":
    register()
