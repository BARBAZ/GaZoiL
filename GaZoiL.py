
###################################################################### Preprocessing ######################################################################

###### Python Builtin modules #####

import io
import logging
import os
import re
import struct
import fileinput
import math

##### Autodesk Maya's API Modules #####

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omanim
import maya.api.OpenMayaRender as omrender

###########################################################################################################################################################

############################################################## Variables / Arrays Definitions ##############################################################

##### Variables #####

run_count = 0
loop = 1

##### Arrays #####

# 1 file importation lifespan | Array must be cleaned between each file importation for the tool to operate properly

Names = []
Bones = []
Joints_Angles = []
Mesh_Ptr = om.MObjectArray()

# Persistant | This Array Contains all Objects of the scene | Only New_Scene() can reset this List

World = [] 
World_Prt = om.MObjectArray() 


##### Constants #####

SKIPPED_LENGTH0 = 14

##### Functions / classes #####

# Assigned Objects #

meshFn = om.MFnMesh()

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

def Name_Bones(Name):
    string = "_bone"
    strings = (Name, string)
    Name = "".join(strings)
    return Name

def Mesh_World_Parent():
    for i in range(len(Names)):
        if(Names[i][1][0] != 0xFFFFFFFF):
            cmds.parent(Names[i][2][0],world=True)

def Bones_World_Parent():
    for i in range(len(Bones)):
        cmds.parent(Bones[i][1][0],world=True)


def Delete_Joints_Mesh():
    for i in range(len(Names)):
        if(Names[i][5][0] == 0):
            cmds.delete(Names[i][2][0])

def Reparent_Joints():
    for i in range(len(Bones)):
        parent_index = Bones[i][0][0]
        if(parent_index != 0xFFFFFFFF):
            cmds.parent(Bones[i][1][0],Bones[parent_index][1][0])

# 3D #

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

def Set_Transforms():
    for i in range(len(Names)):
        Transformation_Matrix = om.MTransformationMatrix(Names[i][4][0])
        Transform_Node = om.MFnTransform(Mesh_Ptr[i])
        Transform_Node.setTransformation(Transformation_Matrix)

def Generate_Joints():
    for i in range(len(Names)):
            cmds.joint(Names[i][2][0], name=Name_Bones(Names[i][2][0]))
            Bones[i][0].append(Names[i][1][0])
            Bones[i][1].append(Name_Bones(Names[i][2][0]))

def Set_Joints_Limit():
    for i in range(len(Bones)):
        cmds.joint(Bones[i][1][0] , lx=(Joints_Angles[i][0][0] , Joints_Angles[i][1][0]))
        cmds.joint(Bones[i][1][0] , ly=(Joints_Angles[i][2][0] , Joints_Angles[i][3][0]))
        cmds.joint(Bones[i][1][0] , lz=(Joints_Angles[i][4][0] , Joints_Angles[i][5][0]))

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

def Array_Copy(copied, new):
    for i in range(len(copied)):
        new.append([])
        elem0 = copied[i][0]
        elem1 = copied[i][1]
        elem2 = copied[i][2]
        elem3 = copied[i][3]
        elem4 = copied[i][4]
        elem5 = copied[i][5]
        new[i].append(elem0)
        new[i].append(elem1)
        new[i].append(elem2)
        new[i].append(elem3)
        new[i].append(elem4)
        new[i].append(elem5)
        
def Detect_Duplicates(Name, file_object): 
    for i in range(len(World)):
        if(Name == World[i][2][0]):
            print "this 3D Object Already exists inside Scene - - Jumping the next item"
            Jump_Parse(file_object)
        
    
# Strings Operations #

def Clean_Name(text):
    text1 = text.replace(' ','_')
    text2 = text1.replace('.','_')
    text3 = text2.replace('\x00','')
    Object_string = "Object_"
    Strings = (Object_string, text3)
    text4 = "".join(Strings)
    return text4

# Misc #

def User_Prompt(text):
    Anwser = raw_input(text)
    return Anwser

def Open_File():
    fullpath = cmds.fileDialog2(fileMode=1)
    fullpath = str(fullpath[0])
    cnt = fullpath.count("/")
    splitpath = fullpath.split("/")
    filename = splitpath[cnt]
    realpath = fullpath.replace(filename,"")
    os.chdir(realpath)
    file_object = io.open(filename,'r+b')
    Import_File(file_object)

# GaZoil #

def Main_Loop(run_count, loop):
    test0 = -1
    test1 = -1
    test2 = -1
    test3 = -1
    if(run_count > 0):
        Run_Query = User_Prompt("Import more files ? Y/N")
        test0 = Run_Query.find("Y")
        test1 = Run_Query.find("y")
        test2 = Run_Query.find("N")
        test3 = Run_Query.find("n")
        if(test0 > -1 or test1 > -1):
            run_count += 1
            Open_File()
        elif(test2 > -1 or test3 > -1):
            loop = 0
            pass
        elif(test0 > -1 or test1 > -1 or test2 > -1 or test3 > -1):
            print "Fatal Error : VAR IQ < 0"
    else:
        run_count += 1
        Open_File()
    return run_count, loop
    

def Import_File(file_object):
    elu = file_object
    Elu_Magic = struct.unpack('<I', elu.read(4))[0]
    Elu_Version = struct.unpack('<I', elu.read(4))[0]
    Material_Count = struct.unpack('<I', elu.read(4))[0]
    Mesh_Count = struct.unpack('<I', elu.read(4))[0]
    create_list(Mesh_Count, Names, 6)
    create_list(Mesh_Count, Bones, 2)
    create_list(Mesh_Count, Joints_Angles, 6)

    if(Elu_Magic == 17297504 and Elu_Version == 20500 or Elu_Version == 20500 or Elu_Version == 20498 or Elu_Version == 20497):
        if(Elu_Version == 20500):
            Import_5014(elu, Mesh_Count)
        elif(Elu_Version == 20499):
            Import_5013(elu, Elu_Version, Mesh_Count) # need fix 
        elif(Elu_Version == 20498):
            Import_5012(elu, Elu_Version, Mesh_Count) # need fix  
        elif(Elu_Version == 20497):
            Import_5011(elu, Elu_Version, Mesh_Count) # need fix 
    else:  
        print "Wrong file Type => Try again !"

def Jump_Parse(file_object, Elu_Version):
    elu = file_object
    if(Elu_Version == 20500):
        Jump_5014(elu)
    elif(Elu_Version == 20499):
        Jump_5013(elu)
    elif(Elu_Version == 20498):
        Jump_5012(elu)
    elif(Elu_Version == 20497):
        Jump_5011(elu)
    else: 
        print "Internal Error !"

def Import_5011(file_object, Elu_Version):

    print "File type not supported"

def Import_5012(file_object, Elu_Version):

    print "File type not supported"

def Import_5013(file_object, Elu_Version):

    print "File type not supported"

def Import_5014(file_object, Mesh_Count):
    elu = file_object
    Mesh_Index = 0
    Mesh_Number = Mesh_Index + 1 # Variable init
    for i in range(Mesh_Count):
        Name_Length = struct.unpack('<I', elu.read(4))[0]
        Name = elu.read(Name_Length)
        Name = Clean_Name(Name)
        #Detect_Duplicates(Name, elu)
        print Name
        Parent_Mesh_Index = struct.unpack('<I', elu.read(4))[0] 
        Parent_Name_Length = struct.unpack('<I', elu.read(4))[0]
        Parent_Name = elu.read(Parent_Name_Length)
        Parent_Name = Clean_Name(Parent_Name)
        LM = struct.unpack('<16f', elu.read(64))
        Local_Matrix = om.MMatrix((
                LM[0],LM[1],LM[2],LM[3],
                LM[4],LM[5],LM[6],LM[7],
                LM[8],LM[9],LM[10],LM[11],
                LM[12],LM[13],LM[14],LM[15]
            ))

        # Assigns the given variables to specific positions of the list

        Names[i][0].append(Mesh_Index)
        Names[i][1].append(Parent_Mesh_Index)
        Names[i][2].append(Name)
        Names[i][3].append(Parent_Name)
        Names[i][4].append(Local_Matrix)
        
        # elu.seek(16, os.SEEK_CUR) debug

        float0 = struct.unpack('<f', elu.read(4))[0]
        float1 = struct.unpack('<f', elu.read(4))[0]
        float2 = struct.unpack('<f', elu.read(4))[0]
        float3 = struct.unpack('<f', elu.read(4))[0]

        print float0 
        print float1 
        print float2 
        print float3

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
        Blend_Vertex_Count = struct.unpack('<I', elu.read(4))[0]

        for j in range(Blend_Vertex_Count):
            Bones_Influences_Count = struct.unpack('<I', elu.read(4))[0]
            
            for j in range(Bones_Influences_Count):
                elu.seek(2, os.SEEK_CUR)
                elu.seek(6, os.SEEK_CUR)
            
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
        Joints_Angles[i][0].append(Lim_X_P)
        Joints_Angles[i][1].append(Lim_X_N)
        Joints_Angles[i][2].append(Lim_Y_P)
        Joints_Angles[i][3].append(Lim_Y_N)
        Joints_Angles[i][4].append(Lim_Z_P)
        Joints_Angles[i][5].append(Lim_Z_N)


    ##### Mesh Construct #####

        if (Vertex_Position_Count > 0):
            Mesh = meshFn.create(Vertices, PolygonFaces, PolygonConnects )
        else:
            Mesh = root_cube()

        Mesh_Ptr.append(Mesh)

    ##### Mesh Naming #####

        DPNode = om.MFnDependencyNode(Mesh)
        DPNode.setName(Name)
        
    ##### UV Mapping #####

        if (Vertex_Position_Count > 0):
            meshFn.renameUVSet('map1', Name)
            meshFn.setUVs(VTexcoords1, VTexcoords2, Name)
            meshFn.assignUVs(PolygonFaces, L_Face_Vertex_Texcoord_IDs, uvSet=Name)
        else:
            pass
        
        Mesh_Index += 1
        Mesh_Number += 1

        print "Mesh Item Imported successfully ",Name
        print "Switching to the next item"

    ##### Post Parsing Operations #####

    Log_Arrays(Names)
    Set_Transforms()
    Set_Parent()
    Generate_Joints()
    #Log_Arrays(Bones)
    Mesh_World_Parent()
    Bones_World_Parent()
    Delete_Joints_Mesh()
    Reparent_Joints()
    Set_Joints_Limit()
    Array_Copy(Names, World)
    Log_Arrays(World)

    print "No more mesh items to import -"
    print "Closing file -"
    print "Generating 3D Models in viewport ! ^^"

    print "EOF"

def Jump_5014(file_object): # Jumps to next 3d object in file
    elu = file_object
    print(elu.tell())
    elu.seek(4, os.SEEK_CUR) # Parent_Mesh_Index
    chunk_size = struct.unpack('<I', elu.read(4))[0]
    elu.seek(chunk_size, os.SEEK_CUR) # Parent_Name
    elu.seek(64, os.SEEK_CUR)
    elu.seek(16, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # vtx_pos
        elu.seek(12, os.SEEK_CUR)
    elu.seek(2, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # vtx_txtcoords
        elu.seek(12, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # ukn
        elu.seek(12, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # ukn
        elu.seek(12, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # vtx_nor
        elu.seek(12, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # ukn
        elu.seek(16, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # ukn
        elu.seek(12, os.SEEK_CUR)
    loops0 = struct.unpack('<I', elu.read(4))[0] # Faces Data
    if(loops0 > 0):
        elu.seek(8, os.SEEK_CUR)
        for j in range(loops0):
            loops1 = struct.unpack('<I', elu.read(4))[0]
            for k in range(loops1):
                elu.seek(SKIPPED_LENGTH0, os.SEEK_CUR)
            elu.seek(2, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # ukn
        elu.seek(12, os.SEEK_CUR)
    elu.seek(4, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # ukn
        elu.seek(8, os.SEEK_CUR)
    elu.seek(4, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # vtx_indices
        elu.seek(14, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # ukn
        elu.seek(64, os.SEEK_CUR)
    for j in range(loops): # ukn
        elu.seek(2, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # ukn
        elu.seek(12, os.SEEK_CUR)
    loops = struct.unpack('<I', elu.read(4))[0]
    for j in range(loops): # Faces Indices
        elu.seek(6, os.SEEK_CUR)
    elu.seek(24, os.SEEK_CUR) # Joint Rotation Limit
    print "=> 3D Object Jumped -"   
        
###########################################################################################################################################################

################################################################### Script instructions ###################################################################

New_Scene()

while(loop):
    Args = Main_Loop(run_count, loop) # Importation functions entrypoint
    run_count = Args[0]
    loop = Args[1]

print "\n"
print "EOS"

###########################################################################################################################################################
