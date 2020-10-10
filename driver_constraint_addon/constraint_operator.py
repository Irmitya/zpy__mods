'''
Copyright (C) 2016 Andreas Esau
andreasesau@gmail.com

Created by Andreas Esau

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy
from bpy.props import EnumProperty, BoolProperty, IntProperty, FloatProperty, StringProperty
from math import radians, degrees
from mathutils import Vector, Quaternion, Euler
from zpy import Is


class local:
    driver = None


class DRIVER_CONSTRAINT_OT_create(bpy.types.Operator):
    bl_description = "This Operator creates a driver for a shape and connects it to a posebone transformation"
    bl_idname = "object.create_driver_constraint"
    bl_label = "Create Driver Constraint"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        layout = self.layout

        if self.mode == "DRIVER":
            row = layout.row()
            row.label(text="Property Type")
            row.prop(self, "property_type", text="")

            row = layout.split()
            row.label(text="Property Data Path")
            row = row.split(align=True, factor=0.8)
            row.prop(self, "prop_data_path", text="")
            row.prop(self, "prop_data_index", text="")

            row = layout.row()
            row.label(text="Transform Type")
            row.prop(self, "type", text="")

            row = layout.row()
            row.label(text="Space")
            row.prop(self, "space", text="")

            row = layout.row()
            row.label(text="Get Driver Limits")
            row.prop(self, "get_limits_auto", text="")

            row = layout.row()
            col = row.column()
            col = col.row(align=True)
            col.label(text="Driver Limits")
            col.prop(self, 'loop_driver_limits', text="", icon='FILE_REFRESH')
            #
            row1 = row.row(align=True)
            row1.scale_x = 0.9
            col1 = row1.column(align=True)
            col1.prop(self, "min_value", text="Min Value")
            col1.prop(self, "max_value", text="Max Value")
            #
            col2 = row1.column(align=True)
            col2.scale_y = 2.0
            col2.prop(self, "flip_driver_limits", text="",
                      toggle=True, icon="ARROW_LEFTRIGHT")

            row = layout.row()
            row.label(text="Set Driver Limits")
            row.prop(self, "set_driver_limit_constraint", text="")

            row = layout.row()
            row.label(text="Interpolation Type")
            row.prop(self, "interpolation_type", text="")

            row = layout.row().split()
            row.label(text="Extrapolation Type")
            row.row(align=True).prop(self, "extrapolation_type", expand=True)

            row = layout.row()
            col = row.column()
            col.label(text="Property Limits")

            row1 = row.row(align=True)
            row1.scale_x = 0.9
            col1 = row1.column(align=True)
            col1.prop(self, "prop_min_value", text="Min Value")
            col1.prop(self, "prop_max_value", text="Max Value")

            col2 = row1.column(align=True)
            col2.scale_y = 2.0
            col2.prop(self, "flip_property_limits", text="",
                      toggle=True, icon="ARROW_LEFTRIGHT")
        elif self.mode == "ACTION":
            col = layout.row()
            col.prop(self, "action_mode", expand=True)

            if self.action_mode == "ADD_CONSTRAINT":
                col = layout.column()
                row = layout.row()
                row.label(text="Action")
                row.prop(self, "action", text="")

                row = layout.row()
                row.label(text="Transform Type")
                row.prop(self, "type", text="")

                row = layout.row()
                row.label(text="Space")
                row.prop(self, "space", text="")

                row = layout.row()
                col = row.column()
                col.label(text="Property Limits")

                row = layout.row()
                row1 = row.row(align=True)
                row1.scale_x = 0.9
                col1 = row1.column(align=True)
                col1.prop(self, "min_value", text="Min Value")
                col1.prop(self, "max_value", text="Max Value")

                row = layout.row()
                col = row.column()
                col.label(text="Action Range")

                row = layout.row()
                row1 = row.row(align=True)
                row1.scale_x = 0.9
                col1 = row1.column(align=True)
                col1.prop(self, "action_frame_start", text="Start")
                col1.prop(self, "action_frame_end", text="End")
            elif self.action_mode == "DELETE_CONSTRAINT":
                col = layout.column()
                row = layout.row()
                row.label(text="Action")
                row.prop(self, "action_constraint", text="")

    def invoke(self, context, event):
        wm = context.window_manager

        self.driver = None
        if context.active_object.type == "ARMATURE" and context.active_pose_bone is not None:
            self.driver = context.active_pose_bone
        else:  # elif context.active_object.type in ["MESH", "EMPTY"]:
            self.driver = context.active_object

        if len(context.selected_objects) > 1:
            obj = None
            for obj2 in context.selected_objects:
                if obj2 != context.view_layer.objects.active:
                    obj = obj2
                    del obj2
                    break
        else:
            obj = context.selected_objects[0]

        clip = self.get_short_path(wm.clipboard)

        if clip != "":
            try:
                prop_object = get_prop_object(context, clip, obj)

                if (prop_object is None):
                    self.property_type = "OBJECT_PROPERTY"
                else:
                    self.prop_data_path = clip
                    self.property_type = prop_object[1]
                    self.get_prop_value(context, prop_object, obj)
            except AttributeError:
                self.report({'INFO'}, "Selected item(s) don't have what's in the clipboard")
                return {'CANCELLED'}

        if self.get_limits_auto:
            local.driver = self.driver
            self.limit_type = self.set_defaults(context)

        if bpy.data.actions and (self.action in bpy.data.actions):
            action = bpy.data.actions[self.action]
            self.action_frame_end = get_action_length(action)

        return wm.invoke_props_dialog(self)

    def execute(self, context):
        wm = context.window_manager
        context = bpy.context
        scene = context.scene
        active_object = context.active_object

        if self.mode == "DRIVER":
            self.create_property_driver(wm, context, scene, active_object)
        elif self.mode == "ACTION":
            self.create_actions_constraints(context)

        return {'FINISHED'}

    def create_actions_constraints(self, context):
        if self.action_mode == "ADD_CONSTRAINT":
            for bone in context.selected_pose_bones:
                if context.active_pose_bone != bone:
                    const = bone.constraints.new("ACTION")
                    if "LOCAL" in self.space:
                        const.target_space = "LOCAL"
                    elif "WORLD" in self.space:
                        const.target_space = "WORLD"
                    const.target = context.active_object
                    const.subtarget = context.active_pose_bone.name

                    if self.type == "LOC_X":
                        const.transform_channel = "LOCATION_X"
                    elif self.type == "LOC_Y":
                        const.transform_channel = "LOCATION_Y"
                    elif self.type == "LOC_Z":
                        const.transform_channel = "LOCATION_Z"
                    elif self.type == "ROT_X":
                        const.transform_channel = "ROTATION_X"
                    elif self.type == "ROT_Y":
                        const.transform_channel = "ROTATION_Y"
                    elif self.type == "ROT_Z":
                        const.transform_channel = "ROTATION_Z"
                    else:
                        const.transform_channel = self.type

                    const.min = self.min_value
                    const.max = self.max_value
                    const.frame_start = self.action_frame_start
                    const.frame_end = self.action_frame_end
                    const.action = bpy.data.actions[self.action]
            bpy.ops.ed.undo_push(message="Action Constraints generated.")
            self.report({'INFO'}, "Action constraints generated.")
        elif self.action_mode == "DELETE_CONSTRAINT":
            for bone in context.selected_pose_bones:
                for const in bone.constraints:
                    # or (self.action_constraint == "ALL_ACTIONS"):
                    if (const.name == self.action_constraint):
                        # bone.constraints.remove(const)
                        # if self.action_constraint != "ALL_ACTIONS":
                        #    break
                        pass
            bpy.ops.ed.undo_push(message="Action Constraints deleted.")
            self.report({'INFO'}, "Action constraints deleted.")

    def set_defaults(self, context):
        driver_src = self.driver
        if not driver_src:
            return

        # set location
        if (driver_src.location != Vector((0, 0, 0))):
            xyz = [
                abs(driver_src.location.x),
                abs(driver_src.location.y),
                abs(driver_src.location.z),
            ]
            m = max(xyz)
            type = ["LOC_X", "LOC_Y", "LOC_Z"]

            for i, value in enumerate(xyz):
                if xyz[i] == m:
                    self.min_value = 0.0
                    self.max_value = driver_src.location[i]
                    self.type = type[i]
                    break

            return "LIMIT_LOCATION"

        # set rotation
        if driver_src.rotation_mode == "QUATERNION":
            driver_rotation = driver_src.rotation_quaternion.to_euler("XYZ")
        else:
            driver_rotation = driver_src.rotation_euler
        if (Vector((driver_rotation.x, driver_rotation.y, driver_rotation.z)) != Vector((0, 0, 0))):
            xyz = [
                abs(driver_rotation.x),
                abs(driver_rotation.y),
                abs(driver_rotation.z),
            ]
            m = max(xyz)
            type = ["ROT_X", "ROT_Y", "ROT_Z"]

            for i, value in enumerate(xyz):
                if xyz[i] == m:
                    self.min_value = 0.0
                    self.max_value = degrees(driver_rotation[i])
                    self.type = type[i]
                    break

            return "LIMIT_ROTATION"

        # set scale
        if (driver_src.scale != Vector((1, 1, 1))):
            xyz = [
                abs(driver_src.scale.x),
                abs(driver_src.scale.y),
                abs(driver_src.scale.z),
            ]
            xyz_delta = [
                abs(1.0 - driver_src.scale.x),
                abs(1.0 - driver_src.scale.y),
                abs(1.0 - driver_src.scale.z),
            ]
            m_delta = max(xyz_delta)
            m = max(xyz)
            type = ["SCALE_X", "SCALE_Y", "SCALE_Z"]

            for i, value in enumerate(xyz):
                if xyz_delta[i] == m_delta:
                    self.min_value = 1.0
                    self.max_value = xyz[i]
                    self.type = type[i]
                    break

            return "LIMIT_SCALE"

    def get_prop_value(self, context, prop_object, obj):
        (data, prop_type) = prop_object

        if (data == obj) and (self.property_type == "OBJECT_DATA_PROPERTY"):
            data = data.data

        if prop_type in ["MODIFIER_PROPERTY", "OBJECT_CONSTRAINT_PROPERTY"]:
            data_path = self.prop_data_path.split(".")[1]
        elif prop_type in ["BONE_PROPERTY"]:
            # this is used for props of that type: bones["bone_name"]["property_name"]
            if self.prop_data_path.rfind("]") == len(self.prop_data_path) - 1:
                from_idx = self.prop_data_path.rfind("[\"")
                to_idx = self.prop_data_path.rfind("\"]") + 1
                data_path = self.prop_data_path[from_idx:to_idx]
            # this is used for props of that type: bones["bone_name"].property_name
            else:
                data_path = self.prop_data_path.split("\"].")[1]
        elif prop_type in ["BONE_CONSTRAINT_PROPERTY"]:
            string_elements = self.prop_data_path.split(".")
            data_path = string_elements[len(string_elements) - 1]
        elif prop_type in ["NODE_PROPERTY"]:
            data_path = "default_value"
        elif "." in self.prop_data_path:
            data, path = get_property_and_path(obj, self.prop_data_path)
            if path is not None:
                data_path = path
            else:
                data_path = ""
        else:
            data_path = self.prop_data_path

        value = getattr(data, data_path, None)
        if Is.iterable(value):
            value = value[self.prop_data_index]

        if (value is not None):
            if data_path in ('scale', 'bbone_scaleinx', 'bbone_scaleiny', 'bbone_scaleoutx', 'bbone_scaleouty'):
                self.prop_min_value = 1

            if data_path in ('influence', 'value'):
                # Set the driver value to the default of on/1  (shapekeys/constraints)
                self.prop_max_value = 1
            else:
                # Use the current value of the target property
                self.prop_max_value = value

        return value

    def create_property_driver(self, wm, context, scene, active_object):
        if len(context.selected_objects) > 1:
            obj = None
            for obj2 in context.selected_objects:
                if obj2 != context.view_layer.objects.active:
                    obj = obj2
                    break
        else:
            obj = context.selected_objects[0]

        driver_found = False
        for obj in context.selected_objects:
            if obj != context.view_layer.objects.active or len(context.selected_objects) == 1:
                curve = None
                prop_object = get_prop_object(context, self.prop_data_path, obj)
                if prop_object is not None:
                    (data, prop_type) = prop_object

                    if (data == obj) and (self.property_type == "OBJECT_DATA_PROPERTY"):
                        data = data.data
                    if prop_type in ["MODIFIER_PROPERTY", "OBJECT_CONSTRAINT_PROPERTY"]:
                        data_path = self.prop_data_path.split(".")[1]
                    elif prop_type in ["BONE_PROPERTY"]:
                        # this is used for props of that type: bones["bone_name"]["property_name"]
                        if self.prop_data_path.rfind("]") == len(self.prop_data_path) - 1:
                            from_idx = self.prop_data_path.rfind("[\"")
                            to_idx = self.prop_data_path.rfind("\"]") + 1
                            data_path = self.prop_data_path[from_idx:to_idx]
                        # this is used for props of that type: bones["bone_name"].property_name
                        else:
                            data_path = self.prop_data_path.split("\"].")[1]
                    elif prop_type in ["BONE_CONSTRAINT_PROPERTY"]:
                        string_elements = self.prop_data_path.split(".")
                        data_path = string_elements[len(string_elements) - 1]

                    elif prop_type in ["NODE_PROPERTY"]:
                        data_path = 'default_value'
                    else:
                        if "." in self.prop_data_path:
                            data, data_path = get_property_and_path(obj, self.prop_data_path)
                        else:
                            data_path = self.prop_data_path

                    if data_path is not None:
                        curve = data.driver_add(data_path, self.prop_data_index)
                else:
                    curve = None

                curves = []
                if curve is not None:
                    curves.append(curve)
                    if type(curve) == list:
                        curves = curve

                # create driver fcurve which defines how the value is driven
                for curve in curves:
                    if curve is not None:
                        driver_found = True
                        if len(curve.driver.variables) < 1:
                            curve_var = curve.driver.variables.new()
                        else:
                            curve_var = curve.driver.variables[0]

                        if len(curve.modifiers) > 0:
                            curve.modifiers.remove(curve.modifiers[0])

                        curve.extrapolation = self.extrapolation_type
                            # extend curve in a constant angle (without the modifier)

                        curve.driver.type = "AVERAGE"
                        curve_var.type = "TRANSFORMS"
                        # setup driver object/bone
                        driver_obj = context.active_object
                        curve_var.targets[0].id = driver_obj
                        if driver_obj.type == "ARMATURE":
                            curve_var.targets[0].bone_target = bpy.context.active_pose_bone.name
                        curve_var.targets[0].transform_space = self.space
                        curve_var.targets[0].transform_type = self.type

                        if self.type in ["ROT_X", "ROT_Y", "ROT_Z"]:
                            min_value = radians(self.min_value)
                            max_value = radians(self.max_value)
                        else:
                            min_value = self.min_value
                            max_value = self.max_value

                        while curve.keyframe_points:
                            curve.keyframe_points.remove(
                                curve.keyframe_points[0])

                        # Use add() instead of insert(), to keep both keys from VERY low values
                        if self.loop_driver_limits:
                            curve.keyframe_points.add(3)
                            point_a, point_b, point_c = curve.keyframe_points[:]
                        else:
                            curve.keyframe_points.add(2)
                            point_a, point_b = curve.keyframe_points[:]

                        # point_a = curve.keyframe_points.insert(
                            # min_value, self.prop_min_value)
                        point_a.co = (min_value, self.prop_min_value)
                        point_a.interpolation = self.interpolation_type

                        # point_b = curve.keyframe_points.insert(
                            # max_value, self.prop_max_value)
                        point_b.co = (max_value, self.prop_max_value)
                        point_b.interpolation = self.interpolation_type

                        if self.loop_driver_limits:
                            dif = abs(max_value - min_value)

                            if max_value >= min_value:
                                # point_c = curve.keyframe_points.insert(
                                    # max_value + dif, self.prop_min_value)
                                point_c.co = (max_value + dif, self.prop_min_value)
                            else:
                                # point_c = curve.keyframe_points.insert(
                                    # min_value + dif, self.prop_max_value)
                                point_c.co = (min_value + dif, self.prop_max_value)
                            point_c.interpolation = self.interpolation_type

        self.set_limit_constraint(context)

        if driver_found:
            msg = self.prop_data_path + " Driver has been added."
            self.report({'INFO'}, msg)
        else:
            msg = self.prop_data_path + " Property has not been found."
            self.report({'WARNING'}, msg)

    def set_limit_constraint(self, context):
        if self.set_driver_limit_constraint:
            if self.limit_type is not None:
                # if "Driver Limit" in self.driver.constraints:
                    # self.driver.constraints.remove(
                        # self.driver.constraints["Driver Limit"])

                const = self.driver.constraints.new(self.limit_type)
                const.name = "Driver Limit"

                if "LOCAL" in self.space:
                    const.owner_space = "LOCAL"
                elif "WORLD" in self.space:
                    const_owner_space = "WORLD"

                if self.min_value < self.max_value:
                    min_value = self.min_value
                    max_value = self.max_value
                else:
                    min_value = self.max_value
                    max_value = self.min_value

                if self.limit_type in ["LIMIT_LOCATION", "LIMIT_SCALE"]:
                    if "X" in self.type:
                        const.use_min_x = True
                        const.use_max_x = True
                        const.min_x = min_value
                        const.max_x = max_value
                    elif "Y" in self.type:
                        const.use_min_y = True
                        const.use_max_y = True
                        const.min_y = min_value
                        const.max_y = max_value
                    elif "Z" in self.type:
                        const.use_min_z = True
                        const.use_max_z = True
                        const.min_z = min_value
                        const.max_z = max_value
                elif self.limit_type == "LIMIT_ROTATION":
                    if "X" in self.type:
                        const.use_limit_x = True
                        const.min_x = radians(min_value)
                        const.max_x = radians(max_value)
                    elif "Y" in self.type:
                        const.use_limit_y = True
                        const.min_y = radians(min_value)
                        const.max_y = radians(max_value)
                    elif "Z" in self.type:
                        const.use_limit_z = True
                        const.min_z = radians(min_value)
                        const.max_z = radians(max_value)

    def get_short_path(self, prop_name):
        # Split property if it's a fullpath
        if prop_name.startswith('bpy.data.'):
            prop_name = prop_name.split('"]', 1)[1]
            if prop_name.startswith('.'):
                prop_name = prop_name[1:]
            if prop_name.endswith(']') and not prop_name.endswith('"]'):
                # Remove the array_index
                index = int(prop_name.rsplit('[', 1)[1][:-1])
                self.prop_data_index = index
                prop_name = prop_name.rsplit('[', 1)[0]

        return prop_name

    driver = None  # bone/object that's getting the driver
    limit_type = None  # type of limit constraint to add to bone/object

    mode: EnumProperty(
        name="Operator Mode",
        items=[
            ("DRIVER", "Driver", "Driver"),
            ("ACTION", "Action", "Action"),
        ],
    )

    def get_property_type_items(self, context):
        if len(context.selected_objects) > 1:
            obj = None
            for obj2 in context.selected_objects:
                if obj2 != context.view_layer.objects.active:
                    obj = obj2
                    del obj2
                    break
        else:
            obj = context.selected_objects[0]

        if (obj.type == "ARMATURE"):
            object_data_icon = "ARMATURE_DATA"
        else:
            object_data_icon = "MESH_DATA"

        items = [
            ("OBJECT_PROPERTY", "Object", "Object", "OBJECT_DATAMODE", 0),
            ("SHAPEKEY_PROPERTY", "Shapekey", "Shapekey", "SHAPEKEY_DATA", 1),
            ("MODIFIER_PROPERTY", "Modifier", "Modifier", "MODIFIER", 5),
            ("OBJECT_DATA_PROPERTY", "Data", "Data", object_data_icon, 2),
            ("MATERIAL_PROPERTY", "Material", "Material", "MATERIAL", 3),
            # ("TEXTURE_PROPERTY","Texture","Texture","TEXTURE",4),
            ("NODE_PROPERTY", "Node", "Node", "NODE", 4),
            ("BONE_PROPERTY", "Bone", "Bone", "BONE_DATA", 6),
            ("BONE_CONSTRAINT_PROPERTY", "Bone Constraint", "Bone Constraint", "CONSTRAINT_BONE", 7),
            ("OBJECT_CONSTRAINT_PROPERTY", "Object Constraint", "Object Constraint", "CONSTRAINT", 8),
        ]
        if obj.type not in ["MESH", "CURVE"]:
            items.pop(2)  # modifier
            items.pop(1)  # shapekey

        return items
    property_type: EnumProperty(
        name="Mode",
        items=get_property_type_items,
        description="Set the space the bone is transformed in. Local Space recommended.",
    )

    def search_for_prop(self, context):
        wm = context.window_manager
        if hasattr(self, "property_type") and self.prop_data_path != "":
            if len(context.selected_objects) > 1:
                obj = None
                for obj2 in context.selected_objects:
                    if obj2 != context.view_layer.objects.active:
                        obj = obj2
                        break
            else:
                obj = context.selected_objects[0]

            prop_object = get_prop_object(context, self.prop_data_path, obj)
            if prop_object is not None:
                self.property_type = prop_object[1]
            else:
                self.prop_data_path = ""
    prop_data_path: StringProperty(
        name="Property Data Path",
        default="",
        update=search_for_prop,
    )

    prop_data_index: IntProperty(
        name="Property Data Index",
        default=-1,
        soft_min=-1,
        soft_max=-1,
        options={'SKIP_SAVE'},
    )

    def get_shapes(self, context):
        shapes = []
        i = 0

        if len(context.selected_objects) > 1:
            obj = None
            for obj2 in context.selected_objects:
                if obj2 != context.view_layer.objects.active:
                    obj = obj2
                    break
        else:
            obj = context.selected_objects[0]
        shape_keys = None
        if obj.type in ["MESH", "CURVE"] and obj.data.shape_keys is not None:
            shape_keys = obj.data.shape_keys.key_blocks

        if shape_keys is not None:
            for shape in shape_keys:
                if shape.relative_key != shape:
                    shapes.append(
                        (shape.name, shape.name, shape.name, 'SHAPEKEY_DATA', i))
                    i += 1
        shapes.append(("CREATE_NEW_SHAPE", "create new shape",
                       "create new shape", 'NEW', i))

        return shapes
    shape_name: EnumProperty(
        name="Shape",
        items=get_shapes,
        description="Select the shape you want to add a driver to.",
    )

    get_limits_auto: BoolProperty(
        name="Get Limits",
        default=True,
        description="This will set the limits based on the bone location/rotation/scale automatically.",
    )

    def update_type_defaults(self, context):
        driver_src = local.driver

        if not driver_src:
            return

        locs = ["LOC_X", "LOC_Y", "LOC_Z"]
        rots = ["ROT_X", "ROT_Y", "ROT_Z"]
        scales = ["SCALE_X", "SCALE_Y", "SCALE_Z"]

        if self.type in locs:
            # set location
            index = locs.index(self.type)
            self.min_value = 0.0
            self.max_value = driver_src.location[index]
        elif (self.type in rots):
            # set rotation
            index = rots.index(self.type)
            if (driver_src.rotation_mode == "QUATERNION"):
                driver_rotation = driver_src.rotation_quaternion.to_euler("XYZ")
            else:
                driver_rotation = driver_src.rotation_euler

            self.min_value = 0.0
            self.max_value = degrees(driver_rotation[index])
        elif (self.type in scales):
            # set scale
            index = scales.index(self.type)
            xyz = [abs(driver_src.scale.x), abs(driver_src.scale.y), abs(driver_src.scale.z)]

            self.min_value = 1.0
            self.max_value = xyz[index]
    type: EnumProperty(
        name="Type",
        items=[
            ("LOC_X", "X Location", "X Location", "None", 0),
            ("LOC_Y", "Y Location", "Y Location", "None", 1),
            ("LOC_Z", "Z Location", "Z Location", "None", 2),
            ("ROT_X", "X Rotation", "X Rotation", "None", 3),
            ("ROT_Y", "Y Rotation", "Y Rotation", "None", 4),
            ("ROT_Z", "Z Rotation", "Z Rotation", "None", 5),
            ("SCALE_X", "X Scale", "X Scale", "None", 6),
            ("SCALE_Y", "Y Scale", "Y Scale", "None", 7),
            ("SCALE_Z", "Z Scale", "Z Scale", "None", 8),
        ],
        description="Set the type you want to be used as input to drive the shapekey.",
        update=update_type_defaults,
    )
    min_value: FloatProperty(
        name="Min Value",
        default=0.0,
        description="That value is used as 0.0 value for the shapekey.",
    )
    max_value: FloatProperty(
        name="Max Value",
        default=1.0,
        description="That value is used as 1.0 value for the shapekey.",
    )
    set_driver_limit_constraint: BoolProperty(
        name="Set Driver limit Constraint",
        default=False,
        description="Set Driver Limit Constraint with given settings.",
    )

    def driver_limits_flip(self, context):
        val1 = float(self.min_value)
        val2 = float(self.max_value)

        self.min_value = val2
        self.max_value = val1
    flip_driver_limits: BoolProperty(
        name="Flip Driver Limits",
        default=False,
        description="This Bool Property flips the Driver Limits.",
        update=driver_limits_flip,
    )

    interpolation_type: EnumProperty(
        name="Interpolation Type",
        items=[
            ("LINEAR", "Linear", "Linear", "IPO_LINEAR", 0),
            ("CONSTANT", "Constant", "Constant", "IPO_CONSTANT", 1),
            ("BEZIER", "Bezier", "Bezier", "IPO_BEZIER", 2),
        ],
        description="Defines the transition from one value to another",
    )
    extrapolation_type: EnumProperty(
        name="Extrapolation Type",
        items=[
            ('LINEAR', "Linear", "Dxtend in the same angle as the nearby keyframes", "IPO_LINEAR", 0),
            ('CONSTANT', "Constant", "Maintain the first and last keyframes indefinitely", "IPO_CONSTANT", 1),
        ],
        description="Defines the extension from the start/end points",
    )
    prop_min_value: FloatProperty(
        name="Min Value",
        default=0.0,
        description="That value is used as 0.0 value for the Property.",
    )
    prop_max_value: FloatProperty(
        name="Max Value",
        default=1.0,
        description="That value is used as 1.0 value for the Property.",
    )
    loop_driver_limits: BoolProperty(
        name="Loop Driver Limits",
        default=False,
        description="Start/End Driver curve with mirrored value",
    )

    def property_limits_flip(self, context):
        val1 = float(self.prop_min_value)
        val2 = float(self.prop_max_value)

        self.prop_min_value = val2
        self.prop_max_value = val1
    flip_property_limits: BoolProperty(
        name="Flip Property Limits",
        default=False,
        description="This Bool Property flips the Property Limits.",
        update=property_limits_flip,
    )


    def get_actions(self, context):
        ACTIONS = []
        for i, action in enumerate(bpy.data.actions):
            ACTIONS.append((action.name, action.name,
                            action.name, "ACTION", i))
        return ACTIONS
    def get_animation_length(self, context):
        action = bpy.data.actions[self.action]
        self.action_frame_end = get_action_length(action)
    action: EnumProperty(
        name="Action",
        items=get_actions,
        description="Choose Action that will be driven by Bone",
        update=get_animation_length,
    )

    def get_action_constraints(self, context):
        action_names = []
        ACTIONS = []
        i = 0
        for bone in context.selected_pose_bones:
            for const in bone.constraints:
                if const.name not in action_names:
                    action_names.append(const.name)
                    ACTIONS.append(
                        (const.name, const.name, const.name, "ACTION", i))
                    i += 1
        ACTIONS.append(("ALL_ACTIONS", "All Actions",
                        "All Actions", "ACTION", i))
        return ACTIONS
    action_constraint: EnumProperty(
        name="Action",
        items=get_action_constraints,
        description="Choose Action Constraint that will be deleted for selected bones.",
    )

    action_mode: EnumProperty(
        name="Action",
        items=(
            ("ADD_CONSTRAINT", "Add Constraints", "Add Constraints"),
            ("DELETE_CONSTRAINT", "Delete Constraints", "Delete Constraints"),
        ),
        description="Delete or Add Action Constraints for selected bones.",
    )
    space: EnumProperty(
        name="Space",
        items=[
            ("LOCAL_SPACE", "Local Space", "Local Space", "None", 0),
            ("TRANSFORM_SPACE", "Transform Space", "Transform Space", "None", 1),
            ("WORLD_SPACE", "World Space", "World Space", "None", 2),
        ],
        description="Set the space the bone is transformed in. Local Space recommended.",
    )
    action_frame_start: IntProperty(
        name="Min Value",
        default=0,
        description="Value where the animations is starting.",
    )
    action_frame_end: IntProperty(
        name="Max Value",
        default=10,
        description="Value where the animation is ending.",
    )


def get_obj_from_path(path, obj=None):
    if path.startswith('bpy.data.'):
        obj2 = eval(path.split('"]', 1)[0] + '"]')
        if Is.object(obj2):
            obj = obj2

    return obj


def split_data_path(path):
    elements = []

    element = ""
    dot_valid = True
    quot_mark_open = False
    for i, c in enumerate(path):
        if c in ["'", '"'] and quot_mark_open is False:
            quot_mark_open = True
            dot_valid = False
        elif c in ["'", '"'] and quot_mark_open is True:
            quot_mark_open = False
            dot_valid = True

        if c != '.' or dot_valid is False:
            element += c
        elif c == '.' and dot_valid:
            elements.append(element)
            element = ""
        if i == len(path) - 1 and element != "":
            elements.append(element)
            element = ""

    return elements


def get_property_and_path(obj, data_path):
    if "." in data_path:
        elements = split_data_path(data_path)  # data_path.split(".")# if "].value" not in data_path else [data_path]
        index = 0
        active_element = elements[index]
        if "key_blocks" not in data_path:
            data = obj
            while hasattr(data, active_element) and index <= len(elements) - 2:
                data = getattr(data, active_element)
                index += 1
                active_element = elements[index]
            if hasattr(data, active_element):
                return data, active_element
        else:
            data = obj.data.shape_keys
            if data is not None:
                data = data.key_blocks
                key = data_path.split('key_blocks["')[1].split('"]')[0]
                if key in data:
                    return data[key], "value"
    return None, None


def get_prop_object(context, prop_name, obj):
    wm = context.window_manager

    # The code that the original person uses, can find the wrong object.
    # This will find the correct target if using the full path in clipboard
    obj = get_obj_from_path(wm.clipboard, obj)

    data = obj.data
    bone = None
    mat = obj.active_material
    scene = context.scene
    render = scene.render

    if obj.type in ["MESH", "CURVE"]:
        shape_keys = obj.data.shape_keys
    else:
        shape_keys = None

    # return if property is found in node
    # nodes["Principled BSDF"].inputs[1].default_value
    if 'nodes["' in prop_name:
        node_name = prop_name.split('"')[1]
        if node_name in mat.node_tree.nodes:
            node = mat.node_tree.nodes[node_name]
            if "inputs[" in prop_name:
                index = int(prop_name.split("inputs[")[1].split("]")[0])
                socket = node.inputs[index]
                return socket, "NODE_PROPERTY"
            elif "outputs[" in prop_name:
                index = int(prop_name.split("outputs[")[1].split("]")[0])
                socket = node.outputs[index]
                return socket, "NODE_PROPERTY"

    # return if property is found in modifier
    if len(obj.modifiers) > 0 and '"' in prop_name:
        modifier_name = prop_name.split('"')[1]
        if modifier_name in obj.modifiers:
            modifier = obj.modifiers[modifier_name]
            return modifier, "MODIFIER_PROPERTY"

    # return if property is found in shapekeys
    if (shape_keys is not None) and ('"' in prop_name):
        shape_name = prop_name.split('"')[1]
        if shape_name in shape_keys.key_blocks:
            return (shape_keys, "SHAPEKEY_PROPERTY")
    if hasattr(shape_keys, prop_name):
        return (shape_keys, "SHAPEKEY_PROPERTY")

    # return if property is found in bone constraint
    if ('"' in prop_name):
        if len(prop_name.split('"')) > 3:
            bone_name = prop_name.split('"')[1]
            const_name = prop_name.split('"')[3]
            if hasattr(obj.pose, "bones") and bone_name in obj.pose.bones:
                cons = obj.pose.bones[bone_name].constraints
                if const_name in cons:
                    return (cons[const_name], "BONE_CONSTRAINT_PROPERTY")

    # return if property is found in bone
    if (obj.type == "ARMATURE") and ('"' in prop_name) and ("bones" in prop_name):

        if (len(prop_name.split('"')) >= 3):
            bone_name = prop_name.split('"')[1]
            if (bone_name in obj.data.bones):
                if (prop_name.rfind("]") == len(prop_name) - 1):
                    from_idx = prop_name.rfind("[")
                    to_idx = prop_name.rfind("]") + 1
                    prop = prop_name[from_idx:to_idx]
                else:
                    from_idx = prop_name.rfind(".") + 1
                    prop = prop_name[from_idx:]

                if hasattr(obj.pose.bones[bone_name], prop):
                    bone = obj.pose.bones[bone_name]
                elif hasattr(obj.data.bones[bone_name], prop):
                    bone = obj.data.bones[bone_name]

                return (bone, "BONE_PROPERTY")

    # return if property is found in object
    if hasattr(obj, prop_name):
        return obj, "OBJECT_PROPERTY"
    if ("." in prop_name):
        ob, data_path = get_property_and_path(obj, prop_name)
        if ob is not None:
            return (ob, "OBJECT_PROPERTY")

    # return if property is found in object data (armature, mesh)
    if hasattr(data, prop_name):
        return data, "OBJECT_DATA_PROPERTY"

    # return if property is found in material
    if (mat is not None) and hasattr(mat, prop_name):
        return (mat, "MATERIAL_PROPERTY")

    # tex = None
    # # return if property is found in texture
    # if tex is not None and hasattr(tex, prop_name):
        # return tex, "TEXTURE_PROPERTY"

    # return if property is found in object constraint
    if ('"' in prop_name) and ("constraint" in prop_name):
        if len(prop_name.split('"')) == 3:
            const_name = prop_name.split('"')[1]
            if const_name in obj.constraints:
                return (obj.constraints[const_name], "OBJECT_CONSTRAINT_PROPERTY")


def get_action_length(action):
    action_length = 0

    for fcurve in action.fcurves:
        if len(fcurve.keyframe_points) > 0:
            length = fcurve.keyframe_points[len(
                fcurve.keyframe_points) - 1].co[0]
            action_length = max(action_length, length)

    return action_length
