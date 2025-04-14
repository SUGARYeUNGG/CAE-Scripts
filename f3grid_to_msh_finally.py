import numpy as np
from fipy import Grid3D, CellVariable, TransientTerm, DiffusionTerm, Gmsh3D
import os
import traceback
import sys
#import pyvista as pv

def read_flac3d(filename):
    """
    读取FLAC3D格式的网格文件，提取节点坐标和单元编号
    
    参数:
        filename: FLAC3D网格文件名
    
    返回:
        vertices: 节点坐标数组 (N, 3)
        cells: 单元节点编号列表，每个元素是一个节点编号数组
        cell_types: 单元类型列表，每个元素是一个字符串，如'B8', 'W6', 'P5'等
    """
    vertices = []
    cells = []
    cell_types = []
    #  输出时 多了一组 单元编号 
    try:
        with open(filename, 'r', encoding='latin-1') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # 只处理以G或Z开头的行
                if line.startswith('G'):
                    parts = line.split()
                    if len(parts) >= 4:
                        # 格式: G node_id x y z
                        # 跳过节点ID，只取坐标
                        x = float(parts[2])
                        y = float(parts[3])
                        z = float(parts[4])
                        vertices.append([x, y, z])
                
                elif line.startswith('Z'):
                    parts = line.split()
                    if len(parts) >= 3:
                        # 格式: Z cell_type node1 node2 node3 ...
                        cell_type = parts[1]  # 如 'B8', 'W6', 'P5' 等
                        
                        # 只处理数字部分，忽略其他字符串
                        node_indices = []
                        for idx in parts[2:]:
                            try:
                                node_idx = int(idx) - 1  # 减1是因为FLAC3D使用1-based索引
                                node_indices.append(node_idx)
                            except ValueError:
                                continue  # 忽略非数字部分
                        
                        if node_indices:  # 只有当有有效的节点编号时才添加单元
                            cells.append(node_indices)
                            cell_types.append(cell_type)
                
                # 其他所有行都忽略
    
    except Exception as e:
        print(f"读取FLAC3D文件时出错: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    return np.array(vertices), cells, cell_types

def create_gmsh_mesh(vertices, cells, cell_types, filename):
    """
    从FLAC3D数据创建Gmsh MSH2格式网格文件
    
    参数:
        vertices: 节点坐标数组 (N, 3)
        cells: 单元节点编号列表
        cell_types: 单元类型列表
        filename: 输出文件名
    
    返回:
        success: 是否成功创建Gmsh网格
    """
    try:
        print(f"创建Gmsh MSH2格式网格文件: {filename}")
        
        # 打开文件
        with open(filename, 'w') as f:
            # 写入Gmsh MSH2格式头部
            f.write("$MeshFormat\n")
            f.write("2.2 0 8\n")  # 版本2.2，ASCII格式，双精度
            f.write("$EndMeshFormat\n\n")
            
            # 写入物理名称（可选）
            f.write("$PhysicalNames\n")
            f.write("0\n")  # 没有物理名称
            f.write("$EndPhysicalNames\n\n")
            
            # 写入节点
            f.write("$Nodes\n")
            f.write(f"{len(vertices)}\n")
            for i, vertex in enumerate(vertices):
                # Gmsh使用1-based索引
                # f.write(f"{i+1} {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")
                # 输出为浮点数，不要省略
                f.write(f"{i+1} {vertex[0]} {vertex[1]} {vertex[2]}\n")
                # f.write(f"{i+1} {vertex[0]} {vertex[1]} {vertex[2]}\n")

            f.write("$EndNodes\n\n")
            
            # 写入单元
            f.write("$Elements\n")
            f.write(f"{len(cells)}\n")
            
            # 单元类型映射: T4=4, B8=5, W6=6, P5=7
            cell_type_map = {
                'T4': 4,  # 四面体
                'B8': 5,  # 六面体
                'W6': 6,  # 楔形
                'P5': 7   # 金字塔
            }
            
            for i, (cell, cell_type) in enumerate(zip(cells, cell_types)):
                # 获取Gmsh单元类型
                gmsh_type = cell_type_map.get(cell_type, 4)  # 默认使用四面体
                
                # 写入单元
                # 格式: 单元ID 单元类型 标签数量 物理标签 基本标签 节点ID1 节点ID2 ...
                # 注意: Gmsh使用1-based索引
                f.write(f"{i+1} {gmsh_type} 2 0 0")  # 2个标签，都是0
                for node_idx in cell[1:]:
                    f.write(f" {node_idx+1}")  # 加1是因为Gmsh使用1-based索引
                f.write("\n")
            
            f.write("$EndElements\n")
        
        print(f"Gmsh MSH2格式网格文件已成功创建: {filename}")
        return True
    except Exception as e:
        print(f"创建Gmsh网格文件时出错: {e}")
        traceback.print_exc()
        return False

def create_fipy_mesh_from_gmsh(gmsh_file):
    """
    从Gmsh文件创建FiPy网格
    
    参数:
        gmsh_file: Gmsh文件路径
    
    返回:
        mesh: FiPy网格对象
    """
    try:
        print(f"从Gmsh文件创建FiPy网格: {gmsh_file}")
        
        # 使用Gmsh3D创建网格
        mesh = Gmsh3D(gmsh_file)
        
        # 获取网格信息
        # 注意：vertexCoords、cellCenters和faceCenters已经是NumPy数组，不需要.value属性
        num_cells = len(mesh.cellCenters[0])
        num_faces = len(mesh.faceCenters[0])
        num_vertices = len(mesh.vertexCoords[0])
        
        print(f"FiPy网格创建成功: {num_cells} 个单元, {num_faces} 个面, {num_vertices} 个顶点")
        return mesh
    except Exception as e:
        print(f"从Gmsh文件创建FiPy网格时出错: {e}")
        traceback.print_exc()
        return None


def f3grid_2_msh(filename,output_filename):
    try:
        # 读取FLAC3D文件
        print("读取FLAC3D文件...")
        vertices, cells, cell_types = read_flac3d(filename)
        print(f"读取到 {len(vertices)} 个节点和 {len(cells)} 个单元")
        
        # 统计不同类型的单元数量
        cell_type_counts = {}
        for ct in cell_types:
            if ct in cell_type_counts:
                cell_type_counts[ct] += 1
            else:
                cell_type_counts[ct] = 1
        
        print("单元类型统计:")
        for ct, count in cell_type_counts.items():
            print(f"  {ct}: {count} 个")
        
        # 创建Gmsh网格文件
        gmsh_file = output_filename
        success = create_gmsh_mesh(vertices, cells, cell_types, gmsh_file)
        
        if not success:
            print("创建Gmsh网格文件失败，程序终止")
            return
        
        # 从Gmsh文件创建FiPy网格
        mesh = create_fipy_mesh_from_gmsh(gmsh_file)
        
        if mesh is None:
            print("创建FiPy网格失败，程序终止")
            return
        
        print("完成!")
    except Exception as e:
        print(f"程序执行出错: {e}")
        traceback.print_exc()

def reorder_flac3d_to_gmsh_hex8(nodes):
    index_map = [2, 4, 7, 5, 0, 1, 6, 3]
    return [nodes[i] for i in index_map]

def reorder_flac3d_to_gmsh_wedge6(nodes):
    index_map = [5, 2, 4, 3, 0, 1]
    return [nodes[i] for i in index_map]

def reorder_flac3d_to_gmsh_pyramid5(nodes):
    index_map = [2, 0, 1, 4, 3]
    return [nodes[i] for i in index_map]

def reorder_flac3d_to_gmsh_tetra4(nodes):
    index_map = [0, 2, 3, 1]
    return [nodes[i] for i in index_map]

def convert_msh_node_order(input_file, output_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    current_line = 0
    output_lines = []

    while current_line < len(lines):
        line = lines[current_line]
        output_lines.append(line)

        if line.strip() == "$Elements":
            current_line += 1
            num_elements = int(lines[current_line].strip())
            output_lines.append(lines[current_line])
            current_line += 1

            for _ in range(num_elements):
                line = lines[current_line].strip()
                parts = line.split()
                elm_id = int(parts[0])
                elm_type = int(parts[1])
                num_tags = int(parts[2])
                tags = parts[3:3+num_tags]
                node_ids = list(map(int, parts[3+num_tags:]))

                if elm_type == 5 and len(node_ids) == 8:
                    node_ids = reorder_flac3d_to_gmsh_hex8(node_ids)
                elif elm_type == 6 and len(node_ids) == 6:
                    node_ids = reorder_flac3d_to_gmsh_wedge6(node_ids)
                elif elm_type == 7 and len(node_ids) == 5:
                    node_ids = reorder_flac3d_to_gmsh_pyramid5(node_ids)
                elif elm_type == 4 and len(node_ids) == 4:
                    node_ids = reorder_flac3d_to_gmsh_tetra4(node_ids)

                new_line = f"{elm_id} {elm_type} {num_tags} {' '.join(tags)} {' '.join(map(str, node_ids))}\n"
                output_lines.append(new_line)
                current_line += 1
        else:
            current_line += 1

    with open(output_file, 'w') as f:
        f.writelines(output_lines)

    print(f"✅ Gmsh 节点顺序转换完成，输出文件：{output_file}")



if __name__ == "__main__":
    f3grid_2_msh("input.f3grid","convert.msh")
    convert_msh_node_order("convert.msh", "output.msh")