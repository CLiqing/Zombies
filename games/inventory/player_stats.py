# player_stats.py
# 1.3 拆分：包含 PlayerLogic (计算) 和 StatsPanelRenderer (绘制) 类

# =======================================================================
# ✨ 布局常数 (像素值)
STAT_PANEL_FIXED_WIDTH = 360     # 像素宽度
STAT_PANEL_FIXED_HEIGHT = 440    # 像素高度 (稍微增加以适应内容)
CONTENT_OFFSET_X = 20            # 内容填充
# =======================================================================

import pygame
import sys
import math

try:
    import inventory.config as cfg
except ImportError:
    print("错误：player_stats.py 无法导入 config.py。")
    sys.exit()

# 导入 render_text 辅助函数 (为了独立性暂时保留本地副本)
def render_text(font, text, color, bold=False, italic=False, antialias=True):
    font.set_bold(bold)
    font.set_italic(italic)
    return font.render(text, antialias, color)


class PlayerLogic:
    """
    仅负责逻辑计算和数据存储的玩家类。
    """
    def __init__(self):
        self.base_stats = cfg.PLAYER_BASE_STATS.copy()
        self.total_stats = {}
        self.current_health = self.base_stats["基础生命值"]
        self.current_essence = self.base_stats.get("基础源质", 0)
        self.calculate_stats([]) # 初始化

    def calculate_stats(self, mod_items):
        """根据激活的模组计算总属性"""
        stats = self.base_stats.copy()
        bonus = {}
        
        # 统计装备加成
        for item in mod_items:
            for affix in item.affixes:
                name = affix["name"]
                value = affix["value"]
                # **[注意] 忽略主词条系数Kmain，计算在别处处理**
                
                bonus[name] = bonus.get(name, 0) + value
        
        # --- 1. 基础生存属性计算 ---
        
        # 生命值 (生命% 为乘算，生命值为加算)
        new_max_health = self.base_stats["基础生命值"] * (1 + bonus.get("生命%", 0)) + bonus.get("生命", 0)
        stats["生命"] = new_max_health
        # 调整当前生命
        self.current_health = min(self.current_health, new_max_health)

        # 护甲 (基础护甲 + 词条护甲)
        stats["护甲"] = self.base_stats["基础护甲"] + bonus.get("护甲", 0) 
        
        # 生命回复
        stats["生命回复"] = bonus.get("生命回复", 0)
        
        # --- 2. 攻击属性计算 ---
        
        # 攻击力
        stats["攻击力"] = self.base_stats["基础攻击力"] + bonus.get("攻击力", 0)
        
        # 射击速度 (线性叠加，有上限)
        fire_rate_bonus = min(bonus.get("射击速度%", 0), cfg.MAX_FIRE_RATE_BONUS)
        stats["射击速度%"] = fire_rate_bonus
        stats["射速"] = self.base_stats["基础射击速度"] * (1 + fire_rate_bonus) # 内部使用射速，外部显示射击速度
        
        # 其他攻击属性
        stats["暴击率"] = self.base_stats["基础暴击率"] + bonus.get("暴击率", 0)
        stats["暴击伤害"] = self.base_stats["基础暴击伤害"] + bonus.get("暴击伤害", 0)
        stats["攻击吸血"] = bonus.get("攻击吸血", 0)
        stats["护甲穿透"] = bonus.get("护甲穿透", 0)
        stats["射程"] = self.base_stats["基础射程"] + bonus.get("射程", 0)
        
        # --- 3. 移动速度计算 ---
        stats["移速"] = self.base_stats["基础移速"] * (1 + bonus.get("移速%", 0))
        
        # --- 4. 护甲减伤计算 (供显示) ---
        armor = stats["护甲"]
        # 使用配置中的 ARMOR_CONSTANT
        armor_const = getattr(cfg, 'ARMOR_CONSTANT', 100)
        # 线性减伤公式: DR = Armor / (Armor + K)
        # 这里的 K = ARMOR_CONSTANT 
        
        # **[保留] 护甲减伤%计算 (用于面板显示)**
        dr_pct = (armor / (armor + armor_const)) * 100
        stats["伤害减免%"] = dr_pct
        
        # 存储结果
        self.total_stats = stats

    def add_essence(self, amount):
        """增加源质"""
        self.current_essence += amount

    def spend_essence(self, amount):
        """消耗源质，如果不足返回 False"""
        if self.current_essence >= amount:
            self.current_essence -= amount
            return True
        return False


class StatsPanelRenderer:
    """
    仅负责绘制玩家属性面板的类。
    """
    # **[修改] 符号和名称统一**
    STAT_SYMBOLS = {
        "攻击力": "† 攻击力",
        "射击速度": "⋚ 射击速度",
        "暴击率": "※ 暴击率",
        "暴击伤害": "▲ 暴击伤害",
        "护甲穿透": "≯ 护甲穿透",
        "射程": "∞ 射程",
        "生命": "♥ 生命",
        "护甲": "▦ 护甲",
        "生命回复": "✚ 生命回复",
        "移动速度": "≫ 移动速度",
        "攻击吸血": "♀ 攻击吸血",
        "原生源质": "§ 源生源质",
    }

    def __init__(self, fonts):
        self.fonts = fonts

    def draw(self, surface, rect, player_logic):
        """
        绘制属性面板
        """
        draw_rect = pygame.Rect(rect.x, rect.y, STAT_PANEL_FIXED_WIDTH, STAT_PANEL_FIXED_HEIGHT)
        
        # 背景
        pygame.draw.rect(surface, (30, 30, 40), draw_rect)
        pygame.draw.rect(surface, cfg.COLOR_GRID, draw_rect, 2)
        
        y = draw_rect.y + 10
        content_start_x = draw_rect.x + 10 + CONTENT_OFFSET_X
        font = self.fonts["main"]
        stats = player_logic.total_stats
        
        # --- 标题 ---
        title_text = render_text(font, "幸存者", cfg.COLOR_TEXT_HEADER, bold=True)
        title_x = draw_rect.x + (draw_rect.width - title_text.get_width()) // 2
        surface.blit(title_text, (title_x, y))
        y += 40
        
        val_color = cfg.COLOR_TEXT
        
        # --- 攻击属性 (红色) ---
        offense_stats = ["攻击力", "射击速度", "暴击率", "暴击伤害", "护甲穿透", "射程"]
        for name in offense_stats:
            display_name = self.STAT_SYMBOLS.get(name, name)
            name_text = render_text(font, display_name + ":", cfg.COLOR_STAT_OFFENSE)
            surface.blit(name_text, (content_start_x, y))
            
            val_str = ""
            if name == "攻击力":
                val_str = f"{int(stats.get('攻击力', 0))}"
            elif name == "射击速度":
                fire_rate_pct = stats.get("射击速度%", 0) # **[修改] 属性名**
                fire_rate_val = stats.get("射速", 0) # 内部计算的实际射速
                
                # 安全检查，防止除以零
                sec_per_attack = 1.0 / fire_rate_val if fire_rate_val > 0 else math.inf
                
                # 额外加成百分比 (如 1.5 -> +50%)
                pct_display = f"{(fire_rate_pct * 100 + 100):.0f}%" 
                
                if fire_rate_val == math.inf or fire_rate_val == 0:
                     val_str = f"{pct_display} (无法攻击)"
                else:
                    val_str = f"{pct_display} ({sec_per_attack:.2f}s/发)"
                    
            elif name == "暴击率":
                val_str = f"{stats.get('暴击率', 0):.2%}"
            elif name == "暴击伤害":
                val_str = f"{stats.get('暴击伤害', 0):.0%}"
            elif name == "护甲穿透":
                val_str = f"{stats.get('护甲穿透', 0):.2%}" # **[修改] 属性名**
            elif name == "射程":
                val_str = f"{int(stats.get('射程', 0))}"
            
            val_text = render_text(font, val_str, val_color)
            surface.blit(val_text, (content_start_x + 120, y))
            y += 25

        # 分割线
        y += 5
        pygame.draw.line(surface, cfg.COLOR_GRID, (content_start_x - 10, y), (draw_rect.right - 10, y), 1)
        y += 15

        # --- 防御属性 (绿色) ---
        defense_stats = ["生命", "护甲", "生命回复", "移动速度", "攻击吸血"]
        for name in defense_stats:
            display_name = self.STAT_SYMBOLS.get(name, name)
            name_text = render_text(font, display_name + ":", cfg.COLOR_STAT_DEFENSE)
            surface.blit(name_text, (content_start_x, y))
            
            val_str = ""
            if name == "生命":
                max_hp = int(stats.get("生命", 0))
                cur_hp = int(min(player_logic.current_health, max_hp))
                val_str = f"{cur_hp} / {max_hp}"
            elif name == "护甲":
                # **[修改] 护甲减伤显示**
                armor = int(stats.get("护甲", 0)) # **[修改] 属性名**
                dr = stats.get("伤害减免%", 0) # 护甲减伤（PlayerLogic已计算）
                val_str = f"{armor} (减伤 {dr:.1f}%)" # 减伤百分比保留一位小数
            elif name == "生命回复":
                val_str = f"+{stats.get('生命回复', 0):.1f}/s"
            elif name == "移动速度":
                val_str = f"{int(stats.get('移速', 0))}"
            elif name == "攻击吸血":
                val_str = f"{stats.get('攻击吸血', 0):.1%}" # **[修改] 属性名**

            val_text = render_text(font, val_str, val_color)
            surface.blit(val_text, (content_start_x + 120, y))
            y += 25
            
        # 分割线
        y += 5
        pygame.draw.line(surface, cfg.COLOR_GRID, (content_start_x - 10, y), (draw_rect.right - 10, y), 1)
        y += 15
        
        # --- 源质 (紫色) ---
        name = "原生源质"
        display_name = self.STAT_SYMBOLS.get(name, name)
        name_text = render_text(font, display_name + ":", cfg.COLOR_STAT_ESSENCE)
        surface.blit(name_text, (content_start_x, y))

        val_str = f"{int(player_logic.current_essence)}"
        val_text = render_text(font, val_str, val_color)
        surface.blit(val_text, (content_start_x + 120, y))