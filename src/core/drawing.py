# drawing.py
import pygame
import math
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config

# --- 1. 地图与贴图加载 ---

def load_tile_images():
    """
    (Spec V) 加载地图图块。
    优先加载 assets/tiles/ 下的 PNG 文件，如果不存在则使用彩色占位符。
    """
    tiles = {}
    TS = (config.TILE_SIZE, config.TILE_SIZE)
    
    # 获取assets/tiles目录的路径
    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(os.path.dirname(current_file))  # 到src目录
    project_root = os.path.dirname(src_dir)  # 到项目根目录
    tiles_dir = os.path.join(project_root, "assets", "tiles")
    
    # 定义地图符号与文件名的映射关系
    tile_mapping = {
        '.': ('road.png', config.COLOR_BROWN),      # 道路
        '~': ('river.png', config.COLOR_DARK_BLUE), # 河流
        '#': ('house.png', config.COLOR_DARK_GREY), # 建筑
        'T': ('tree.png', config.COLOR_DARK_GREEN), # 树木
        'S': ('pipe.png', config.COLOR_LIGHT_GREY), # 下水道
    }
    
    for symbol, (filename, fallback_color) in tile_mapping.items():
        tile_path = os.path.join(tiles_dir, filename)
        
        # 尝试加载PNG文件
        if os.path.exists(tile_path):
            try:
                image = pygame.image.load(tile_path)
                # 缩放到指定的瓷砖大小，使用SCALE算法确保像素完美对齐
                tiles[symbol] = pygame.transform.scale(image, TS)
                # 确保图像完全不透明（如果需要的话）
                tiles[symbol] = tiles[symbol].convert()
                print(f"[OK] Loaded tile image: {filename}")
            except Exception as e:
                print(f"[WARN] Failed to load {filename}: {e}, using solid color")
                tiles[symbol] = pygame.Surface(TS)
                tiles[symbol].fill(fallback_color)
        else:
            # 文件不存在，使用纯色占位符
            tiles[symbol] = pygame.Surface(TS)
            tiles[symbol].fill(fallback_color)
    
    return tiles

def draw_trees(surface, city_map, camera, tile_images):
    """
    新增函数：专门绘制树木 ('T')，用于实现树木遮挡效果。
    这个函数应该在实体（玩家/怪物）绘制之后调用。
    """
    TS = config.TILE_SIZE
    
    # 计算可见的行列范围 (与 draw_map 相同)
    start_col = max(0, int(camera.camera_rect.x // TS))
    end_col = min(city_map.get_dimensions()[0], int((camera.camera_rect.right + TS - 1) // TS))
    start_row = max(0, int(camera.camera_rect.y // TS))
    end_row = min(city_map.get_dimensions()[1], int((camera.camera_rect.bottom + TS - 1) // TS))
    
    # 获取树木贴图
    tree_image = tile_images.get('T')
    if not tree_image:
        return # 如果没有树木贴图，则不绘制
        
    for r in range(start_row, end_row):
        for c in range(start_col, end_col):
            tile_symbol = city_map.get_tile(r, c)
            
            # --- 关键修改：只绘制树木 ---
            if tile_symbol == 'T':
                # 世界坐标 = 网格坐标 * 瓷砖大小
                world_x = c * TS
                world_y = r * TS
                screen_x, screen_y = camera.apply_to_coords(world_x, world_y)
                # 确保整数像素对齐，避免缝隙
                surface.blit(tree_image, (int(screen_x), int(screen_y)))

def draw_map(surface, city_map, camera, tile_images):
    """(Spec V) 高效绘制可见区域的地图"""
    TS = config.TILE_SIZE
    
    # 计算可见的行列范围
    start_col = max(0, int(camera.camera_rect.x // TS))
    end_col = min(city_map.get_dimensions()[0], int((camera.camera_rect.right + TS - 1) // TS))
    start_row = max(0, int(camera.camera_rect.y // TS))
    end_row = min(city_map.get_dimensions()[1], int((camera.camera_rect.bottom + TS - 1) // TS))
    
    # print(f"\n{'='*60}")
    # print(f"DEBUG: draw_map() 调用")
    # print(f"{'='*60}")
    # print(f"摄像机位置: camera_rect.x={camera.camera_rect.x}, camera_rect.y={camera.camera_rect.y}")
    # print(f"摄像机范围: right={camera.camera_rect.right}, bottom={camera.camera_rect.bottom}")
    # print(f"TILE_SIZE: {TS}")
    # print(f"地图尺寸: {city_map.get_dimensions()}")
    # print(f"可见行范围: {start_row} 到 {end_row} (共 {end_row - start_row} 行)")
    # print(f"可见列范围: {start_col} 到 {end_col} (共 {end_col - start_col} 列)")
    # print(f"预计绘制瓷砖数: {(end_row - start_row) * (end_col - start_col)}")
    # print(f"{'='*60}\n")
    
    # count = 0
    # tiles_by_type = {}
    
    for r in range(start_row, end_row):
        for c in range(start_col, end_col):
            tile_symbol = city_map.get_tile(r, c)
            if tile_symbol in tile_images and tile_symbol != 'T':
                image = tile_images[tile_symbol]
                
                # (Spec II) 转换世界坐标到屏幕坐标
                # 世界坐标 = 网格坐标 * 瓷砖大小
                world_x = c * TS
                world_y = r * TS
                screen_x, screen_y = camera.apply_to_coords(world_x, world_y)
                # 确保整数像素对齐，避免缝隙
                surface.blit(image, (int(screen_x), int(screen_y)))
                
                # # 统计瓷砖类型
                # tiles_by_type[tile_symbol] = tiles_by_type.get(tile_symbol, 0) + 1
                # count += 1
    
    # print(f"实际绘制瓷砖数: {count}")
    # print(f"瓷砖类型统计: {tiles_by_type}")
    # print(f"{'='*60}\n")
# --- 2. 实体绘制 (Spec III) ---

def draw_player(surface, player, camera, sprite_images=None):
    """(Spec III) 绘制玩家：使用精灵图像"""
    
    # (Spec II) 转换坐标
    screen_x, screen_y = camera.apply_to_coords(player.pos.x, player.pos.y)
    screen_pos = (int(screen_x), int(screen_y))
    
    # 使用图像绘制
    if sprite_images and 'player' in sprite_images:
        image = sprite_images['player']
        # 缩放到玩家大小（直径）
        size = player.radius * 2
        scaled_image = pygame.transform.scale(image, (int(size), int(size)))
        # 旋转图像（图像朝向正右，需要旋转到angle_rad）
        angle_deg = -math.degrees(player.angle_rad)  # Pygame旋转是顺时针，所以取负
        rotated_image = pygame.transform.rotate(scaled_image, angle_deg)
        # 获取旋转后的rect并居中
        rect = rotated_image.get_rect(center=screen_pos)
        surface.blit(rotated_image, rect)
    else:
        # 降级方案：绘制圆圈
        pygame.draw.circle(surface, player.color, screen_pos, player.radius)
        # 绘制朝向线（y 轴向下，因此使用 +sin）
        end_x = int(screen_pos[0] + player.radius * math.cos(player.angle_rad))
        end_y = int(screen_pos[1] + player.radius * math.sin(player.angle_rad))
        pygame.draw.line(surface, player.facing_line_color, screen_pos, (end_x, end_y), 2)

def draw_monster(surface, monster_sprite, camera, sprite_images=None):
    """(Spec III) 根据怪物类型和精英状态绘制图案"""
    logic = monster_sprite.logic
    
    # 只有非游荡者在复活时才跳过渲染
    if logic.is_reviving and logic.type != 'Wanderer':
        return
    
    screen_x, screen_y = camera.apply_to_coords(monster_sprite.pos.x, monster_sprite.pos.y)
    screen_pos = (int(screen_x), int(screen_y))
    angle_rad = monster_sprite.angle_rad
    
    t = logic.type
    e = logic.is_elite
    skills = logic.elite_skills
    
    # 检查是否是庞然（需要缩放）
    size_multiplier = 1.0
    if hasattr(logic, 'get_size_multiplier'):
        size_multiplier = logic.get_size_multiplier()
    
    # 确定使用的图像key
    image_key = None
    if sprite_images:
        if t == 'Wanderer':
            if e and '呼唤者' in skills and 'wanderer-召唤' in sprite_images:
                image_key = 'wanderer-召唤'
            elif e and '不死者' in skills and 'wanderer-不死' in sprite_images:
                image_key = 'wanderer-不死'
            elif 'wanderer' in sprite_images:
                image_key = 'wanderer'
        elif t == 'Bucket':
            if e and '庞然' in skills and 'bucket-巨人' in sprite_images:
                image_key = 'bucket-巨人'
            elif e and '荆棘守卫' in skills and 'bucket-荆棘' in sprite_images:
                image_key = 'bucket-荆棘'
            elif 'bucket' in sprite_images:
                image_key = 'bucket'
        elif t == 'Ghoul':
            if e and '暗影猎手' in skills and 'ghoul-暗影' in sprite_images:
                image_key = 'ghoul-暗影'
            elif e and '银翼猎手' in skills and 'ghoul-飞天' in sprite_images:
                image_key = 'ghoul-飞天'
            elif 'ghoul' in sprite_images:
                image_key = 'ghoul'
    
    # 使用图像绘制
    if image_key:
        image = sprite_images[image_key]
        
        # 根据怪物类型计算尺寸
        if t in ['Wanderer', 'Bucket']:
            # 圆形怪物：图像直径 = 2×半径
            size = monster_sprite.radius * 2 * size_multiplier
            scaled_image = pygame.transform.scale(image, (int(size), int(size)))
        else:  # Ghoul
            # 三角形怪物：使用width和height
            scaled_image = pygame.transform.scale(image, (int(monster_sprite.width * size_multiplier), int(monster_sprite.height * size_multiplier)))
        
        # 旋转图像
        angle_deg = -math.degrees(angle_rad)
        rotated_image = pygame.transform.rotate(scaled_image, angle_deg)
        
        # 复活中的游荡者：降低透明度
        if logic.is_reviving and t == 'Wanderer':
            rotated_image = rotated_image.copy()
            rotated_image.set_alpha(128)  # 50%透明度
        
        # 绘制
        rect = rotated_image.get_rect(center=screen_pos)
        surface.blit(rotated_image, rect)
    else:
        # 降级方案：使用原来的几何图形绘制
        if t == 'Wanderer':
            r = monster_sprite.radius * size_multiplier
            # 浅蓝色（活着），灰色（复活中的尸体）
            if logic.is_reviving:
                color = config.COLOR_GREY  # 尸体
            else:
                color = (100, 200, 255)  # 浅蓝色
            _draw_rotated_triangle(surface, color, screen_pos, r, angle_rad)
            
        elif t == 'Bucket':
            r = monster_sprite.radius * size_multiplier
            color = config.COLOR_ORANGE
            if e:
                if '庞然' in skills: 
                    color = config.COLOR_GREY
                elif '荆棘守卫' in skills: 
                    color = (150, 50, 150)  # 紫色
            pygame.draw.circle(surface, color, screen_pos, int(r))
            
        elif t == 'Ghoul':
            w = monster_sprite.width * size_multiplier
            h = monster_sprite.height * size_multiplier
            color = config.COLOR_RED
            if e and '银翼猎手' in skills:
                # 宽三角
                _draw_rotated_triangle(surface, color, screen_pos, max(w, h) / 2, angle_rad, aspect_ratio=w/h)
            else:
                # 细长三角
                _draw_rotated_triangle(surface, color, screen_pos, h / 2, angle_rad, aspect_ratio=w/h)
    
    # 绘制不死者残躯标记
    if hasattr(logic, 'undying_active') and logic.undying_active:
        # 在怪物头顶显示红色"DEATH"文字
        font = pygame.font.Font(None, 24)
        text_surface = font.render("DEATH", True, (255, 0, 0))
        text_rect = text_surface.get_rect(center=(screen_pos[0], screen_pos[1] - int(monster_sprite.radius * size_multiplier) - 20))
        surface.blit(text_surface, text_rect)

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
    hp_bar_rect = pygame.Rect(10, config.SCREEN_HEIGHT - hp_bar_height - 10, hp_bar_width, hp_bar_height)
    hp_fill_rect = pygame.Rect(10, config.SCREEN_HEIGHT - hp_bar_height - 10, int(hp_bar_width * hp_ratio), hp_bar_height)
    
    pygame.draw.rect(surface, config.COLOR_RED, hp_bar_rect)
    pygame.draw.rect(surface, config.COLOR_GREEN, hp_fill_rect)
    pygame.draw.rect(surface, config.COLOR_WHITE, hp_bar_rect, 2)
    
    # 2. 背包按钮 (左上角)
    bag_rect = pygame.Rect(10, 10, 50, 50)
    pygame.draw.rect(surface, config.COLOR_GREY, bag_rect)
    text_surf = font.render("BAG", True, config.COLOR_WHITE)
    surface.blit(text_surf, text_surf.get_rect(center=bag_rect.center))

    # 3. 存活天数 (右下角)
    day_text = f"Day: {current_day}"
    text_surf = font.render(day_text, True, config.COLOR_WHITE)
    text_rect = text_surf.get_rect(bottomright=(config.SCREEN_WIDTH - 10, config.SCREEN_HEIGHT - 10))
    surface.blit(text_surf, text_rect)


def draw_minimap(surface, city_map, player, monsters_group, camera, minimap_font):
    """(Spec V) 绘制小地图和威胁指示器"""
    
    # 1. 绘制小地图背景
    MM_RECT = pygame.Rect(config.MINIMAP_POS, (config.MINIMAP_SIZE, config.MINIMAP_SIZE))
    surface.fill(config.COLOR_BLACK, MM_RECT)
    pygame.draw.rect(surface, config.COLOR_WHITE, MM_RECT, 1)

    TS = config.MINIMAP_TILE_SIZE
    W, H = city_map.get_dimensions()

    # 2. 绘制地格颜色
    for r in range(H):
        for c in range(W):
            tile = city_map.get_tile(r, c)
            color = None
            if tile == '#': color = config.COLOR_WHITE
            elif tile in ('.', 'T'): color = config.COLOR_DARK_GREY
            elif tile == '~': color = config.COLOR_BLUE
            
            if color:
                mini_x = MM_RECT.x + c * TS
                mini_y = MM_RECT.y + r * TS
                pygame.draw.rect(surface, color, (mini_x, mini_y, TS, TS))

    # 3. 绘制玩家 (亮绿)
    player_map_c = player.pos.x / config.TILE_SIZE
    player_map_r = player.pos.y / config.TILE_SIZE
    player_mini_x = MM_RECT.x + player_map_c * TS
    player_mini_y = MM_RECT.y + player_map_r * TS
    pygame.draw.rect(surface, config.COLOR_BRIGHT_GREEN, (player_mini_x - 1, player_mini_y - 1, TS + 2, TS + 2))

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
        m_map_c = m.pos.x / config.TILE_SIZE
        m_map_r = m.pos.y / config.TILE_SIZE
        m_mini_x = MM_RECT.x + m_map_c * TS
        m_mini_y = MM_RECT.y + m_map_r * TS
        
        # 确保绘制在小地图内
        if MM_RECT.collidepoint(m_mini_x, m_mini_y):
            pygame.draw.rect(surface, config.COLOR_RED, (m_mini_x, m_mini_y, TS, TS))

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
        half_size = config.MINIMAP_SIZE / 2
        
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
        _draw_rotated_triangle(surface, config.COLOR_RED, (arrow_pos_x, arrow_pos_y), 5, angle_rad)

def draw_monster_attack_effects(surface, monsters, camera):
    """
    绘制怪物攻击特效（铁桶圆环）
    """
    for monster in monsters:
        if monster.logic.type == 'Bucket' and monster.ring_radius > 0:
            center_screen = camera.apply_to_coords(monster.pos.x, monster.pos.y)
            radius = int(monster.ring_radius)
            
            if radius > 0:
                # 铁桶的颜色（根据是否精英）
                if monster.logic.is_elite:
                    base_color = config.COLOR_ORANGE
                else:
                    base_color = config.COLOR_GREY
                
                # 创建半透明表面
                ring_surface = pygame.Surface((radius*2+20, radius*2+20), pygame.SRCALPHA)
                
                # 填充半透明圆盘（主体）
                fill_alpha = int(80)  # 约30%透明度
                if monster.logic.is_elite:
                    fill_color = (255, 200, 150, fill_alpha)
                else:
                    fill_color = (180, 180, 180, fill_alpha)
                pygame.draw.circle(ring_surface, fill_color, 
                                 (radius+10, radius+10), radius)
                
                # 绘制外圈光晕效果（3层渐变）
                for i in range(3):
                    # 从内到外，透明度递减
                    alpha = int(60 * (1 - i * 0.3))
                    offset = i * 6
                    
                    # 浅橙色/浅灰色
                    if monster.logic.is_elite:
                        color = (255, 220, 180, alpha)
                    else:
                        color = (200, 200, 200, alpha)
                    
                    if radius + offset > 0:
                        pygame.draw.circle(ring_surface, color, 
                                         (radius+10, radius+10), 
                                         radius + offset, 6)
                
                # Blit到屏幕
                blit_pos = (center_screen[0] - radius - 10, center_screen[1] - radius - 10)
                surface.blit(ring_surface, blit_pos)

def draw_corpse_explosions(surface, explosions, camera, sprite_images=None):
    """
    绘制尸爆效果：铁桶图像从当前尺寸放大到最大半径
    """
    for explosion in explosions:
        center_screen = camera.apply_to_coords(explosion.pos.x, explosion.pos.y)
        
        if explosion.is_exploding:
            # 爆炸阶段：绘制放大的铁桶图像
            radius = int(explosion.current_radius)
            
            if radius > 0 and sprite_images and 'bucket' in sprite_images:
                # 使用铁桶图像
                image = sprite_images['bucket']
                # 图像尺寸随爆炸半径放大
                size = radius * 2
                scaled_image = pygame.transform.scale(image, (int(size), int(size)))
                
                # 设置透明度（随爆炸进度逐渐消失）
                alpha = int(255 * (1.0 - explosion.explosion_progress))
                scaled_image.set_alpha(alpha)
                
                # 绘制
                rect = scaled_image.get_rect(center=center_screen)
                surface.blit(scaled_image, rect)
            else:
                # 降级方案：红色爆炸圈
                explosion_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                alpha = int(255 * (1.0 - explosion.explosion_progress))
                color_with_alpha = (255, 100, 0, alpha)
                pygame.draw.circle(explosion_surface, color_with_alpha, (radius, radius), radius, 3)
                
                blit_pos = (center_screen[0] - radius, center_screen[1] - radius)
                surface.blit(explosion_surface, blit_pos)
        else:
            # 延迟阶段：在尸体位置闪烁警告
            if int(explosion.timer * 4) % 2 == 0:  # 每0.25秒闪烁
                pygame.draw.circle(surface, (255, 200, 0), center_screen, 10, 2)


def draw_collision_shapes(surface, player, monsters_group, bullets_group, camera):
    """调试用：绘制玩家/怪物/子弹的碰撞形状与尺寸标签

    - 玩家：圆（player.radius）和 rect
    - 游荡者/铁桶：圆（monster.radius）与 rect 边界
    - 食尸鬼：rect (width x height) 以及近似半径 circle = max(w,h)/2
    - 子弹：小圆
    """
    # 颜色定义
    player_color = (0, 255, 0)
    monster_color = (255, 0, 0)
    elite_color = (255, 165, 0)
    bullet_color = (255, 255, 0)
    outline_color = (255, 255, 255)

    # 简单字体用于绘制标签
    try:
        font = pygame.font.Font(None, 14)
    except:
        font = None

    # 玩家：circle + rect
    p_screen = camera.apply_to_coords(player.pos.x, player.pos.y)
    pygame.draw.circle(surface, player_color, (int(p_screen[0]), int(p_screen[1])), int(player.radius), 1)
    # rect
    p_rect = camera.apply_to_rect(player.rect)
    pygame.draw.rect(surface, player_color, p_rect, 1)
    if font:
        txt = font.render(f"P r={player.radius}", True, outline_color)
        surface.blit(txt, (p_screen[0] + 6, p_screen[1] - 6))

    # 怪物
    for m in monsters_group:
        m_screen = camera.apply_to_coords(m.pos.x, m.pos.y)
        # 标记颜色：精英用不同颜色
        col = elite_color if getattr(m.logic, 'is_elite', False) else monster_color

        if getattr(m, 'radius', 0) and m.radius > 0 and m.logic.type != 'Ghoul':
            # 圆形怪物
            pygame.draw.circle(surface, col, (int(m_screen[0]), int(m_screen[1])), int(m.radius), 1)
            # rect boundary for sprite image
            m_rect = camera.apply_to_rect(m.rect)
            pygame.draw.rect(surface, col, m_rect, 1)
            if font:
                txt = font.render(f"{m.logic.type} r={m.radius}", True, outline_color)
                surface.blit(txt, (m_screen[0] + 6, m_screen[1] - 6))
        else:
            # 使用宽高的 rect（食尸鬼）
            # 对于 Ghoul 绘制旋转矩形（世界坐标）并将顶点转换为屏幕坐标
            if getattr(m.logic, 'type', None) == 'Ghoul':
                w = getattr(m, 'width', 0)
                h = getattr(m, 'height', 0)
                angle = getattr(m, 'angle_rad', 0)
                # 计算世界空间的四个角
                cx, cy = m.pos.x, m.pos.y
                hw = w / 2.0
                hh = h / 2.0
                ca = math.cos(angle)
                sa = math.sin(angle)
                local = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
                world_pts = []
                for lx, ly in local:
                    rx = cx + (lx * ca - ly * sa)
                    ry = cy + (lx * sa + ly * ca)
                    world_pts.append((rx, ry))

                # 转换为屏幕坐标
                screen_pts = [camera.apply_to_coords(px, py) for (px, py) in world_pts]
                # 绘制多边形
                pygame.draw.polygon(surface, col, screen_pts, 1)
                # 绘制角点
                for pt in screen_pts:
                    pygame.draw.circle(surface, outline_color, (int(pt[0]), int(pt[1])), 2)
                if font:
                    txt = font.render(f"Ghoul w={int(w)} h={int(h)}", True, outline_color)
                    surface.blit(txt, (m_screen[0] + 6, m_screen[1] - 6))
            else:
                m_rect = camera.apply_to_rect(m.rect)
                pygame.draw.rect(surface, col, m_rect, 1)
                approx_r = max(getattr(m, 'width', 0), getattr(m, 'height', 0)) / 2
                pygame.draw.circle(surface, col, (int(m_screen[0]), int(m_screen[1])), int(approx_r), 1)
                if font:
                    txt = font.render(f"{m.logic.type} w={m.width} h={m.height}", True, outline_color)
                    surface.blit(txt, (m_screen[0] + 6, m_screen[1] - 6))

    # 子弹
    for b in bullets_group:
        b_screen = camera.apply_to_coords(b.pos.x, b.pos.y)
        pygame.draw.circle(surface, bullet_color, (int(b_screen[0]), int(b_screen[1])), int(getattr(b, 'radius', 2)), 1)
        if font:
            txt = font.render(f"b r={getattr(b, 'radius', 0)}", True, outline_color)
            surface.blit(txt, (b_screen[0] + 4, b_screen[1] - 4))

def draw_game_over_ui(surface, game):
    """
    绘制Game Over界面
    """
    # 绘制半透明灰色遮罩
    overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    overlay.fill((50, 50, 50))
    overlay.set_alpha(200)
    surface.blit(overlay, (0, 0))
    
    # Game Over 文字（使用系统字体支持中文）
    try:
        font_large = pygame.font.SysFont('microsoftyahei,simsun,simhei,arial', 72, bold=True)
        font_medium = pygame.font.SysFont('microsoftyahei,simsun,simhei,arial', 36)
    except:
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 36)
    
    text = font_large.render("GAME OVER", True, config.COLOR_RED)
    text_rect = text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 3))
    surface.blit(text, text_rect)
    
    # 统计信息
    day_text = font_medium.render(f"存活天数: {game.current_day}", True, config.COLOR_WHITE)
    day_rect = day_text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 20))
    surface.blit(day_text, day_rect)
    
    # 按钮
    button_y = config.SCREEN_HEIGHT // 2 + 80
    button_width = 180
    button_height = 50
    button_spacing = 40
    
    # 从头开始按钮
    restart_x = config.SCREEN_WIDTH // 2 - button_width - button_spacing // 2
    restart_rect = pygame.Rect(restart_x, button_y, button_width, button_height)
    pygame.draw.rect(surface, config.COLOR_GREEN, restart_rect)
    pygame.draw.rect(surface, config.COLOR_WHITE, restart_rect, 2)
    restart_text = font_medium.render("从头开始", True, config.COLOR_BLACK)
    restart_text_rect = restart_text.get_rect(center=restart_rect.center)
    surface.blit(restart_text, restart_text_rect)
    game.restart_button_rect = restart_rect  # 保存按钮位置供点击检测
    
    # 回到上一天按钮
    retry_x = config.SCREEN_WIDTH // 2 + button_spacing // 2
    retry_rect = pygame.Rect(retry_x, button_y, button_width, button_height)
    pygame.draw.rect(surface, config.COLOR_BLUE, retry_rect)
    pygame.draw.rect(surface, config.COLOR_WHITE, retry_rect, 2)
    retry_text = font_medium.render("回到上一天", True, config.COLOR_WHITE)
    retry_text_rect = retry_text.get_rect(center=retry_rect.center)
    surface.blit(retry_text, retry_text_rect)
    game.retry_button_rect = retry_rect  # 保存按钮位置供点击检测