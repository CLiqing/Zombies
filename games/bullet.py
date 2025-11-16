# bullet.py
import pygame
import settings

class Bullet(pygame.sprite.Sprite):
    """
    (Spec IV) 子弹实体类
    """
    def __init__(self, start_pos_vec, direction_vec, max_range):
        super().__init__()
        
        self.pos = pygame.math.Vector2(start_pos_vec)
        self.vel = direction_vec * settings.BULLET_SPEED
        self.max_range = max_range
        self.distance_traveled = 0
        
        self.radius = settings.BULLET_RADIUS
        self.color = settings.BULLET_COLOR

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