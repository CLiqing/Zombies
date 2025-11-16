# utils.py
# 包含所有与 ModItem 形状生成相关的辅助函数和优化算法。

import random
import math
import numpy as np
import sys
import os

# 添加路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# 注意：utils.py 必须能够导入 config
try:
    from systems.inventory import config as cfg
except ImportError:
    # 假设在实际运行环境中 config 是可用的
    # 如果 config 不可用，我们将使用默认值
    print("警告：utils.py 无法导入 config.py，使用默认值 MOD_PANEL_ROWS = 6。")
    class ConfigMock:
        MOD_PANEL_ROWS = 6
    cfg = ConfigMock()

# --- 全局常量 (用于形状生成和优化) ---

MOD_PANEL_ROWS = cfg.MOD_PANEL_ROWS
# 用于形状生成的内部大网格尺寸 (确保有足够的空间移动)
GRID_SIZE = MOD_PANEL_ROWS + 10 # 增加一些裕度

# --- 形状几何辅助函数 ---

def get_bounding_box_dims(cells_set):
    """
    计算单元格集合的边界框尺寸 (行数, 列数)。
    """
    # 修复：处理 NumPy 数组的空检查
    if isinstance(cells_set, np.ndarray):
        if cells_set.shape[0] == 0:
            return 0, 0
        rows = cells_set[:, 0]
        cols = cells_set[:, 1]
    else: # 假设是 Python set
        if not cells_set:
            return 0, 0
        rows = [r for r, c in cells_set]
        cols = [c for r, c in cells_set]
    
    height = max(rows) - min(rows) + 1
    width = max(cols) - min(cols) + 1
    return height, width

def check_dims_constraint(cells_set, max_dim=MOD_PANEL_ROWS):
    """检查尺寸约束：行数或列数至少有一个不超过 max_dim。"""
    height, width = get_bounding_box_dims(cells_set)
    return height <= max_dim or width <= max_dim

def get_min_perimeter(N):
    """计算 N 个单元格形成的最紧凑形状的理论最小周长。"""
    if N <= 0:
        return 0
    if N == 1:
        return 4
    k = math.sqrt(N)
    p_min = 2 * (math.ceil(k) + math.floor(k))
    return int(p_min)

def calculate_perimeter_for_set(cells_set):
    """根据单元格集合计算周长。"""
    perimeter = 0
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] 
    
    # 将输入转换为 Python set 以便快速查找
    if isinstance(cells_set, np.ndarray):
        cells_set = set(map(tuple, cells_set))
    
    for r, c in cells_set:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            # 如果邻居在网格外 (边界) 或不在 cells_set 中 (周长边)
            if not (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE) or (nr, nc) not in cells_set:
                perimeter += 1
    return perimeter

# --- 周长优化算法核心 ---

def optimize_polyomino(initial_cells, max_moves=100):
    """
    通过局部移动优化 N-omino 的形状，最小化其周长，并检查尺寸约束。
    """
    current_cells = initial_cells.copy()
    current_perimeter = calculate_perimeter_for_set(current_cells) 
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] 
    
    for _ in range(max_moves):
        best_perimeter_reduction = 0
        best_move = None 
        
        removable_cells = list(current_cells)
        random.shuffle(removable_cells)
        
        for r_remove, c_remove in removable_cells:
            
            for dr, dc in directions:
                r_add, c_add = r_remove + dr, c_remove + dc
                
                if (0 <= r_add < GRID_SIZE and 0 <= c_add < GRID_SIZE and 
                    (r_add, c_add) not in current_cells):

                    new_cells = current_cells.copy()
                    new_cells.remove((r_remove, c_remove))
                    new_cells.add((r_add, c_add))
                    
                    # 关键检查 1: 确保新形状满足尺寸限制
                    if not check_dims_constraint(new_cells):
                        continue
                        
                    # 优化检查：新周长是否更好
                    new_perimeter = calculate_perimeter_for_set(new_cells)
                    reduction = current_perimeter - new_perimeter
                    
                    if reduction > best_perimeter_reduction:
                        best_perimeter_reduction = reduction
                        best_move = ((r_remove, c_remove), (r_add, c_add))

        if best_move and best_perimeter_reduction > 0:
            (r_remove, c_remove), (r_add, c_add) = best_move
            current_cells.remove((r_remove, c_remove))
            current_cells.add((r_add, c_add))
            current_perimeter -= best_perimeter_reduction
        else:
            break
            
    return current_cells

def generate_and_optimize_polyomino(N, max_optimization_moves=100, max_init_attempts=50):
    """
    生成一个随机的连通形状，然后通过周长优化使其紧凑。
    """
    initial_cells = None
    
    for attempt in range(max_init_attempts):
        temp_cells = set()
        # 在大网格的中心区域随机选择起点
        start_r = random.randint(GRID_SIZE // 2 - 2, GRID_SIZE // 2 + 1) 
        start_c = random.randint(GRID_SIZE // 2 - 2, GRID_SIZE // 2 + 1)
        
        temp_cells.add((start_r, start_c))
        
        boundary_candidates = set()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] 
        
        # 初始化边界
        for dr, dc in directions:
            nr, nc = start_r + dr, start_c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                 boundary_candidates.add((nr, nc))

        count = 1
        
        # 随机连通生长 (随机 BFS)
        while count < N and boundary_candidates:
            next_cell = random.choice(list(boundary_candidates))
            nr, nc = next_cell
            
            temp_cells.add((nr, nc))
            count += 1
            
            boundary_candidates.remove(next_cell)
            
            # 更新边界
            for dr, dc in directions:
                nnr, nnc = nr + dr, nc + dc
                if 0 <= nnr < GRID_SIZE and 0 <= nnc < GRID_SIZE and (nnr, nnc) not in temp_cells:
                    boundary_candidates.add((nnr, nnc))
        
        # 检查 N 数量和尺寸约束
        if count == N and check_dims_constraint(temp_cells):
            initial_cells = temp_cells
            break

    if initial_cells is None:
        return set() # 返回空集表示失败

    optimized_cells = optimize_polyomino(initial_cells, max_optimization_moves)
    
    return optimized_cells