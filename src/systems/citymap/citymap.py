# citymap.py
from . import config
import random

class CityMap:
    """
    负责加载、解析和管理游戏地图数据的类。
    """
    def __init__(self):
        # 1. 初始化地图数据
        self._map_data = []
        self._width = 0
        self._height = 0
        self._parse_map()
        
        # 2. 玩家位置 (初始为 None，待 _initialize_player_position 初始化)
        self._player_pos = None
        self._initialize_player_position()

    def _parse_map(self):
        """解析 config 中的地图字符串，存储为二维列表 (行, 列)。"""
        lines = config.CITY_MAP.split('\n')
        
        # 移除空行并存储数据
        self._map_data = [list(line) for line in lines if line.strip()]
            
        if not self._map_data:
            raise ValueError("地图数据为空或格式不正确。")
            
        self._height = len(self._map_data)
        self._width = len(self._map_data[0])
        
        # 检查所有行长度是否一致
        if any(len(row) != self._width for row in self._map_data):
            raise ValueError("地图行长度不一致。")

    def _initialize_player_position(self):
        """寻找一个随机的可通行起点作为玩家初始位置。"""
        start_points = []
        for r in range(self._height):
            for c in range(self._width):
                if self._map_data[r][c] in config.WALKABLE_TILES:
                    start_points.append((r, c))
                    
        if start_points:
            # 随机选择一个起点
            self._player_pos = random.choice(start_points)
        else:
            raise RuntimeError("地图上没有可供玩家站立的可通行地格。")

    # --- 玩家位置管理 ---

    def get_player_position(self):
        """返回玩家的当前位置 (行, 列)。"""
        return self._player_pos

    def set_player_position(self, r, c):
        """
        设置玩家的新位置 (行, 列)。
        
        返回: True (设置成功) / False (位置不可通行)
        """
        if self._is_valid_coordinate(r, c) and self.is_walkable(r, c):
            self._player_pos = (r, c)
            return True
        return False
        
    def get_player_current_tile(self):
        """
        返回玩家当前位置下方的地格符号，用于绘图和交互判断。
        
        返回: 地格符号字符串 (例如 '.', '#', 'T', 'S')。
        """
        if self._player_pos is None:
            return None
        r, c = self._player_pos
        return self.get_tile(r, c)


    # --- 地图信息与查询 ---

    def get_dimensions(self):
        """返回地图的尺寸 (宽度, 高度)。"""
        return self._width, self._height

    def get_tile(self, r, c):
        """返回指定坐标 (行r, 列c) 的地格符号。"""
        if self._is_valid_coordinate(r, c):
            return self._map_data[r][c]
        return None # 越界

    def is_walkable(self, r, c):
        """检查地格是否可被玩家步行 (包括树木 'T')。"""
        tile = self.get_tile(r, c)
        return tile in config.WALKABLE_TILES

    def _is_valid_coordinate(self, r, c):
        """检查坐标是否在地图范围内。"""
        return 0 <= r < self._height and 0 <= c < self._width

    # --- 僵尸出生点获取 ---

    def get_ghoul_spawn_points(self):
        """
        返回所有食尸鬼 (Ghoul) 的出生点列表 (S 地格)。
        """
        spawn_points = []
        for r in range(self._height):
            for c in range(self._width):
                if self._map_data[r][c] in config.GHOUL_SPAWN_TILES:
                    spawn_points.append((r, c))
        return spawn_points

    def get_wanderer_spawn_points(self):
        """
        返回所有游荡者 (Wanderer) 的潜在出生点 (墙体 #)。
        返回: 所有墙体地格的坐标 (r, c)。
        """
        spawn_points = []
        for r in range(self._height):
            for c in range(self._width):
                # 仅考虑内部墙体，排除最外层边界
                if self._map_data[r][c] in config.WANDERER_SPAWN_TILES and \
                   0 < r < self._height - 1 and 0 < c < self._width - 1:
                         spawn_points.append((r, c))
        return spawn_points

    def get_bucket_spawn_points(self):
        """
        返回铁桶 (Bucket) 的潜在出生点 (墙体 # 内部)。
        实现逻辑: 限制在地图上半部分，且周围有密集墙体，模拟大型建筑内部。
        """
        spawn_points = []
        # 将搜索范围限制在地图上半部分
        limit_r = self._height // 2 
        
        for r in range(limit_r):
            for c in range(self._width):
                if self._map_data[r][c] in config.BUCKET_SPAWN_TILES and \
                   0 < r < self._height - 1 and 0 < c < self._width - 1:
                        
                    # 额外筛选：检查其周围 8 个地格中，是否有至少 3 个是墙体
                    wall_neighbors = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0: continue
                            if self.get_tile(r + dr, c + dc) == '#':
                                wall_neighbors += 1
                                
                    if wall_neighbors >= 3:
                        spawn_points.append((r, c))
                        
        return spawn_points

    def is_slow_tile(self, r, c):
        """检查地格是否为河流 (~)，仅食尸鬼可以通行。"""
        return self.get_tile(r, c) in config.IS_RIVER