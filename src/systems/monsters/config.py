# monsters/config.py
# 怪物独有的数值常量和技能参数

# --- 怪物等级成长参数 (基于 Level a) ---
MONSTER_GROWTH_PARAMS = {
    # 基础值
    "HP_BASE": 1000,
    "ARMOR_BASE": 50,
    "DMG_BASE": 100,
    # 增长率
    "HP_LINEAR_G": 0.5,      # G_HP
    "HP_QUADRATIC_P": 0.05,  # P_HP (二次项)
    "ARMOR_LINEAR_G": 0.2,   # G_A
    "DMG_LINEAR_G": 0.3      # G_D
}

# 怪物基础属性修正 (Level a=0) - 基于特长调整
MONSTER_BASE_STATS = {
    "Wanderer": {"HP_MOD": 1.0, "ARMOR_MOD": 1.0, "DMG_MOD": 1.0}, # 游荡者: 标准
    "Bucket":   {"HP_MOD": 1.2, "ARMOR_MOD": 1.5, "DMG_MOD": 0.8}, # 铁桶: 高血高防，低攻
    "Ghoul":    {"HP_MOD": 0.8, "ARMOR_MOD": 0.6, "DMG_MOD": 1.3}  # 食尸鬼: 低血低防，高攻
}

# --- 怪物技能机制参数 ---
MONSTER_SKILL_PARAMS = {
    # 游荡者 (Wanderer)
    "Wanderer_Aura_Factor": 0.10,      # 团结光环：自身基础攻击力的 10%
    "Wanderer_Aura_Range": 200,        # 光环范围 (px)
    "Wanderer_Revive_HP": 1.00,        # 重生 HP 100%
    "Wanderer_Revive_Delay": 3.0,      # 重生延迟 (秒)
    "Wanderer_Elite_Spawn_Min": 1,
    "Wanderer_Elite_Spawn_Max": 3,     # 每次召唤数量
    
    # 铁桶 (Bucket)
    "Bucket_Block_Chance": 0.15,       # 格挡概率 15%
    "Bucket_Block_Reduction": 0.90,    # 格挡时减少90%伤害（只承受10%）
    "Bucket_Block_Cooldown": 1.0,      # 格挡冷却时间 1秒
    "Bucket_Armor_Aura": 10,           # 铁甲光环：每个铁桶提供+10护甲
    "Bucket_Armor_Aura_Range": 200,    # 铁甲光环范围 (px)
    "Bucket_AOE_Range": 100,           # AoE 攻击范围 (px)
    "Bucket_Corpse_Explosion_HP_Dmg": 0.05, # 尸爆：最大生命值 5% 伤害
    "Bucket_Corpse_Explosion_Range": 300,   # 尸爆范围 (px)
    "Bucket_Giant_HP_Threshold": 0.20, # 巨人：每减少 20% HP
    "Bucket_Giant_Buff_Factor": 0.10,  # 巨人：攻防增加 10%

    # 食尸鬼 (Ghoul)
    "Ghoul_Dash_Min_Range": 300,       # 迅扑触发最小范围 (px)
    "Ghoul_Dash_Max_Range": 500,       # 迅扑触发最大范围 (px)
    "Ghoul_Evade_Chance": 0.20,        # 闪避率 20%
    "Ghoul_Lone_Wolf_Armor_Ignore": 0.20, # 独狼：无视 20% 护甲
    "Ghoul_Elite_Crit_Chance": 0.15,   # 暴击率 15%
    "Ghoul_Elite_Crit_Dmg": 0.50,      # 暴击伤害 50%
}

# --- 难度和怪物生成 ---
STARTING_DAY = 1
MAX_DAY = 100 

def MONSTER_COUNT_FORMULA(days, map_area):
    """根据天数和地图面积计算总怪物数量。"""
    # 基础数量 + 线性增长 + 根号增长
    base_count = map_area / 100 
    return int(base_count + days * 2 + days**1.5 * 0.1)

def ELITE_CHANCE_FORMULA(days):
    """计算生成精英怪的概率。"""
    # 从 0.1% 增长到 MAX_DAY 时的 10%
    return min(0.001 + days * 0.001, 0.10)