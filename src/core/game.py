# game.py
import pygame
import sys
import math
import random

# 添加父目录到路径
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入所有模块
import config
from core import drawing
from systems.citymap.citymap import CityMap
from entities.player import Player
from entities.bullet import Bullet
from entities.monster_sprite import MonsterSprite
from systems.monsters.monster_logic import generate_monsters
from core.camera import Camera

class Game:
    """
    主游戏类，负责管理游戏循环、状态、实体和渲染。
    """
    def __init__(self):
        pygame.init()
        pygame.font.init()
        
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("Zombie Survival")
        self.clock = pygame.time.Clock()
        self.is_running = True
        
        # 禁用文本输入/输入法（这样键盘事件才能正常工作）
        pygame.key.stop_text_input()
        
        # (Spec V) 加载字体
        self.font_main = pygame.font.Font(None, 24) # 用于 UI
        self.font_minimap = pygame.font.Font(None, 16) # 用于小地图
        
        # 游戏状态
        self.current_day = 1
        
        # # DEBUG: 添加首帧暂停标志
        # self.first_frame_rendered = False
        # self.paused = False
        
        self.load_data()

    def load_data(self):
        """加载所有游戏资源和初始状态"""
        
        # 1. 地图
        self.city_map = CityMap()
        # (Spec V) 加载地图贴图
        self.tile_images = drawing.load_tile_images()
        
        # 2. 实体组
        self.all_sprites = pygame.sprite.Group()
        self.monsters = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.walls = pygame.sprite.Group() # (Spec IV) 碰撞组

        # 3. 创建墙体碰撞器 (Spec IV)
        self.create_wall_colliders()

        # 4. 创建玩家
        start_r, start_c = self.city_map.get_player_position()
        # 将网格坐标转换为世界像素坐标 (中心)
        start_x = start_c * config.TILE_SIZE + config.TILE_SIZE / 2
        start_y = start_r * config.TILE_SIZE + config.TILE_SIZE / 2
        
        self.player = Player(start_x, start_y)
        self.all_sprites.add(self.player)

        # 5. 创建摄像机 (Spec II)
        self.camera = Camera(config.WORLD_WIDTH, config.WORLD_HEIGHT)

        # 6. 生成第一波怪物
        self.spawn_wave()

    def create_wall_colliders(self):
        """(Spec IV) 遍历地图，为 '#' 和 '~' 创建碰撞 Sprite"""
        W, H = self.city_map.get_dimensions()
        for r in range(H):
            for c in range(W):
                tile = self.city_map.get_tile(r, c)
                # (Spec IV) 玩家不可穿过 # 和 ~
                if tile == '#' or tile == '~':
                    wall_sprite = pygame.sprite.Sprite()
                    wall_sprite.rect = pygame.Rect(
                        c * config.TILE_SIZE, 
                        r * config.TILE_SIZE, 
                        config.TILE_SIZE, 
                        config.TILE_SIZE
                    )
                    # (用于怪物 AI 区分)
                    wall_sprite.tile_type = tile 
                    self.walls.add(wall_sprite)

    def spawn_wave(self):
        """(Spec IV) 生成新一波怪物"""
        print(f"--- Spawning Wave for Day {self.current_day} ---")
        monster_data_list = generate_monsters(self.city_map, self.current_day)
        
        for data in monster_data_list:
            r, c = data.position
            # 转换为世界像素坐标 (中心)
            x = c * config.TILE_SIZE + config.TILE_SIZE / 2
            y = r * config.TILE_SIZE + config.TILE_SIZE / 2
            
            m = MonsterSprite(data, x, y)
            self.all_sprites.add(m)
            self.monsters.add(m)

    def run(self):
        """主游戏循环"""
        while self.is_running:
            # (Spec I) 控制帧率，并获取 dt (增量时间)
            self.dt = self.clock.tick(config.FPS) / 1000.0
            
            self.events()
            self.update()
            self.draw()
            
            # # DEBUG: 如果已暂停，跳过更新和绘制
            # if not self.paused:
            #     self.update()
            #     self.draw()
            #     
            #     # DEBUG: 第一帧渲染完成后暂停
            #     if not self.first_frame_rendered:
            #         self.first_frame_rendered = True
            #         self.paused = True
            #         print("\n" + "="*60)
            #         print("DEBUG: 第一帧渲染完成，游戏已暂停")
            #         print("窗口保持打开，请对比打印数据和显示图像")
            #         print("关闭窗口可退出程序")
            #         print("="*60 + "\n")

    def events(self):
        """处理所有输入事件"""
        mouse_world_pos = self.camera.get_mouse_world_pos()

        for event in pygame.event.get():
            # DEBUG: 打印所有事件
            # if event.type != pygame.MOUSEMOTION:  # 忽略鼠标移动事件
            #     print(f"事件: {pygame.event.event_name(event.type)}")
            
            if event.type == pygame.QUIT:
                # print("检测到退出事件")
                self.is_running = False
            
            # DEBUG: 检测键盘事件
            # if event.type == pygame.KEYDOWN:
            #     print(f"!!! 检测到按键按下: {pygame.key.name(event.key)}")
            
            # (Spec IV) 射击
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 左键点击
                    # print("检测到鼠标左键点击")
                    bullet = self.player.shoot(mouse_world_pos)
                    if bullet:
                        self.all_sprites.add(bullet)
                        self.bullets.add(bullet)

    def update(self):
        """更新所有游戏逻辑"""
        
        # 1. 获取鼠标在世界中的位置，用于玩家朝向
        mouse_world_pos = self.camera.get_mouse_world_pos()

        # 2. 更新实体
        self.player.update(self.dt, mouse_world_pos, self.walls)
        self.monsters.update(self.dt, self.player.pos, self.walls)
        self.bullets.update(self.dt)
        
        # 3. 更新摄像机 (Spec II)
        self.camera.update(self.player)

        # 4. 碰撞检测 (Spec IV)
        
        # 子弹 vs 怪物
        # groupcollide: 检查两组，True/True 表示碰撞后双方都销毁
        # (Spec IV) 子弹碰撞怪物后，子弹销毁
        hits = pygame.sprite.groupcollide(self.monsters, self.bullets, False, True)
        for monster_hit in hits:
            # (Spec IV) 伤害判定
            # (简化：造成玩家 '攻击力' 属性的伤害)
            damage = self.player.logic.total_stats.get("攻击力", 10)
            
            # (TODO: 在 monster_logic.py 中添加 take_damage 方法)
            monster_hit.logic.current_hp -= damage
            
            if monster_hit.logic.current_hp <= 0:
                monster_hit.logic.is_alive = False
                monster_hit.kill() # 从所有组中移除

        # 5. 游戏循环 (Spec IV)
        if not self.monsters: # 如果怪物组为空
            self.current_day += 1
            self.spawn_wave()

    def draw(self):
        """渲染所有内容到屏幕"""
        
        self.screen.fill(config.COLOR_BLACK) # 清屏
        
        # 1. 绘制地图 (Spec V)
        drawing.draw_map(self.screen, self.city_map, self.camera, self.tile_images)

        # 2. 绘制实体 (Spec III)
        # 按照特定顺序绘制
        
        # 绘制所有怪物
        for monster in self.monsters:
            drawing.draw_monster(self.screen, monster, self.camera)
            
        # 绘制玩家
        drawing.draw_player(self.screen, self.player, self.camera)
        
        # 绘制子弹 (覆盖在其他实体之上)
        for bullet in self.bullets:
            # 子弹有自己的 image，可以直接 blit
            self.screen.blit(bullet.image, self.camera.apply_to_rect(bullet.rect))

        # 绘制树木 (覆盖在实体之上，实现遮挡效果)
        drawing.draw_trees(self.screen, self.city_map, self.camera, self.tile_images)

        # 3. 绘制 UI (Spec V) - (不跟随摄像机)
        drawing.draw_ui(self.screen, self.player.logic, self.current_day, self.font_main)
        
        # 4. 绘制小地图 (Spec V)
        drawing.draw_minimap(self.screen, self.city_map, self.player, self.monsters, self.camera, self.font_minimap)

        # 5. 刷新屏幕
        pygame.display.flip()

    def quit(self):
        pygame.quit()
        sys.exit()