# inventory_gui.py
# (Refactored) 只包含背包界面的类
import pygame
import sys
import random

try:
    import config as cfg
    from ui_elements import GridPanel, Button, render_text, draw_tooltip, draw_context_menu
    from player_stats import PlayerStats
    # item_generator 仅用于类型提示，不在此处创建物品
    from item_generator import ModItem
except ImportError as e:
    print(f"错误：inventory_gui.py 导入失败: {e}")
    sys.exit()

class InventoryScreen:
    """主游戏应用"""
    def __init__(self, screen, fonts, player_stats, initial_mod_items, initial_inv_items):
        self.screen = screen
        self.fonts = fonts
        self.player_stats = player_stats
        self.clock = pygame.time.Clock()
        
        self.screen_width, self.screen_height = self.screen.get_size()

        # 1. 初始化面板 (位置将在 _calculate_layout 中设置)
        self.mod_panel = GridPanel((0,0,1,1), cfg.MOD_PANEL_ROWS, cfg.MOD_PANEL_COLS)
        self.inv_panel = GridPanel((0,0,1,1), cfg.INV_PANEL_ROWS, cfg.INV_PANEL_COLS)
        
        self.stats_panel_rect = pygame.Rect(0,0,1,1)
        
        self.back_button = Button((0,0,1,1), "返回", self.fonts["button"], "back",
                                  cfg.COLOR_BUTTON_BACK, cfg.COLOR_BUTTON_BACK_HOVER)
        
        # 1.3 动态计算布局
        self._calculate_layout(self.screen_width, self.screen_height)

        # 2. 加载初始物品
        for item, (r, c) in initial_mod_items.items():
            self.mod_panel.add_item(item, r, c)
            
        for item, (r, c) in initial_inv_items.items():
            self.inv_panel.add_item(item, r, c)

        # 3. 状态变量
        self.running = True
        self.dragging_item = None # (item, offset_x, offset_y)
        self.drag_origin_panel = None
        self.drag_origin_pos = None
        
        self.click_start_pos = None
        self.click_start_item = None
        
        self.hovered_item = None
        
        self.context_menu = {"active": False, "item": None, "rect": None, "options": []}
        
        # 1.6.3 双击
        self.last_click_time = 0
        self.last_clicked_item = None

        # 4. 初始属性计算
        self.player_stats.calculate_stats(self.mod_panel.items.keys())

    def _calculate_layout(self, width, height):
        """1.3 居中布局 & 1.1 响应式"""
        self.screen_width = width
        self.screen_height = height
        
        # 定义逻辑尺寸
        mod_w = cfg.MOD_PANEL_COLS * cfg.CELL_SIZE
        mod_h = cfg.MOD_PANEL_ROWS * cfg.CELL_SIZE
        inv_w = cfg.INV_PANEL_COLS * cfg.CELL_SIZE
        inv_h = cfg.INV_PANEL_ROWS * cfg.CELL_SIZE
        stats_w = cfg.STATS_PANEL_WIDTH
        
        # 左侧面板取最大宽度
        left_w = max(mod_w, inv_w)
        
        # 总内容区
        total_w = left_w + cfg.PANEL_GAP + stats_w
        total_h = mod_h + cfg.PANEL_GAP + inv_h
        
        # 计算起始点 (居中)
        start_x = (width - total_w) // 2
        start_y = (height - total_h) // 2
        
        # 1.2 标题高度
        title_h = self.fonts["main"].get_height() + 10 # 5px padding
        
        # 设置 Rects
        mod_rect = (start_x, start_y + title_h, mod_w, mod_h)
        self.mod_panel.update_rect(mod_rect)
        
        inv_rect = (start_x, start_y + title_h + mod_h + cfg.PANEL_GAP + title_h, inv_w, inv_h)
        self.inv_panel.update_rect(inv_rect)
        
        stats_rect_h = mod_h + cfg.PANEL_GAP + inv_h + title_h * 2
        self.stats_panel_rect = pygame.Rect(start_x + left_w + cfg.PANEL_GAP, start_y, stats_w, stats_rect_h)
        
        # 1.5 返回按钮
        btn_rect = (width - 100 - cfg.PANEL_GAP, height - 40 - cfg.PANEL_GAP, 100, 40)
        self.back_button.update_rect(btn_rect)

    def run(self):
        """主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            
        # 循环结束，返回修改后的物品列表
        return self.mod_panel.items, self.inv_panel.items

    def handle_events(self):
        """处理所有输入事件"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                # TODO: 也许应该返回一个 "quit" 信号?
            
            # 1.1 窗口缩放
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self._calculate_layout(event.w, event.h)
                
            # 1.5 返回按钮
            if self.back_button.handle_event(event, (mouse_x, mouse_y)) == "back":
                self.running = False

            # --- 鼠标按下 ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 1. 左键 (拖动 / 旋转)
                if event.button == 1:
                    if self.context_menu["active"]:
                        self.handle_context_click()
                        self.context_menu["active"] = False
                        continue
                        
                    item, pos, panel = self.get_item_at_pos(mouse_x, mouse_y)
                    
                    if item:
                        self.click_start_pos = (mouse_x, mouse_y)
                        self.click_start_item = item
                        
                        screen_x, screen_y = panel.grid_to_screen(pos[0], pos[1])
                        self.dragging_item = (item, mouse_x - screen_x, mouse_y - screen_y)
                        self.drag_origin_panel = panel
                        self.drag_origin_pos = pos
                        
                        panel.remove_item(item)
                        # 立即更新属性
                        if panel == self.mod_panel:
                            self.player_stats.calculate_stats(self.mod_panel.items.keys())
                
                # 2. 右键 (上下文菜单)
                if event.button == 3:
                    if self.context_menu["active"]:
                        self.context_menu["active"] = False
                    
                    item, pos, panel = self.get_item_at_pos(mouse_x, mouse_y)
                    if item:
                        self.open_context_menu(item, panel, (mouse_x, mouse_y))

            # --- 鼠标松开 ---
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.dragging_item:
                        self.handle_drop(mouse_x, mouse_y)
                    
                    # 1.6.3 双击旋转
                    elif self.click_start_item:
                        dist_sq = (mouse_x - self.click_start_pos[0])**2 + (mouse_y - self.click_start_pos[1])**2
                        if dist_sq < 5**2: # 是单击
                            current_time = pygame.time.get_ticks()
                            if current_time - self.last_click_time < 500 and self.click_start_item == self.last_clicked_item:
                                # 双击！
                                self.handle_rotate(self.click_start_item)
                                self.last_click_time = 0
                                self.last_clicked_item = None
                            else:
                                # 单击
                                self.last_click_time = current_time
                                self.last_clicked_item = self.click_start_item
                            
                    self.dragging_item = None
                    self.click_start_item = None
                    self.click_start_pos = None

            # --- 鼠标移动 ---
            if event.type == pygame.MOUSEMOTION:
                if not self.dragging_item:
                    item, _, _ = self.get_item_at_pos(mouse_x, mouse_y)
                    self.hovered_item = item
                else:
                    self.click_start_item = None # 开始拖动，取消单击
                    self.last_clicked_item = None # 取消双击

    def get_item_at_pos(self, x, y):
        """辅助函数：检查两个面板"""
        item, pos = self.mod_panel.get_item_at(x, y)
        if item:
            return item, pos, self.mod_panel
        
        item, pos = self.inv_panel.get_item_at(x, y)
        if item:
            return item, pos, self.inv_panel
            
        return None, None, None

    def handle_drop(self, mouse_x, mouse_y):
        """处理物品放下逻辑"""
        item, offset = self.dragging_item[0], self.dragging_item[1:]
        placed = False
        
        # 1. 尝试放入强化面板
        grid_pos = self.mod_panel.screen_to_grid(mouse_x, mouse_y)
        if grid_pos:
            drop_r = grid_pos[0] - (offset[1] // self.mod_panel.cell_size)
            drop_c = grid_pos[1] - (offset[0] // self.mod_panel.cell_size)
            if self.mod_panel.add_item(item, drop_r, drop_c):
                placed = True
                self.player_stats.calculate_stats(self.mod_panel.items.keys())
        
        # 2. 尝试放入背包
        if not placed:
            grid_pos = self.inv_panel.screen_to_grid(mouse_x, mouse_y)
            if grid_pos:
                drop_r = grid_pos[0] - (offset[1] // self.inv_panel.cell_size)
                drop_c = grid_pos[1] - (offset[0] // self.inv_panel.cell_size)
                if self.inv_panel.add_item(item, drop_r, drop_c):
                    placed = True

        # 3. 放回原处
        if not placed:
            self.drag_origin_panel.add_item(item, self.drag_origin_pos[0], self.drag_origin_pos[1])
            if self.drag_origin_panel == self.mod_panel:
                self.player_stats.calculate_stats(self.mod_panel.items.keys())

    def handle_rotate(self, item):
        """处理物品旋转逻辑 (双击)"""
        panel = None
        pos = None
        if item in self.mod_panel.items:
            panel, pos = self.mod_panel, self.mod_panel.items[item]
        elif item in self.inv_panel.items:
            panel, pos = self.inv_panel, self.inv_panel.items[item]
        else:
            # 物品在拖动失败后被点击
            self.drag_origin_panel.add_item(item, self.drag_origin_pos[0], self.drag_origin_pos[1])
            panel = self.drag_origin_panel
            pos = self.drag_origin_pos
        
        original_shape = item.shape
        panel.remove_item(item)
        item.rotate()
        
        if panel.is_valid_placement(item, pos[0], pos[1]):
            panel.add_item(item, pos[0], pos[1])
        else:
            item.shape = original_shape # 转回去
            panel.add_item(item, pos[0], pos[1])
            
        if panel == self.mod_panel:
            self.player_stats.calculate_stats(self.mod_panel.items.keys())

    def open_context_menu(self, item, panel, pos):
        """打开右键菜单"""
        options = [
            ("摧毁", "destroy"),
            ("精炼 (Reroll All)", "refine_1"),
            ("精炼 (Lock)", "refine_2"),
        ]
        
        menu_width = 200
        menu_height = 5 + len(options) * 30 + 5
        
        # 防止菜单出界
        x, y = pos
        if x + menu_width > self.screen_width:
            x -= menu_width
        if y + menu_height > self.screen_height:
            y -= menu_height
            
        self.context_menu = {
            "active": True, "item": item, "panel": panel,
            "rect": pygame.Rect(x, y, menu_width, menu_height),
            "options": options
        }

    def handle_context_click(self):
        """处理对右键菜单的点击"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        item = self.context_menu["item"]
        panel = self.context_menu["panel"]
        
        current_y = self.context_menu["rect"].y + 5
        for text, action in self.context_menu["options"]:
            option_rect = pygame.Rect(self.context_menu["rect"].x, current_y, self.context_menu["rect"].width, 30)
            if option_rect.collidepoint(mouse_x, mouse_y):
                if action == "destroy":
                    panel.remove_item(item)
                elif action == "refine_1":
                    item.reroll_affixes(level=1)
                elif action == "refine_2":
                    print(f"物品 {item.quality} 尝试二级精炼...（演示：锁定第一个词条）")
                    item.reroll_affixes(level=2, locked_indices=[0])
                
                if panel == self.mod_panel:
                    self.player_stats.calculate_stats(self.mod_panel.items.keys())
                break
            current_y += 30

    def update(self):
        """更新游戏状态"""
        pass

    def draw(self):
        """绘制所有内容"""
        self.screen.fill(cfg.COLOR_BACKGROUND)
        mouse_pos = pygame.mouse.get_pos()
        
        # 1. 绘制标题 (1.2)
        mod_title_y = self.mod_panel.rect.y - self.fonts["main"].get_height() - 5
        self.screen.blit(render_text(self.fonts["main"], f"枪械强化模组 ({cfg.MOD_PANEL_ROWS}x{cfg.MOD_PANEL_COLS})", cfg.COLOR_TEXT_HEADER, bold=True), 
                         (self.mod_panel.rect.x, mod_title_y))
        
        inv_title_y = self.inv_panel.rect.y - self.fonts["main"].get_height() - 5
        self.screen.blit(render_text(self.fonts["main"], f"背包 ({cfg.INV_PANEL_ROWS}x{cfg.INV_PANEL_COLS})", cfg.COLOR_TEXT_HEADER, bold=True), 
                         (self.inv_panel.rect.x, inv_title_y))
        
        # 2. 绘制面板
        self.mod_panel.draw(self.screen)
        self.inv_panel.draw(self.screen)
        self.player_stats.draw(self.screen, self.stats_panel_rect)
        
        # 3. 绘制返回按钮
        self.back_button.draw(self.screen, mouse_pos)
        
        # 4. 绘制拖动的物品 (在最上层)
        if self.dragging_item:
            item, offset_x, offset_y = self.dragging_item
            item.draw(self.screen, mouse_pos[0] - offset_x, mouse_pos[1] - offset_y, cfg.CELL_SIZE)
            
        # 5. 绘制悬停提示
        if self.hovered_item and not self.dragging_item and not self.context_menu["active"]:
            draw_tooltip(self.screen, self.hovered_item, mouse_pos[0], mouse_pos[1], self.fonts)

        # 6. 绘制右键菜单
        if self.context_menu["active"]:
            draw_context_menu(self.screen, self.context_menu, self.fonts["main"])
            
        pygame.display.flip()