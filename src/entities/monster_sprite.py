# monster_sprite.py
import pygame
import math
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config
from systems.monsters.monster_logic import Monster

class MonsterSprite(pygame.sprite.Sprite):
    """
    怪物精灵类，包装 Monster 逻辑类，处理 AI、移动和渲染。
    """
    def __init__(self, monster_data_logic, world_pos_x, world_pos_y):
        super().__init__()
        
        # 1. 逻辑
        self.logic = monster_data_logic
        
        # 2. 位置与物理
        self.pos = pygame.math.Vector2(world_pos_x, world_pos_y)
        self.vel = pygame.math.Vector2(0, 0)
        
        # 3. 尺寸与渲染 (Spec III)
        self.radius = 0
        self.width = 0
        self.height = 0
        self._set_dimensions()
        
        # (Spec III) 三角形/圆形的朝向
        self.angle_rad = 0 
        
        # 4. AI 状态变量
        # 监控范围（超过此距离则使用巡逻逻辑）
        self.detection_range = 400  # 400像素
        
        # 攻击状态
        self.last_attack_time = 0  # 上次攻击时间
        self.attack_state = 'idle'  # 'idle', 'attacking', 'knockback'
        self.knockback_timer = 0  # 后退计时器
        self.knockback_distance = 0  # 需要后退的距离
        self.knockback_direction = pygame.math.Vector2(0, 0)  # 后退方向
        
        # 铁桶圆环攻击
        self.ring_animation_timer = 0  # 圆环动画计时器
        self.ring_radius = 0  # 当前圆环半径
        self.ring_has_hit = False  # 圆环是否已击中玩家
        
        # 食尸鬼迅扑状态
        self.is_dashing = False  # 是否在迅扑
        self.dash_accel_timer = 0  # 迅扑加速计时器
        self.dash_speed_mult = 1.0  # 当前速度倍数
        self.has_attacked_after_dash = False  # 迅扑后是否已攻击
        self.last_dash_time = -999  # 上次迅扑时间（初始化为很久之前）
        self.dash_cooldown = 5.0  # 迅扑冷却时间（秒）
        
        # 游荡者：随机游荠状态
        self.wander_timer = 0
        self.wander_direction = pygame.math.Vector2(0, 0)
        self.wander_change_interval = 2.0  # 每2秒改变一次方向
        
        # 食尸鬼：椭圆巡逻状态
        self.patrol_center = pygame.math.Vector2(world_pos_x, world_pos_y)  # 巡逻中心
        self.patrol_angle = 0  # 当前角度
        self.patrol_speed = 1.0  # 巡逻角速度 (弧度/秒)
        self.patrol_radius_x = 200  # 椭圆半长轴（增加）
        self.patrol_radius_y = 60   # 椭圆半短轴（减少，更扁平）
        
        # 性能优化：缓存的光环加成
        self.cached_aura_bonus = 0  # 由Game._precalculate_auras()每帧更新
        
        # 5. Pygame 碰撞 Rect
        if self.radius > 0:
            size = self.radius * 2
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        else:
            self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        self.rect = self.image.get_rect(center=self.pos)

    def _set_dimensions(self):
        """根据 Spec III 设置实体的尺寸"""
        t = self.logic.type
        e = self.logic.is_elite
        skills = self.logic.elite_skills

        if t == 'Wanderer':
            self.radius = config.WANDERER_ELITE_RADIUS if e else config.WANDERER_RADIUS
        
        elif t == 'Bucket':
            self.radius = config.BUCKET_ELITE_RADIUS if e else config.BUCKET_RADIUS
        
        elif t == 'Ghoul':
            if e and '飞天' in skills:
                self.width, self.height = config.GHOUL_ELITE_FLYING_SIZE
            elif e:
                self.width, self.height = config.GHOUL_ELITE_SIZE
            else:
                self.width, self.height = config.GHOUL_SIZE

    def update(self, dt, player_pos, wall_sprites):
        """更新怪物AI和位置"""
        import random
        
        # 处理后退硬直状态
        if self.attack_state == 'knockback':
            self._update_knockback(dt, wall_sprites)
            return  # 后退期间不做其他更新
        
        # 处理铁桶圆环动画
        if self.logic.type == 'Bucket' and self.ring_animation_timer > 0:
            self.ring_animation_timer -= dt
            # 圆环扩散（从0到attack_range，耗时attack_cooldown）
            progress = 1.0 - (self.ring_animation_timer / self.logic.attack_cooldown)
            self.ring_radius = self.logic.attack_range * min(progress, 1.0)
            
            # 圆环动画结束
            if self.ring_animation_timer <= 0:
                self.ring_radius = 0
                self.ring_has_hit = False
        
        # 计算到玩家的距离
        dist_to_player = self.pos.distance_to(player_pos)
        
        # 食尸鬼迅扑逻辑
        if self.logic.type == 'Ghoul':
            self._update_dash(dt, dist_to_player)
        
        # 根据怪物类型和距离选择AI行为
        if dist_to_player <= self.detection_range:
            # 在监控范围内：所有怪物都追踪玩家
            direction = player_pos - self.pos
            if direction.length() > 0:
                direction.normalize_ip()
                # 修复：pygame坐标系y向下为正，atan2参数应该是(dy, dx)
                self.angle_rad = math.atan2(direction.y, direction.x)
            
            BASE_MONSTER_SPEED = 50
            move_speed = BASE_MONSTER_SPEED * self.logic.movement_speed * self.dash_speed_mult
            
            # 所有怪物：保持最小距离，避免和玩家重合
            player_radius = config.PLAYER_RADIUS
            monster_radius = self.radius if hasattr(self, 'radius') and self.radius > 0 else max(self.width, self.height) / 2
            min_distance = player_radius + monster_radius + 10
            
            if self.logic.type in ['Wanderer', 'Ghoul']:
                # 游荡者和食尸鬼：攻击冷却期间保持距离
                current_time = pygame.time.get_ticks() / 1000.0
                time_since_attack = current_time - self.last_attack_time
                
                # 如果在攻击冷却期间，并且距离玩家很近，则停止移动
                if time_since_attack < self.logic.attack_cooldown:
                    if dist_to_player <= min_distance:
                        self.vel = pygame.math.Vector2(0, 0)
                        return  # 停止移动
            
            elif self.logic.type == 'Bucket':
                # 铁桶：始终保持最小距离
                if dist_to_player <= min_distance:
                    self.vel = pygame.math.Vector2(0, 0)
                    return  # 停止移动
            
            self.vel = direction * move_speed
            
        else:
            # 超出监控范围：根据类型使用不同AI
            if self.logic.type == 'Bucket':
                # 铁桶：不移动
                self.vel = pygame.math.Vector2(0, 0)
                
            elif self.logic.type == 'Wanderer':
                # 游荡者：完全随机游荠
                self.wander_timer += dt
                if self.wander_timer >= self.wander_change_interval:
                    self.wander_timer = 0
                    # 随机选择新方向
                    angle = random.uniform(0, 2 * math.pi)
                    self.wander_direction = pygame.math.Vector2(
                        math.cos(angle),
                        math.sin(angle)
                    )
                    self.angle_rad = angle
                
                BASE_MONSTER_SPEED = 50
                move_speed = BASE_MONSTER_SPEED * self.logic.movement_speed * 0.5  # 游荠速度减半
                self.vel = self.wander_direction * move_speed
                
            elif self.logic.type == 'Ghoul':
                # 食尸鬼：椭圆巡逻
                self.patrol_angle += self.patrol_speed * dt
                if self.patrol_angle > 2 * math.pi:
                    self.patrol_angle -= 2 * math.pi
                
                # 计算椭圆上的目标位置
                target_x = self.patrol_center.x + self.patrol_radius_x * math.cos(self.patrol_angle)
                target_y = self.patrol_center.y + self.patrol_radius_y * math.sin(self.patrol_angle)
                target_pos = pygame.math.Vector2(target_x, target_y)
                
                # 朝向目标移动
                direction = target_pos - self.pos
                if direction.length() > 5:  # 避免在目标附近震荡
                    direction.normalize_ip()
                    # 修复：pygame坐标系y向下为正，atan2参数应该是(dy, dx)
                    self.angle_rad = math.atan2(direction.y, direction.x)
                    
                    BASE_MONSTER_SPEED = 50
                    move_speed = BASE_MONSTER_SPEED * self.logic.movement_speed * 0.7  # 巡逻速度适中
                    self.vel = direction * move_speed
                else:
                    self.vel = pygame.math.Vector2(0, 0)

        # 移动和碰撞 (与 Player 相同)
        self.pos.x += self.vel.x * dt
        self.rect.centerx = self.pos.x
        self._check_collision('x', wall_sprites)
        
        self.pos.y += self.vel.y * dt
        self.rect.centery = self.pos.y
        self._check_collision('y', wall_sprites)

    def _check_collision(self, direction, wall_sprites):
        """辅助函数：检测并解决碰撞"""
        hits = pygame.sprite.spritecollide(self, wall_sprites, False)
        if hits:
            # 食尸鬼可以穿过河流
            if self.logic.type == 'Ghoul' and hits[0].tile_type == '~':
                return  # 忽略河流碰撞
            
            # 其他怪物或墙体碰撞：处理碰撞
            if direction == 'x':
                if self.vel.x > 0: self.rect.right = hits[0].rect.left
                if self.vel.x < 0: self.rect.left = hits[0].rect.right
                self.pos.x = self.rect.centerx
                
                # 游荡者撞墙后改变方向，避免鬼打墙
                if self.logic.type == 'Wanderer':
                    self.wander_timer = self.wander_change_interval  # 立即触发方向改变
            
            if direction == 'y':
                if self.vel.y > 0: self.rect.bottom = hits[0].rect.top
                if self.vel.y < 0: self.rect.top = hits[0].rect.bottom
                self.pos.y = self.rect.centery
                
                # 游荡者撞墙后改变方向，避免鬼打墙
                if self.logic.type == 'Wanderer':
                    self.wander_timer = self.wander_change_interval  # 立即触发方向改变
    
    def _update_dash(self, dt, dist_to_player):
        """更新食尸鬼的迅扑状态"""
        current_time = pygame.time.get_ticks() / 1000.0
        
        # 触发迅扑：在300-500px范围内，且不在冷却中
        if not self.is_dashing and config.GHOUL_DASH_MIN_RANGE <= dist_to_player <= config.GHOUL_DASH_MAX_RANGE:
            # 检查冷却时间
            if current_time - self.last_dash_time >= self.dash_cooldown:
                self.is_dashing = True
                self.dash_accel_timer = 0
                self.dash_speed_mult = 1.0
                self.has_attacked_after_dash = False
                self.last_dash_time = current_time
                # print(f"{self.logic.name} 发动了迅扑！")
        
        # 迅扑加速阶段
        if self.is_dashing:
            if self.dash_accel_timer < config.GHOUL_DASH_ACCEL_TIME:
                # 0.5秒内加速到3倍
                self.dash_accel_timer += dt
                progress = min(self.dash_accel_timer / config.GHOUL_DASH_ACCEL_TIME, 1.0)
                self.dash_speed_mult = 1.0 + (config.GHOUL_DASH_SPEED_MULT - 1.0) * progress
            else:
                # 保持3倍速度
                self.dash_speed_mult = config.GHOUL_DASH_SPEED_MULT
    
    def _update_knockback(self, dt, wall_sprites):
        """更新后退硬直状态"""
        if self.knockback_distance <= 0:
            self.attack_state = 'idle'
            self.vel = pygame.math.Vector2(0, 0)
            return
        
        # 计算本帧后退距离
        move_dist = config.MONSTER_KNOCKBACK_SPEED * dt
        move_dist = min(move_dist, self.knockback_distance)
        
        # 移动
        old_pos = self.pos.copy()
        self.pos += self.knockback_direction * move_dist
        self.rect.center = self.pos
        
        # 检查碰撞
        hits = pygame.sprite.spritecollide(self, wall_sprites, False)
        if hits:
            # 碰到墙壁，停止后退
            self.pos = old_pos
            self.rect.center = self.pos
            self.knockback_distance = 0
            self.attack_state = 'idle'
            print(f"{self.logic.name} 后退时撞到墙壁")
        else:
            self.knockback_distance -= move_dist
    
    def start_attack(self, player_pos, all_monsters, game=None):
        """
        开始攻击动作
        
        Args:
            player_pos: 玩家位置
            all_monsters: 所有怪物列表（用于计算光环）
            game: Game实例（用于添加铁桶到活跃圆环列表）
        
        Returns:
            dict or None: 攻击信息，如果无法攻击则返回None
        """
        current_time = pygame.time.get_ticks() / 1000.0
        
        # 检查是否可以攻击（传入世界坐标）
        if not self.logic.can_attack(self.pos, player_pos, current_time, self.last_attack_time):
            return None
        
        # 检查距离（使用世界坐标）
        dist = self.pos.distance_to(player_pos)
        if dist > self.logic.attack_range:
            return None
        
        # 记录攻击时间
        self.last_attack_time = current_time
        
        # 性能优化：使用缓存的光环加成计算伤害
        # 只为兼容旧代码保留nearby_monsters计算
        nearby_monsters = []
        for m in all_monsters:
            if m == self or not m.logic.is_alive:
                continue
            m_dist = self.pos.distance_to(m.pos)
            nearby_monsters.append((m.logic, m_dist))
        
        # 执行攻击
        attack_info = self.logic.perform_attack(player_pos, nearby_monsters)
        attack_info['attacker_pos'] = self.pos.copy()  # 添加攻击者位置
        
        # 性能优化：使用缓存的光环加成计算伤害（所有怪物类型）
        attack_info['damage'] = self.logic.calculate_damage_with_cache(self.cached_aura_bonus)
        
        # print(f"{self.logic.name} 发动了攻击！")
        
        # 根据怪物类型处理攻击后动作
        if self.logic.type == 'Bucket':
            # 铁桶：启动圆环动画
            self.ring_animation_timer = self.logic.attack_cooldown
            self.ring_radius = 0
            self.ring_has_hit = False
            self.attack_state = 'attacking'
            # 铁桶的AoE伤害由圆环触碰判定，不在这里直接造成伤害
            attack_info['deferred'] = True  # 标记为延迟伤害
            
            # 性能优化：添加到活跃圆环列表
            if game and self not in game.active_bucket_rings:
                game.active_bucket_rings.append(self)
        else:
            # 游荡者和食尸鬼：后退
            self.attack_state = 'knockback'
            direction = self.pos - player_pos
            if direction.length() > 0:
                direction.normalize_ip()
            self.knockback_direction = direction
            self.knockback_distance = self.logic.attack_range
            
            # 食尸鬼：迅扑后首次攻击，结束迅扑状态
            if self.logic.type == 'Ghoul' and self.is_dashing:
                self.has_attacked_after_dash = True
                self.is_dashing = False
                self.dash_speed_mult = 1.0
                # print(f"{self.logic.name} 迅扑攻击命中，结束迅扑状态")
        
        return attack_info