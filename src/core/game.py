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

class CorpseExplosion:
    """铁桶死亡尸爆效果"""
    def __init__(self, pos, max_radius, delay, damage, monster_name):
        self.pos = pos  # 爆炸位置
        self.max_radius = max_radius  # 最大半径
        self.delay = delay  # 延迟时间
        self.timer = delay  # 倒计时
        self.damage = damage  # 伤害值
        self.monster_name = monster_name  # 怪物名称
        self.is_exploding = False  # 是否正在爆炸
        self.explosion_progress = 0  # 爆炸进度 0-1
        self.current_radius = 0  # 当前半径
        self.finished = False  # 是否完成
    
    def update(self, dt):
        """更新尸爆状态"""
        if self.finished:
            return
        
        if not self.is_exploding:
            # 延迟阶段
            self.timer -= dt
            if self.timer <= 0:
                self.is_exploding = True
                self.explosion_progress = 0
                print(f"{self.monster_name} 的尸体爆炸了！")
        else:
            # 爆炸扩散阶段（假设0.5秒扩散完成）
            self.explosion_progress += dt / 0.5
            if self.explosion_progress >= 1.0:
                self.explosion_progress = 1.0
                self.finished = True
            self.current_radius = self.max_radius * self.explosion_progress

class Game:
    """
    主游戏类，负责管理游戏循环、状态、实体和渲染。
    """
    def __init__(self, custom_map=None, monster_generator=None):
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
        self.game_over = False  # 游戏结束标志
        self.corpse_explosions = []  # 尸爆效果列表
        self.active_bucket_rings = []  # 活跃的铁桶圆环列表（性能优化）
        
        # 保存自定义地图和怪物生成函数
        self.custom_map = custom_map
        self.monster_generator = monster_generator if monster_generator else generate_monsters
        
        # # DEBUG: 添加首帧暂停标志
        # self.first_frame_rendered = False
        # self.paused = False
        
        self.load_data()

    def load_data(self):
        """加载所有游戏资源和初始状态"""
        
        # 1. 地图
        self.city_map = CityMap(self.custom_map)
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
        monster_data_list = self.monster_generator(self.city_map, self.current_day)
        
        for data in monster_data_list:
            r, c = data.position
            # 转换为世界像素坐标 (中心)
            x = c * config.TILE_SIZE + config.TILE_SIZE / 2
            y = r * config.TILE_SIZE + config.TILE_SIZE / 2
            
            # 添加随机偏移，避免同一位置的怪物完全重叠
            offset_range = config.TILE_SIZE * 0.3  # 在网格中心附近30%范围内随机
            x += random.uniform(-offset_range, offset_range)
            y += random.uniform(-offset_range, offset_range)
            
            # 先创建怪物精灵以获取半径
            m = MonsterSprite(data, x, y)
            
            # 限制在地图边界内，考虑怪物半径
            map_width, map_height = self.city_map.get_dimensions()
            monster_radius = m.radius if m.radius > 0 else max(m.width, m.height) / 2
            x = max(monster_radius, min(x, map_width * config.TILE_SIZE - monster_radius))
            y = max(monster_radius, min(y, map_height * config.TILE_SIZE - monster_radius))
            
            # 更新怪物位置
            m.pos.x = x
            m.pos.y = y
            m.rect.center = m.pos
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
            
            # Game Over 时的按钮点击
            if event.type == pygame.MOUSEBUTTONDOWN and self.game_over:
                if event.button == 1:  # 左键
                    mouse_pos = pygame.mouse.get_pos()
                    # 检查是否点击了重新开始按钮（在draw方法中定义）
                    if hasattr(self, 'restart_button_rect') and self.restart_button_rect.collidepoint(mouse_pos):
                        self._restart_game()
                    elif hasattr(self, 'retry_button_rect') and self.retry_button_rect.collidepoint(mouse_pos):
                        self._restart_game()
            
            # (Spec IV) 射击（游戏未结束时）
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                if event.button == 1: # 左键点击
                    # print("检测到鼠标左键点击")
                    bullet = self.player.shoot(mouse_world_pos)
                    if bullet:
                        self.all_sprites.add(bullet)
                        self.bullets.add(bullet)
    
    def _restart_game(self):
        """重新开始游戏"""
        print("\n重新开始游戏...")
        self.current_day = 1
        self.game_over = False
        self.corpse_explosions.clear()
        
        # 清空所有精灵组
        self.all_sprites.empty()
        self.monsters.empty()
        self.bullets.empty()
        
        # 重新加载游戏数据
        self.load_data()

    def update(self):
        """更新所有游戏逻辑"""
        
        # 游戏结束后不更新
        if self.game_over:
            return
        
        # 0. 性能优化：预计算光环效果（每帧一次）
        self._precalculate_auras()
        
        # 1. 获取鼠标在世界中的位置，用于玩家朝向
        mouse_world_pos = self.camera.get_mouse_world_pos()

        # 2. 更新实体
        self.player.update(self.dt, mouse_world_pos, self.walls)
        self.monsters.update(self.dt, self.player.pos, self.walls)
        self.bullets.update(self.dt)
        
        # 3. 更新摄像机 (Spec II)
        self.camera.update(self.player)
        
        # 4. 更新尸爆效果
        for explosion in self.corpse_explosions[:]:
            explosion.update(self.dt)
            # 爆炸时检查玩家是否在范围内
            if explosion.is_exploding and not explosion.finished:
                dist = self.player.pos.distance_to(explosion.pos)
                if dist <= explosion.current_radius and not self.player.is_dead:
                    # 只在刚开始爆炸时造成一次伤害
                    if explosion.explosion_progress < 0.1:  # 避免重复伤害
                        self.player.take_damage(explosion.damage, f"{explosion.monster_name}的尸爆")
            
            # 移除完成的爆炸
            if explosion.finished:
                self.corpse_explosions.remove(explosion)

        # 5. 怪物攻击玩家
        if not self.player.is_dead:
            for monster in self.monsters:
                attack_info = monster.start_attack(self.player.pos, self.monsters.sprites(), self)
                if attack_info:
                    # 检查是否是延迟伤害（铁桶圆环）
                    if not attack_info.get('deferred', False):
                        self._handle_monster_attack(attack_info)
                    # 铁桶的伤害由圆环触碰时在MonsterSprite.update中触发
            
            # 检测铁桶圆环触碰（只遍历活跃列表 - 性能优化）
            for monster in self.active_bucket_rings[:]:
                # 检查圆环是否已经结束（ring_animation_timer 归零表示结束）
                if monster.ring_animation_timer <= 0:
                    # 圆环动画结束，从活跃列表移除
                    if monster in self.active_bucket_rings:
                        self.active_bucket_rings.remove(monster)
                    continue
                
                # 只有当圆环开始扩散后才检测碰撞
                if monster.ring_radius <= 0:
                    continue
                
                # 如果还没击中玩家，检测碰撞
                if not monster.ring_has_hit:
                    dist = self.player.pos.distance_to(monster.pos)
                    
                    # 圆环触碰判定：玩家距离 <= 圆环当前半径 + 容差
                    # 容差考虑玩家半径和帧时间
                    tolerance = self.player.radius + 15  # 玩家半径 + 额外容差
                    
                    if dist <= monster.ring_radius + tolerance:
                        # 使用缓存的光环加成计算伤害
                        damage = monster.logic.calculate_damage_with_cache(monster.cached_aura_bonus)
                        armor_ignore = 0  # 铁桶无护甲穿透
                        self.player.take_damage(damage, monster.logic.name, armor_ignore)
                        
                        # 标记已击中，但不结束圆环动画，让它继续扩散
                        monster.ring_has_hit = True
                        # print(f"{monster.logic.name} 的圆环击中了玩家！")
        
        # 6. 碰撞检测 (Spec IV)
        
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
                
                # 铁桶死亡触发尸爆
                if monster_hit.logic.type == 'Bucket':
                    from systems.monsters import config as mcfg
                    explosion_damage = monster_hit.logic.max_hp * mcfg.MONSTER_SKILL_PARAMS['Bucket_Corpse_Explosion_HP_Dmg']
                    explosion = CorpseExplosion(
                        monster_hit.pos.copy(),
                        config.CORPSE_EXPLOSION_RANGE,
                        config.CORPSE_EXPLOSION_DELAY,
                        explosion_damage,
                        monster_hit.logic.name
                    )
                    self.corpse_explosions.append(explosion)
                    print(f"{monster_hit.logic.name} 死亡，将在{config.CORPSE_EXPLOSION_DELAY}秒后爆炸")
                
                monster_hit.kill() # 从所有组中移除
        
        # 7. 检查玩家死亡
        if self.player.is_dead and not self.game_over:
            self.game_over = True
            print("\n=== GAME OVER ===")

        # 8. 游戏循环 (Spec IV)
        if not self.monsters: # 如果怪物组为空
            self.current_day += 1
            self.spawn_wave()
    
    def _precalculate_auras(self):
        """性能优化：预计算所有怪物的光环加成（每帧一次）"""
        # 为每个游荡者计算团结光环加成
        for monster in self.monsters:
            if not monster.logic.is_alive:
                monster.cached_aura_bonus = 0
                continue
                
            if monster.logic.type == 'Wanderer':
                # 计算200px内的其他游荡者数量
                wanderer_count = 0
                for m in self.monsters:
                    if (m != monster and m.logic.is_alive and 
                        m.logic.type == 'Wanderer'):
                        # 使用平方距离避免开方运算
                        dx = monster.pos.x - m.pos.x
                        dy = monster.pos.y - m.pos.y
                        dist_sq = dx * dx + dy * dy
                        if dist_sq <= 200 * 200:  # 200px范围
                            wanderer_count += 1
                
                # 每个附近游荡者提供10%加成
                monster.cached_aura_bonus = wanderer_count * 0.1
            else:
                monster.cached_aura_bonus = 0
    
    def _handle_monster_attack(self, attack_info):
        """处理怪物攻击"""
        armor_ignore = attack_info.get('armor_ignore', 0)
        
        # 跳过延迟伤害（铁桶圆环）
        if attack_info.get('deferred', False):
            return
        
        if attack_info['type'] == 'melee':
            # 近战攻击：直接对玩家造成伤害
            self.player.take_damage(attack_info['damage'], attack_info['attacker_name'], armor_ignore)
        
        elif attack_info['type'] == 'aoe':
            # AoE攻击：检查玩家是否在范围内
            dist = self.player.pos.distance_to(attack_info['attacker_pos'])
            if dist <= attack_info['range']:
                self.player.take_damage(attack_info['damage'], attack_info['attacker_name'], armor_ignore)

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
        
        # 绘制怪物攻击特效（铁桶圆环）
        drawing.draw_monster_attack_effects(self.screen, self.monsters, self.camera)
        
        # 绘制尸爆效果
        drawing.draw_corpse_explosions(self.screen, self.corpse_explosions, self.camera)

        # 3. 绘制 UI (Spec V) - (不跟随摄像机)
        drawing.draw_ui(self.screen, self.player.logic, self.current_day, self.font_main)
        
        # 4. 绘制小地图 (Spec V)
        drawing.draw_minimap(self.screen, self.city_map, self.player, self.monsters, self.camera, self.font_minimap)
        
        # 5. Game Over UI
        if self.game_over:
            drawing.draw_game_over_ui(self.screen, self)

        # 6. 刷新屏幕
        pygame.display.flip()

    def quit(self):
        pygame.quit()
        sys.exit()