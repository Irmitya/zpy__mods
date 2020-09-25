import bpy


class RIGIFY_OT_copy_rigify_type(bpy.types.Operator):
    bl_description = "Transfer all rigify parameters values from the active bone to the selected"
    bl_idname = 'zpy.copy_rigify_type'
    bl_label = "Copy Parameters"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        active = context.active_pose_bone

        for bone in context.selected_pose_bones:
            if bone == active:
                continue
            for var in ('rigify_type', 'rigify_parameters'):
                if bone.get(var):
                    del bone[var]
                if active.get(var):
                    bone[var] = active[var]

        return {'FINISHED'}


class BONE_PT_rigify_buttons_copy_parameters(bpy.types.Panel):
    bl_parent_id = 'BONE_PT_rigify_buttons'
    bl_label = ""  # Rigify Type
    bl_options = {'HIDE_HEADER'}
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_context = 'bone'

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        layout.operator('zpy.copy_rigify_type')
