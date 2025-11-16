# monsters/monster_logic.py
import math
import random
import sys
import os

# 添加父目录到路径以便导入config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 导入自身目录下的配置
from systems.monsters import config as mcfg 

# --- 怪物基类 (Monster) ---
class Monster:
    """所有僵尸怪物的基类，包含基本属性和伤害计算"""
    
    def __init__(self, monster_type, level, is_elite, position):
        self.type = monster_type       # 'Wanderer', 'Bucket', 'Ghoul'
        self.is_elite = is_elite
        # 精英怪物等级+20
        self.level = level + 20 if is_elite else level  # 怪物等级 a
        self.position = position       # (r, c) 初始位置
        self.drop_bias = monster_type 
        
        self.name = self._get_display_name()
        
        # 1. 计算基础属性 (M_HP, M_ARMOR, M_DMG)
        self._calculate_base_stats()
        
        # 2. 技能状态
        self.skills_active = {} 
        self.elite_skills = self._get_elite_skills()
        self._init_skills()

        # 3. 初始状态
        self.current_hp = self.max_hp
        self.is_alive = True
        self.is_reviving = False
        self.revive_timer = 0
        self.has_revived = False  # 游荡者只能复活一次
        
        # 防御技能冷却
        self.last_block_time = -999  # 铁桶格挡冷却
        self.cached_armor_bonus = 0  # 铁甲光环缓存的护甲加成
        
    def _get_display_name(self):
        """返回更友好的名称"""
        name_map = {"Wanderer": "游荡者", "Bucket": "铁桶", "Ghoul": "食尸鬼"}
        prefix = "精英" if self.is_elite else ""
        return prefix + name_map.get(self.type, "未知怪物")

    def _calculate_base_stats(self):
        """
        计算怪物随等级 a 成长后的属性，并应用类型修正。
        """
        a = self.level
        params = mcfg.MONSTER_GROWTH_PARAMS
        mods = mcfg.MONSTER_BASE_STATS.get(self.type, {"HP_MOD": 1, "ARMOR_MOD": 1, "DMG_MOD": 1})
        
        # HP (二次方增长)
        growth_hp = (1 + params["HP_LINEAR_G"] * a + params["HP_QUADRATIC_P"] * a**2)
        self.max_hp = params["HP_BASE"] * growth_hp * mods["HP_MOD"]
        self.max_hp = math.ceil(self.max_hp)

        # ARMOR (线性增长)
        growth_armor = (1 + params["ARMOR_LINEAR_G"] * a)
        self.armor = params["ARMOR_BASE"] * growth_armor * mods["ARMOR_MOD"]
        self.armor = math.ceil(self.armor)

        # DAMAGE (线性增长)
        growth_dmg = (1 + params["DMG_LINEAR_G"] * a)
        self.damage = params["DMG_BASE"] * growth_dmg * mods["DMG_MOD"]
        self.damage = math.ceil(self.damage)

        # 速度 (基础值)
        self.movement_speed = 1.0 
        if self.type == "Wanderer" and not self.is_elite:
            self.movement_speed = 1.1
        
        # 攻击参数（从config导入）
        self.attack_range = self._get_attack_range()
        self.attack_cooldown = self._get_attack_cooldown() 
            
    def _init_skills(self):
        """初始化怪物独有的技能状态和属性"""
        # 游荡者
        if self.type == "Wanderer":
            self.skills_active['revive_timer'] = 0.0
            self.revive_delay = mcfg.MONSTER_SKILL_PARAMS["Wanderer_Revive_Delay"]

        # 铁桶
        elif self.type == "Bucket":
            self.skills_active['giant_stacks'] = 0
            
        # 食尸鬼
        elif self.type == "Ghoul":
            self.evade_chance = mcfg.MONSTER_SKILL_PARAMS["Ghoul_Evade_Chance"]
            if '暴击' in self.elite_skills:
                self.crit_chance = mcfg.MONSTER_SKILL_PARAMS["Ghoul_Elite_Crit_Chance"]
                self.crit_damage_mult = 1.0 + mcfg.MONSTER_SKILL_PARAMS["Ghoul_Elite_Crit_Dmg"]
            else:
                self.crit_chance = 0.0
                self.crit_damage_mult = 1.0
        
    def _get_elite_skills(self):
        """确定精英怪的分支技能"""
        if not self.is_elite: return []
        
        if self.type == "Wanderer":
            # 游荡者精英只有一个分支
            return ['召唤'] 
        elif self.type == "Bucket":
            # 铁桶精英随机获得一个分支
            return random.choice([['烈爆'], ['巨人']])
        elif self.type == "Ghoul":
            # 食尸鬼精英随机获得一个分支
            return random.choice([['暴击'], ['飞天']])
        return []

    # --- 简化战斗接口 (用于测试输出) ---
    def get_info(self):
        """返回怪物的关键信息字典"""
        info = {
            "名称": self.name,
            "类型": self.type,
            "等级(a)": self.level,
            "精英": self.is_elite,
            "位置(r, c)": self.position,
            "Max HP": self.max_hp,
            "护甲(Armor)": self.armor,
            "攻击力(DMG)": self.damage,
            "移动速度": f"{self.movement_speed * 100:.0f}%",
            "基础技能": self.get_base_skill_info(),
            "进阶技能": self.get_advanced_skill_info(),
            "精英技能": ", ".join(self.elite_skills) if self.elite_skills else "无"
        }
        return info
    
    def get_base_skill_info(self):
        """返回先天技能信息"""
        if self.type == "Bucket":
            return f"概率格挡({mcfg.MONSTER_SKILL_PARAMS['Bucket_Block_Chance']*100:.0f}%), 范围AoE({mcfg.MONSTER_SKILL_PARAMS['Bucket_AOE_Range']}px)"
        elif self.type == "Ghoul":
            return f"迅扑(距{mcfg.MONSTER_SKILL_PARAMS['Ghoul_Dash_Min_Range']}~{mcfg.MONSTER_SKILL_PARAMS['Ghoul_Dash_Max_Range']}px)"
        return "无"
        
    def get_advanced_skill_info(self):
        """返回进阶技能信息"""
        info = []
        if self.type == "Wanderer":
            info.append(f"团结光环({mcfg.MONSTER_SKILL_PARAMS['Wanderer_Aura_Factor']*100:.0f}% DMG, 可叠加)")
            info.append(f"重生(3秒后复活)")
        elif self.type == "Bucket":
            info.append(f"护甲光环({mcfg.MONSTER_SKILL_PARAMS['Bucket_Armor_Aura_Factor']*100:.0f}% Armor)")
            info.append(f"尸爆({mcfg.MONSTER_SKILL_PARAMS['Bucket_Corpse_Explosion_HP_Dmg']*100:.0f}% MaxHP Dmg)")
        elif self.type == "Ghoul":
            info.append(f"闪避({mcfg.MONSTER_SKILL_PARAMS['Ghoul_Evade_Chance']*100:.0f}%)")
            info.append(f"独狼(无视{mcfg.MONSTER_SKILL_PARAMS['Ghoul_Lone_Wolf_Armor_Ignore']*100:.0f}%护甲)")
        return ", ".join(info)
    
    def _get_attack_range(self):
        """获取怪物的攻击范围"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        import config
        return config.MONSTER_ATTACK_RANGE.get(self.type, 50)
    
    def _get_attack_cooldown(self):
        """获取怪物的攻击冷却时间"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        import config
        return config.MONSTER_ATTACK_COOLDOWN.get(self.type, 1.5)
    
    def can_attack(self, monster_world_pos, target_pos, current_time, last_attack_time):
        """
        判断怪物是否可以攻击目标
        
        Args:
            monster_world_pos: 怪物的世界坐标 (x, y) 像素
            target_pos: 目标位置 (x, y) 像素
            current_time: 当前时间（秒）
            last_attack_time: 上次攻击时间（秒）
        
        Returns:
            bool: 是否可以攻击
        """
        if not self.is_alive:
            return False
        
        # 检查冷却
        if current_time - last_attack_time < self.attack_cooldown:
            return False
        
        # 检查距离（使用世界坐标）
        import math
        dx = target_pos[0] - monster_world_pos[0]
        dy = target_pos[1] - monster_world_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        return distance <= self.attack_range
    
    def calculate_damage(self, nearby_monsters):
        """
        计算怪物的实际攻击伤害（考虑光环效果）
        
        Args:
            nearby_monsters: 附近的怪物列表 [(monster, distance), ...]
        
        Returns:
            float: 实际伤害值
        """
        base_damage = self.damage
        
        # 游荡者：团结光环（附近每有一个游荡者，攻击力提升10%）
        if self.type == "Wanderer":
            wanderer_count = sum(1 for m, dist in nearby_monsters 
                               if m.type == "Wanderer" and dist <= mcfg.MONSTER_SKILL_PARAMS["Wanderer_Aura_Range"])
            if wanderer_count > 0:
                bonus = wanderer_count * mcfg.MONSTER_SKILL_PARAMS["Wanderer_Aura_Factor"]
                base_damage *= (1 + bonus)
        
        return base_damage
    
    def calculate_damage_with_cache(self, cached_aura_bonus):
        """
        使用缓存的光环加成计算伤害（性能优化版本）
        
        Args:
            cached_aura_bonus: 预计算的光环加成比例（例如 0.2 表示 20%）
        
        Returns:
            float: 实际伤害值
        """
        base_damage = self.damage
        
        # 直接应用缓存的加成
        if cached_aura_bonus > 0:
            base_damage *= (1 + cached_aura_bonus)
        
        return base_damage
    
    def perform_attack(self, target_pos, nearby_monsters):
        """
        执行攻击，返回攻击信息
        
        Args:
            target_pos: 目标位置 (x, y)
            nearby_monsters: 附近的怪物列表 [(monster, distance), ...]
        
        Returns:
            dict: 攻击信息 {
                'damage': 伤害值,
                'type': 攻击类型 ('melee', 'aoe'),
                'range': 攻击范围（AoE时使用）,
                'position': 攻击位置,
                'armor_ignore': 护甲穿透比例（食尸鬼独狼技能）
            }
        """
        damage = self.calculate_damage(nearby_monsters)
        
        attack_info = {
            'damage': damage,
            'attacker_name': self.name,
            'attacker_type': self.type,
            'position': target_pos,
            'armor_ignore': 0  # 默认无护甲穿透
        }
        
        if self.type == "Bucket":
            # 铁桶：AoE攻击
            attack_info['type'] = 'aoe'
            attack_info['range'] = self.attack_range
        elif self.type == "Ghoul":
            # 食尸鬼：近战攻击 + 独狼技能
            attack_info['type'] = 'melee'
            attack_info['armor_ignore'] = mcfg.MONSTER_SKILL_PARAMS['Ghoul_Lone_Wolf_Armor_Ignore']
        else:
            # 游荡者：近战攻击
            attack_info['type'] = 'melee'
        
        return attack_info
    
    def take_damage(self, damage, damage_source="未知"):
        """
        怪物受到伤害，触发防御技能判定
        
        Args:
            damage: 基础伤害值
            damage_source: 伤害来源
        
        Returns:
            dict: {
                'blocked': bool,  # 是否被格挡
                'evaded': bool,   # 是否被闪避
                'actual_damage': float,  # 实际伤害
                'died': bool,  # 是否死亡
                'will_revive': bool  # 是否会复活
            }
        """
        if not self.is_alive or self.is_reviving:
            return {
                'blocked': False,
                'evaded': False,
                'actual_damage': 0,
                'died': False,
                'will_revive': False
            }
        
        import random
        import pygame
        
        blocked = False
        evaded = False
        actual_damage = damage
        current_time = pygame.time.get_ticks() / 1000.0
        
        # 铁桶：格挡判定
        if self.type == "Bucket":
            block_cd = mcfg.MONSTER_SKILL_PARAMS['Bucket_Block_Cooldown']
            if current_time - self.last_block_time >= block_cd:
                block_chance = mcfg.MONSTER_SKILL_PARAMS['Bucket_Block_Chance']
                if random.random() < block_chance:
                    blocked = True
                    self.last_block_time = current_time
                    reduction = mcfg.MONSTER_SKILL_PARAMS['Bucket_Block_Reduction']
                    actual_damage *= (1 - reduction)  # 减少90%伤害
        
        # 食尸鬼：闪避判定
        if self.type == "Ghoul" and not blocked:
            evade_chance = mcfg.MONSTER_SKILL_PARAMS['Ghoul_Evade_Chance']
            if random.random() < evade_chance:
                evaded = True
                actual_damage = 0  # 完全闪避
        
        # 扣除生命值
        self.current_hp -= actual_damage
        
        # Debug日志
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        import config as game_config
        if game_config.DEBUG_COMBAT_LOG:
            if blocked:
                print(f"[COMBAT] {self.name} 格挡！受到 {actual_damage:.1f} 伤害（原始：{damage:.1f}，减免90%）- HP: {self.current_hp:.1f}/{self.max_hp}", flush=True)
            elif evaded:
                print(f"[COMBAT] {self.name} 闪避！完全躲开攻击 - HP: {self.current_hp:.1f}/{self.max_hp}", flush=True)
            else:
                print(f"[COMBAT] {self.name} 受到 {actual_damage:.1f} 伤害 - HP: {self.current_hp:.1f}/{self.max_hp}", flush=True)
        
        # 判定死亡
        died = False
        will_revive = False
        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_alive = False
            died = True
            
            # 游荡者：复活判定
            if self.type == "Wanderer" and not self.has_revived:
                will_revive = True
                self.is_reviving = True
                self.revive_timer = mcfg.MONSTER_SKILL_PARAMS['Wanderer_Revive_Delay']
                self.has_revived = True  # 标记已使用复活
        
        return {
            'blocked': blocked,
            'evaded': evaded,
            'actual_damage': actual_damage,
            'died': died,
            'will_revive': will_revive
        }

# --- 怪物生成核心函数 ---

def generate_monsters(city_map, current_day):
    """
    根据天数和地图，随机生成怪物列表。
    注意：允许多个怪物共享同一出生点。
    """
    a = current_day # 怪物等级 a
    
    # 1. 确定总怪物数量
    map_width, map_height = city_map.get_dimensions()
    map_area = map_width * map_height
    total_monsters = mcfg.MONSTER_COUNT_FORMULA(current_day, map_area)
    
    # 2. 确定精英怪概率
    elite_chance = mcfg.ELITE_CHANCE_FORMULA(current_day)
    
    # 3. 获取所有可能的出生点
    spawn_points = {
        "Wanderer": city_map.get_wanderer_spawn_points(),
        "Bucket": city_map.get_bucket_spawn_points(),
        "Ghoul": city_map.get_ghoul_spawn_points()
    }
    
    valid_types = [t for t, points in spawn_points.items() if points]
    if not valid_types:
        print("警告：地图上没有有效的怪物出生点。")
        return []

    monsters = []
    
    # 4. 随机生成怪物（按比例：游荡者50%、食尸鬼30%、铁桶20%）
    monster_weights = {
        "Wanderer": 0.5,  # 游荡者占50%
        "Ghoul": 0.3,     # 食尸鬼占30%
        "Bucket": 0.2     # 铁桶占20%
    }
    
    # 过滤出有效的怪物类型及其权重
    valid_weights = [monster_weights.get(t, 0) for t in valid_types]
    
    for _ in range(total_monsters):
        # 按权重随机选择怪物类型
        monster_type = random.choices(valid_types, weights=valid_weights, k=1)[0]
        
        type_points = spawn_points[monster_type]
        if not type_points:
            continue
            
        pos = random.choice(type_points)
        is_elite = random.random() < elite_chance
        
        monster = Monster(monster_type, a, is_elite, pos)
        monsters.append(monster)
        
    return monsters