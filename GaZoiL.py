
###################################################################### Preprocessing ######################################################################

###### Python Builtin modules #####

import io
import os
import struct

##### Autodesk Maya's API Modules #####

import maya.cmds as cmds
import maya.api.OpenMaya as om

###########################################################################################################################################################

############################################################## Variables / Arrays Definitions ##############################################################

##### Variables #####

run_count = 0
loop = 1
ffilters = "RS3 Models Files (*.elu);;All Files (*.*)"

##### Arrays #####

Names = []
Object_Ptr = om.MObjectArray()

Attrs_P2T  = ["coverage","translateFrame","rotateFrame","mirrorU","mirrorV","stagger","wrapU","wrapV","repeatUV","offset","rotateUV","noiseUV","vertexUvOne","vertexUvTwo","vertexUvThree","vertexCameraOne","outUV","outUvFilterSize"]
Attrs_File = ["coverage","translateFrame","rotateFrame","mirrorU","mirrorV","stagger","wrapU","wrapV","repeatUV","offset","rotateUV","noiseUV","vertexUvOne","vertexUvTwo","vertexUvThree","vertexCameraOne",  "uv" ,  "uvFilterSize" , "outColor" ]
Attrs_Shdr = ["color"]

##### Dictionnaries #####

Skin_Clusters = {}
Joints = {}

##### Constants #####

SKIPPED_LENGTH0 = 14

##### Functions / classes #####

# Assigned Objects #

meshFn = om.MFnMesh()
Yup_mul_0 = om.MMatrix((1,0,0,0,0,0,-1,0,0,1,0,0,0,0,0,1))
Yup_mul_1 = om.MMatrix((1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1))
Matrix_Quat = om.MQuaternion(0.707,0,0,0.707)

###########################################################################################################################################################

################################################################## Functions Definitions ##################################################################

##### Maya Functions #####

# UI #

def New_Scene(): # Allowed for debugging | Remove before Production
    cmds.file(newFile=True, force=True)

def Set_Parent(): # Add Transforms relationship
    for i in range(len(Names)):
        if(Names[i][1][0] != 0xFFFFFFFF):
            cmds.parent(Names[i][2][0] ,Names[i][3][0], relative=True)

def Get_MObject(Name):
    selection = om.MSelectionList()
    selection.add(Name)
    MObject = selection.getDependNode(0)
    return MObject

def Get_Selected():
    selection = om.MSelectionList()
    selection.add(cmds.ls(sl=1)[0])
    MObject = selection.getDependNode(0)
    print ("selected %s"% (cmds.ls(sl=1)[0]))
    return MObject

def Object_World_Parent():
    Parents = []
    for i in range(len(Names)):
        hasParent = bool(cmds.listRelatives(Names[i][2][0], parent=True))
        Parents.append(hasParent)
    for i in range(len(Names)):
        if(Parents[i]):
            cmds.parent(Names[i][2][0], world=True)

def Hide_Mesh():
    for i in range(len(Names)):
        if(Names[i][5][0]):
            cmds.hide(Names[i][2][0])

# 3D #
'''
def Auto_Shader():

    for i in range(len(Names)):
        if(Names[i][5][0]):
            # Material mgmt
            cmds.shadingNode('lambert',asShader=1,name=Names[i][2][0].replace("Object","Shader"))
            cmds.sets(r=1, nss=1, em=1, name=Names[i][2][0].replace("Object","ShadingGroup"))
            strings0 = (Names[i][2][0].replace("Object","Shader"),".outColor")
            strings1 = (Names[i][2][0].replace("Object","ShadingGroup"),".surfaceShader")
            attr0 = "".join(strings0)
            attr1 = "".join(strings1)
            cmds.connectAttr(attr0,attr1,f=1)
            cmds.select(Names[i][2][0])
            cmds.sets(e=1,fe=Names[i][2][0].replace("Object","ShadingGroup"))
            # Texture mgmt
            # Albedo 
            cmds.shadingNode('file', asTexture=True, isColorManaged=True)
    
            cmds.shadingNode('place2dTexture', asUtility=True)
            #
'''

def root_cube():
    vertices = [om.MPoint(-0.2, -0.2, 0.2),
                om.MPoint(0.2, -0.2, 0.2), 
                om.MPoint(0.2, 0.2, 0.2), 
                om.MPoint(-0.2, 0.2, 0.2), 
                om.MPoint(-0.2 , 0.2, -0.2), 
                om.MPoint(0.2, 0.2, -0.2), 
                om.MPoint(0.2, -0.2, -0.2),
                om.MPoint(-0.2, -0.2, -0.2)]
                
    polygonFaces = [4] * 6
    polygonConnects = [0,1,2,3,1,6,5,2,7,6,5,4,3,2,5,4,3,0,7,4,0,1,6,7]
    Mesh = meshFn.create(vertices, polygonFaces, polygonConnects )
    return Mesh

def Freeze_Transformation():
    for i in range(len(Names)):
        if not(Names[i][5][0]):
            cmds.makeIdentity(Names[i][2][0],a=True)

def Set_Transforms():
    for i in range(len(Names)):
        Transformation_Matrix = om.MTransformationMatrix(Names[i][4][0])

        ##### Debug #####
        #Transformation_Matrix.setRotationOrientation(Matrix_Quat) # Rotate the whole object
        #Transformation_Matrix.rotateBy(Matrix_Quat, 2) # rotate objects too ;.; 
        #Transformation_Matrix.setRotation(Matrix_Quat) # rotate object weird result
        #Transformation_Matrix.setRotationComponents(Matrix_Quat,1) #  KO	
        #Transformation_Matrix.reorderRotation	(	6	) # Does nothing 

        Transform_Node = om.MFnTransform(Object_Ptr[i])
        Transform_Node.setTransformation(Transformation_Matrix)

def Vertices_Weights():
    for key in Skin_Clusters:
        cmds.skinCluster(Names[0][2][0] , key, name=To_Skin(key))
        List = Skin_Clusters.get(key)
        for j in range(len(List)):
            Vtx_Idx = List[j][0]
            Bones_array = List[j][1]
            Weights_array = List[j][2]
            Bone_Count = len(List[j][1])
            for k in range(Bone_Count):
                cmds.skinPercent( To_Skin(key), Vtx_String(Vtx_Idx, key), transformValue=[(Names[Bones_array[k]][2][0], Weights_array[k][0])])

def Get_Joint_Angles(name):
    x = cmds.joint(name, q=1, ax=1)
    y = cmds.joint(name, q=1, ay=1)
    z = cmds.joint(name, q=1, az=1)
    return x, y, z
            
def Calc_Limits(x, y, z, List):
    X_Limits = []
    Y_Limits = []
    Z_Limits = []
    X_Limits.append(x - List[0])
    X_Limits.append(x + List[3])
    Y_Limits.append(y - List[1])
    Y_Limits.append(y + List[4])
    Z_Limits.append(z - List[2])
    Z_Limits.append(z + List[5])
    return X_Limits, Y_Limits, Z_Limits

def Set_Limits():
    for key in Joints:
        List = Joints.get(key)
        print key
        Log_Arrays(List)
        '''
        Rot_XYZ = Get_Joint_Angles(key)
        Log_Arrays(Rot_XYZ)
        Joints = Calc_Limits(Floats[0], Floats[1], Floats[2], Limits_List)
        Lim_X = Joints[0]
        Lim_Y = Joints[1]
        Lim_Z = Joints[2]
        cmds.joint(key, e=1, lx=(Lim_X[0],Lim_X[1]))
        cmds.joint(key, e=1, ly=(Lim_Y[0],Lim_Y[1]))
        cmds.joint(key, e=1, lz=(Lim_Z[0],Lim_Z[1]))
        '''
def Orient_Joint():
    for i in range(len(Names)):
        if not(Names[i][5][0]):
            cmds.joint(Names[i][2][0],e=True,zso=True,oj='yxz')


##### Pythonic Functions #####

# Array Operations #

def Log_Arrays(array):
    print ""
    for i in range(len(array)):
        element = array[i]
        print element
    print ""

def create_list(itm_cnt, list, num_element): # Itm_cnt = numbers of items in list - list = an initialized python list item - Num_element = number of element per row 
    index = 0
    for i in range(itm_cnt):
        list.append([])
        for j in range(num_element):
            list[index].append([])
        index += 1
    return list

# Strings Operations #

def Clean_Name(text):
    text1 = text.replace(' ','_')
    text2 = text1.replace('.','_')
    text3 = text2.replace('\x00','')
    Object_string = "Object_"
    Strings = (Object_string, text3)
    text4 = "".join(Strings)
    return text4

def To_Bones(Name):
    bone_suffix = "_bone"
    strings = (Name, bone_suffix)
    bone_name = "".join(strings)
    return bone_name

def To_Skin(Name):
    skin_suffix = "_SC"
    strings = (Name, skin_suffix)
    skin_name = "".join(strings)
    return skin_name

def Vtx_String(vtx_idx, mesh):
    vtx_string = 'vtx'
    dot = "."
    vtx_idx_string = str(vtx_idx)
    strings = (mesh, dot, vtx_string, vtx_idx_string)
    f_string = "".join(strings)
    return f_string

def Rad_Str(float):
    int_offset = int(round(float))
    int_str = str(int_offset)
    rad_str = "deg"
    string = (int_str, rad_str)
    text = "".join(string)
    return text

# Misc #

def Open_File():
    fullpath = cmds.fileDialog2(fileMode=1, ff=ffilters)
    fullpath = str(fullpath[0])
    cnt = fullpath.count("/")
    splitpath = fullpath.split("/")
    filename = splitpath[cnt]
    realpath = fullpath.replace(filename,"")
    os.chdir(realpath)
    file_object = io.open(filename,'r+b')
    Import_File(file_object)

# GaZoil #

def Import_File(file_object):
    elu = file_object
    Elu_Magic = struct.unpack('<I', elu.read(4))[0]
    Elu_Version = struct.unpack('<I', elu.read(4))[0]
    Material_Count = struct.unpack('<I', elu.read(4))[0]
    Object_Count = struct.unpack('<I', elu.read(4))[0]
    create_list(Object_Count, Names, 6)

    if(Elu_Magic == 17297504 and Elu_Version == 20500 or Elu_Version == 20500 or Elu_Version == 20498 or Elu_Version == 20497):
        if(Elu_Version == 20500):
            for i in range(Object_Count):
                Obj_Args = Object_Header1(elu)
                print Obj_Args[0]
                Names[i][0].append(i)
                Names[i][1].append(Obj_Args[2])
                Names[i][2].append(Obj_Args[0])
                Names[i][3].append(Obj_Args[1])
                Import_5014(elu, i, Obj_Args[0])
            #Auto_Shader()
            Object_World_Parent()
            Set_Parent()
            Set_Transforms()
            #Object_World_Parent()
            #Freeze_Transformation()
            #Orient_Joint()
            #Vertices_Weights()
            print "EOF"
        elif(Elu_Version == 20499):
            Object_Header1(file_object)
            Import_5013(elu, Elu_Version, Object_Count) 
        elif(Elu_Version == 20498):
            Object_Header0(file_object)
            Import_5012(elu, Elu_Version, Object_Count)
        elif(Elu_Version == 20497):
            Object_Header0(file_object)
            Import_5011(elu, Elu_Version, Object_Count)
    else:  
        print "Wrong file Type => Internal Error !"

def Object_Header0(file_object):
    elu = file_object
    Name_Length = struct.unpack('<I', elu.read(4))[0]
    Name = elu.read(Name_Length)
    Name = Clean_Name(Name)
    Parent_Name_Length = struct.unpack('<I', elu.read(4))[0]
    Parent_Name = elu.read(Parent_Name_Length)
    Parent_Name = Clean_Name(Parent_Name)
    Parent_Mesh_Index = struct.unpack('<I', elu.read(4))[0]
    return Name, Parent_Name, Parent_Mesh_Index

def Object_Header1(file_object):
    elu = file_object
    Name_Length = struct.unpack('<I', elu.read(4))[0]
    Name = elu.read(Name_Length)
    Name = Clean_Name(Name)
    Parent_Mesh_Index = struct.unpack('<I', elu.read(4))[0] 
    Parent_Name_Length = struct.unpack('<I', elu.read(4))[0]
    Parent_Name = elu.read(Parent_Name_Length)
    Parent_Name = Clean_Name(Parent_Name)
    return Name, Parent_Name, Parent_Mesh_Index 

def Import_5011(file_object, Elu_Version):

    print "File type not supported"

def Import_5012(file_object, Elu_Version):

    print "File type not supported"

def Import_5013(file_object, Elu_Version):

    print "File type not supported"

def Import_5014(file_object, iterator, Object_Name):
    elu = file_object
    i = iterator
    Name = Object_Name
    LM = struct.unpack('<16f', elu.read(64))
    Local_Matrix = om.MMatrix((
            LM[0],LM[1],LM[2],LM[3],
            LM[4],LM[5],LM[6],LM[7],
            LM[8],LM[9],LM[10],LM[11],
            LM[12],LM[13],LM[14],LM[15]
        ))
    #Local_Matrix.__imul__(Yup_mul_0)
    print Local_Matrix

    # Assigns the given variables to specific positions of the list

    Names[i][4].append(Local_Matrix)
    
    # elu.seek(16, os.SEEK_CUR) debug

    float0 = struct.unpack('<f', elu.read(4))[0]
    float1 = struct.unpack('<f', elu.read(4))[0]
    float2 = struct.unpack('<f', elu.read(4))[0]
    float3 = struct.unpack('<f', elu.read(4))[0]

    Vertex_Position_Count = struct.unpack('<I', elu.read(4))[0]
    Vertices = []

    for j in range(Vertex_Position_Count):
        vpx, vpy, vpz = struct.unpack('<3f', elu.read(12))
        Vertices.append(om.MPoint(vpx, vpy, vpz))
    
    elu.seek(2, os.SEEK_CUR)

    if(Vertex_Position_Count > 0):
        Mesh_Flag = 1
    else:
        Mesh_Flag = 0

    Names[i][5].append(Mesh_Flag)

    Vertex_Textcoords = []
    VTexcoords0 = []
    VTexcoords1 = []
    VTexcoords2 = []
    Vertex_Textcoord_Count = struct.unpack('<I', elu.read(4))[0]
    VTID = 0

    for j in range(Vertex_Textcoord_Count):
        vtx, vty, vtz = struct.unpack('<3f', elu.read(12))
        Vertex_Textcoords.append((vtx, 1.0 - vty))
        VTexcoords0.append(VTID)
        VTexcoords1.append(vtx)
        VTexcoords2.append(1.0 - vty) # flip y => if binary data contains 0,70 the end value will equal to 0,30
        VTID = VTID + 1

    Unknown_Count = struct.unpack('<I', elu.read(4))[0]
    UKN_ARRAY=[]
    create_list(Unknown_Count, UKN_ARRAY, 1)

    for j in range(Unknown_Count):
        UKN0 = struct.unpack('<f', elu.read(4))[0]
        UKN1 = struct.unpack('<f', elu.read(4))[0]
        UKN2 = struct.unpack('<f', elu.read(4))[0]
        UKN_ARRAY[j][0].append((UKN0, UKN1, UKN2))

    #Log_Arrays(UKN_ARRAY)

    Unknown_Count = struct.unpack('<I', elu.read(4))[0]
    UKN_ARRAY=[]
    create_list(Unknown_Count, UKN_ARRAY, 1)

    for j in range(Unknown_Count):
        UKN0 = struct.unpack('<f', elu.read(4))[0]
        UKN1 = struct.unpack('<f', elu.read(4))[0]
        UKN2 = struct.unpack('<f', elu.read(4))[0]
        UKN_ARRAY[j][0].append((UKN0, UKN1, UKN2))

    #Log_Arrays(UKN_ARRAY)

    Vertex_Normal_Count = struct.unpack('<I', elu.read(4))[0]
    Vertex_Normals = []

    for j in range(Vertex_Normal_Count):
        vnx, vny, vnz = struct.unpack('<3f', elu.read(12))
        Vertex_Normals.append((vnx, vny, vnz))

    Unknown_Count = struct.unpack('<I', elu.read(4))[0] # Probably Faces Bi-Normals /  chunk >0 count only on mesh 
    UKN_ARRAY=[]
    create_list(Unknown_Count, UKN_ARRAY, 1)

    for j in range(Unknown_Count):
        UKN0 = struct.unpack('<f', elu.read(4))[0]
        UKN1 = struct.unpack('<f', elu.read(4))[0]
        UKN2 = struct.unpack('<f', elu.read(4))[0]
        UKN3 = struct.unpack('<f', elu.read(4))[0]
        UKN_ARRAY[j][0].append((UKN0, UKN1, UKN2, UKN3))

    #Log_Arrays(UKN_ARRAY)

    Unknown_Count = struct.unpack('<I', elu.read(4))[0]

    for j in range(Unknown_Count):
        elu.seek(12,os.SEEK_CUR)

    Face_Count = struct.unpack('<I', elu.read(4))[0]
    PolygonFaces = []
    PolygonConnects = []
    FaceID = []
    FaceID_C = 0
    L_Face_Vertex_IDs = []
    L_Face_Vertex_IDs_C = 0
    L_Face_Vertex_Texcoord_IDs = []

    if(Face_Count > 0): 
        Face_Index_Count = struct.unpack('<I', elu.read(4))[0]
        Face_Count = struct.unpack('<I', elu.read(4))[0]

        for j in range(Face_Count):
            FaceID.append(FaceID_C)
            FaceID_C = FaceID_C + 1
            L_Face_Vertex_IDs_C = 0
            Face_Vertex_Index_Count = struct.unpack('<I', elu.read(4))[0]
            PolygonFaces.append(Face_Vertex_Index_Count)

            for k in range(Face_Vertex_Index_Count):
                L_Face_Vertex_IDs.append(L_Face_Vertex_IDs_C)
                L_Face_Vertex_IDs_C = L_Face_Vertex_IDs_C + 1
                Faces_Data, Textcoords, ukn0, ukn1, ukn2 = struct.unpack('<2HI2H', elu.read(12))
                PolygonConnects.append(Faces_Data)
                L_Face_Vertex_Texcoord_IDs.append(Textcoords)
                elu.seek(2, os.SEEK_CUR)
            elu.seek(2, os.SEEK_CUR)

    else:
        for j in range(Face_Count):
            elu.seek(32, os.SEEK_CUR) # unknown
            
    Unknown_Count = struct.unpack('<I', elu.read(4))[0]

    for j in range(Unknown_Count):
        elu.seek(12,os.SEEK_CUR)

    elu.seek(4,os.SEEK_CUR)

    Skinning_Data = []
    Vertex_Index = -1

    Blend_Vertex_Count = struct.unpack('<I', elu.read(4))[0] # Blend_Vertex_Count

    for j in range(Blend_Vertex_Count):
        Bones_Influences_Count = struct.unpack('<I', elu.read(4))[0]
        Vertex_Index += 1
        Skinning_Data.append([])
        Skinning_Data[Vertex_Index].append([Vertex_Index])
        Skinning_Data[Vertex_Index].append([])
        Skinning_Data[Vertex_Index].append([])
        
        for k in range(Bones_Influences_Count):
            elu.seek(2, os.SEEK_CUR)
            Bone_Index = struct.unpack('<H', elu.read(2))[0]
            Bone_Weight = struct.unpack('f', elu.read(4))
            Skinning_Data[Vertex_Index][1].append(Bone_Index)
            Skinning_Data[Vertex_Index][2].append(Bone_Weight)
            
    if(Names[i][5][0]):
        Skin_Clusters[Name] = Skinning_Data

    elu.seek(4, os.SEEK_CUR)

    Vertex_Count = struct.unpack('<I', elu.read(4))[0]
    Vertex_Indices = []
    VTexcoords3 = []

    for j in range(Vertex_Count):
        Vertex_Position_Index = Vertex_Normal_Index = Vertex_Textcoord_Index = Vertex_Unknown0_Index = Vertex_Unknown1_Index = 0
        Vertex_Position_Index, Vertex_Normal_Index, Vertex_Textcoord_Index, Vertex_Unknown0_Index, Vertex_Unknown1_Index = struct.unpack('<3HIH', elu.read(12))
        
        elu.seek(2, os.SEEK_CUR)
        Vertex_Indices.append((Vertex_Position_Index, Vertex_Normal_Index, Vertex_Textcoord_Index, Vertex_Unknown0_Index, Vertex_Unknown1_Index))
        VTexcoords3.append(Vertex_Textcoord_Index)

    Unknown_Count = struct.unpack('<I', elu.read(4))[0]

    for j in range(Unknown_Count):
        elu.seek(64, os.SEEK_CUR)

    for j in range(Unknown_Count):
        elu.seek(2, os.SEEK_CUR)

    Unknown_Count = struct.unpack('<I', elu.read(4))[0]

    for j in range(Unknown_Count):
        elu.seek(12,os.SEEK_CUR)

    Face_Index_Count = struct.unpack('<I', elu.read(4))[0]
    Face_Count = int(Face_Index_Count / 3)

    for j in range(Face_Index_Count):
        elu.seek(2, os.SEEK_CUR)
    
    # Probably Bones constraint Max rotation angles | 6 floats (min angle -x, -y, -z) (max angle x, y, z)

    Lim_X_P = struct.unpack('<f', elu.read(4))[0]
    Lim_Y_P = struct.unpack('<f', elu.read(4))[0]
    Lim_Z_P = struct.unpack('<f', elu.read(4))[0]
    Lim_X_N = struct.unpack('<f', elu.read(4))[0]
    Lim_Y_N = struct.unpack('<f', elu.read(4))[0]
    Lim_Z_N = struct.unpack('<f', elu.read(4))[0]
    Joints_Limits = []
    Joints_Limits.append(Lim_X_N)
    Joints_Limits.append(Lim_Y_N)
    Joints_Limits.append(Lim_Z_N)
    Joints_Limits.append(Lim_X_P)
    Joints_Limits.append(Lim_Y_P)
    Joints_Limits.append(Lim_Z_P)
    Joints[Name] = Joints_Limits

    ##### Mesh / Bone Construct #####

    if (Vertex_Position_Count > 0):
        Object = meshFn.create(Vertices, PolygonFaces, PolygonConnects )
    else:
        cmds.joint(name=Name)
        Object = Get_MObject(Name)
        
    
    Object_Ptr.append(Object)

    ##### Mesh Naming #####

    DPNode = om.MFnDependencyNode(Object)
    DPNode.setName(Name)
        
    ##### UV Mapping #####

    if (Vertex_Position_Count > 0):
        meshFn.renameUVSet('map1', Name)
        meshFn.setUVs(VTexcoords1, VTexcoords2, Name)
        meshFn.assignUVs(PolygonFaces, L_Face_Vertex_Texcoord_IDs, uvSet=Name)
    else:
        pass

    print "Mesh Item Imported successfully ",Name
    print "Switching to the next item"

###########################################################################################################################################################

################################################################### Script instructions ###################################################################

New_Scene()
Open_File()
Hide_Mesh()

print "\n"
print "EOS"

###########################################################################################################################################################