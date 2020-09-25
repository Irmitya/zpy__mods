import bpy
import os
if os.name == 'nt':
    # There's an error that happens after running this but it DOES reopen the console
    try:
        bpy.ops.wm.console_toggle()
    except:
        pass
