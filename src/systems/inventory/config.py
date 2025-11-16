# config.py
# 存放游戏常量和设置
import os
import math

# --- 屏幕与UI ---
# 初始大小 (3/4 of 1600x900)
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 675
SCREEN_RESIZABLE = True
WINDOW_TITLE = "Zombies"

CELL_SIZE = 20  # 每个网格单元的像素大小
GRID_STROKE = 1
PANEL_GAP = 20  # 面板间的间距

# --- 字体 ---
# 使用相对于项目根目录的路径
_current_file = os.path.abspath(__file__)
_src_dir = os.path.dirname(os.path.dirname(os.path.dirname(_current_file)))  # 到src目录
_project_root = os.path.dirname(_src_dir)  # 到项目根目录
FONT_PATH = os.path.join(_project_root, "assets", "fonts", "NotoSansSC-Regular.ttf")

FONT_SIZE_MAIN = 18
FONT_SIZE_SMALL = 14
FONT_SIZE_AFFIX_MAIN = 17 # 主词条
FONT_SIZE_AFFIX_OTHER = 15 # 其他词条
FONT_SIZE_BUTTON = 16

# --- 颜色定义 ---
COLOR_BACKGROUND = (20, 20, 30)
COLOR_GRID = (50, 50, 70)
COLOR_TEXT = (230, 230, 230)
COLOR_TEXT_HEADER = (255, 200, 100)
COLOR_TOOLTIP_BG = (0, 0, 0, 210) # (R, G, B, Alpha)
COLOR_CONTEXT_BG = (40, 40, 50)
COLOR_CONTEXT_BORDER = (100, 100, 120)
COLOR_CONTEXT_HIGHLIGHT = (70, 70, 90)
COLOR_DISABLED = (100, 100, 100) # 灰色，用于不可用按钮

# 按钮颜色
COLOR_BUTTON_BG = (80, 80, 100)
COLOR_BUTTON_HOVER = (110, 110, 140)
COLOR_BUTTON_TEXT = (255, 255, 255)
COLOR_BUTTON_BACK = (150, 50, 50)
COLOR_BUTTON_BACK_HOVER = (180, 70, 70)

# 属性颜色
COLOR_STAT_OFFENSE = (255, 120, 120) # 红色
COLOR_STAT_DEFENSE = (120, 255, 120) # 绿色
COLOR_STAT_ESSENCE = (200, 120, 255) # 紫色

# 装备品质颜色
QUALITY_COLORS = {
    "普通": (150, 150, 150),
    "精良": (100, 150, 255),
    "史诗": (200, 100, 255),
    "传奇": (255, 200, 0),
}

# --- 区域定义 (逻辑尺寸) ---
PANEL_COLS_COMMON = 20 

# 枪械强化模组 (左上)
MOD_PANEL_ROWS = 6
MOD_PANEL_COLS = PANEL_COLS_COMMON

# 背包 (左下)
INV_PANEL_ROWS = 20
INV_PANEL_COLS = PANEL_COLS_COMMON

# 玩家属性 (右)
STATS_PANEL_WIDTH = 360 

# --- 游戏规则 ---

# 1.1 源质符号
SYMBOL_ESSENCE = "⚛"

# 1.1 摧毁获得的源质
ESSENCE_GAIN = {
    "普通": 5,
    "精良": 10,
    "史诗": 15,
    "传奇": 25
}

# 1.1 精炼消耗
COST_REROLL = {
    "普通": 10,
    "精良": 20,
    "史诗": 30,
    "传奇": 50
}

# 1.1 高级精炼消耗 (Lock)
COST_LOCK = {
    "史诗": 40,
    "传奇": 60
}

# 装备品质设置: (词条数量N范围, 方格大小c范围, 品质系数b, 掉落概率P, **稀有词条数量 rare_n_range**)
QUALITY_SETTINGS = {
    "普通": {
        "n_range": (1, 1),
        "rare_n_range": (0, 0), # 普通装备不出现稀有词条
        "c_range": (1, 3),
        "b": 1.0,
        "p": 20.0,
        "bias": "游荡者" 
    },
    "精良": {
        "n_range": (2, 2),
        "rare_n_range": (0, 1), # 精良装备最多有 1 个稀有词条
        "c_range": (4, 6),
        "b": 1.25,
        "p": 5.0,
        "bias": "游荡者"
    },
    "史诗": {
        "n_range": (3, 3),
        "rare_n_range": (1, 2), # 史诗装备保证至少 1 个稀有词条，最多 2 个
        "c_range": (7, 9),
        "b": 1.5,
        "p": 1.0,
        "bias": "游荡者"
    },
    "传奇": {
        "n_range": (4, 5), 
        "rare_n_range": (2, 4), # 传奇装备至少 2 个稀有词条，最多 4 个
        "c_range": (10, 12),
        "b": 2.0,
        "p": 0.2,
        "bias": "游荡者"
    }
}

# 掉落来源显示名称
BIAS_DISPLAY_NAMES = {
    "游荡者": "游荡者",
    "铁桶": "铁桶",
    "食尸鬼": "食尸鬼"
}

# --- 词缀数值计算因子 ---
SPACE_GROWTH_FACTOR = 0.05      # 通用词缀空间成长因子 Sc
LEVEL_GROWTH_FACTOR = 0.05      # 通用词缀等级成长因子 Sa

RARE_SPACE_GROWTH_FACTOR = 0.025 # 稀有词缀空间成长因子 S'c
RARE_LEVEL_GROWTH_FACTOR = 0.025 # 稀有词缀等级成长因子 S'a

# 主词条乘数
MAIN_AFFIX_MULTIPLIER = 1.5

# 词条基础数值 (用于计算)
BASE_STAT_VALUES = {
    # --- 通用 (高成长 0.05) ---
    "攻击力": 10,          
    "护甲": 2,              
    "生命": 20,          
    "生命%": 0.01,        
    "生命回复": 0.5,        # **此值为绝对值 (HP/s)，非百分比**

    # --- 稀有 (衰减成长 0.025) ---
    "暴击率": 0.01,         
    "暴击伤害": 0.03,       
    "攻击吸血": 0.005,      
    "移速%": 0.01,          

    # --- 枪械强化 (衰减成长 0.025) ---
    "射击速度%": 0.015,     
    "护甲穿透": 0.01,       
    "射程": 10,             
}

# **稀有词缀名称列表 (用于判断成长因子和稀有度)**
RARE_AFFIX_NAMES = [
    "暴击率", "暴击伤害", "攻击吸血", "移速%", 
    "射击速度%", "护甲穿透", "射程"
]
# **通用词缀名称列表 (用于稀有词条数量限制)**
GENERAL_AFFIX_NAMES = [
    "攻击力", "护甲", "生命", "生命%", "生命回复"
]


# 词缀池划分与权重
AFFIX_POOLS = {
    "生存数值": {
        "护甲": 15,
        "生命": 15,
        "生命回复": 5,
    },
    "生存百分比": {
        "生命%": 5,
    },
    "攻击数值": {
        "攻击力": 15,
    },
    "攻击百分比": {
        "暴击率": 5,
        "暴击伤害": 5,
    },
    "稀有通用": {
        "射击速度%": 5,
    },
    # 怪物专属稀有属性 (史诗及以上才进入掉落池)
    "稀有专属_游荡者": {
        "移速%": 5,
    },
    "稀有专属_铁桶": {
        "攻击吸血": 5,
    },
    "稀有专属_食尸鬼": {
        "护甲穿透": 5,
    },
    # 传奇专属独立词条
    "独立词条_射程": {
        "射程": 1, 
    }
}

# 怪物掉落倾向 (针对权重调整和主词条判断)
MONSTER_DROP_BIAS = {
    "游荡者": {}, 
    "铁桶": {
        "生存数值": 10,  
        "生存百分比": 10, 
    }, 
    "食尸鬼": {
        "攻击数值": 10,   
        "攻击百分比": 10,  
    },
}

# 用于 item_generator 内部判断主词条池的名称列表
SURVIVAL_AFFIXES = ["护甲", "生命", "生命%", "生命回复"]
OFFENSE_AFFIXES = ["攻击力", "暴击率", "暴击伤害"]


# --- 玩家属性与伤害 ---
PLAYER_BASE_STATS = {
    "基础攻击力": 100,      
    "基础射击速度": 1.0,    
    "基础射程": 300,        
    "基础暴击率": 0.05,     
    "基础暴击伤害": 1.5,     
    "基础生命值": 1000,     
    "基础护甲": 50,         
    "基础移速": 100,
    "基础源质": 500,        
}

# 属性上限
MAX_FIRE_RATE_BONUS = 3.0 

# 伤害计算
DIFFICULTY_CONSTANT = 100 
ARMOR_CONSTANT = 100 

def ceil_to_nearest_ten(n):
    """向上取整到最近的10的倍数"""
    return math.ceil(n / 10.0) * 10