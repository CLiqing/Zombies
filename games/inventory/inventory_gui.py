# inventory_gui.py
# 包含 InventoryScreen 类
import pygame
import sys

try:
    import config as cfg
    from ui_elements import GridPanel, Button, render_text, draw_tooltip, draw_context_menu
    from player_stats import StatsPanelRenderer
except ImportError as e:
    print(f"错误：inventory_gui.py 导入失败: {e}")
    sys.exit()

class InventoryScreen:
    """背包与强化界面"""
    def __init__(self, screen, fonts, player_logic, initial_mod_items, initial_inv_items):
        self.screen = screen
        self.fonts = fonts
        self.player_logic = player_logic
        self.stats_renderer = StatsPanelRenderer(fonts)
        
        self.clock = pygame.time.Clock()
        
        self.screen_width, self.screen_height = self.screen.get_size()

        # 1. 初始化面板
        self.mod_panel = GridPanel((0,0,1,1), cfg.MOD_PANEL_ROWS, cfg.MOD_PANEL_COLS)
        self.inv_panel = GridPanel((0,0,1,1), cfg.INV_PANEL_ROWS, cfg.INV_PANEL_COLS)
        
        self.stats_panel_rect = pygame.Rect(0,0,1,1)
        
        self.back_button = Button((0,0,1,1), "返回", self.fonts["button"], "back",
                                  cfg.COLOR_BUTTON_BACK, cfg.COLOR_BUTTON_BACK_HOVER)
        
        self._calculate_layout(self.screen_width, self.screen_height)

        # 2. 加载初始物品
        for item, (r, c) in initial_mod_items.items():
            self.mod_panel.add_item(item, r, c)
            
        for item, (r, c) in initial_inv_items.items():
            self.inv_panel.add_item(item, r, c)

        # 3. 状态变量
        self.running = True
        self.dragging_item = None
        self.drag_origin_panel = None
        self.drag_origin_pos = None
        
        # 记录拖动开始时的物品形状（用于回滚时的形状恢复）
        self.drag_original_shape = None 
        
        self.click_start_pos = None
        self.click_start_item = None
        
        self.hovered_item = None
        
        self.context_menu = {"active": False, "item": None, "rect": None, "options": []}
        
        self.last_click_time = 0
        self.last_clicked_item = None

        # 4. 初始属性计算
        self.player_logic.calculate_stats(self.mod_panel.items.keys())

    def _calculate_layout(self, width, height):
        """1.4 居中布局逻辑优化"""
        self.screen_width = width
        self.screen_height = height
        
        # 定义逻辑尺寸 (像素)
        mod_w = cfg.MOD_PANEL_COLS * cfg.CELL_SIZE
        mod_h = cfg.MOD_PANEL_ROWS * cfg.CELL_SIZE
        
        inv_w = cfg.INV_PANEL_COLS * cfg.CELL_SIZE
        inv_h = cfg.INV_PANEL_ROWS * cfg.CELL_SIZE
        
        # Stats Panel Renderer 使用固定宽度
        from player_stats import STAT_PANEL_FIXED_WIDTH, STAT_PANEL_FIXED_HEIGHT
        stats_w = STAT_PANEL_FIXED_WIDTH
        
        # 标题高度估计
        title_h = self.fonts["main"].get_height() + 10
        
        # --- 计算内容区总尺寸 ---
        left_col_h = title_h + mod_h + cfg.PANEL_GAP + title_h + inv_h
        left_col_w = max(mod_w, inv_w) 
        total_content_w = left_col_w + cfg.PANEL_GAP * 2 + stats_w
        total_content_h = max(left_col_h, STAT_PANEL_FIXED_HEIGHT + title_h) 
        
        # --- 计算左上角起点 (使其居中) ---
        start_x = max(0, (width - total_content_w) // 2)
        start_y = max(0, (height - total_content_h) // 2)
        
        # --- 设置 Mod 面板 ---
        mod_x = start_x
        mod_y = start_y + title_h
        self.mod_panel.update_rect((mod_x, mod_y, mod_w, mod_h))
        
        # --- 设置 Inv 面板 ---
        inv_x = start_x
        inv_y = mod_y + mod_h + cfg.PANEL_GAP + title_h
        self.inv_panel.update_rect((inv_x, inv_y, inv_w, inv_h))
        
        # --- 设置 属性 面板 ---
        stats_x = start_x + left_col_w + cfg.PANEL_GAP * 2
        stats_y = start_y 
        self.stats_panel_rect = pygame.Rect(stats_x, stats_y, stats_w, STAT_PANEL_FIXED_HEIGHT)
        
        # --- 设置 返回按钮 ---
        btn_rect = (width - 100 - cfg.PANEL_GAP, height - 40 - cfg.PANEL_GAP, 100, 40)
        self.back_button.update_rect(btn_rect)

    def run(self):
        """主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            
        return self.mod_panel.items, self.inv_panel.items

    def handle_events(self):
        """处理事件"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self._calculate_layout(event.w, event.h)
                
            if self.back_button.handle_event(event, (mouse_x, mouse_y)) == "back":
                self.running = False

            # --- 键盘事件处理：拖动中按空格旋转 ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.dragging_item:
                        item, _, _ = self.dragging_item
                        self.handle_drag_rotate(item, mouse_x, mouse_y)
                        self.click_start_item = None
                        self.last_clicked_item = None
            # --- 结束键盘事件处理 ---

            if event.type == pygame.MOUSEBUTTONDOWN:
                # 左键
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
                        
                        # 记录初始形状
                        self.drag_original_shape = item.shape
                        
                        panel.remove_item(item)
                        # 属性实时更新
                        if panel == self.mod_panel:
                            self.player_logic.calculate_stats(self.mod_panel.items.keys())
                
                # 右键
                if event.button == 3:
                    if self.context_menu["active"]:
                        self.context_menu["active"] = False
                    
                    item, pos, panel = self.get_item_at_pos(mouse_x, mouse_y)
                    if item:
                        self.open_context_menu(item, panel, (mouse_x, mouse_y))

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    
                    # 1. 处理拖放结束
                    if self.dragging_item:
                        self.handle_drop(mouse_x, mouse_y)
                    
                    # 2. 处理双击逻辑 (仅在非拖动状态下检查)
                    elif self.click_start_item: 
                        dist_sq = (mouse_x - self.click_start_pos[0])**2 + (mouse_y - self.click_start_pos[1])**2
                        if dist_sq < 5**2:
                            current_time = pygame.time.get_ticks()
                            if current_time - self.last_click_time < 500 and self.click_start_item == self.last_clicked_item:
                                self.handle_rotate(self.click_start_item)
                                self.last_click_time = 0
                                self.last_clicked_item = None
                            else:
                                self.last_click_time = current_time
                                self.last_clicked_item = self.click_start_item
                            
                    # 3. 清理拖动和点击状态
                    self.dragging_item = None
                    self.drag_original_shape = None
                    self.click_start_item = None
                    self.click_start_pos = None

            if event.type == pygame.MOUSEMOTION:
                if not self.dragging_item:
                    item, _, _ = self.get_item_at_pos(mouse_x, mouse_y)
                    self.hovered_item = item
                else:
                    self.click_start_item = None
                    self.last_clicked_item = None

    def get_item_at_pos(self, x, y):
        item, pos = self.mod_panel.get_item_at(x, y)
        if item: return item, pos, self.mod_panel
        
        item, pos = self.inv_panel.get_item_at(x, y)
        if item: return item, pos, self.inv_panel
            
        return None, None, None

    def handle_drop(self, mouse_x, mouse_y):
        item, offset = self.dragging_item[0], self.dragging_item[1:]
        placed = False
        
        # 1. 尝试放入强化面板
        grid_pos = self.mod_panel.screen_to_grid(mouse_x, mouse_y)
        if grid_pos:
            drop_r = grid_pos[0] - (offset[1] // self.mod_panel.cell_size)
            drop_c = grid_pos[1] - (offset[0] // self.mod_panel.cell_size)
            if self.mod_panel.add_item(item, drop_r, drop_c):
                placed = True
                self.player_logic.calculate_stats(self.mod_panel.items.keys())
        
        # 2. 尝试放入背包
        if not placed:
            grid_pos = self.inv_panel.screen_to_grid(mouse_x, mouse_y)
            if grid_pos:
                drop_r = grid_pos[0] - (offset[1] // self.inv_panel.cell_size)
                drop_c = grid_pos[1] - (offset[0] // self.inv_panel.cell_size)
                if self.inv_panel.add_item(item, drop_r, drop_c):
                    placed = True

        # 3. [修复] 回滚到原处，并恢复原始形状，使用原生 add_item
        if not placed:
            panel = self.drag_origin_panel
            r, c = self.drag_origin_pos
            
            # 1. 恢复物品被拿起时的形状
            if self.drag_original_shape is not None:
                item.shape = self.drag_original_shape
            
            # 2. 使用原生方法 add_item 将其放回原位，确保更新 GridPanel 的查找表
            if panel.add_item(item, r, c): 
                placed = True
            else:
                # 理论上，如果物品形状正确，回滚到原位不应失败。
                # 如果这个警告出现，请检查 GridPanel 类的 remove_item 是否彻底清理了占用网格。
                print(f"严重警告: 物品 {item} 形状恢复后，回滚到原位 ({r}, {c}) 失败。")

            if panel == self.mod_panel:
                self.player_logic.calculate_stats(self.mod_panel.items.keys())
                
    # --- 拖动时旋转的方法 ---
    def handle_drag_rotate(self, item, mouse_x, mouse_y):
        """
        处理在拖动过程中按空格键旋转物品。
        如果旋转后超出边界，则回滚到旋转前的形状。
        """
        if not self.dragging_item:
            return

        # 记录旋转前的形状
        original_shape = item.shape
        
        # 执行旋转
        item.rotate()
        
        # 检查新形状是否可以在其原始面板的原位置容纳 (主要检查边界)
        panel = self.drag_origin_panel
        item_r, item_c = self.drag_origin_pos
        
        # 获取旋转后物品的尺寸 (item.get_bounds() 返回 (width, height))
        # 假设 item 具有 get_bounds 方法。
        item_w, item_h = item.get_bounds() 
        
        is_valid = True
        
        # 边界检查: 确保物品不会超出右侧或底部的边界
        if item_r + item_h > panel.rows or item_c + item_w > panel.cols:
            is_valid = False

        if is_valid:
            # 旋转成功，物品保持新形状
            pass
        else:
            # 旋转失败（超出边界），恢复旋转前的形状
            item.shape = original_shape 
            
        # 属性刷新
        if panel == self.mod_panel:
            self.player_logic.calculate_stats(self.mod_panel.items.keys())
    # --- 结束拖动旋转方法 ---

    def handle_rotate(self, item):
        """双击触发的旋转 (原逻辑，尝试放回原位置)"""
        panel = None
        pos = None
        if item in self.mod_panel.items:
            panel, pos = self.mod_panel, self.mod_panel.items[item]
        elif item in self.inv_panel.items:
            panel, pos = self.inv_panel, self.inv_panel.items[item]
        else:
            # 理论上，这不应该发生，但作为安全回退
            self.drag_origin_panel.add_item(item, self.drag_origin_pos[0], self.drag_origin_pos[1])
            panel = self.drag_origin_panel
            pos = self.drag_origin_pos
        
        original_shape = item.shape
        panel.remove_item(item)
        item.rotate()
        
        if panel.is_valid_placement(item, pos[0], pos[1]):
            panel.add_item(item, pos[0], pos[1])
        else:
            item.shape = original_shape
            panel.add_item(item, pos[0], pos[1])
            
        if panel == self.mod_panel:
            self.player_logic.calculate_stats(self.mod_panel.items.keys())

    def open_context_menu(self, item, panel, pos):
        """
        1.1 打开右键菜单
        生成带源质消耗的文本，并检查是否可用。
        """
        options = []
        
        # 1. 摧毁
        gain = cfg.ESSENCE_GAIN.get(item.quality, 0)
        txt_destroy = f"摧毁 (获得 §{gain})"
        options.append((txt_destroy, "destroy", True)) # 始终可用
        
        # 2. 精炼 (Reroll All)
        cost_reroll = cfg.COST_REROLL.get(item.quality, 0)
        can_afford_reroll = self.player_logic.current_essence >= cost_reroll
        txt_reroll = f"精炼 (需要 §{cost_reroll})"
        options.append((txt_reroll, "refine_1", can_afford_reroll))
        
        # 3. 高级精炼 (Lock) - 仅限史诗/传奇
        if item.quality in ["史诗", "传奇"]:
            cost_lock = cfg.COST_LOCK.get(item.quality, 0)
            can_afford_lock = self.player_logic.current_essence >= cost_lock
            txt_lock = f"高级精炼 (需要 §{cost_lock})"
            options.append((txt_lock, "refine_2", can_afford_lock))
        
        menu_width = 220
        menu_height = 5 + len(options) * 30 + 5
        
        x, y = pos
        if x + menu_width > self.screen_width: x -= menu_width
        if y + menu_height > self.screen_height: y -= menu_height
            
        self.context_menu = {
            "active": True, "item": item, "panel": panel,
            "rect": pygame.Rect(x, y, menu_width, menu_height),
            "options": options
        }

    def handle_context_click(self):
        """处理右键菜单点击，包含源质交易"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        item = self.context_menu["item"]
        panel = self.context_menu["panel"]
        
        current_y = self.context_menu["rect"].y + 5
        
        # 注意：这里要按照 options 的顺序遍历
        for option in self.context_menu["options"]:
            # 解构新格式
            if len(option) == 3:
                text, action, enabled = option
            else:
                text, action = option
                enabled = True

            option_rect = pygame.Rect(self.context_menu["rect"].x, current_y, self.context_menu["rect"].width, 30)
            
            # 只有启用且点击时才触发
            if enabled and option_rect.collidepoint(mouse_x, mouse_y):
                
                if action == "destroy":
                    # 获得源质
                    gain = cfg.ESSENCE_GAIN.get(item.quality, 0)
                    self.player_logic.add_essence(gain)
                    panel.remove_item(item)
                    
                elif action == "refine_1":
                    # 消耗源质
                    cost = cfg.COST_REROLL.get(item.quality, 0)
                    if self.player_logic.spend_essence(cost):
                        item.reroll_affixes(level=1)
                    
                elif action == "refine_2":
                    cost = cfg.COST_LOCK.get(item.quality, 0)
                    if self.player_logic.spend_essence(cost):
                        # 演示：锁定第一个
                        item.reroll_affixes(level=2, locked_indices=[0])
                
                # 刷新属性
                if panel == self.mod_panel:
                    self.player_logic.calculate_stats(self.mod_panel.items.keys())
                
                # 只要点击了有效选项，就关闭菜单
                break
            
            current_y += 30

    def update(self):
        pass

    def draw(self):
        self.screen.fill(cfg.COLOR_BACKGROUND)
        mouse_pos = pygame.mouse.get_pos()
        
        # 绘制标题
        mod_title_y = self.mod_panel.rect.y - self.fonts["main"].get_height() - 5
        self.screen.blit(render_text(self.fonts["main"], f"枪械强化模组 ({cfg.MOD_PANEL_ROWS}x{cfg.MOD_PANEL_COLS})", cfg.COLOR_TEXT_HEADER, bold=True), 
                         (self.mod_panel.rect.x, mod_title_y))
        
        inv_title_y = self.inv_panel.rect.y - self.fonts["main"].get_height() - 5
        self.screen.blit(render_text(self.fonts["main"], f"背包 ({cfg.INV_PANEL_ROWS}x{cfg.INV_PANEL_COLS})", cfg.COLOR_TEXT_HEADER, bold=True), 
                         (self.inv_panel.rect.x, inv_title_y))
        
        # 绘制面板
        self.mod_panel.draw(self.screen)
        self.inv_panel.draw(self.screen)
        
        # 1.3 绘制属性面板 (调用 renderer)
        self.stats_renderer.draw(self.screen, self.stats_panel_rect, self.player_logic)
        
        self.back_button.draw(self.screen, mouse_pos)
        
        if self.dragging_item:
            item, offset_x, offset_y = self.dragging_item
            item.draw(self.screen, mouse_pos[0] - offset_x, mouse_pos[1] - offset_y, cfg.CELL_SIZE)
            
        if self.hovered_item and not self.dragging_item and not self.context_menu["active"]:
            draw_tooltip(self.screen, self.hovered_item, mouse_pos[0], mouse_pos[1], self.fonts)

        if self.context_menu["active"]:
            draw_context_menu(self.screen, self.context_menu, self.fonts["main"])
            
        pygame.display.flip()