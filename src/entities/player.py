# player.py
import pygame
import math
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config
from systems.inventory.player_stats import PlayerLogic
from entities.bullet import Bullet

class Player(pygame.sprite.Sprite):
    """
    玩家精灵类，负责处理输入、移动、碰撞和渲染。
    """
    def __init__(self, world_pos_x, world_pos_y):
        super().__init__()
        
        # 1. 逻辑与属性
        self.logic = PlayerLogic()
        self.logic.calculate_stats([]) # 初始化

        # 2. 位置与物理
        # 使用 Vector2 进行精确的浮点数位置计算
        self.pos = pygame.math.Vector2(world_pos_x, world_pos_y)
        self.vel = pygame.math.Vector2(0, 0)
        self.radius = config.PLAYER_RADIUS
        
        # self.image 是 Pygame 碰撞检测的必需品
        # 我们使用一个透明的 surface，因为我们将自定义绘制
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)

        # 3. 渲染 (Spec III)
        self.angle_rad = 0 # 玩家朝向 (弧度)
        self.color = config.COLOR_GREEN
        self.facing_line_color = config.COLOR_RED

        # 4. 射击冷却和双手射击
        self.last_shot_time = 0
        self.last_shot_hand = 'right'  # 上次射击的手，用于交替
        
        # 5. 受伤状态
        self.is_dead = False

    def update(self, dt, mouse_world_pos, wall_sprites):
        self._get_input()
        self._update_angle(mouse_world_pos)
        self._move_and_collide(dt, wall_sprites)

    def _get_input(self):
        """处理键盘输入，更新速度向量"""
        self.vel.x, self.vel.y = 0, 0
        keys = pygame.key.get_pressed()
        
        # DEBUG: 检查是否有任何键被按下
        # pressed_count = sum(keys)
        # if pressed_count > 0:
        #     print(f"Total keys pressed: {pressed_count}")
        #     print(f"WASD状态: W={keys[pygame.K_w]}, A={keys[pygame.K_a]}, S={keys[pygame.K_s]}, D={keys[pygame.K_d]}")
        
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.vel.y = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.vel.y = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel.x = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel.x = 1

        # 标准化向量，确保斜向移动速度一致
        if self.vel.length() > 0:
            self.vel.normalize_ip()
            # print(f">>> 速度向量设置为: ({self.vel.x:.2f}, {self.vel.y:.2f})")

    def _update_angle(self, mouse_world_pos):
        """(Spec III) 更新玩家朝向，使其指向鼠标位置"""
        dx = mouse_world_pos[0] - self.pos.x
        dy = mouse_world_pos[1] - self.pos.y
        # 使用标准的 atan2(dy, dx)（world coordinates with y increasing downward）
        self.angle_rad = math.atan2(dy, dx)

    def _move_and_collide(self, dt, wall_sprites):
        """(Spec IV) 移动并处理与墙体的碰撞"""
        move_speed = self.logic.total_stats["移速"] # px/s
        
        # DEBUG: 打印移动信息
        # if self.vel.x != 0 or self.vel.y != 0:
        #     print(f">>> 正在移动: speed={move_speed}, dt={dt:.4f}, 位置=({self.pos.x:.1f}, {self.pos.y:.1f})")
        
        # D = 速度 * 时间
        self.pos.x += self.vel.x * move_speed * dt
        self.rect.centerx = self.pos.x
        self._check_collision('x', wall_sprites)
        
        self.pos.y += self.vel.y * move_speed * dt
        self.rect.centery = self.pos.y
        self._check_collision('y', wall_sprites)

    def _check_collision(self, direction, wall_sprites):
        """辅助函数：检测并解决碰撞"""
        hits = pygame.sprite.spritecollide(self, wall_sprites, False)
        if hits:
            if direction == 'x':
                if self.vel.x > 0: # 向右移动
                    self.rect.right = hits[0].rect.left
                if self.vel.x < 0: # 向左移动
                    self.rect.left = hits[0].rect.right
                self.pos.x = self.rect.centerx
            
            if direction == 'y':
                if self.vel.y > 0: # 向下移动
                    self.rect.bottom = hits[0].rect.top
                if self.vel.y < 0: # 向上移动
                    self.rect.top = hits[0].rect.bottom
                self.pos.y = self.rect.centery

    def shoot(self, mouse_world_pos):
        """(Spec IV) 射击，生成子弹对象"""
        
        # 射速检查
        now = pygame.time.get_ticks()
        fire_rate_hz = self.logic.total_stats.get("射速", 1.0) # 每秒次数
        if fire_rate_hz <= 0: return None
        
        cooldown_ms = 1000 / fire_rate_hz
        if now - self.last_shot_time < cooldown_ms:
            return None # 仍在冷却中

        self.last_shot_time = now

        # (Spec IV) 子弹方向由玩家指向鼠标
        dx = mouse_world_pos[0] - self.pos.x
        dy = mouse_world_pos[1] - self.pos.y
        dir_vec = pygame.math.Vector2(dx, dy).normalize()
        
        max_range = self.logic.total_stats.get("射程", 500) # 默认射程
        
        # 随机选择左手或右手（50%概率）
        import random
        use_left_hand = random.random() < 0.5
        
        # 计算左右手的偏移（相对朝向±30度，距离为玩家半径）
        hand_angle_offset = math.radians(30) if use_left_hand else math.radians(-30)
        hand_angle = self.angle_rad + hand_angle_offset
        hand_offset = pygame.math.Vector2(
            math.cos(hand_angle) * self.radius,
            -math.sin(hand_angle) * self.radius  # Pygame y轴向下
        )
        
        # 子弹起始位置 = 玩家位置 + 手的偏移 + 朝向偏移
        start_pos = self.pos + hand_offset + dir_vec * (config.BULLET_RADIUS + 2)
        
        # TODO: 测试用可命中目标数为2，正式游戏从属性获取：self.logic.total_stats.get("穿透", 1) + 1
        hit_count = 2  # 测试用（可以穿透击中2个目标）

        return Bullet(start_pos, dir_vec, max_range, hit_count)
    
    def take_damage(self, damage, damage_source="未知", armor_ignore=0):
        """
        玩家受到伤害
        
        Args:
            damage: 基础伤害值
            damage_source: 伤害来源（用于日志）
            armor_ignore: 护甲穿透比例（0-1），攻击者无视的护甲百分比
        
        Returns:
            float: 实际受到的伤害
        """
        if self.is_dead:
            return 0
        
        # 获取玩家护甲
        base_armor = self.logic.total_stats.get("护甲", 0)
        
        # 应用护甲穿透：实际护甲 = 基础护甲 × (1 - 穿透比例)
        effective_armor = base_armor * (1 - armor_ignore)
        
        # 从player_stats.py导入护甲常数
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'systems', 'inventory'))
        from systems.inventory import config as inv_cfg
        armor_const = getattr(inv_cfg, 'ARMOR_CONSTANT', 100)
        
        # 计算伤害减免：DR = Armor / (Armor + K)
        dr = effective_armor / (effective_armor + armor_const) if (effective_armor + armor_const) > 0 else 0
        
        # 计算实际伤害
        actual_damage = damage * (1 - dr)
        
        # 扣除生命值
        self.logic.current_health -= actual_damage
        
        # Debug日志输出
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        import config as game_config
        if game_config.DEBUG_COMBAT_LOG:
            if armor_ignore > 0:
                print(f"[COMBAT] 玩家受到 {actual_damage:.1f} 点伤害（原始伤害：{damage:.1f}，护甲：{base_armor:.0f}→{effective_armor:.0f}（穿透{armor_ignore*100:.0f}%），减伤：{dr*100:.1f}%）- 来源：{damage_source}", flush=True)
            else:
                print(f"[COMBAT] 玩家受到 {actual_damage:.1f} 点伤害（原始伤害：{damage:.1f}，护甲减伤：{dr*100:.1f}%）- 来源：{damage_source}", flush=True)
            print(f"[COMBAT] 玩家当前生命值：{self.logic.current_health:.1f} / {self.logic.total_stats.get('生命', 0):.1f}", flush=True)
        
        # 检查死亡
        if self.logic.current_health <= 0:
            self.logic.current_health = 0
            self.is_dead = True
            print("玩家死亡！")
        
        return actual_damage