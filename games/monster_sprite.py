# monster_sprite.py
import pygame
import math
import settings
# 导入您提供的 monster_logic
from monsters.monster_logic import Monster

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
        
        # 4. Pygame 碰撞 Rect
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
            self.radius = settings.WANDERER_ELITE_RADIUS if e else settings.WANDERER_RADIUS
        
        elif t == 'Bucket':
            self.radius = settings.BUCKET_ELITE_RADIUS if e else settings.BUCKET_RADIUS
        
        elif t == 'Ghoul':
            if e and '飞天' in skills:
                self.width, self.height = settings.GHOUL_ELITE_FLYING_SIZE
            elif e:
                self.width, self.height = settings.GHOUL_ELITE_SIZE
            else:
                self.width, self.height = settings.GHOUL_SIZE

    def update(self, dt, player_pos, wall_sprites):
        # 简单的 AI：朝向玩家移动
        direction = player_pos - self.pos
        if direction.length() > 0:
            direction.normalize_ip()
            
            # (Spec III) 更新朝向
            self.angle_rad = math.atan2(-direction.y, direction.x)

        # 速度基于 monster_logic 中的 'movement_speed' (通常是 1.0 或 1.1)
        # 我们需要一个基础速度
        BASE_MONSTER_SPEED = 50 # 假设基础速度为 50 px/s
        move_speed = BASE_MONSTER_SPEED * self.logic.movement_speed
        
        self.vel = direction * move_speed

        # 移动和碰撞 (与 Player 相同)
        self.pos.x += self.vel.x * dt
        self.rect.centerx = self.pos.x
        self._check_collision('x', wall_sprites)
        
        self.pos.y += self.vel.y * dt
        self.rect.centery = self.pos.y
        self._check_collision('y', wall_sprites)

    def _check_collision(self, direction, wall_sprites):
        """辅助函数：检测并解决碰撞"""
        # 注意：食尸鬼 Ghoul 可以穿过河流 '~'
        # 玩家的碰撞器包含了 '#' 和 '~'
        # 我们需要一个只包含 '#' 的碰撞组给食尸鬼
        # (简化：暂时让所有怪物都不能穿墙)
        
        hits = pygame.sprite.spritecollide(self, wall_sprites, False)
        if hits:
            # (TODO: 检查 self.logic.type == 'Ghoul' 并且
            #  hits[0].tile_type == '~'，如果是则忽略碰撞)
            
            if direction == 'x':
                if self.vel.x > 0: self.rect.right = hits[0].rect.left
                if self.vel.x < 0: self.rect.left = hits[0].rect.right
                self.pos.x = self.rect.centerx
            
            if direction == 'y':
                if self.vel.y > 0: self.rect.bottom = hits[0].rect.top
                if self.vel.y < 0: self.rect.top = hits[0].rect.bottom
                self.pos.y = self.rect.centery