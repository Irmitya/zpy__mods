from zpy import utils, Set, Get
from math import *
from mathutils import *
from ... import __package__ as __addon__


def prefs():
    return utils.prefs(__addon__).bone_widgets


import bpy
import numpy
from .jsonFunctions import objectDataToDico


def not_linked(src):
    return not bool(getattr(src, 'library', None))


def get_collection(context):
    bw_collection_name = prefs().bonewidget_collection_name

    def scan(data):
        for col in data:
            if (col.name == bw_collection_name) and (not_linked(col)):
                return col

    collection = scan(context.scene.collection.children)

    if not collection:
        collection = scan(bpy.data.collections)

        if not collection:
            # Widgets collection hasn't been created or the one in file is linked
            collection = bpy.data.collections.new(bw_collection_name)

        context.scene.collection.children.link(collection)
        collection.hide_viewport = True

    return collection


"New version doesn't have/use this function"
# def get_collection_view_layer(collection):
    # return bpy.context.view_layer.layer_collection.children[collection.name]


def boneMatrix(widget, matchBone):
    "I believe these are commented because I use my own matrix"
        # "Original has this commented but I only had it"
            # widget.matrix_local = matchBone.bone.matrix_local
    # need to make this take the armature scale into account
    # id_data below now points to the armature data rather than the object
    # widget.matrix_world = bpy.context.active_pose_bone.id_data.matrix_world @ matchBone.bone.matrix_local
    # widget.matrix_world = matchBone.matrix_world @ matchBone.bone.matrix_local
    widget.matrix_world = utils.multiply_matrix(
        matchBone.id_data.matrix_world,
        matchBone.bone.matrix_local,
    )
    "I believe these are commented because I use my own matrix"
        # "Original is commented but I don't have it commented, idk why"
            # widget.scale = [matchBone.bone.length, matchBone.bone.length, matchBone.bone.length]
    widget.data.update()


def fromWidgetFindBone(widget):
    matchBone = None
    for ob in bpy.context.scene.objects:
        if ob.type == "ARMATURE":
            for bone in ob.pose.bones:
                if bone.custom_shape == widget:
                    matchBone = bone

    return matchBone


def createWidget(context, bone, widget, relative, size, scale, slide, rotate, collection=inf):
    bw_widget_prefix = prefs().widget_prefix + '-' + bone.id_data.name + '_'
    wgt_name = wgt_data_name = bw_widget_prefix + bone.name

    if collection is inf:
        collection = get_collection(context)

    # Custom check to "keep visiblity?"
    isolate_collection = collection.hide_viewport
    Set.visible(context, collection)

    if bone.custom_shape_transform:
        matrixBone = bone.custom_shape_transform
    else:
        matrixBone = bone

    if bone.custom_shape:
        old_shape = bone.custom_shape
        wgt_name = old_shape.name
        wgt_data_name = old_shape.data.name
        old_shape.name += "_old"
        old_shape.data.name += "_old"
        if collection.objects.get(old_shape.name):
            collection.objects.unlink(old_shape)

    # make the data name include the prefix
    newData = bpy.data.meshes.new(wgt_data_name)

    if relative:
        boneLength = 1
    else:
        boneLength = (1 / bone.bone.length)

    # print('\n\n\n', *rotate,'\n\n\n')
    newData.from_pydata(
        numpy.array(widget['vertices']) * [
            size * scale[0] * boneLength,
            size * scale[2] * boneLength,
            size * scale[1] * boneLength
            ] + [*slide],   # [0, slide, 0],
        widget['edges'],
        widget['faces'],
        )
    for v in newData.vertices:
        v.co.rotate(Euler((*rotate,)))

    # newData.from_pydata(
        # numpy.array(widget['vertices']) * [
            # size*scale[0]*boneLength,
            # size*scale[2]*boneLength,
            # size*scale[1]*boneLength
            # ] + [0,slide,0],
        # widget['edges'],
        # widget['faces']
        # )

    newData.update(calc_edges=True)

    newObject = bpy.data.objects.new(wgt_name, newData)

    # context.scene.collection.objects.link(newObject)
    collection.objects.link(newObject)
    # if isolate_collection:
        # utils.update(context)
    collection.hide_viewport = isolate_collection

    # When it creates the widget it still doesn't take the armature scale into account
    "original uses matrix_world. I don't know if I care"
        # newObject.matrix_local = matrixBone.bone.matrix_local
    newObject.matrix_world = matrixBone.bone.matrix_local
    newObject.scale = [matrixBone.bone.length] * 3
    # context.scene.update()

    context.view_layer.update()

    bone.custom_shape = newObject
    bone.bone.show_wire = True


def symmetrizeWidget(context, bone, collection):
    mirrorBone = findMirrorObject(bone)

    bw_widget_prefix = prefs().widget_prefix + '-' + bone.id_data.name + '_'
    wgt_name = wgt_data_name = bw_widget_prefix + mirrorBone.name

    # if mirrorBone.custom_shape_transform:
        # mirrorBone = mirrorBone.custom_shape_transform

    mirrorWidget = mirrorBone.custom_shape
    if mirrorWidget:
        wgt_name = mirrorWidget.name
        wgt_data_name = mirrorWidget.data.name

        mirrorWidget.name = mirrorWidget.name + "_old"
        mirrorWidget.data.name = mirrorWidget.data.name + "_old"

        if collection.objects.get(mirrorWidget.name):
            collection.objects.unlink(mirrorWidget)

    widget = bone.custom_shape
    newData = widget.data.copy()
    newData.name = wgt_data_name
    for vert in newData.vertices:
        vert.co = numpy.array(vert.co) * (-1, 1, 1)

    newObject = widget.copy()
    newObject.data = newData
    newData.update()
    newObject.name = wgt_name

    collection.objects.link(newObject)

    newObject.matrix_local = mirrorBone.bone.matrix_local
    newObject.scale = [mirrorBone.bone.length] * 3

    layer = context.view_layer
    layer.update()

    mirrorBone.custom_shape = newObject
    mirrorBone.bone.show_wire = True


def editWidget(context, active_bone):
    widget = active_bone.custom_shape

    armature = active_bone.id_data
    Set.mode(context, 'OBJECT', armature)
    Set.select(armature, False)

    '''  # 2.7
    if context.space_data.lock_camera_and_layers == False :
        visibleLayers = numpy.array(bpy.context.space_data.layers)+widget.layers-armature.layers
        bpy.context.space_data.layers = visibleLayers.tolist()

    else :
        visibleLayers = numpy.array(bpy.context.scene.layers)+widget.layers-armature.layers
        bpy.context.scene.layers = visibleLayers.tolist()
    '''

    "Commented because the new version only uses get_collection"
    if widget.users_collection:
        collection = widget.users_collection[0]
    else:
        collection = get_collection(context)
        collection.objects.link(widget)
    Set.in_scene(context, collection)
    Set.visible(context, collection)
    "Commented because new version uses operator"
        # get_collection_view_layer(collection).hide_viewport = False
    if getattr(context.space_data, 'local_view', None):
        bpy.ops.view3d.localview()

    # select object and make it active
    Set.select(widget, True)
    Set.active(context, widget)
    Set.mode(context, 'EDIT', widget)


def returnToArmature(context, widget):
    bone = fromWidgetFindBone(widget)
    armature = bone.id_data

    # Unhide collection if it was hidden in a previous run
    if widget.users_collection:  # Try to use the widget's collection
        collection = widget.users_collection[0]
    else:  # otherwise use default
        collection = get_collection(context)
    Set.visible(context, collection)

    Set.mode(context, 'OBJECT', widget)

    # collection = get_collection(context)
    if [x for x in armature.users_collection if x != collection]:
        # Don't hide the active collection
        collection.hide_viewport = True
    "New version doesn't have this"
        # get_collection_view_layer(collection).hide_viewport = True

    if getattr(context.space_data, 'local_view', None):
        bpy.ops.view3d.localview()

    Set.active(context, armature)
    Set.select(armature, True)

    Set.mode(context, 'POSE', armature)
    # Set.select(bone, True)
    # Set.active(context, bone)
    armature.data.bones[bone.name].select = True
    armature.data.bones.active = armature.data.bones[bone.name]


def findMirrorObject(object):
    if object.name.endswith("L"):
        suffix = 'R'
    elif object.name.endswith("R"):
        suffix = 'L'
    elif object.name.endswith("l"):
        suffix = 'r'
    elif object.name.endswith("r"):
        suffix = 'l'
    else:  # what if the widget ends in .001?
        # print('Object suffix unknown using blank')
        suffix = ''

    objectName = list(object.name)
    objectBaseName = objectName[:-1]
    mirroredObjectName = "".join(objectBaseName) + suffix

    if object.id_data.type == 'ARMATURE':
        return object.id_data.pose.bones.get(mirroredObjectName)
    else:
        return bpy.context.scene.objects.get(mirroredObjectName)


def findMatchBones(context):
    widgetsAndBones = {}

    if context.object.type == 'ARMATURE':
        for bone in context.selected_pose_bones:
            if bone.name.endswith("L") or bone.name.endswith("R"):
                widgetsAndBones[bone] = bone.custom_shape
                mirrorBone = findMirrorObject(bone)
                if mirrorBone:
                    widgetsAndBones[mirrorBone] = mirrorBone.custom_shape

        armature = context.object
        activeObject = context.active_pose_bone
    else:
        for shape in context.selected_objects:
            bone = fromWidgetFindBone(shape)
            if bone.name.endswith("L") or bone.name.endswith("R"):
                widgetsAndBones[fromWidgetFindBone(shape)] = shape

                mirrorShape = findMirrorObject(shape)
                if mirrorShape:
                    widgetsAndBones[mirrorShape] = mirrorShape

        activeObject = fromWidgetFindBone(context.object)
        armature = activeObject.id_data

    return (widgetsAndBones, activeObject, armature)
