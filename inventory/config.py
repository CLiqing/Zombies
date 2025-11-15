# config.py
# 存放游戏常量和设置

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
# We'll load fonts in code, but define sizes
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

# 按钮颜色
COLOR_BUTTON_BG = (80, 80, 100)
COLOR_BUTTON_HOVER = (110, 110, 140)
COLOR_BUTTON_TEXT = (255, 255, 255)
COLOR_BUTTON_BACK = (150, 50, 50)
COLOR_BUTTON_BACK_HOVER = (180, 70, 70)

# 属性颜色
COLOR_STAT_OFFENSE = (255, 120, 120) # 红色
COLOR_STAT_DEFENSE = (120, 255, 120) # 绿色

# 装备品质颜色
QUALITY_COLORS = {
    "普通": (150, 150, 150),
    "精良": (100, 150, 255),
    "史诗": (200, 100, 255),
    "传奇": (255, 200, 0),
}

# --- 区域定义 (逻辑尺寸) ---
# 枪械强化模组 (左上)
MOD_PANEL_ROWS = 6 # 修改为 6
MOD_PANEL_COLS = 20

# 背包 (左下)
INV_PANEL_ROWS = 20
INV_PANEL_COLS = 40

# 玩家属性 (右)
STATS_PANEL_WIDTH = 400
# Note: Actual RECTs will be calculated dynamically in main.py and inventory_gui.py

# --- 游戏规则 ---

# 装备品质设置: (词条数量N范围, 方格大小c范围, 品质系数b, 掉落概率P)
QUALITY_SETTINGS = {
    "普通": {
        "n_range": (1, 1),
        "c_range": (1, 3),
        "b": 1.0,
        "p": 20.0,
        "bias": "游荡者"
    },
    "精良": {
        "n_range": (2, 2),
        "c_range": (4, 6),
        "b": 1.2,
        "p": 5.0,
        "bias": "游荡者"
    },
    "史诗": {
        "n_range": (3, 3),
        "c_range": (7, 9),
        "b": 1.5,
        "p": 1.0,
        "bias": "铁皮"
    },
    "传奇": {
        "n_range": (4, 5),
        "c_range": (10, 12),
        "b": 2.0,
        "p": 0.2,
        "bias": "食尸鬼"
    }
}

# 掉落来源显示名称
BIAS_DISPLAY_NAMES = {
    "游荡者": "游魂",
    "铁皮": "铁桶",
    "食尸鬼": "食尸鬼"
}

# 词缀数值计算因子
SPACE_GROWTH_FACTOR = 0.05 # 空间成长因子
LEVEL_GROWTH_FACTOR = 0.1  # 等级成长因子

# 词条基础数值 (用于计算)
BASE_STAT_VALUES = {
    # --- 通用 ---
    "攻击力": 5,
    "防御力": 3,
    "生命值": 20,
    "生命力%": 0.02, # 2%
    "回血速度": 0.5,
    # --- 稀有 ---
    "暴击率": 0.01, # 1%
    "暴击伤害": 0.1, # 10%
    "吸血": 0.005, # 0.5%
    "移速%": 0.01, # 1%
    # --- 枪械强化 ---
    "射速%": 0.02, # 2%
    "穿透率": 0.05, # 5%
    "射程": 10,
}

# 词缀池与稀有度 (权重)
AFFIX_POOLS = {
    "通用": {
        "攻击力": 10,
        "防御力": 10,
        "生命值": 10,
        "生命力%": 5,
        "回血速度": 5,
    },
    "稀有": {
        "暴击率": 3,
        "暴击伤害": 3,
        "吸血": 2,
        "移速%": 3,
    },
    "枪械": {
        "射速%": 4,
        "穿透率": 3,
        "射程": 2,
    }
}

# 怪物掉落倾向 (增加对应词缀池的权重)
MONSTER_DROP_BIAS = {
    "游荡者": {"通用": 5, "稀有": 0, "枪械": 0},
    "铁皮": {"通用": 3, "稀有": 0, "枪械": 0, "防御力": 10, "生命力%": 10}, # 特殊覆盖
    "食尸鬼": {"通用": 0, "稀有": 5, "枪械": 5},
}


# --- 玩家属性与伤害 ---

# 玩家基础属性
PLAYER_BASE_STATS = {
    "基础攻击力": 50,
    "基础射速": 1.0, # 1 a/s (为了方便计算百分比，改为1)
    "基础射程": 300, # 新增
    "基础暴击率": 0.05, # 5%
    "基础暴击伤害": 1.5, # 150%
    "基础生命值": 1000,
    "基础护甲值": 50,
    "基础移速": 100,
}

# 属性上限
MAX_FIRE_RATE_BONUS = 3.0 # 300% (即总共400% = 基础 * 4)

# 伤害计算
DIFFICULTY_CONSTANT = 50 # 旧
ARMOR_CONSTANT = 500 # 新增 护甲基数