# main.py
# (New) 主程序入口
import pygame
import sys
import random

try:
    import config as cfg
    from item_generator import create_mod_item
    from player_stats import PlayerStats
    from ui_elements import Button, GridPanel, render_text # GridPanel for inv logic
    from inventory_gui import InventoryScreen
except ImportError as e:
    print(f"错误：main.py 导入失败: {e}")
    sys.exit()

class MainMenu:
    """主菜单/测试界面"""
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(cfg.WINDOW_TITLE) # 1.4
        
        # 1.1 窗口大小和可缩放
        self.screen = pygame.display.set_mode(
            (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), 
            pygame.RESIZABLE if cfg.SCREEN_RESIZABLE else 0
        )
        self.screen_width, self.screen_height = self.screen.get_size()
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 加载字体
        try:
            # 尝试使用 'SimHei'
            self.fonts = {
                "main": pygame.font.SysFont("SimHei", cfg.FONT_SIZE_MAIN),
                "small": pygame.font.SysFont("SimHei", cfg.FONT_SIZE_SMALL),
                "affix_main": pygame.font.SysFont("SimHei", cfg.FONT_SIZE_AFFIX_MAIN),
                "affix_other": pygame.font.SysFont("SimHei", cfg.FONT_SIZE_AFFIX_OTHER),
                "button": pygame.font.SysFont("SimHei", cfg.FONT_SIZE_BUTTON),
            }
        except:
            print("警告：'SimHei' 字体未找到，使用默认字体。")
            self.fonts = {
                "main": pygame.font.Font(None, cfg.FONT_SIZE_MAIN),
                "small": pygame.font.Font(None, cfg.FONT_SIZE_SMALL),
                "affix_main": pygame.font.Font(None, cfg.FONT_SIZE_AFFIX_MAIN + 2), # Default bold
                "affix_other": pygame.font.Font(None, cfg.FONT_SIZE_AFFIX_OTHER),
                "button": pygame.font.Font(None, cfg.FONT_SIZE_BUTTON + 2),
            }

        # 游戏状态 (数据)
        # 我们用字典 {item: (r, c)} 来存储
        self.mod_items = {} 
        self.inv_items = {}
        
        # 玩家属性
        self.player_stats = PlayerStats(self.fonts)
        
        # 2.3 界面元素
        self.buttons = []
        self.stats_panel_rect = pygame.Rect(0,0,1,1)
        
        # 临时创建 inv_panel 只是为了 'find_first_empty_slot' 逻辑
        # 它不会被绘制
        self.inv_panel_logic = GridPanel((0,0,1,1), cfg.INV_PANEL_ROWS, cfg.INV_PANEL_COLS)

        self._calculate_layout(self.screen_width, self.screen_height)
        
        # 添加初始物品
        self._generate_test_items()
        self.player_stats.calculate_stats(self.mod_items.keys())

    def _generate_test_items(self):
        """生成初始测试物品"""
        item1 = create_mod_item("普通", 1, "游荡者")
        self.add_item_to_inventory(item1)
        
        item2 = create_mod_item("精良", 5, "铁皮")
        self.add_item_to_inventory(item2)
        
        item5 = create_mod_item("精良", 5, "游荡者")
        # 装备上
        self.mod_items[item5] = (0, 0)
        

    def _calculate_layout(self, width, height):
        """计算主菜单布局"""
        self.screen_width = width
        self.screen_height = height
        
        # 属性面板在右侧
        self.stats_panel_rect = pygame.Rect(
            width - cfg.STATS_PANEL_WIDTH - cfg.PANEL_GAP,
            cfg.PANEL_GAP,
            cfg.STATS_PANEL_WIDTH,
            height - cfg.PANEL_GAP * 2
        )
        
        # 按钮在左侧
        self.buttons = []
        btn_w, btn_h = 200, 50
        btn_x = cfg.PANEL_GAP * 2
        btn_y = cfg.PANEL_GAP * 2
        
        btn_inventory = Button((btn_x, btn_y, btn_w, btn_h), "进入背包", self.fonts["button"], "inventory")
        self.buttons.append(btn_inventory)
        btn_y += btn_h + cfg.PANEL_GAP
        
        gen_buttons = [
            ("生成 普通", "gen_common", "普通"),
            ("生成 精良", "gen_rare", "精良"),
            ("生成 史诗", "gen_epic", "史诗"),
            ("生成 传奇", "gen_legendary", "传奇"),
        ]
        
        for text, action, quality in gen_buttons:
            color = cfg.QUALITY_COLORS[quality]
            hover_color = tuple(min(c + 30, 255) for c in color)
            btn = Button((btn_x, btn_y, btn_w, btn_h), text, self.fonts["button"], action,
                         bg_color=color, hover_color=hover_color)
            self.buttons.append(btn)
            btn_y += btn_h + 10


    def add_item_to_inventory(self, item):
        """安全地将物品添加到背包的第一个空位"""
        # 同步逻辑面板
        self.inv_panel_logic.items = {}
        self.inv_panel_logic.grid_data = [[None for _ in range(cfg.INV_PANEL_COLS)] for _ in range(cfg.INV_PANEL_ROWS)]
        for i, (r, c) in self.inv_items.items():
            self.inv_panel_logic.add_item(i, r, c)
            
        pos = self.inv_panel_logic.find_first_empty_slot(item)
        if pos:
            self.inv_items[item] = pos
            print(f"已生成 {item.quality} 物品并放入背包。")
        else:
            print("背包已满，无法生成物品。")

    def run(self):
        """主循环"""
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()

    def handle_events(self):
        """处理主菜单事件"""
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self._calculate_layout(event.w, event.h)
            
            # 检查按钮点击
            for button in self.buttons:
                action = button.handle_event(event, mouse_pos)
                if action:
                    self.handle_button_click(action)
                    break # 每次点击只处理一个按钮

    def handle_button_click(self, action):
        """处理按钮动作"""
        if action == "inventory":
            # 2.3 进入背包
            inv_screen = InventoryScreen(
                self.screen, self.fonts, self.player_stats, 
                self.mod_items, self.inv_items
            )
            # 阻塞式运行背包，直到返回
            new_mods, new_inv = inv_screen.run()
            
            # 更新主菜单的数据
            self.mod_items = new_mods
            self.inv_items = new_inv
            
            # 重新计算属性
            self.player_stats.calculate_stats(self.mod_items.keys())
        
        elif action == "gen_common":
            item = create_mod_item("普通", random.randint(1, 5))
            self.add_item_to_inventory(item)
        elif action == "gen_rare":
            item = create_mod_item("精良", random.randint(5, 10))
            self.add_item_to_inventory(item)
        elif action == "gen_epic":
            item = create_mod_item("史诗", random.randint(10, 15))
            self.add_item_to_inventory(item)
        elif action == "gen_legendary":
            item = create_mod_item("传奇", random.randint(15, 20))
            self.add_item_to_inventory(item)

    def draw(self):
        """绘制主菜单"""
        self.screen.fill(cfg.COLOR_BACKGROUND)
        mouse_pos = pygame.mouse.get_pos()
        
        # 绘制标题
        title = render_text(self.fonts["main"], "主菜单 / 测试平台", cfg.COLOR_TEXT_HEADER, bold=True)
        self.screen.blit(title, (cfg.PANEL_GAP * 2, cfg.PANEL_GAP))
        
        # 绘制按钮
        for button in self.buttons:
            button.draw(self.screen, mouse_pos)
            
        # 绘制属性面板
        self.player_stats.draw(self.screen, self.stats_panel_rect)
        
        pygame.display.flip()

# --- 启动游戏 ---
if __name__ == "__main__":
    main_menu = MainMenu()
    main_menu.run()