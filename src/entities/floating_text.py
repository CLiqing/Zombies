# floating_text.py
import pygame

class FloatingText:
    """浮动文字效果，用于显示BLOCK、MISS等提示"""
    
    def __init__(self, text, pos, color, duration=1.0, font_size=20):
        """
        Args:
            text: 显示的文字
            pos: 初始位置 (x, y)
            color: 文字颜色 (R, G, B)
            duration: 持续时间（秒）
            font_size: 字体大小
        """
        self.text = text
        self.pos = pygame.math.Vector2(pos[0], pos[1])
        self.color = color
        self.duration = duration
        self.timer = 0
        self.finished = False
        
        # 向上飘动
        self.velocity_y = -50  # 向上50px/s
        
        # 渲染文字
        self.font = pygame.font.Font(None, font_size)
        self.surface = self.font.render(text, True, color)
        self.rect = self.surface.get_rect(center=(self.pos.x, self.pos.y))
    
    def update(self, dt):
        """更新浮动文字状态"""
        if self.finished:
            return
        
        self.timer += dt
        
        # 向上飘动
        self.pos.y += self.velocity_y * dt
        self.rect.center = (self.pos.x, self.pos.y)
        
        # 检查是否结束
        if self.timer >= self.duration:
            self.finished = True
    
    def get_alpha(self):
        """获取当前透明度（0-255）"""
        # 最后0.3秒淡出
        fade_start = self.duration - 0.3
        if self.timer >= fade_start:
            fade_progress = (self.timer - fade_start) / 0.3
            return int(255 * (1.0 - fade_progress))
        return 255
