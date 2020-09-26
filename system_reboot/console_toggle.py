import bpy
import os


def toggle():
    if os.name == 'nt':
        # Only open console window, for Windows OS
        bpy.ops.wm.console_toggle()


if __name__ == '__main__':
    toggle()
