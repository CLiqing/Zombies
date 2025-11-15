# item_generator.py
# 包含 ModItem 类和物品生成逻辑
import random
import pygame
try:
    import config as cfg
except ImportError:
    print("错误：item_generator.py 无法导入 config.py。")
    sys.exit()

class ModItem:
    """代表一个枪械强化模组"""
    def __init__(self, quality, monster_level, bias_type="游荡者"):
        self.quality = quality
        self.monster_level = monster_level
        self.bias_type = bias_type
        self.bias_display_name = cfg.BIAS_DISPLAY_NAMES.get(bias_type, "未知")

        settings = cfg.QUALITY_SETTINGS[self.quality]
        self.n = random.randint(*settings["n_range"]) # 词条数量
        self.c = random.randint(*settings["c_range"]) # 方格大小
        self.b = settings["b"] # 品质系数
        self.color = cfg.QUALITY_COLORS[self.quality]
        
        self.shape = self._generate_shape() # 形状, e.g., {(0, 0), (0, 1), (1, 1)}
        self.affixes = self._generate_affixes() # 词缀列表

    def _generate_shape(self):
        """生成一个c个方块的随机连通形状"""
        cells = set()
        start_cell = (0, 0)
        cells.add(start_cell)
        
        frontier = set(self._get_neighbors(start_cell, cells, True))
        
        while len(cells) < self.c and frontier:
            new_cell = random.choice(list(frontier))
            cells.add(new_cell)
            frontier.remove(new_cell)
            
            new_neighbors = self._get_neighbors(new_cell, cells, True)
            frontier.update(new_neighbors)
            
        return self._normalize_shape(cells)

    def _get_neighbors(self, cell, existing_cells, is_frontier=False):
        """获取一个单元格的相邻（非对角线）单元格"""
        r, c = cell
        neighbors = set()
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if is_frontier:
                if (nr, nc) not in existing_cells:
                    neighbors.add((nr, nc))
            else:
                neighbors.add((nr, nc))
        return neighbors

    def _normalize_shape(self, cells):
        """将形状的左上角移动到 (0, 0)"""
        if not cells:
            return set()
        min_r = min(r for r, c in cells)
        min_c = min(c for r, c in cells)
        return set((r - min_r, c - min_c) for r, c in cells)

    def _generate_affixes(self, locked_affixes=None):
        """根据规则生成词缀列表"""
        if locked_affixes is None:
            locked_affixes = []
        
        affixes = list(locked_affixes) # 包含锁定的词条
        num_to_generate = self.n - len(locked_affixes)
        
        # 1. 构建加权词缀池
        weighted_pool = {}
        bias = cfg.MONSTER_DROP_BIAS.get(self.bias_type, {})

        for pool_name, pool_affixes in cfg.AFFIX_POOLS.items():
            pool_weight_bonus = bias.get(pool_name, 0)
            for affix_name, base_weight in pool_affixes.items():
                specific_bonus = bias.get(affix_name, 0)
                total_weight = base_weight + pool_weight_bonus + specific_bonus
                if total_weight > 0:
                    weighted_pool[affix_name] = total_weight
        
        pool_keys = list(weighted_pool.keys())
        pool_weights = list(weighted_pool.values())

        # 2. 随机选择词缀
        if not pool_keys: 
            print(f"警告: {self.bias_type} 的词缀池为空。")
            return affixes

        chosen_names = random.choices(pool_keys, weights=pool_weights, k=num_to_generate)
        
        # 3. 计算词缀数值
        for name in chosen_names:
            base_val = cfg.BASE_STAT_VALUES.get(name, 0)
            
            value = (base_val * self.b) * \
                    (1 + self.c * cfg.SPACE_GROWTH_FACTOR) * \
                    (1 + self.monster_level * cfg.LEVEL_GROWTH_FACTOR)
            
            if base_val < 1.0:
                value *= random.uniform(0.9, 1.1)
            else:
                value = int(value * random.uniform(0.9, 1.1))

            affixes.append({"name": name, "value": value, "is_main": False})
        
        # 标记第一个为主属性
        if affixes:
            affixes[0]["is_main"] = True
            
        return affixes

    def reroll_affixes(self, level=1, locked_indices=None):
        """精炼：重新生成词缀 (Lvl 1 或 Lvl 2)"""
        locked_affixes = []
        if level == 2 and locked_indices:
            locked_affixes = [self.affixes[i] for i in locked_indices if i < len(self.affixes)]
            if len(locked_affixes) > 2:
                locked_affixes = locked_affixes[:2]
        
        # 重置主属性标记
        for affix in locked_affixes:
            affix["is_main"] = False

        self.affixes = self._generate_affixes(locked_affixes=locked_affixes)

    def rotate(self):
        """顺时针旋转90度"""
        new_shape = set((c, -r) for r, c in self.shape)
        self.shape = self._normalize_shape(new_shape)

    def get_bounds(self):
        """获取形状的边界 (width, height) in cells"""
        if not self.shape:
            return (0, 0)
        max_r = max(r for r, c in self.shape)
        max_c = max(c for r, c in self.shape)
        return (max_c + 1, max_r + 1) # 宽度, 高度

    def draw(self, surface, x, y, cell_size):
        """在指定屏幕坐标(x, y)绘制物品 (修复 1.6.5: 移除内部线条)"""
        # 1. 绘制所有实心方块
        for (r, c) in self.shape:
            cell_rect = pygame.Rect(
                x + c * cell_size,
                y + r * cell_size,
                cell_size,
                cell_size
            )
            pygame.draw.rect(surface, self.color, cell_rect)
        
        # 2. 绘制外边框 (只绘制不与其他方块相邻的边)
        for (r, c) in self.shape:
            cx, cy = x + c * cell_size, y + r * cell_size
            # 检查邻居
            neighbors = self._get_neighbors((r,c), set(), False)
            
            # 上
            if (r-1, c) not in self.shape:
                pygame.draw.line(surface, cfg.COLOR_BACKGROUND, (cx, cy), (cx + cell_size, cy), 1)
            # 下
            if (r+1, c) not in self.shape:
                pygame.draw.line(surface, cfg.COLOR_BACKGROUND, (cx, cy + cell_size), (cx + cell_size, cy + cell_size), 1)
            # 左
            if (r, c-1) not in self.shape:
                pygame.draw.line(surface, cfg.COLOR_BACKGROUND, (cx, cy), (cx, cy + cell_size), 1)
            # 右
            if (r, c+1) not in self.shape:
                pygame.draw.line(surface, cfg.COLOR_BACKGROUND, (cx + cell_size, cy), (cx + cell_size, cy + cell_size), 1)

def create_mod_item(quality, monster_level, bias_type=None):
    """
    创建 ModItem 的工厂函数。
    """
    if bias_type is None:
        bias_type = cfg.QUALITY_SETTINGS[quality]["bias"]
    
    return ModItem(quality, monster_level, bias_type)