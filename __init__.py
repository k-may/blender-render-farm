import os
import time
import bpy

from bpy.props import (IntProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       PointerProperty)

from bpy.types import (Operator,
                       PropertyGroup,
                       UIList)

bl_info = {
    "name": "Render-Farm",
    "author": "Kev Mayo",
    "blender": (3, 0, 0),
    "location": "View3D > Properties > BlenderKit",
    "category": "3D View",
}


# -------------------------------------------------------------------
#   Render
# -------------------------------------------------------------------

def hide_object(ob):
    ob.hide_render = True
    ob.hide_viewport = True
    children = ob.children
    # print("\nHIDE : ", ob.name, len(children))
    for child in children:
        child.hide_render = True
        child.hide_viewport = True


def show_object(ob):
    ob.hide_render = False
    ob.hide_viewport = False
    children = ob.children
    # print("\nSHOW : ", ob.name, len(children))
    for child in children:
        child.hide_render = False
        child.hide_viewport = False


def hide_objects():
    for ob in bpy.context.scene.render_farm_objects:
        hide_object(ob.object)


def _get_cameras(self):
    return get_cameras()


def get_cameras():
    cameras = []
    scene = bpy.context.scene
    for ob in scene.objects:
        if ob.type == 'CAMERA':
            cameras.append(ob)
    return cameras


# -------------------------------------------------------------------
#   Operators
# -------------------------------------------------------------------


class MaterialsMoveOperator(Operator):
    """Move items up and down, add and remove"""
    bl_idname = "render_farm_materials.list_action"
    bl_label = "List Actions"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}

    action: bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", "")))

    def random_color(self):
        from mathutils import Color
        from random import random
        return Color((random(), random(), random()))

    def invoke(self, context, event):
        scn = context.scene
        idx = scn.render_farm_materials_index

        try:
            item = scn.render_farm_materials[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(scn.render_farm_materials) - 1:
                item_next = scn.render_farm_materials[idx + 1].name
                scn.render_farm_materials.move(idx, idx + 1)
                scn.render_farm_materials_index += 1
                info = 'Item "%s" moved to position %d' % (item.name, scn.render_farm_materials_index + 1)
                self.report({'INFO'}, info)

            elif self.action == 'UP' and idx >= 1:
                item_prev = scn.render_farm_materials[idx - 1].name
                scn.render_farm_materials.move(idx, idx - 1)
                scn.render_farm_materials_index -= 1
                info = 'Item "%s" moved to position %d' % (item.name, scn.render_farm_materials_index + 1)
                self.report({'INFO'}, info)

            elif self.action == 'REMOVE':
                item = scn.render_farm_materials[scn.render_farm_materials_index]
                info = 'Item %s removed from scene' % (item)
                scn.render_farm_materials.remove(idx)
                if scn.render_farm_materials_index == 0:
                    scn.render_farm_materials_index = 0
                else:
                    scn.render_farm_materials_index -= 1
                self.report({'INFO'}, info)

        if self.action == 'ADD':
            item = scn.render_farm_materials.add()
            mat = scn.render_farm_all_materials[scn.render_farm_all_materials_index]
            item.id = len(scn.render_farm_materials)
            item.material = mat.material
            item.name = mat.name
            # col = self.random_color()
            # item.material.diffuse_color = (col.r, col.g, col.b, 1.0)
            scn.render_farm_materials_index = (len(scn.render_farm_materials) - 1)
            info = '%s added to list' % (item.name)
            self.report({'INFO'}, info)
        return {"FINISHED"}


class MaterialsAddAllOperator(Operator):
    """Add all materials of the current Blend-file to the UI list"""
    bl_idname = "render_farm.add_bmaterials"
    bl_label = "Add all available Materials"
    bl_description = "Add all available materials to the UI list"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(bpy.data.materials)

    def execute(self, context):
        scn = context.scene
        for mat in bpy.data.materials:
            if not context.scene.render_farm_materials.get(mat.name):
                item = scn.render_farm_materials.add()
                item.id = len(scn.render_farm_materials)
                item.material = mat
                item.name = item.material.name
                scn.render_farm_materials_index = (len(scn.render_farm_materials) - 1)
                info = '%s added to list' % (item.name)
                self.report({'INFO'}, info)
        return {'FINISHED'}


class MaterialsPrintOperator(Operator):
    """Print all items and their properties to the console"""
    bl_idname = "render_farm.print_items"
    bl_label = "Print Items to Console"
    bl_description = "Print all items and their properties to the console"
    bl_options = {'REGISTER', 'UNDO'}

    reverse_order: BoolProperty(
        default=False,
        name="Reverse Order")

    @classmethod
    def poll(cls, context):
        return bool(context.scene.render_farm_materials)

    def execute(self, context):
        scn = context.scene
        if self.reverse_order:
            for i in range(scn.render_farm_materials_index, -1, -1):
                mat = scn.render_farm_materials[i].material
                print("Material:", mat, "-", mat.name, mat.diffuse_color)
        else:
            for item in scn.render_farm_materials:
                mat = item.material
                print("Material:", mat, "-", mat.name, mat.diffuse_color)
        return {'FINISHED'}


class MaterialsClear(Operator):
    """Clear all items of the list and remove from scene"""
    bl_idname = "render_farm.clear_materials_list"
    bl_label = "Clear List and Remove Materials"
    bl_description = "Clear all items of the list and remove from scene"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bool(context.scene.render_farm_materials)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        if bool(context.scene.render_farm_materials):
            context.scene.render_farm_materials.clear()
            self.report({'INFO'}, "All materials removed from scene")
        else:
            self.report({'INFO'}, "Nothing to remove")
        return {'FINISHED'}


class ObjectsClearOperator(Operator):
    bl_idname = "render_farm.clear_objects_list"
    bl_label = "Clear List and Remove Objects"
    bl_description = "Clear all items of the list and remove from scene"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bool(context.scene.render_farm_objects)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        if bool(context.scene.render_farm_objects):
            # Clear the list
            context.scene.render_farm_objects.clear()
            self.report({'INFO'}, "All objects removed from list")
        else:
            self.report({'INFO'}, "Nothing to remove")
        return {'FINISHED'}


class ObjectsAddOperator(Operator):
    bl_idname = "my_list.new_item"
    bl_label = "Add selected Objects"

    def execute(self, context):
        scn = context.scene

        for obj in bpy.context.selected_objects:
            added = bool(scn.render_farm_objects.get(obj.name))
            self.report({'INFO'}, obj.name + " : " + str(added))
            if not scn.render_farm_objects.get(obj.name):
                item = context.scene.render_farm_objects.add()
                scn = context.scene
                item.id = len(scn.render_farm_objects)
                item.name = obj.name
                item.object = obj
                scn.render_farm_objects_index = (len(scn.render_farm_objects) - 1)
                info = '%s added to list' % (item.name)
                self.report({'INFO'}, info)
        return {'FINISHED'}


class RenderObjectsOperator(Operator):
    bl_idname = "render.items"
    bl_label = "Render Items"

    @classmethod
    def poll(cls, context):
        cameras = get_cameras()
        return bool(len(cameras))

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        scn = context.scene
        path = scn.render_farm_savePath.path

        info = 'Rendering : Path ==> %s' % path
        self.report({'INFO'}, info)
        # print('Rendering : Path ==> ' , path);


        # set export options
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'
        startTime = time.time()

        hide_objects()
        scene = context.scene
        prev_ob = None
        cameras = get_cameras()
        images = []
        for r_ob in scene.render_farm_objects:

            obj = r_ob.object

            if bool(prev_ob):
                hide_object(prev_ob)

            show_object(obj)

            for r_mat in scene.render_farm_materials:

                #assign material
                if(obj.data.materials):
                    obj.data.materials[0] = r_mat.material
                else:
                    obj.data.materials.append(r_mat.material)

                for cam in cameras:
                    bpy.context.scene.camera = cam
                    renderPath = os.path.join(path, r_mat.material.name + "_" + obj.name + "_" + cam.name)
                    self.report({'INFO'}, 'Rendering... %s' % renderPath)
                    bpy.context.scene.render.filepath = renderPath
                    bpy.ops.render.render(write_still=True)
                    images.append(renderPath + ".png")

            prev_ob = r_ob.object

        endTime = time.time()
        total = endTime - startTime

        info = "Rendering : Elapsed ==> %s" % total
        self.report({'INFO'}, info)

        return {'FINISHED'}


# -------------------------------------------------------------------
#   ui
# -------------------------------------------------------------------


class RenderFarmPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render Farm'

    @classmethod
    def poll(cls, context):
        return (context.object is not None)


class RenderOptionsPanel(RenderFarmPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_test_1"
    bl_label = "Render Options"

    def draw(self, context):
        scn = context.scene
        layout = self.layout

        row = layout.row()
        row.operator(RenderObjectsOperator.bl_idname, text="Render")

        col = layout.column(align=True)
        col.label(text='Out Path')
        col.prop(scn.render_farm_savePath, "path", text="")

        row = layout.row()

        if scn.update_cameras:
            row.prop(scn, "update_cameras", toggle=True, icon='FILE_REFRESH')

        row.label(text="Cameras")
        row.template_list("ObjectsList", "", scn, "render_farm_all_cameras",
                          scn, "render_farm_all_materials_index", rows=2)


class ObjectsList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name, icon_value=layout.icon(item.object))


class ObjectsPanel(RenderFarmPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_test_2"
    bl_label = "Objects"

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    def draw(self, context):
        layout = self.layout

        scn = bpy.context.scene
        rows = 2
        row = layout.row()
        row.template_list("ObjectsList", "", scn, "render_farm_objects",
                          scn, "render_farm_objects_index", rows=rows)

        box = layout.row()
        box.operator(ObjectsAddOperator.bl_idname, icon='WORLD')

        box = layout.row()
        box.operator(ObjectsClearOperator.bl_idname, icon='REMOVE')


class MaterialsList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mat = item.material
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.3)
            split.label(text="Index: %d" % (index))
            # static method UILayout.icon returns the integer value of the icon ID
            # "computed" for the given RNA object.
            split.prop(mat, "name", text="", emboss=False, icon_value=layout.icon(mat))

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=layout.icon(mat))

    def invoke(self, context, event):
        pass


class MaterialsPanel(RenderFarmPanel, bpy.types.Panel):
    bl_idname = 'TEXT_PT_my_panel'
    bl_label = "Materials"

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene

        rows = 2
        row = layout.row()
        row.template_list("MaterialsList", "custom_def_list", scene, "render_farm_materials",
                          scene, "render_farm_materials_index")

        col = row.column(align=True)
        col.operator(MaterialsMoveOperator.bl_idname, icon='REMOVE', text="").action = 'REMOVE'
        col.separator()
        col.operator(MaterialsMoveOperator.bl_idname, icon='TRIA_UP', text="").action = 'UP'
        col.operator(MaterialsMoveOperator.bl_idname, icon='TRIA_DOWN', text="").action = 'DOWN'

        if scene.update_materials:
            col.prop(scene, "update_materials", toggle=True, icon='FILE_REFRESH')

        row = layout.row()
        row.template_list("MaterialsList", "custom_def_list", scene, "render_farm_all_materials",
                          scene, "render_farm_all_materials_index", rows=rows)
        col = row.column(align=True)
        col.operator(MaterialsMoveOperator.bl_idname, icon='ADD', text="").action = 'ADD'
        col.separator()
        col.operator(MaterialsMoveOperator.bl_idname, icon='TRIA_UP', text="").action = 'UP'
        col.operator(MaterialsMoveOperator.bl_idname, icon='TRIA_DOWN', text="").action = 'DOWN'

        row = layout.row()
        row.operator(MaterialsAddAllOperator.bl_idname, icon="NODE_MATERIAL")
        row = layout.row()
        col = row.column(align=True)
        row = col.row(align=True)
        row.operator(MaterialsPrintOperator.bl_idname, icon="LINENUMBERS_ON")
        row = col.row(align=True)
        row.operator(MaterialsClear.bl_idname, icon="X")


# -------------------------------------------------------------------
#   Collection
# -------------------------------------------------------------------

class MaterialsPropertyGroup(PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    material: PointerProperty(
        name="Material",
        type=bpy.types.Material)


class ObjectsPropertyGroup(PropertyGroup):
    object: PointerProperty(
        name="Object",
        type=bpy.types.Object)


class FilePathProperty(PropertyGroup):
    path: StringProperty(
        name="",
        description="Path to Directory",
        default="",
        maxlen=1024,
        subtype='DIR_PATH')


class CamerasPropertyGroup(PropertyGroup):
    camera: PointerProperty(
        name="Camera",
        type=bpy.types.Object
    )


# -------------------------------------------------------------------
#   Register
# -------------------------------------------------------------------

classes = (

    RenderOptionsPanel,
    RenderObjectsOperator,

    ObjectsAddOperator,
    ObjectsClearOperator,
    ObjectsPanel,
    ObjectsList,

    MaterialsMoveOperator,
    MaterialsPrintOperator,
    MaterialsClear,
    MaterialsAddAllOperator,
    MaterialsList,
    MaterialsPanel,

    MaterialsPropertyGroup,
    ObjectsPropertyGroup,
    FilePathProperty
)

def get_update_cameras(self):
    update = set(s.object for s in self.render_farm_all_cameras).symmetric_difference(self.allCameras)
    if update:
        set_update_cameras(self, True)
    return False


def set_update_cameras(self, value):
    if (value):
        self.render_farm_all_cameras.clear()
        for c in self.allCameras:
            cam = self.render_farm_all_cameras.add()
            cam.name = c.name
            cam.object = c


def get_scene_materials(self):
    return bpy.data.materials


def get_update_materials(self):
    update = set(s.material for s in self.render_farm_all_materials).symmetric_difference(self.allMaterials)
    if update:
        set_update_materials(self, True)
    return False


def set_update_materials(self, value):
    if value:
        self.render_farm_all_materials.clear()  # update (or get) instead?
        for m in bpy.data.materials:
            s = self.render_farm_all_materials.add()
            s.name = m.name
            s.material = m


def register():

    print("\n\nRegister")

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # Custom scene properties
    bpy.types.Scene.render_farm_all_materials = CollectionProperty(type=MaterialsPropertyGroup)
    bpy.types.Scene.render_farm_all_materials_index = IntProperty()

    bpy.types.Scene.allMaterials = property(get_scene_materials)
    bpy.types.Scene.update_materials = BoolProperty(
        get=get_update_materials,
        set=set_update_materials,
        name="Update Scene Materials")

    bpy.types.Scene.render_farm_all_cameras = CollectionProperty(type=ObjectsPropertyGroup)
    bpy.types.Scene.render_farm_all_cameras_index = IntProperty()

    bpy.types.Scene.allCameras = property(_get_cameras)
    bpy.types.Scene.update_cameras = BoolProperty(
        name="Update Scene Cameras",
        get=get_update_cameras,
        set=set_update_cameras
    )

    bpy.types.Scene.render_farm_materials = CollectionProperty(type=MaterialsPropertyGroup)
    bpy.types.Scene.render_farm_materials_index = IntProperty()

    bpy.types.Scene.render_farm_objects = CollectionProperty(type=ObjectsPropertyGroup)
    bpy.types.Scene.render_farm_objects_index = IntProperty()

    bpy.types.Scene.render_farm_savePath = PointerProperty(type=FilePathProperty)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.allMaterials
    del bpy.types.Scene.update_materials

    del bpy.types.Scene.render_farm_all_materials
    del bpy.types.Scene.render_farm_all_materials_index

    del bpy.types.Scene.render_farm_materials
    del bpy.types.Scene.render_farm_materials_index

    del bpy.types.Scene.render_farm_all_cameras
    del bpy.types.Scene.render_farm_all_cameras_index

    del bpy.types.Scene.allCameras
    del bpy.types.Scene.update_cameras

    del bpy.types.Scene.render_farm_objects
    del bpy.types.Scene.render_farm_objects_index

    del bpy.types.Scene.render_farm_savePath


if __name__ == "__main__":
    register()
