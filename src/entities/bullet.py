# bullet.py
import pygame
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config

class Bullet(pygame.sprite.Sprite):
    """
    (Spec IV) 子弹实体类
    """
    def __init__(self, start_pos_vec, direction_vec, max_range, hit_count=2):
        super().__init__()
        
        self.pos = pygame.math.Vector2(start_pos_vec)
        self.vel = direction_vec * config.BULLET_SPEED
        self.max_range = max_range
        self.distance_traveled = 0
        
        # TODO: 测试用可命中目标数为2，正式游戏应该从玩家属性获取，默认为1
        self.hit_count = hit_count  # 剩余可命中目标数（2表示可以穿透击中2个目标）
        self.hit_monsters = set()  # 已命中的怪物集合（防止同一怪物被命中多次）
        
        self.radius = config.BULLET_RADIUS
        self.color = config.BULLET_COLOR

        # Pygame 碰撞检测
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        # 在 image 中心的 (radius, radius) 处绘制
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        """更新子弹位置并检查生命周期"""
        
        # 1. 移动
        move_distance = self.vel.length() * dt
        self.pos += self.vel * dt
        self.rect.center = self.pos
        
        # 2. 检查射程
        self.distance_traveled += move_distance
        if self.distance_traveled > self.max_range:
            self.kill() # (Spec IV) 超射程，销毁