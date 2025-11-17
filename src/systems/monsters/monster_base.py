# monster_base.py
"""
怪物基类，定义所有怪物的通用属性和方法
"""
import math
import random
import sys
import os

# 添加父目录到路径以便导入config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 导入自身目录下的配置
from systems.monsters import config as mcfg 


class MonsterBase:
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
        """返回更友好的名称 - 子类可以重写"""
        name_map = {"Wanderer": "游荡者", "Bucket": "铁桶", "Ghoul": "食尸鬼"}
        prefix = "精英" if self.is_elite else ""
        return prefix + name_map.get(self.type, "未知怪物")

    def _calculate_base_stats(self):
        """
        计算怪物随等级 a 成长后的属性，并应用类型修正。
        子类可以重写此方法来自定义成长曲线
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

        # 速度 (基础值) - 子类可以重写
        self.movement_speed = 1.0 
        
        # 攻击参数（从config导入）
        self.attack_range = self._get_attack_range()
        self.attack_cooldown = self._get_attack_cooldown() 
    
    def _get_elite_skills(self):
        """确定精英怪的分支技能 - 子类必须重写"""
        return []
    
    def _init_skills(self):
        """初始化怪物独有的技能状态和属性 - 子类可以重写"""
        pass
    
    def _get_attack_range(self):
        """获取怪物的攻击范围"""
        import config
        return config.MONSTER_ATTACK_RANGE.get(self.type, 50)
    
    def _get_attack_cooldown(self):
        """获取怪物的攻击冷却时间"""
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
        dx = target_pos[0] - monster_world_pos[0]
        dy = target_pos[1] - monster_world_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        return distance <= self.attack_range
    
    def calculate_damage(self, nearby_monsters):
        """
        计算怪物的实际攻击伤害（考虑光环效果）
        子类可以重写此方法来添加特殊伤害计算
        
        Args:
            nearby_monsters: 附近的怪物列表 [(monster, distance), ...]
        
        Returns:
            float: 实际伤害值
        """
        return self.damage
    
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
        子类可以重写此方法来自定义攻击行为
        
        Args:
            target_pos: 目标位置 (x, y)
            nearby_monsters: 附近的怪物列表 [(monster, distance), ...]
        
        Returns:
            dict: 攻击信息
        """
        damage = self.calculate_damage(nearby_monsters)
        
        attack_info = {
            'damage': damage,
            'attacker_name': self.name,
            'attacker_type': self.type,
            'position': target_pos,
            'armor_ignore': 0,  # 默认无护甲穿透
            'type': 'melee'     # 默认近战
        }
        
        return attack_info
    
    def take_damage(self, damage, damage_source="未知"):
        """
        怪物受到伤害，触发防御技能判定
        子类可以重写此方法来添加特殊防御机制
        
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
        
        # 扣除生命值
        actual_damage = damage
        self.current_hp -= actual_damage
        
        # Debug日志
        import config as game_config
        if game_config.DEBUG_COMBAT_LOG:
            print(f"[COMBAT] {self.name} 受到 {actual_damage:.1f} 伤害 - HP: {self.current_hp:.1f}/{self.max_hp}", flush=True)
        
        # 判定死亡
        died = False
        will_revive = False
        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_alive = False
            died = True
        
        return {
            'blocked': False,
            'evaded': False,
            'actual_damage': actual_damage,
            'died': died,
            'will_revive': will_revive
        }
    
    # --- 信息查询接口 ---
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
        """返回先天技能信息 - 子类可以重写"""
        return "无"
        
    def get_advanced_skill_info(self):
        """返回进阶技能信息 - 子类可以重写"""
        return "无"
