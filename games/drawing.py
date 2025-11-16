# drawing.py
import pygame
import math
import settings

# --- 1. 地图与贴图加载 ---

def load_tile_images():
    """
    (Spec V) 加载地图图块。
    由于没有 .png 文件，我们创建彩色的 Surface 作为占位符。
    """
    tiles = {}
    TS = (settings.TILE_SIZE, settings.TILE_SIZE)

    # .: road.png (棕色)
    tiles['.'] = pygame.Surface(TS)
    tiles['.'].fill(settings.COLOR_BROWN)
    
    # ~: river.png (深蓝)
    tiles['~'] = pygame.Surface(TS)
    tiles['~'].fill(settings.COLOR_DARK_BLUE)
    
    # #: house.png (深灰)
    tiles['#'] = pygame.Surface(TS)
    tiles['#'].fill(settings.COLOR_DARK_GREY)
    
    # T: tree.png (深绿)
    tiles['T'] = pygame.Surface(TS)
    tiles['T'].fill(settings.COLOR_DARK_GREEN)
    
    # S: pipe.png (浅灰)
    tiles['S'] = pygame.Surface(TS)
    tiles['S'].fill(settings.COLOR_LIGHT_GREY)
    
    return tiles

def draw_map(surface, city_map, camera, tile_images):
    """(Spec V) 高效绘制可见区域的地图"""
    TS = settings.TILE_SIZE
    
    # 计算可见的行列范围
    start_col = max(0, camera.camera_rect.x // TS)
    end_col = min(city_map.get_dimensions()[0], (camera.camera_rect.right // TS) + 2)
    start_row = max(0, camera.camera_rect.y // TS)
    end_row = min(city_map.get_dimensions()[1], (camera.camera_rect.bottom // TS) + 2)
    
    for r in range(start_row, end_row):
        for c in range(start_col, end_col):
            tile_symbol = city_map.get_tile(r, c)
            if tile_symbol in tile_images:
                image = tile_images[tile_symbol]
                
                # (Spec II) 转换世界坐标到屏幕坐标
                screen_pos = camera.apply_to_coords(c * TS, r * TS)
                surface.blit(image, screen_pos)

# --- 2. 实体绘制 (Spec III) ---

def draw_player(surface, player, camera):
    """(Spec III) 绘制玩家：绿色圆圈 + 红色朝向线"""
    
    # (Spec II) 转换坐标
    screen_pos = camera.apply_to_coords(player.pos.x, player.pos.y)
    
    # 绘制圆圈
    pygame.draw.circle(surface, player.color, screen_pos, player.radius)
    
    # 绘制朝向线
    end_x = screen_pos[0] + player.radius * math.cos(player.angle_rad)
    # Pygame 的 y 轴是反的，所以 sin 的结果要取反
    end_y = screen_pos[1] - player.radius * math.sin(player.angle_rad)
    
    pygame.draw.line(surface, player.facing_line_color, screen_pos, (end_x, end_y), 2)

def draw_monster(surface, monster_sprite, camera):
    """(Spec III) 根据怪物类型和精英状态绘制图案"""
    logic = monster_sprite.logic
    screen_pos = camera.apply_to_coords(monster_sprite.pos.x, monster_sprite.pos.y)
    angle_rad = monster_sprite.angle_rad
    
    t = logic.type
    e = logic.is_elite
    skills = logic.elite_skills

    if t == 'Wanderer':
        r = monster_sprite.radius
        color = settings.COLOR_WHITE # 假设游荡者是白色
        _draw_rotated_triangle(surface, color, screen_pos, r, angle_rad)
        
    elif t == 'Bucket':
        r = monster_sprite.radius
        color = settings.COLOR_ORANGE
        if e:
            if '烈爆' in skills: color = settings.COLOR_RED
            elif '巨人' in skills: color = settings.COLOR_GREY
        pygame.draw.circle(surface, color, screen_pos, r)
        
    elif t == 'Ghoul':
        w = monster_sprite.width
        h = monster_sprite.height
        color = settings.COLOR_RED
        if e and '飞天' in skills:
            # 宽三角
            _draw_rotated_triangle(surface, color, screen_pos, max(w, h) / 2, angle_rad, aspect_ratio=w/h)
        else:
            # 细长三角
            _draw_rotated_triangle(surface, color, screen_pos, h / 2, angle_rad, aspect_ratio=w/h)

def _draw_rotated_triangle(surface, color, center, size, angle_rad, aspect_ratio=1.0):
    """辅助函数：绘制一个旋转的等腰三角形 (尖端朝向 angle_rad)"""
    
    # 调整高度和宽度
    h = size
    w = size * aspect_ratio
    
    # 1. 定义三个顶点 (朝向右侧, angle=0)
    p1 = (center[0] + h, center[1])                  # 尖端
    p2 = (center[0] - h, center[1] - w) # 左下
    p3 = (center[0] - h, center[1] + w) # 左上

    # 2. 将它们旋转
    p1_rot = _rotate_point(center, p1, angle_rad)
    p2_rot = _rotate_point(center, p2, angle_rad)
    p3_rot = _rotate_point(center, p3, angle_rad)
    
    pygame.draw.polygon(surface, color, [p1_rot, p2_rot, p3_rot])

def _rotate_point(origin, point, angle_rad):
    """围绕原点旋转一个点"""
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle_rad) * (px - ox) - math.sin(angle_rad) * (py - oy)
    qy = oy + math.sin(angle_rad) * (px - ox) + math.cos(angle_rad) * (py - oy)
    return qx, qy


# --- 3. UI & 小地图 (Spec V) ---

def draw_ui(surface, player_logic, current_day, font):
    """(Spec V) 绘制固定的 UI 元素"""
    
    # 1. 玩家血量 (左下角)
    max_hp = player_logic.total_stats.get("生命", 100)
    current_hp = player_logic.current_health
    hp_ratio = current_hp / max_hp
    hp_bar_width = 200
    hp_bar_height = 20
    hp_bar_rect = pygame.Rect(10, settings.SCREEN_HEIGHT - hp_bar_height - 10, hp_bar_width, hp_bar_height)
    hp_fill_rect = pygame.Rect(10, settings.SCREEN_HEIGHT - hp_bar_height - 10, int(hp_bar_width * hp_ratio), hp_bar_height)
    
    pygame.draw.rect(surface, settings.COLOR_RED, hp_bar_rect)
    pygame.draw.rect(surface, settings.COLOR_GREEN, hp_fill_rect)
    pygame.draw.rect(surface, settings.COLOR_WHITE, hp_bar_rect, 2)
    
    # 2. 背包按钮 (左上角)
    bag_rect = pygame.Rect(10, 10, 50, 50)
    pygame.draw.rect(surface, settings.COLOR_GREY, bag_rect)
    text_surf = font.render("BAG", True, settings.COLOR_WHITE)
    surface.blit(text_surf, text_surf.get_rect(center=bag_rect.center))

    # 3. 存活天数 (右下角)
    day_text = f"Day: {current_day}"
    text_surf = font.render(day_text, True, settings.COLOR_WHITE)
    text_rect = text_surf.get_rect(bottomright=(settings.SCREEN_WIDTH - 10, settings.SCREEN_HEIGHT - 10))
    surface.blit(text_surf, text_rect)


def draw_minimap(surface, city_map, player, monsters_group, camera, minimap_font):
    """(Spec V) 绘制小地图和威胁指示器"""
    
    # 1. 绘制小地图背景
    MM_RECT = pygame.Rect(settings.MINIMAP_POS, (settings.MINIMAP_SIZE, settings.MINIMAP_SIZE))
    surface.fill(settings.COLOR_BLACK, MM_RECT)
    pygame.draw.rect(surface, settings.COLOR_WHITE, MM_RECT, 1)

    TS = settings.MINIMAP_TILE_SIZE
    W, H = city_map.get_dimensions()

    # 2. 绘制地格颜色
    for r in range(H):
        for c in range(W):
            tile = city_map.get_tile(r, c)
            color = None
            if tile == '#': color = settings.COLOR_WHITE
            elif tile in ('.', 'T'): color = settings.COLOR_DARK_GREY
            elif tile == '~': color = settings.COLOR_BLUE
            
            if color:
                mini_x = MM_RECT.x + c * TS
                mini_y = MM_RECT.y + r * TS
                pygame.draw.rect(surface, color, (mini_x, mini_y, TS, TS))

    # 3. 绘制玩家 (亮绿)
    player_map_c = player.pos.x / settings.TILE_SIZE
    player_map_r = player.pos.y / settings.TILE_SIZE
    player_mini_x = MM_RECT.x + player_map_c * TS
    player_mini_y = MM_RECT.y + player_map_r * TS
    pygame.draw.rect(surface, settings.COLOR_BRIGHT_GREEN, (player_mini_x - 1, player_mini_y - 1, TS + 2, TS + 2))

    # 4. 绘制怪物 (红)
    monsters_on_screen = 0
    closest_monster = None
    min_dist_sq = float('inf')
    
    visible_rect = camera.camera_rect
    
    for m in monsters_group:
        # (Spec V - a. 判定条件)
        if visible_rect.colliderect(m.rect):
            monsters_on_screen += 1
            
        # (Spec V - b. 查找最近)
        dist_sq = player.pos.distance_squared_to(m.pos)
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            closest_monster = m
        
        # 绘制在小地图上的位置
        m_map_c = m.pos.x / settings.TILE_SIZE
        m_map_r = m.pos.y / settings.TILE_SIZE
        m_mini_x = MM_RECT.x + m_map_c * TS
        m_mini_y = MM_RECT.y + m_map_r * TS
        
        # 确保绘制在小地图内
        if MM_RECT.collidepoint(m_mini_x, m_mini_y):
            pygame.draw.rect(surface, settings.COLOR_RED, (m_mini_x, m_mini_y, TS, TS))

    # 5. (Spec V - 新增) 威胁指示系统
    if monsters_on_screen == 0 and closest_monster:
        # (Spec V - c. 指示器)
        
        # 获取怪物相对于玩家的方向
        dx = closest_monster.pos.x - player.pos.x
        dy = closest_monster.pos.y - player.pos.y
        
        if dx == 0 and dy == 0: return # 怪物在玩家正下方，忽略
        
        angle_rad = math.atan2(dy, dx) # 注意：这里用 dy, dx (世界坐标)
        
        # 核心逻辑：计算箭头在小地图边框上的位置
        # (使用三角函数和正切/余切来找到矩形边界上的交点)
        half_size = settings.MINIMAP_SIZE / 2
        
        # 归一化到小地图中心
        edge_x = half_size * math.cos(angle_rad)
        edge_y = half_size * math.sin(angle_rad)

        # 调整到矩形边缘
        if abs(edge_x) > abs(edge_y):
            # 交点在左右边缘
            scale = half_size / abs(edge_x)
        else:
            # 交点在上下边缘
            scale = half_size / abs(edge_y)
            
        edge_x *= scale
        edge_y *= scale
        
        # 转换回小地图的屏幕坐标
        arrow_pos_x = MM_RECT.centerx + edge_x
        arrow_pos_y = MM_RECT.centery + edge_y

        # 绘制箭头 (一个指向外侧的红色三角形)
        # 我们使用 angle_rad (dy, dx) 来确定方向
        _draw_rotated_triangle(surface, settings.COLOR_RED, (arrow_pos_x, arrow_pos_y), 5, angle_rad)