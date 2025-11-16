# camera.py
import pygame
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config

class Camera:
    """
    负责管理世界坐标到屏幕坐标的转换，并保持玩家居中。
    """
    def __init__(self, world_width, world_height):
        # 摄像机偏移量 (camera_x, camera_y)
        # 这是摄像机左上角在 *世界坐标系* 中的位置
        self.camera_rect = pygame.Rect(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        self.world_width = world_width
        self.world_height = world_height

    def update(self, target_sprite):
        """
        更新摄像机偏移量，使其保持玩家位于屏幕中心。
        (Spec II: camera_x = P_player - SCREEN_WIDTH/2)
        """
        # 计算理想的 camera_x, camera_y
        x = target_sprite.rect.centerx - (config.SCREEN_WIDTH / 2)
        y = target_sprite.rect.centery - (config.SCREEN_HEIGHT / 2)

        # 限制摄像机移动范围，防止看到地图外的黑色区域
        x = max(0, min(x, self.world_width - config.SCREEN_WIDTH))
        y = max(0, min(y, self.world_height - config.SCREEN_HEIGHT))

        self.camera_rect.x = x
        self.camera_rect.y = y

    def apply_to_rect(self, world_rect):
        """
        将一个世界坐标的 Rect 转换为屏幕坐标的 Rect。
        (Spec II: P_screen = P_world - camera)
        """
        screen_x = world_rect.x - self.camera_rect.x
        screen_y = world_rect.y - self.camera_rect.y
        return pygame.Rect(screen_x, screen_y, world_rect.width, world_rect.height)

    def apply_to_coords(self, world_x, world_y):
        """
        将世界坐标 (x, y) 转换为屏幕坐标 (x, y)。
        """
        screen_x = world_x - self.camera_rect.x
        screen_y = world_y - self.camera_rect.y
        return screen_x, screen_y

    def get_mouse_world_pos(self):
        """
        将屏幕上的鼠标位置转换为世界坐标。
        """
        mouse_screen_x, mouse_screen_y = pygame.mouse.get_pos()
        mouse_world_x = mouse_screen_x + self.camera_rect.x
        mouse_world_y = mouse_screen_y + self.camera_rect.y
        return mouse_world_x, mouse_world_y