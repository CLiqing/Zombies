# test_inventory.py
# 背包系统测试入口
import pygame
import sys
import random
import os

# 添加父目录到路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from systems.inventory import config as cfg
    from systems.inventory.item_generator import create_mod_item
    from systems.inventory.player_stats import PlayerLogic, StatsPanelRenderer, STAT_PANEL_FIXED_WIDTH, STAT_PANEL_FIXED_HEIGHT
    from systems.inventory.ui_elements import Button, GridPanel, render_text
    from systems.inventory.inventory_gui import InventoryScreen
except ImportError as e:
    print(f"错误：test_inventory.py 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit()

class MainMenu:
    """主菜单/测试界面"""
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(cfg.WINDOW_TITLE)
        
        self.screen = pygame.display.set_mode(
            (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), 
            pygame.RESIZABLE if cfg.SCREEN_RESIZABLE else 0
        )
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 1.2 加载指定字体
        font_path = cfg.FONT_PATH
        if not os.path.exists(font_path):
            print(f"警告：字体文件 {font_path} 不存在，尝试使用系统默认字体。")
            font_path = None # Fallback
            
        try:
            self.fonts = {
                "main": pygame.font.Font(font_path, cfg.FONT_SIZE_MAIN) if font_path else pygame.font.SysFont("SimHei", cfg.FONT_SIZE_MAIN),
                "small": pygame.font.Font(font_path, cfg.FONT_SIZE_SMALL) if font_path else pygame.font.SysFont("SimHei", cfg.FONT_SIZE_SMALL),
                "affix_main": pygame.font.Font(font_path, cfg.FONT_SIZE_AFFIX_MAIN) if font_path else pygame.font.SysFont("SimHei", cfg.FONT_SIZE_AFFIX_MAIN),
                "affix_other": pygame.font.Font(font_path, cfg.FONT_SIZE_AFFIX_OTHER) if font_path else pygame.font.SysFont("SimHei", cfg.FONT_SIZE_AFFIX_OTHER),
                "button": pygame.font.Font(font_path, cfg.FONT_SIZE_BUTTON) if font_path else pygame.font.SysFont("SimHei", cfg.FONT_SIZE_BUTTON),
            }
        except Exception as e:
            print(f"字体加载失败: {e}")
            sys.exit()

        # 游戏数据
        self.mod_items = {} 
        self.inv_items = {}
        
        # 1.3 初始化逻辑和渲染
        self.player_logic = PlayerLogic()
        self.stats_renderer = StatsPanelRenderer(self.fonts)
        
        # 界面元素
        self.buttons = []
        self.stats_panel_rect = pygame.Rect(0,0,1,1)
        
        # 逻辑面板 (不显示，仅用于计算空位)
        self.inv_panel_logic = GridPanel((0,0,1,1), cfg.INV_PANEL_ROWS, cfg.INV_PANEL_COLS)

        self._calculate_layout(self.screen.get_width(), self.screen.get_height())
        
        # 初始物品
        self._generate_test_items()
        self.player_logic.calculate_stats(self.mod_items.keys())

    def _generate_test_items(self):
        """生成初始测试物品"""
        self.add_item_to_inventory(create_mod_item("普通", 1, "游荡者"))
        self.add_item_to_inventory(create_mod_item("精良", 5, "铁桶"))
        item_equipped = create_mod_item("精良", 5, "游荡者")
        self.mod_items[item_equipped] = (0, 0)
        

    def _calculate_layout(self, width, height):
        """计算主菜单布局"""
        # 属性面板在右侧，使用固定尺寸
        self.stats_panel_rect = pygame.Rect(
            width - STAT_PANEL_FIXED_WIDTH - cfg.PANEL_GAP,
            cfg.PANEL_GAP,
            STAT_PANEL_FIXED_WIDTH,
            STAT_PANEL_FIXED_HEIGHT
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
            
            for button in self.buttons:
                action = button.handle_event(event, mouse_pos)
                if action:
                    self.handle_button_click(action)
                    break 

    def handle_button_click(self, action):
        """处理按钮动作"""
        # 定义掉落来源列表
        MOB_SOURCES = ["游荡者", "铁桶", "食尸鬼"] 
        
        if action == "inventory":
            # 传入逻辑类实例
            inv_screen = InventoryScreen(
                self.screen, self.fonts, self.player_logic, 
                self.mod_items, self.inv_items
            )
            # 阻塞运行
            new_mods, new_inv = inv_screen.run()
            
            self.mod_items = new_mods
            self.inv_items = new_inv
            
            self.player_logic.calculate_stats(self.mod_items.keys())
        
        elif action == "gen_common":
            source = random.choice(MOB_SOURCES)
            item = create_mod_item("普通", random.randint(1, 5), source)
            self.add_item_to_inventory(item)
        elif action == "gen_rare":
            source = random.choice(MOB_SOURCES)
            item = create_mod_item("精良", random.randint(5, 10), source)
            self.add_item_to_inventory(item)
        elif action == "gen_epic":
            source = random.choice(MOB_SOURCES)
            item = create_mod_item("史诗", random.randint(10, 15), source)
            self.add_item_to_inventory(item)
        elif action == "gen_legendary":
            source = random.choice(MOB_SOURCES)
            item = create_mod_item("传奇", random.randint(15, 20), source)
            self.add_item_to_inventory(item)

    def draw(self):
        """绘制主菜单"""
        self.screen.fill(cfg.COLOR_BACKGROUND)
        mouse_pos = pygame.mouse.get_pos()
        
        # 绘制标题
        title = render_text(self.fonts["main"], "主菜单 / 测试平台", cfg.COLOR_TEXT_HEADER, bold=True)
        self.screen.blit(title, (cfg.PANEL_GAP * 2, cfg.PANEL_GAP))
        
        for button in self.buttons:
            button.draw(self.screen, mouse_pos)
            
        # 1.3 绘制属性面板
        self.stats_renderer.draw(self.screen, self.stats_panel_rect, self.player_logic)
        
        pygame.display.flip()

# --- 启动游戏 ---
if __name__ == "__main__":
    main_menu = MainMenu()
    main_menu.run()
