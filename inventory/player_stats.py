# player_stats.py
# 包含 PlayerStats 类

# =======================================================================
# ✨ 布局常数 (像素值)
STAT_PANEL_FIXED_WIDTH = 360   # 像素宽度
STAT_PANEL_FIXED_HEIGHT = 400  # 像素高度

CONTENT_OFFSET_X = 20          # 内容填充
# =======================================================================


import pygame
import sys # 需要导入 sys 用于 exit()
try:
    import config as cfg
except ImportError:
    print("错误：player_stats.py 无法导入 config.py。")
    sys.exit()

# 导入 render_text (现在它在 ui_elements.py 中)
# 我们将从 main.py 或 inventory_gui.py 传入字体和 render_text 函数
# 为了独立性，我们暂时假设 render_text 在这里
def render_text(font, text, color, bold=False, italic=False, antialias=True):
    """渲染文本的本地副本，以防万一。理想情况下从 ui_elements 导入。"""
    font.set_bold(bold)
    font.set_italic(italic)
    return font.render(text, antialias, color)

class PlayerStats:
    """计算和显示玩家属性"""
    def __init__(self, fonts):
        self.fonts = fonts # 传入一个字体字典
        self.base_stats = cfg.PLAYER_BASE_STATS.copy()
        self.total_stats = {}
        self.current_health = self.base_stats["基础生命值"]
        self.calculate_stats([]) # 初始化

    def calculate_stats(self, mod_items):
        """根据激活的模组计算总属性"""
        
        # 记录旧的最大生命值
        old_max_health = self.total_stats.get("生命值", self.base_stats["基础生命值"])

        stats = self.base_stats.copy()
        bonus = {}
        for item in mod_items:
            for affix in item.affixes:
                name = affix["name"]
                value = affix["value"]
                bonus[name] = bonus.get(name, 0) + value
        
        # --- 应用加成 ---
        # 1.6.2 生命值
        new_max_health = self.base_stats["基础生命值"] * (1 + bonus.get("生命力%", 0)) + bonus.get("生命值", 0)
        stats["生命值"] = new_max_health
        # 调整当前生命
        self.current_health = min(self.current_health, new_max_health)

        # 2. 护甲值修改：基础护甲值+护甲
        stats["护甲值"] = self.base_stats["基础护甲值"] + bonus.get("护甲", 0)
        
        stats["攻击力"] = self.base_stats["基础攻击力"] + bonus.get("攻击力", 0)
        
        # 1.6.2 射速
        fire_rate_bonus = min(bonus.get("射速%", 0), cfg.MAX_FIRE_RATE_BONUS)
        stats["射速%"] = fire_rate_bonus # 存储百分比
        stats["射速"] = self.base_stats["基础射速"] * (1 + fire_rate_bonus) # 存储最终值
        
        stats["暴击率"] = self.base_stats["基础暴击率"] + bonus.get("暴击率", 0)
        stats["暴击伤害"] = self.base_stats["基础暴击伤害"] + bonus.get("暴击伤害", 0)
        
        stats["吸血"] = bonus.get("吸血", 0)
        stats["移速"] = self.base_stats["基础移速"] * (1 + bonus.get("移速%", 0))
        stats["穿透率"] = bonus.get("穿透率", 0)
        stats["射程"] = self.base_stats["基础射程"] + bonus.get("射程", 0)
        stats["回血速度"] = bonus.get("回血速度", 0)

        # 1.6.2 伤害减免
        armor = stats["护甲值"]
        stats["伤害减免%"] = (armor / (armor + cfg.ARMOR_CONSTANT)) * 100
        
        self.total_stats = stats

    # 增加 content_offset_x 参数 (默认为 0)
    def draw(self, surface, rect, content_offset_x=CONTENT_OFFSET_X):
        """绘制属性面板 (使用固定的像素尺寸，并支持内容水平偏移)"""
        
        # 4. 根据顶部的常数设置固定的绘制区域尺寸
        new_width = STAT_PANEL_FIXED_WIDTH
        new_height = STAT_PANEL_FIXED_HEIGHT
        
        # 使用传入 rect 的左上角作为起点
        draw_rect = pygame.Rect(rect.x, rect.y, new_width, new_height)
        
        pygame.draw.rect(surface, (30, 30, 40), draw_rect)
        pygame.draw.rect(surface, cfg.COLOR_GRID, draw_rect, 2)
        
        y = draw_rect.y + 10
        
        # 定义属性内容起始 X 坐标
        # x 现在是面板内部的左边界 (10)，加上新的偏移量
        content_start_x = draw_rect.x + 10 + content_offset_x
        
        font = self.fonts["main"]
        
        # 1. 标题修改为“幸存者”并居中，移除斜体
        title_text = render_text(font, "幸存者", cfg.COLOR_TEXT_HEADER, bold=True, italic=False)
        # 标题居中计算不需要 content_offset_x，因为它影响的是内容
        title_x = draw_rect.x + (draw_rect.width - title_text.get_width()) // 2
        surface.blit(title_text, (title_x, y))
        y += 40
        
        # 攻击属性 (红色)
        offense_stats = ["攻击力", "射击速度", "暴击率", "暴击伤害", "护甲穿透", "射程"]
        
        # 生存属性 (绿色)
        defense_stats = ["生命", "护甲", "生命回复", "移动速度", "攻击吸血"]
        
        val_color = cfg.COLOR_TEXT
        
        # 攻击
        for name in offense_stats:
            name_text = render_text(font, name + ":", cfg.COLOR_STAT_OFFENSE)
            # 属性名称的位置
            surface.blit(name_text, (content_start_x, y))
            
            val_str = ""
            
            if name == "攻击力":
                val = self.total_stats.get("攻击力", 0)
                val_str = f"{int(val)}"
            elif name == "射击速度":
                fire_rate_pct = self.total_stats.get("射速%", 0)
                fire_rate_val = self.total_stats.get("射速", 0)
                sec_per_attack = 1.0 / fire_rate_val if fire_rate_val > 0 else 0
                val_str = f"{(1 + fire_rate_pct):.0%} ({sec_per_attack:.2f}s攻击一次)"
            elif name == "暴击率":
                val_str = f"{self.total_stats.get('暴击率', 0):.2%}"
            elif name == "暴击伤害":
                val_str = f"{self.total_stats.get('暴击伤害', 0):.0%}"
            elif name == "护甲穿透":
                val_str = f"{self.total_stats.get('穿透率', 0):.2%}"
            elif name == "射程":
                val_str = f"{int(self.total_stats.get('射程', 0))}"
            
            val_text = render_text(font, val_str, val_color)
            # 属性值的位置
            surface.blit(val_text, (content_start_x + 120, y))
            y += 25

        # 分割线
        y += 5
        # 分割线从 content_start_x 开始，长度延伸到 draw_rect.right - 10
        pygame.draw.line(surface, cfg.COLOR_GRID, (content_start_x - 10, y), (draw_rect.right - 10, y), 1)
        y += 15

        # 防御
        for name in defense_stats:
            name_text = render_text(font, name + ":", cfg.COLOR_STAT_DEFENSE)
            # 属性名称的位置
            surface.blit(name_text, (content_start_x, y))
            
            val_str = ""
            if name == "生命":
                max_hp = int(self.total_stats.get("生命值", 0))
                cur_hp = int(min(self.current_health, max_hp))
                val_str = f"{cur_hp} / {max_hp}"
            elif name == "护甲":
                armor = int(self.total_stats.get("护甲值", 0))
                dr = self.total_stats.get("伤害减免%", 0)
                val_str = f"{armor} (伤害减免 {dr:.2f}%)"
            elif name == "生命回复":
                val_str = f"+{int(self.total_stats.get('回血速度', 0))}/s"
            elif name == "移动速度":
                val_str = f"{int(self.total_stats.get('移速', 0))}"
            elif name == "攻击吸血":
                val_str = f"+{self.total_stats.get('吸血', 0):.0%}"

            val_text = render_text(font, val_str, val_color)
            # 属性值的位置
            surface.blit(val_text, (content_start_x + 120, y))
            y += 25