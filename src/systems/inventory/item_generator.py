# item_generator.py
# 包含 ModItem 类和物品生成逻辑 (核心逻辑)
import random
import pygame
import sys
import math
import os

# 添加路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from systems.inventory import config as cfg
    from systems.inventory.utils import generate_and_optimize_polyomino, get_bounding_box_dims
    
    if not hasattr(cfg, 'ceil_to_nearest_ten'):
         def ceil_to_nearest_ten(n):
            return math.ceil(n / 10.0) * 10
         cfg.ceil_to_nearest_ten = ceil_to_nearest_ten

except ImportError as e:
    print(f"警告：item_generator.py 导入 config/utils 失败: {e}。使用默认值和模拟函数。")
    
    # 模拟导入的函数和常量，以便代码结构能通过
    def generate_and_optimize_polyomino(N): return {(0, 0)}
    def get_bounding_box_dims(cells_set): return 1, 1
    def ceil_to_nearest_ten(n): return math.ceil(n / 10.0) * 10
    
    class cfg: 
        MAIN_AFFIX_MULTIPLIER = 1.5
        QUALITY_SETTINGS = {"普通": {"n_range": (1, 1), "rare_n_range": (0, 0), "c_range": (1, 3), "b": 1.0}}
        QUALITY_COLORS = {"普通": (150, 150, 150)}
        BIAS_DISPLAY_NAMES = {"游荡者": "游荡者"}
        BASE_STAT_VALUES = {}
        RARE_AFFIX_NAMES = []
        GENERAL_AFFIX_NAMES = []
        AFFIX_POOLS = {}
        MONSTER_DROP_BIAS = {}
        SURVIVAL_AFFIXES = []
        OFFENSE_AFFIXES = []
        SPACE_GROWTH_FACTOR = 0.05
        LEVEL_GROWTH_FACTOR = 0.05
        RARE_SPACE_GROWTH_FACTOR = 0.025
        RARE_LEVEL_GROWTH_FACTOR = 0.025
        COLOR_BACKGROUND = (20, 20, 30)
        ceil_to_nearest_ten = ceil_to_nearest_ten


class ModItem:
    """代表一个枪械强化模组"""
    def __init__(self, quality, monster_level, bias_type="游荡者"):
        self.quality = quality
        self.monster_level = monster_level
        self.bias_type = bias_type
        self.bias_display_name = cfg.BIAS_DISPLAY_NAMES.get(bias_type, "未知")

        settings = cfg.QUALITY_SETTINGS[self.quality]
        self.n = random.randint(*settings["n_range"]) # 词条数量
        self.rare_n_min, self.rare_n_max = settings["rare_n_range"] # 稀有词条数量限制
        self.c = random.randint(*settings["c_range"]) # 方格大小 (N)
        self.b = settings["b"] # 品质系数
        self.color = cfg.QUALITY_COLORS[self.quality]
        
        self.shape_mode = "Optimized" 

        self.shape = self._generate_shape() 
        self.affixes = self._generate_affixes() # 词缀列表

    def _generate_shape(self):
        """使用周长优化算法生成形状。"""
        optimized_cells = generate_and_optimize_polyomino(self.c)
        if not optimized_cells:
            return self._normalize_shape({(0, 0)}) 
        return self._normalize_shape(optimized_cells)

    def _normalize_shape(self, cells):
        """将形状的左上角移动到 (0, 0)"""
        if not cells:
            return set()
        min_r = min(r for r, c in cells)
        min_c = min(c for r, c in cells)
        return set((r - min_r, c - min_c) for r, c in cells)

    def _get_weighted_pool_by_type(self, is_rare_pool, is_epic_or_better, locked_names):
        """
        根据词缀类型（稀有/通用）和品质门槛构建加权词缀池。
        返回的池子已排除 locked_names 中的词条。
        """
        weighted_pool = {}
        bias = cfg.MONSTER_DROP_BIAS.get(self.bias_type, {})
        
        for pool_name, pool_affixes in cfg.AFFIX_POOLS.items():
            
            is_affix_rare = any(name in cfg.RARE_AFFIX_NAMES for name in pool_affixes.keys())

            # 过滤：只构建稀有池 或 通用池
            if is_rare_pool and not is_affix_rare: continue
            if not is_rare_pool and is_affix_rare: continue

            # 专属稀有属性和射程的品质门槛
            if pool_name.startswith("稀有专属_"):
                if not is_epic_or_better or pool_name != f"稀有专属_{self.bias_type}":
                    continue
            if pool_name == "独立词条_射程":
                if self.quality != "传奇":
                    continue
            
            pool_weight_bonus = bias.get(pool_name, 0)
            
            for affix_name, base_weight in pool_affixes.items():
                if affix_name in locked_names: continue # 排除已锁定的词条
                
                total_weight = base_weight + pool_weight_bonus
                if total_weight > 0:
                    weighted_pool[affix_name] = total_weight
        
        return weighted_pool


    def _generate_affixes(self, locked_affixes=None):
        """
        根据规则生成词缀列表：不重复、满足稀有数量、主词条必中。
        """
        if locked_affixes is None:
            locked_affixes = []
            
        affixes = list(locked_affixes) 
        num_to_generate = self.n - len(locked_affixes)
        
        if num_to_generate <= 0:
            return affixes

        is_epic_or_better = self.quality in ["史诗", "传奇"]
        locked_names = [a["name"] for a in locked_affixes]
        
        # 1. 确定主词条数量（减去已锁定的主词条数量）
        main_affix_count = 1
        if self.quality == "传奇" and self.n == 5:
            main_affix_count = 2
        
        # 统计已锁定的主词条数量
        locked_main_count = sum(1 for a in locked_affixes if a.get("is_main", False))
        main_affix_count = max(0, main_affix_count - locked_main_count)
        
        # 2. 计算已锁定和所需稀有/通用词条数量
        locked_rare_n = sum(1 for name in locked_names if name in cfg.RARE_AFFIX_NAMES)
        
        rare_n_target = max(self.rare_n_min - locked_rare_n, 0) # 至少需要的稀有数量
        rare_n_max = self.rare_n_max - locked_rare_n           # 最多能有的稀有数量

        # 3. 词条抽取：分为主词条和普通词条 (确保不重复)
        chosen_names = []
        mains_to_generate = main_affix_count
        
        # 构建所有可用的词缀池 (不含已锁定词条)
        full_rare_pool = self._get_weighted_pool_by_type(True, is_epic_or_better, locked_names)
        full_general_pool = self._get_weighted_pool_by_type(False, is_epic_or_better, locked_names)
        
        # A. 抽取主词条 (不重复)
        while mains_to_generate > 0:
            
            # 构建主词条必中池 (只包含未选和未锁定词条)
            main_affix_candidates = {}
            
            # 1) 整合所有未选的词条
            available_names = set(full_rare_pool.keys()) | set(full_general_pool.keys())
            
            # 2) 过滤和加权
            for name in available_names:
                # **修复：普通装备不应抽取稀有词条作为主词条**
                if self.rare_n_max == 0 and name in cfg.RARE_AFFIX_NAMES:
                    continue
                    
                weight = full_rare_pool.get(name, full_general_pool.get(name))
                
                if self.bias_type == "铁桶" and name in cfg.SURVIVAL_AFFIXES:
                    main_affix_candidates[name] = weight
                elif self.bias_type == "食尸鬼" and name in cfg.OFFENSE_AFFIXES:
                    main_affix_candidates[name] = weight
                elif self.bias_type == "游荡者":
                    main_affix_candidates[name] = weight

            if not main_affix_candidates: break
                
            keys = list(main_affix_candidates.keys())
            weights = list(main_affix_candidates.values())
            
            if sum(weights) == 0: break
            
            main_name = random.choices(keys, weights=weights, k=1)[0]
            chosen_names.append(main_name)
            
            # 从两个池中移除
            full_rare_pool.pop(main_name, None)
            full_general_pool.pop(main_name, None)
            
            mains_to_generate -= 1
        
        # B. 抽取剩余的普通词条（满足稀有数量约束）
        
        chosen_rare_n = sum(1 for name in chosen_names if name in cfg.RARE_AFFIX_NAMES)
        remaining_to_generate = num_to_generate - len(chosen_names)
        
        if remaining_to_generate > 0:
            
            # 确定必须是稀有/通用的数量
            must_be_rare = max(rare_n_target - chosen_rare_n, 0)
            
            # 优先抽取必须满足的稀有词条
            for _ in range(must_be_rare):
                if not full_rare_pool: break
                
                name = random.choices(list(full_rare_pool.keys()), weights=list(full_rare_pool.values()), k=1)[0]
                chosen_names.append(name)
                full_rare_pool.pop(name)
                
            # 抽取剩余词条 (稀有或通用皆可，但要考虑最大限制)
            remaining_after_constraint = num_to_generate - len(chosen_names)
            
            if remaining_after_constraint > 0:
                
                combined_pool = {}
                
                # 稀有池：确保不超过 rare_n_max
                current_rare_n = sum(1 for name in chosen_names if name in cfg.RARE_AFFIX_NAMES)
                max_extra_rare = self.rare_n_max - current_rare_n
                
                if max_extra_rare > 0:
                    rare_names = list(full_rare_pool.keys())
                    
                    # 按照权重排序并取前 max_extra_rare 个，防止 rare pool 数量多于 max_extra_rare 
                    # 这里简化为将整个稀有池加入，交由 random.choices 决定
                    combined_pool.update(full_rare_pool)
                
                # 通用池：直接加入
                combined_pool.update(full_general_pool)
                
                if combined_pool:
                    
                    # 为了确保稀有词条不超过 max_extra_rare，我们手动执行加权抽取
                    keys = list(combined_pool.keys())
                    weights = [combined_pool[k] for k in keys]
                    
                    k_count = min(remaining_after_constraint, len(keys))
                    
                    if sum(weights) > 0:
                        
                        # 复杂抽取逻辑：多次抽取直到满足 k_count，并检查稀有词条限制
                        while len(chosen_names) < num_to_generate:
                            
                            # 重新构建当前池（已移除已选词条）
                            current_pool = {k:v for k,v in combined_pool.items() if k not in chosen_names}
                            
                            if not current_pool: break
                            
                            # 稀有词条超限检查
                            current_rare_count = sum(1 for name in chosen_names if name in cfg.RARE_AFFIX_NAMES)
                            
                            keys_current = list(current_pool.keys())
                            weights_current = list(current_pool.values())

                            # 如果当前已达到最大稀有数，则将稀有词条的权重设为0
                            if current_rare_count >= self.rare_n_max:
                                weights_current = [0 if k in cfg.RARE_AFFIX_NAMES else w for k, w in zip(keys_current, weights_current)]
                            
                            if sum(weights_current) == 0: break # 没有可抽取的词条了
                            
                            next_name = random.choices(keys_current, weights=weights_current, k=1)[0]
                            chosen_names.append(next_name)


        # 4. 计算词缀数值 (应用 K_main 和射程/回血取整)
        # 注意：已锁定的主词条已经在 locked_affixes 中，这里只处理新生成的词条
        mains_generated = 0 
        
        for name in chosen_names:
            base_val = cfg.BASE_STAT_VALUES.get(name, 0)
            
            # --- 应用主词条乘数 K_main ---
            # 只有当还需要生成主词条时，才将新词条标记为主词条
            is_main_affix = False
            k_main = 1.0
            if mains_generated < main_affix_count:
                k_main = cfg.MAIN_AFFIX_MULTIPLIER
                is_main_affix = True
                mains_generated += 1
            
            # --- 选择成长因子 ---
            if name in cfg.RARE_AFFIX_NAMES:
                s_c = cfg.RARE_SPACE_GROWTH_FACTOR
                s_a = cfg.RARE_LEVEL_GROWTH_FACTOR
            else:
                s_c = cfg.SPACE_GROWTH_FACTOR
                s_a = cfg.LEVEL_GROWTH_FACTOR

            value = (base_val * self.b * k_main) * \
                    (1 + self.c * s_c) * \
                    (1 + self.monster_level * s_a)
            
            value *= random.uniform(0.9, 1.1)
            
            # --- 取整规则 ---
            if name == "射程":
                # 射程向上取整为10的倍数
                value = cfg.ceil_to_nearest_ten(value)
            elif name == "生命回复":
                # 确保不超过两位小数
                value = round(value, 2) 
            elif base_val >= 1.0: 
                value = int(value) # 其他整数属性取整

            affixes.append({"name": name, "value": value, "is_main": is_main_affix})
            
        return affixes

    def reroll_affixes(self, level=1, locked_indices=None):
        """
        精炼：重新生成词缀。
        Level 2 精炼：自动保留所有主词条（最多2个），只随机副词条。
        """
        locked_affixes = []
        
        if level == 2:
            # 1. 自动识别并锁定所有当前的主词条
            main_affix_indices = [i for i, affix in enumerate(self.affixes) if affix["is_main"]]
            
            for i in main_affix_indices:
                locked_affixes.append(self.affixes[i].copy())
        
        elif level == 1:
            # Level 1 精炼，不保留任何词条，忽略 locked_indices
            pass 
        
        # 保持锁定词条的 is_main 状态，_generate_affixes 会正确处理
        self.affixes = self._generate_affixes(locked_affixes=locked_affixes)

    def rotate(self):
        """顺时针旋转90度"""
        new_shape = set((c, -r) for r, c in self.shape)
        self.shape = self._normalize_shape(new_shape)

    def get_bounds(self):
        """获取形状的边界 (width, height) in cells"""
        return get_bounding_box_dims(self.shape)

    def draw(self, surface, x, y, cell_size):
        """在指定屏幕坐标(x, y)绘制物品"""
        for (r, c) in self.shape:
            cell_rect = pygame.Rect(
                x + c * cell_size,
                y + r * cell_size,
                cell_size,
                cell_size
            )
            pygame.draw.rect(surface, self.color, cell_rect)
            
        for (r, c) in self.shape:
            cx, cy = x + c * cell_size, y + r * cell_size
            if (r-1, c) not in self.shape:
                pygame.draw.line(surface, cfg.COLOR_BACKGROUND, (cx, cy), (cx + cell_size, cy), 1)
            if (r+1, c) not in self.shape:
                pygame.draw.line(surface, cfg.COLOR_BACKGROUND, (cx, cy + cell_size), (cx + cell_size, cy + cell_size), 1)
            if (r, c-1) not in self.shape:
                pygame.draw.line(surface, cfg.COLOR_BACKGROUND, (cx, cy), (cx, cy + cell_size), 1)
            if (r, c+1) not in self.shape:
                pygame.draw.line(surface, cfg.COLOR_BACKGROUND, (cx + cell_size, cy), (cx + cell_size, cy + cell_size), 1)

def create_mod_item(quality, monster_level, bias_type=None):
    """创建 ModItem 的工厂函数。"""
    if bias_type is None:
        bias_type = cfg.QUALITY_SETTINGS[quality]["bias"]
    return ModItem(quality, monster_level, bias_type)