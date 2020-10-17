# file:///C:\Program%20Files\Blender%20Foundation\Blender\2.91\scripts\addons\rigify\metarig_menu.py
# Rigify's Add Metarig buttons show in the Add Armature despite them only working
# in object mode. The goal here is to overwrite the automated draw function it uses
# to only show the buttons when you can actually use them.

from rigify import metarig_menu


class backup:
    def make_metarig_menu_func(bl_idname, text):
        """ For some reason lambda's don't work for adding multiple menu
            items, so we use this instead to generate the functions.
        """
        def metarig_menu(self, context):
            if context.mode != 'OBJECT':
                return
            self.layout.operator(bl_idname, icon='OUTLINER_OB_ARMATURE', text=text)
        return metarig_menu


    def make_submenu_func(bl_idname, text):
        def metarig_menu(self, context):
            if context.mode != 'OBJECT':
                return
            self.layout.menu(bl_idname, icon='OUTLINER_OB_ARMATURE', text=text)
        return metarig_menu

    draw = None


class overwrite():
    def __init__(self):
        # Save old draw functions
        self.make_metarig_menu_func = metarig_menu.make_metarig_menu_func
        self.make_submenu_func = metarig_menu.make_submenu_func
        metarig_menu.make_metarig_menu_func = backup.make_metarig_menu_func
        metarig_menu.make_submenu_func = backup.make_submenu_func
        self.reload()

    def remove(self):
        metarig_menu.make_metarig_menu_func = self.make_metarig_menu_func
        metarig_menu.make_submenu_func = self.make_submenu_func
        self.reload()

    def reload(self):
        # Reload draw functions
        try:
            metarig_menu.unregister()
        except:
            return

        metarig_menu.metarig_ops.clear()
        metarig_menu.armature_submenus.clear()
        metarig_menu.menu_funcs.clear()

        metarig_menu.create_metarig_ops()
        metarig_menu.create_menu_funcs()
        metarig_menu.create_armature_submenus()

        metarig_menu.register()


def register():
    backup.draw = overwrite()


def unregister():
    backup.draw.remove()
