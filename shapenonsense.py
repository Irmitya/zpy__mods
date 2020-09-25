from zpy import Get, utils
import bpy
import math
import mathutils
from mathutils import Vector
bl_info = {
    "name": "Shape key nonsense",
    "location": "View3D > Add > Mesh > SKNonsense",
    "description": "Shape key addon test",
    "category": "Mesh"
}


def precision_drop(num, precision):
    prec = 10**precision
    return int(num * prec) / prec


def find_doubles_with_other(obj, selobj):
    newdict = {}
    for vert in obj.data.vertices:
        try:
            newdict[tuple(vert.co)].append(vert)
        except:
            newdict.update({tuple(vert.co): [vert]})

    matchesdict = {}
    nomatch = []
    for vert in selobj.data.vertices:
        try:
            m = newdict[tuple(vert.co)]
            matchesdict.update({vert: m})
        except:
            nomatch.append(vert)

    return (matchesdict, nomatch)


def copydoublesco(ob_key, selob_key, matchdict):
    for vert in matchdict:
        obvert = matchdict[vert][0]
        selob_key.data[vert.index].co = ob_key.data[obvert.index].co


def round_pass(obj, selobj, ob_key, selob_key, vertexlist, scale, precision, positionpassdict):
    newmatch = []

    for vert in vertexlist:
        try:
            coords = vert.co.copy() * scale
            x = precision_drop(coords[0], precision)
            y = precision_drop(coords[1], precision)
            z = precision_drop(coords[2], precision)
            q = positionpassdict[(x, y, z)]
            # append the a list containing 0 =the vertices on the active object
            # found to match the current vertex and 1= the current vertex
            newmatch.append([q, vert])
        except:
            pass

    for vertpair in newmatch:
        sobvert = vertpair[1]
        obvert = vertpair[0][0]
        sodelta = sobvert.co - obvert.co

        # since the first index is a list of vertices, find which vertex is closest to the
        # vertex

        for verts in vertpair[0]:
            sodelta2 = sobvert.co - verts.co
            if sodelta2 < sodelta:
                obvert = verts
                sodelta = sodelta2

        basis = obj.data.shape_keys.key_blocks[0]
        delta = basis.data[obvert.index].co - ob_key.data[obvert.index].co
        selob_key.data[vertpair[1].index].co -= delta


def generate_rounded_pos_dict(obj, precision, scale):
    newdict = {}
    verts = obj.data.vertices
    prec = 10 ** precision

    for vert in verts:
        coords = vert.co.copy() * scale
        x = int(coords[0] * prec) / prec
        y = int(coords[1] * prec) / prec
        z = int(coords[2] * prec) / prec

        try:
            newdict[(x, y, z)].append(vert)
        except:
            newdict.update({(x, y, z): [vert]})

    return newdict


# transfers the active shape key of the active object
# to a new key in the selected object
def transfer_by_pos2(context, obj, selobj, ob_key, precision, scale):
    if (selobj.data.shape_keys is None):
        selobj.shape_key_add(from_mix=False).name = "Basis"
        selobj.active_shape_key_index = 0

    selobj_keys = selobj.data.shape_keys.key_blocks

    index = 0
    for (del_index, del_key) in enumerate(selobj_keys):
        if ob_key.name == del_key.name:
            index = del_index
            selobj.shape_key_remove(del_key)
            break
    selob_key = selobj.shape_key_add(name=ob_key.name, from_mix=False)

    if index:
        active = selobj.active_shape_key_index
        selobj.active_shape_key_index = len(selobj_keys) - 1
        while selobj_keys[index] != selob_key:
            bpy.ops.object.shape_key_move((dict(object=selobj)), type='UP')
        selobj.active_shape_key_index = active

    # find matches using a rounding precision of 5 and a scale of 1

    ddict = find_doubles_with_other(obj, selobj)
    nomatch = ddict[1]
    ddict = ddict[0]
    copydoublesco(ob_key, selob_key, ddict)

    # set precision and scale to use for the second pass

    # generates a dictionary which archives verts in active obj:matching vert in selected obj
    pass2 = generate_rounded_pos_dict(obj, precision, scale)
    round_pass(obj, selobj, ob_key, selob_key, nomatch, scale, precision, pass2)

    selob_key.vertex_group = ob_key.vertex_group
    selob_key.relative_key = ob_key.relative_key
    selob_key.slider_min = ob_key.slider_min
    selob_key.slider_max = ob_key.slider_max
    selob_key.value = ob_key.value

    driver = Get.driver(ob_key, 'value')
    if driver:
        utils.copy_driver(driver, selob_key, 'value')


class transfer_by_pos2_op(bpy.types.Operator):
    bl_description = ""
    bl_idname = 'mesh.transfer_by_pos2'
    bl_label = "Transfer shape key to selected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        if properties.precision == 3:
            desc = " (Fast)"
        elif properties.precision == 2:
            desc = " (Slow)"
        elif properties.precision == 1:
            desc = " (Slowest)"
        else:
            desc = ""
        return "Transfer active shapekey from active object, to selected"\
            f"{desc}.\nAlt + Click to transfer all shapekeys"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if len(context.selected_objects) > 1:
            if obj and obj.type == 'MESH' and obj.data.shape_keys:
                return True

    def __init__(self):
        self.all = False

    def invoke(self, context, event):
        self.all = event.alt
        return self.execute(context)

    def execute(self, context):
        obj = context.active_object
        keys = obj.data.shape_keys.key_blocks

        def transfer(key):
            for selobj in context.selected_objects:
                if selobj.type == 'MESH' and selobj != obj:
                    transfer_by_pos2(context, obj, selobj, key, self.precision, self.scale)

        if self.all and len(keys) > 1:
            count = 0
            total = len(keys) - 1
            for (index, key) in enumerate(keys[1:]):
                perc = round(((index + 1) / total * 100))
                print(f"\rTransferring shape {count}/{total} ({perc}%): [{key.name}]", " " * 10, end="")

                transfer(key)
                count += 1
            else:
                print(f"\rTransferred {count}/{total} shapekeys from {obj.name}", " " * 20)
        else:
            transfer(obj.active_shape_key)


        return {'FINISHED'}

    precision: bpy.props.FloatProperty(default=3)
    scale: bpy.props.FloatProperty(default=.2)


# class ShapesPanel(bpy.types.Panel):
class ShapesPanel:
    bl_description = "Creates a Panel in the Object properties window"
    bl_label = "Shape key nonsense"
    bl_space_type = 'PROPERTIES'  # 'VIEW_3D'
    bl_region_type = 'WINDOW'  # 'TOOLS'
    bl_context = 'data'
    bl_category = "Shape key nonsense"

    def draw(self, context):
        layout = self.layout

        obj = context.object
        if not obj.data.shape_keys or len([o for o in context.selected_objects if o.type == 'MESH']) <= 1:
            return

        row = layout.split(factor=0.75, align=True)
        row.operator("mesh.transfer_by_pos2").precision = 3
        row.operator("mesh.transfer_by_pos2", text="2.0").precision = 2
        row.operator("mesh.transfer_by_pos2", text="1.0").precision = 1

        "Button for Joshua's addon"
        # layout.operator('object.shape_key_remap')


def register():
    bpy.types.DATA_PT_shape_keys.append(ShapesPanel.draw)


def unregister():
    bpy.types.DATA_PT_shape_keys.remove(ShapesPanel.draw)
