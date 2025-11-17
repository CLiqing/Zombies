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
from entities.floating_text import FloatingText
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
        self.has_damaged = False  # 是否已造成伤害
    
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
        
        # 加载精灵图像
        self.sprite_images = self._load_sprite_images()
        
        # 游戏状态
        self.current_day = 1
        self.game_over = False  # 游戏结束标志
        self.corpse_explosions = []  # 尸爆效果列表
        self.active_bucket_rings = []  # 活跃的铁桶圆环列表（性能优化）
        self.floating_texts = []  # 浮动文字列表（BLOCK、MISS等）
        
        # 保存自定义地图和怪物生成函数
        self.custom_map = custom_map
        self.monster_generator = monster_generator if monster_generator else generate_monsters
        
        # # DEBUG: 添加首帧暂停标志
        # self.first_frame_rendered = False
        # self.paused = False
        
        self.load_data()

    def _load_sprite_images(self):
        """加载精灵图片资源，返回名称->Surface字典（如果找不到文件则返回空字典）

        加载目录: project_root/assets/sprites
        键使用文件名（不含扩展名），例如 'player', 'wanderer', 'bucket-烈爆'。
        """
        sprites = {}
        # assets 位于工程根目录下（src/core -> src -> project root），因此向上两级到达项目根
        sprites_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'sprites')
        sprites_dir = os.path.normpath(sprites_dir)

        if os.path.isdir(sprites_dir):
            for fname in os.listdir(sprites_dir):
                if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    continue
                key = os.path.splitext(fname)[0]
                path = os.path.join(sprites_dir, fname)
                try:
                    img = pygame.image.load(path).convert_alpha()
                    sprites[key] = img
                except Exception as e:
                    print(f"Warning: failed to load sprite '{path}': {e}")
        else:
            print(f"Warning: sprites directory not found: {sprites_dir}")

        return sprites

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
        
        # 2.5. 更新浮动文字
        from entities.floating_text import FloatingText
        for text in self.floating_texts[:]:
            text.update(self.dt)
            if text.finished:
                self.floating_texts.remove(text)
        
        # 2.6. 更新游荡者复活倒计时
        for monster in self.monsters:
            if monster.logic.is_reviving:
                monster.logic.revive_timer -= self.dt
                if monster.logic.revive_timer <= 0:
                    # 复活！
                    monster.logic.is_reviving = False
                    monster.logic.is_alive = True
                    monster.logic.current_hp = monster.logic.max_hp
                    if config.DEBUG_COMBAT_LOG:
                        print(f"[COMBAT] {monster.logic.name} 复活了！HP: {monster.logic.current_hp:.1f}/{monster.logic.max_hp}", flush=True)
        
        # 2.7. 更新精英技能状态
        current_time = pygame.time.get_ticks() / 1000.0
        for monster in self.monsters:
            # 呼唤者：检查是否可以召唤
            if hasattr(monster.logic, 'elite_type') and monster.logic.elite_type == 'summoner':
                if monster.logic.can_summon(current_time) and len(self.monsters) < 500:
                    # 检查玩家是否在威胁范围内
                    from systems.monsters import config as mcfg
                    threat_range = mcfg.MONSTER_SKILL_PARAMS['Wanderer_Summoner_Range']
                    dist = monster.pos.distance_to(self.player.pos)
                    if dist <= threat_range:
                        summon_count = monster.logic.perform_summon(current_time)
                        # 在呼唤者附近随机生成小怪
                        for _ in range(summon_count):
                            if len(self.monsters) >= 500:
                                break
                            # 随机偏移位置，确保不超出地图边界
                            import random
                            offset_x = random.randint(-50, 50)
                            offset_y = random.randint(-50, 50)
                            spawn_x = max(50, min(monster.pos.x + offset_x, config.WORLD_WIDTH - 50))
                            spawn_y = max(50, min(monster.pos.y + offset_y, config.WORLD_HEIGHT - 50))
                            spawn_pos = pygame.Vector2(spawn_x, spawn_y)
                            
                            # 创建普通游荡者
                            from systems.monsters.monster_factory import create_monster
                            from entities.monster_sprite import MonsterSprite
                            new_monster_logic = create_monster("Wanderer", monster.logic.level - 20, False, (0, 0))
                            new_monster = MonsterSprite(new_monster_logic, spawn_pos)
                            self.monsters.add(new_monster)
                            
                            if config.DEBUG_COMBAT_LOG:
                                print(f"[COMBAT] {monster.logic.name} 召唤了 {new_monster_logic.name}！", flush=True)
            
            # 不死者：更新残躯状态
            if hasattr(monster.logic, 'elite_type') and monster.logic.elite_type == 'undying':
                if monster.logic.update_undying(current_time):
                    # 残躯结束，真正死亡
                    monster.kill()
        
        # 3. 更新摄像机 (Spec II)
        self.camera.update(self.player)
        
        # 4. 更新尸爆效果
        for explosion in self.corpse_explosions[:]:
            explosion.update(self.dt)
            # 爆炸时检查玩家是否在范围内
            if explosion.is_exploding and not explosion.finished and not explosion.has_damaged:
                dist = self.player.pos.distance_to(explosion.pos)
                if dist <= explosion.current_radius and not self.player.is_dead:
                    # 使用has_damaged标志确保伤害只造成一次
                    self.player.take_damage(explosion.damage, f"{explosion.monster_name}的尸爆")
                    explosion.has_damaged = True
            
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
        
        # 子弹 vs 怪物 (使用穿透机制)
        from entities.floating_text import FloatingText

        # 使用圆形碰撞检测：避免细长的食尸鬼在未旋转 rect 时产生不自然的视觉
        def _monster_bullet_collide(monster_sprite, bullet_sprite):
            # 使用 monster_sprite.collision_radius（已在 MonsterSprite._set_dimensions 中设置）
            br = getattr(bullet_sprite, 'radius', None)
            if getattr(monster_sprite.logic, 'type', None) == 'Ghoul' and br is not None:
                # 对于 Ghoul 使用旋转矩形检测：将子弹点旋转到怪物局部坐标系后做 AABB + 半径检测
                # 交换 width/height 保证短边朝向前方
                w = getattr(monster_sprite, 'height', 0)
                h = getattr(monster_sprite, 'width', 0)
                angle = monster_sprite.angle_rad
                # 将子弹相对于怪物中心的向量旋转 -angle
                dx = bullet_sprite.pos.x - monster_sprite.pos.x
                dy = bullet_sprite.pos.y - monster_sprite.pos.y
                ca = math.cos(-angle)
                sa = math.sin(-angle)
                lx = dx * ca - dy * sa
                ly = dx * sa + dy * ca
                # AABB 检查：最近点
                half_w = w / 2.0
                half_h = h / 2.0
                nearest_x = max(-half_w, min(lx, half_w))
                nearest_y = max(-half_h, min(ly, half_h))
                ddx = lx - nearest_x
                ddy = ly - nearest_y
                return (ddx*ddx + ddy*ddy) <= (br * br)
            else:
                mr = getattr(monster_sprite, 'collision_radius', None)
                if mr is None or br is None:
                    # 回退到 rect 碰撞
                    return monster_sprite.rect.colliderect(bullet_sprite.rect)
                dx = monster_sprite.pos.x - bullet_sprite.pos.x
                dy = monster_sprite.pos.y - bullet_sprite.pos.y
                return (dx*dx + dy*dy) <= (mr + br) * (mr + br)

        hits = pygame.sprite.groupcollide(self.monsters, self.bullets, False, False, collided=_monster_bullet_collide)
        
        for monster_hit, bullets in hits.items():
            # 跳过正在复活的游荡者
            if monster_hit.logic.is_reviving:
                continue
            
            for bullet in bullets:
                # 检查这个子弹是否已经命中过这个怪物（跨帧检查）
                if monster_hit in bullet.hit_monsters:
                    continue  # 已经命中过，跳过
                
                # 记录命中
                bullet.hit_monsters.add(monster_hit)
                
                # 获取玩家攻击力
                damage = self.player.logic.total_stats.get("攻击力", 10)
                
                # 调用怪物受伤方法
                result = monster_hit.logic.take_damage(damage, "玩家")
                
                # 处理荆棘守卫反弹
                if result.get('reflected_damage', 0) > 0:
                    # 反弹伤害给玩家
                    self.player.take_damage(result['reflected_damage'], f"{monster_hit.logic.name}的荆棘反弹")
                    # 添加反弹文字提示
                    text_pos = (monster_hit.pos.x, monster_hit.pos.y - 50)
                    text = FloatingText("REFLECT", text_pos, (255, 100, 100), 1.0, 24)
                    self.floating_texts.append(text)
                
                # 处理格挡
                if result['blocked']:
                    text_pos = (monster_hit.pos.x, monster_hit.pos.y - 30)
                    text = FloatingText("BLOCK", text_pos, (255, 255, 0), 1.0, 24)  # 黄色
                    self.floating_texts.append(text)
                
                # 处理闪避
                if result['evaded']:
                    text_pos = (monster_hit.pos.x, monster_hit.pos.y - 30)
                    text = FloatingText("MISS", text_pos, (255, 255, 255), 1.0, 24)  # 白色
                    self.floating_texts.append(text)
                
                # 处理死亡
                if result['died']:
                    # 铁桶死亡触发尸爆
                    if monster_hit.logic.type == 'Bucket':
                        from systems.monsters import config as mcfg
                        explosion_damage = monster_hit.logic.max_hp * mcfg.MONSTER_SKILL_PARAMS['Bucket_Corpse_Explosion_HP_Dmg']
                        
                        # 庞然：尸爆范围增加
                        explosion_range = config.CORPSE_EXPLOSION_RANGE
                        if hasattr(monster_hit.logic, 'get_range_bonus'):
                            explosion_range += monster_hit.logic.get_range_bonus()
                        
                        explosion = CorpseExplosion(
                            monster_hit.pos.copy(),
                            explosion_range,
                            config.CORPSE_EXPLOSION_DELAY,
                            explosion_damage,
                            monster_hit.logic.name
                        )
                        self.corpse_explosions.append(explosion)
                    
                    # 游荡者复活：不立即移除
                    if not result['will_revive']:
                        monster_hit.kill()  # 从所有组中移除
                
                # 处理子弹命中计数
                if result['evaded']:
                    # 闪避：不消耗命中次数，子弹继续飞行
                    pass
                elif result['blocked']:
                    # 格挡：不消耗命中次数，子弹继续飞行
                    pass
                else:
                    # 实际命中：消耗1次命中次数
                    bullet.hit_count -= 1
                    if bullet.hit_count <= 0:
                        bullet.kill()  # 命中次数耗尽，销毁子弹
        
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
        from systems.monsters import config as mcfg
        
        # 为每个怪物计算光环加成
        for monster in self.monsters:
            if not monster.logic.is_alive:
                monster.cached_aura_bonus = 0
                monster.logic.cached_armor_bonus = 0
                continue
                
            if monster.logic.type == 'Wanderer':
                # 团结光环：计算200px内的其他游荡者数量
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
                
                # 每个附近游荡者提供10%攻击加成
                monster.cached_aura_bonus = wanderer_count * 0.1
            else:
                monster.cached_aura_bonus = 0
            
            # 铁甲光环：计算200px内的所有铁桶数量（包括自己）
            armor_aura_range = mcfg.MONSTER_SKILL_PARAMS['Bucket_Armor_Aura_Range']
            armor_per_bucket = mcfg.MONSTER_SKILL_PARAMS['Bucket_Armor_Aura']
            bucket_count = 0
            
            for m in self.monsters:
                if m.logic.is_alive and m.logic.type == 'Bucket':
                    dx = monster.pos.x - m.pos.x
                    dy = monster.pos.y - m.pos.y
                    dist_sq = dx * dx + dy * dy
                    if dist_sq <= armor_aura_range * armor_aura_range:
                        bucket_count += 1
            
            # 每个附近铁桶提供+10护甲
            monster.logic.cached_armor_bonus = bucket_count * armor_per_bucket
    
    def _handle_monster_attack(self, attack_info):
        """处理怪物攻击"""
        armor_ignore = attack_info.get('armor_ignore', 0)
        
        # 跳过延迟伤害（铁桶圆环）
        if attack_info.get('deferred', False):
            return
        
        if attack_info['type'] == 'melee':
            # 近战攻击：直接对玩家造成伤害
            actual_damage = self.player.take_damage(attack_info['damage'], attack_info['attacker_name'], armor_ignore)
            
            # 处理暴击显示
            if attack_info.get('is_crit', False):
                # 找到攻击者以显示暴击文字
                for monster in self.monsters:
                    if monster.logic.name == attack_info['attacker_name']:
                        text_pos = (monster.pos.x, monster.pos.y - 40)
                        text = FloatingText("CRIT!", text_pos, (255, 50, 50), 1.2, 28)
                        self.floating_texts.append(text)
                        break
            
            # 处理吸血
            lifesteal_factor = attack_info.get('lifesteal_factor', 0)
            if lifesteal_factor > 0 and actual_damage > 0:
                heal_amount = actual_damage * lifesteal_factor
                # 找到攻击者并治疗
                for monster in self.monsters:
                    if monster.logic.name == attack_info['attacker_name']:
                        old_hp = monster.logic.current_hp
                        monster.logic.current_hp = min(monster.logic.current_hp + heal_amount, monster.logic.max_hp)
                        healed = monster.logic.current_hp - old_hp
                        if healed > 0 and config.DEBUG_COMBAT_LOG:
                            print(f"[COMBAT] {monster.logic.name} 吸血回复 {healed:.1f} HP！", flush=True)
                        break
        
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
            drawing.draw_monster(self.screen, monster, self.camera, self.sprite_images)
            
        # 绘制玩家
        drawing.draw_player(self.screen, self.player, self.camera, self.sprite_images)
        
        # 绘制子弹 (覆盖在其他实体之上)
        for bullet in self.bullets:
            # 子弹有自己的 image，可以直接 blit
            self.screen.blit(bullet.image, self.camera.apply_to_rect(bullet.rect))

        # 绘制碰撞调试图形（玩家/怪物/子弹） - 通过 config.DEBUG_DRAW_COLLISIONS 控制
        try:
            import config as game_config
        except Exception:
            game_config = config
        if getattr(game_config, 'DEBUG_DRAW_COLLISIONS', False):
            drawing.draw_collision_shapes(self.screen, self.player, self.monsters, self.bullets, self.camera)

        # 绘制树木 (覆盖在实体之上，实现遮挡效果)
        drawing.draw_trees(self.screen, self.city_map, self.camera, self.tile_images)
        
        # 绘制怪物攻击特效（铁桶圆环）
        drawing.draw_monster_attack_effects(self.screen, self.monsters, self.camera)
        
        # 绘制尸爆效果
        drawing.draw_corpse_explosions(self.screen, self.corpse_explosions, self.camera, self.sprite_images)
        
        # 绘制浮动文字（BLOCK、MISS等）
        for text in self.floating_texts:
            screen_x, screen_y = self.camera.apply_to_coords(text.pos.x, text.pos.y)
            # 应用透明度
            alpha = text.get_alpha()
            if alpha < 255:
                text.surface.set_alpha(alpha)
            self.screen.blit(text.surface, (screen_x - text.rect.width // 2, screen_y - text.rect.height // 2))

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