from . import config
import random

class CityMap:
    """
    负责加载、解析和管理游戏地图数据的类。
    """
    def __init__(self, map_string=None):
        # 1. 初始化地图数据
        self._map_data = []
        self._width = 0
        self._height = 0
        self._map_string = map_string  # 保存自定义地图字符串
        self._parse_map()
        
        # 2. 玩家位置 (初始为 None，待 _initialize_player_position 初始化)
        self._player_pos = None
        self._initialize_player_position()

    # (略去 _parse_map, _initialize_player_position, 玩家位置管理方法)
    # ... (保持原样)

    def _parse_map(self):
        """解析地图字符串，存储为二维列表 (行, 列)。"""
        # 如果提供了自定义地图，使用自定义地图，否则使用 config 中的地图
        map_data = self._map_string if self._map_string else config.CITY_MAP
        lines = map_data.split('\n')
        
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

    def _get_tile_or_wall(self, r, c):
        """
        获取指定坐标的地格符号。
        如果坐标越界，则返回墙壁符号 '#' (实现边界按墙壁算)。
        """
        if self._is_valid_coordinate(r, c):
            return self._map_data[r][c]
        return '#' # 越界则算作墙壁

    # --- 僵尸出生点获取 ---

    def get_ghoul_spawn_points(self):
        """
        返回所有食尸鬼 (Ghoul) 的出生点列表 (S 地格)。
        (保持原样，逻辑不变)
        """
        spawn_points = []
        for r in range(self._height):
            for c in range(self._width):
                if self._map_data[r][c] in config.GHOUL_SPAWN_TILES:
                    spawn_points.append((r, c))
        return spawn_points

    def get_wanderer_spawn_points(self):
        """
        返回所有游荡者 (Wanderer) 的合法出生点。
        合法出生点: 十字相邻的网格存在墙壁的空地网格。
        """
        spawn_points = []
        # 十字相邻方向 (上, 下, 左, 右)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] 

        for r in range(self._height):
            for c in range(self._width):
                # 1. 必须是空地网格 (可通行地格)
                if self.is_walkable(r, c):
                    has_wall_neighbor = False
                    
                    # 2. 检查十字相邻的网格是否存在墙壁
                    for dr, dc in directions:
                        neighbor_tile = self._get_tile_or_wall(r + dr, c + dc)
                        # 注意：边界越界时 _get_tile_or_wall 会返回 '#'，符合“边界按墙壁算”的逻辑
                        if neighbor_tile == '#':
                            has_wall_neighbor = True
                            break
                    
                    if has_wall_neighbor:
                        spawn_points.append((r, c))
                        
        return spawn_points

    def get_bucket_spawn_points(self):
        """
        返回铁桶 (Bucket) 的合法出生点。
        合法出生点: 九宫格内有至少三格是墙壁的空地网格。
        """
        spawn_points = []
        
        for r in range(self._height):
            for c in range(self._width):
                # 1. 必须是空地网格 (可通行地格)
                if self.is_walkable(r, c):
                    wall_neighbors = 0
                    
                    # 2. 检查九宫格 (3x3 区域)
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            # 排除中心点自身，因为中心点已经是空地
                            if dr == 0 and dc == 0: 
                                continue
                            
                            neighbor_tile = self._get_tile_or_wall(r + dr, c + dc)
                            # 注意：边界越界时 _get_tile_or_wall 会返回 '#'
                            if neighbor_tile == '#':
                                wall_neighbors += 1
                                
                    # 3. 满足至少三格是墙壁的条件
                    if wall_neighbors >= 3:
                        spawn_points.append((r, c))
                        
        return spawn_points

    def is_slow_tile(self, r, c):
        """检查地格是否为河流 (~)，仅食尸鬼可以通行。"""
        return self.get_tile(r, c) in config.IS_RIVER
