# ui_elements.py
# 包含 GridPanel, Button, 和绘图辅助函数
import pygame
import sys
import os

# 添加路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from systems.inventory import config as cfg
except ImportError:
    print("错误：ui_elements.py 无法导入 config.py。")
    import traceback
    traceback.print_exc()
    sys.exit()

# --- 辅助函数 ---

def render_text(font, text, color, bold=False, italic=False, antialias=True):
    """渲染文本"""
    font.set_bold(bold)
    font.set_italic(italic)
    return font.render(text, antialias, color)

def draw_tooltip(surface, item, x, y, fonts):
    """绘制物品悬停提示框"""
    if not item:
        return

    font_main = fonts["main"]
    font_small = fonts["small"]
    font_affix_main = fonts["affix_main"]
    font_affix_other = fonts["affix_other"]

    # 1. 准备文本
    header_texts = []
    main_affix_texts = []
    other_affix_texts = []
    
    # Line 1: 名称
    name_str = f"{item.bias_display_name}的{item.quality}源质"
    header_texts.append(render_text(font_main, name_str, item.color, bold=True))
    
    # Line 2: 等级 (1.5 移除 c 和 n 的显示)
    level_str = f"Lv {item.monster_level}"
    header_texts.append(render_text(font_small, level_str, cfg.COLOR_TEXT))
    
    # Line 3+: 词缀（分为主词条和其他词条）
    for affix in item.affixes:
        name = affix["name"]
        val = affix["value"]
        color = cfg.COLOR_TEXT
        
        # **【修正逻辑】**
        # 稀有词缀判断：检查词缀名称是否在 RARE_AFFIX_NAMES 列表中
        if name in cfg.RARE_AFFIX_NAMES:
            color = (100, 200, 255) # 稀有词缀高亮
        
        # 格式化数值显示
        if name == "生命回复":
            # 生命回复始终显示为绝对值（HP/s），保留一位小数
            text_str = f"+{val:.1f} {name}"
        elif val < 1.0 and val > 0:
            # 百分比显示：去掉名称末尾的%符号（如果有）
            display_name = name.rstrip('%')
            text_str = f"+{val:.2%} {display_name}"
        elif name in ["护甲穿透", "射程"] and val == int(val):
            # 护甲穿透和射程虽然是稀有词缀，但可能需要显示为整数
            text_str = f"+{int(val)} {name}"
        elif isinstance(val, float):
             text_str = f"+{val:.1f} {name}"
        else:
            text_str = f"+{int(val)} {name}"
        
        is_main = affix.get("is_main", False)
        font_to_use = font_affix_main if is_main else font_affix_other
        text_surf = render_text(font_to_use, text_str, color, bold=is_main)
        
        # 根据是否是主词条分类
        if is_main:
            main_affix_texts.append(text_surf)
        else:
            other_affix_texts.append(text_surf)


    # 2. 计算背景框大小
    all_texts = header_texts + main_affix_texts + other_affix_texts
    if not all_texts: return
    
    max_w = max(t.get_width() for t in all_texts)
    
    # 计算总高度：包括文本高度、间距、以及分隔线
    total_h = sum(t.get_height() for t in all_texts) + (len(all_texts) - 1) * 5
    if main_affix_texts and other_affix_texts:
        total_h += 10  # 为分隔线增加额外空间
    
    padding = 10
    bg_rect = pygame.Rect(0, 0, max_w + padding * 2, total_h + padding * 2)
    
    # 3. 调整位置，防止出界
    bg_rect.topleft = (x + 15, y + 15)
    screen_w, screen_h = surface.get_size()
    if bg_rect.right > screen_w:
        bg_rect.right = x - 15
    if bg_rect.bottom > screen_h:
        bg_rect.bottom = y - 15
        
    # 4. 绘制
    tooltip_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
    tooltip_surface.fill(cfg.COLOR_TOOLTIP_BG)
    pygame.draw.rect(tooltip_surface, item.color, (0, 0, bg_rect.width, bg_rect.height), 1)
    
    current_y = padding
    
    # 绘制头部（名称和等级）
    for text in header_texts:
        tooltip_surface.blit(text, (padding, current_y))
        current_y += text.get_height() + 5
    
    # 绘制主词条
    for text in main_affix_texts:
        tooltip_surface.blit(text, (padding, current_y))
        current_y += text.get_height() + 5
    
    # 如果有主词条和副词条，绘制分隔线
    if main_affix_texts and other_affix_texts:
        current_y += 2  # 额外间距
        line_y = current_y
        pygame.draw.line(tooltip_surface, cfg.COLOR_GRID, 
                        (padding, line_y), (bg_rect.width - padding, line_y), 1)
        current_y += 8  # 分隔线后的间距
    
    # 绘制其他词条
    for text in other_affix_texts:
        tooltip_surface.blit(text, (padding, current_y))
        current_y += text.get_height() + 5
        
    surface.blit(tooltip_surface, bg_rect.topleft)

def draw_context_menu(surface, menu_data, font):
    """
    绘制右键菜单
    1.6 更新: 支持 disabled 状态 (灰色且不可交互)
    menu_data["options"] 结构现在预期为 [(text, action, enabled), ...]
    """
    if not menu_data["active"]:
        return
        
    rect = menu_data["rect"]
    options = menu_data["options"]
    
    pygame.draw.rect(surface, cfg.COLOR_CONTEXT_BG, rect)
    pygame.draw.rect(surface, cfg.COLOR_CONTEXT_BORDER, rect, 1)
    
    mouse_x, mouse_y = pygame.mouse.get_pos()
    
    current_y = rect.y + 5
    for i, option in enumerate(options):
        # 兼容旧格式 (text, action) 和新格式 (text, action, enabled)
        if len(option) == 3:
            text, action, enabled = option
        else:
            text, action = option
            enabled = True

        option_rect = pygame.Rect(rect.x, current_y, rect.width, 30)
        
        text_color = cfg.COLOR_TEXT
        bg_color = None

        if not enabled:
            text_color = cfg.COLOR_DISABLED # 灰色
        elif option_rect.collidepoint(mouse_x, mouse_y):
            text_color = (255, 255, 255)
            bg_color = cfg.COLOR_CONTEXT_HIGHLIGHT
            
        if bg_color:
            pygame.draw.rect(surface, bg_color, option_rect)
            
        text_surf = render_text(font, text, text_color)
        surface.blit(text_surf, (rect.x + 10, current_y + (30 - text_surf.get_height()) // 2))
        current_y += 30

# --- 核心UI类 (GridPanel, Button) 保持不变 ---
class GridPanel:
    """代表一个网格区域 (强化面板或背包)"""
    def __init__(self, rect, rows, cols):
        self.rect = pygame.Rect(rect)
        self.rows = rows
        self.cols = cols
        self.cell_size = cfg.CELL_SIZE
        self.grid_data = [[None for _ in range(cols)] for _ in range(rows)]
        self.items = {} # {item: (r, c)}

    def update_rect(self, rect):
        """更新矩形位置 (用于缩放)"""
        self.rect = pygame.Rect(rect)

    def screen_to_grid(self, screen_x, screen_y):
        """将屏幕坐标转换为网格坐标 (row, col)"""
        if not self.rect.collidepoint(screen_x, screen_y):
            return None
        
        local_x = screen_x - self.rect.x
        local_y = screen_y - self.rect.y
        row, col = local_y // self.cell_size, local_x // self.cell_size
        
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return (row, col)
        return None

    def grid_to_screen(self, row, col):
        """将网格坐标转换为屏幕坐标 (x, y)"""
        return (self.rect.x + col * self.cell_size, self.rect.y + row * self.cell_size)

    def get_item_at(self, screen_x, screen_y):
        """获取指定屏幕坐标下的物品及其位置"""
        grid_pos = self.screen_to_grid(screen_x, screen_y)
        if grid_pos:
            r, c = grid_pos
            item = self.grid_data[r][c]
            if item:
                return item, self.items[item]
        return None, None

    def is_valid_placement(self, item, row, col, item_to_ignore=None):
        """检查物品是否可以放置在 (row, col)"""
        for (r, c) in item.shape:
            grid_r, grid_c = row + r, col + c
            if not (0 <= grid_r < self.rows and 0 <= grid_c < self.cols):
                return False
            existing_item = self.grid_data[grid_r][grid_c]
            if existing_item and existing_item != item_to_ignore:
                return False
        return True

    def add_item(self, item, row, col):
        """在 (row, col) 放置物品"""
        if not self.is_valid_placement(item, row, col):
            return False
            
        if item in self.items:
            self.remove_item(item)
            
        self.items[item] = (row, col)
        for (r, c) in item.shape:
            self.grid_data[row + r][col + c] = item
        return True
    
    def find_first_empty_slot(self, item):
        """查找第一个能放下物品的空位"""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.is_valid_placement(item, r, c):
                    return (r, c)
        return None

    def remove_item(self, item):
        """从网格中移除物品"""
        if item in self.items:
            base_r, base_c = self.items[item]
            for (r, c) in item.shape:
                grid_r, grid_c = base_r + r, base_c + c
                if 0 <= grid_r < self.rows and 0 <= grid_c < self.cols:
                    if self.grid_data[grid_r][grid_c] == item:
                        self.grid_data[grid_r][grid_c] = None
            del self.items[item]
            return True
        return False

    def draw(self, surface):
        """绘制网格和所有物品"""
        pygame.draw.rect(surface, (30, 30, 40), self.rect)
        for r in range(self.rows + 1):
            y = self.rect.y + r * self.cell_size
            pygame.draw.line(surface, cfg.COLOR_GRID, (self.rect.x, y), (self.rect.right, y), cfg.GRID_STROKE)
        for c in range(self.cols + 1):
            x = self.rect.x + c * self.cell_size
            pygame.draw.line(surface, cfg.COLOR_GRID, (x, self.rect.y), (x, self.rect.bottom), cfg.GRID_STROKE)
            
        for item, (r, c) in self.items.items():
            x, y = self.grid_to_screen(r, c)
            item.draw(surface, x, y, self.cell_size)

class Button:
    """一个简单的UI按钮"""
    def __init__(self, rect, text, font, action_id, 
                 bg_color=cfg.COLOR_BUTTON_BG, 
                 hover_color=cfg.COLOR_BUTTON_HOVER, 
                 text_color=cfg.COLOR_BUTTON_TEXT):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.action_id = action_id
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def update_rect(self, rect):
        """更新位置"""
        self.rect = pygame.Rect(rect)

    def draw(self, surface, mouse_pos):
        """绘制按钮"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        
        text_surf = render_text(self.font, self.text, self.text_color, bold=True)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event, mouse_pos):
        """处理点击事件"""
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.rect.collidepoint(mouse_pos):
                return self.action_id
        return None