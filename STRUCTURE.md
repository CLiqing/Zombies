# Zombies 游戏项目重构说明

## 新项目结构

项目已重构为更清晰的模块化结构：

```
Zombies/
├── README.md                    # 项目主说明文档
├── STRUCTURE.md                 # 本文件 - 项目结构说明
├── 疑问.txt                     # 原有问题记录
├── assets/                      # 游戏资源
│   ├── fonts/                   # 字体文件
│   └── tiles/                   # 地图贴图（PNG格式）
│       ├── road.png             # 道路贴图
│       ├── river.png            # 河流贴图
│       ├── house.png            # 建筑/墙体贴图
│       ├── tree.png             # 树木贴图
│       └── pipe.png             # 下水道入口贴图
│
├── games/                       # 【已废弃】旧代码目录，保留作为参考
│
└── src/                         # 【新】主源代码目录
    ├── __init__.py
    ├── config.py                # 全局配置（原settings.py）
    │
    ├── core/                    # 核心游戏引擎
    │   ├── __init__.py
    │   ├── game.py             # Game类 - 游戏主循环
    │   ├── camera.py           # Camera类 - 摄像机系统
    │   └── drawing.py          # 绘制函数
    │
    ├── entities/                # 游戏实体
    │   ├── __init__.py
    │   ├── player.py           # Player类 - 玩家
    │   ├── bullet.py           # Bullet类 - 子弹
    │   └── monster_sprite.py   # MonsterSprite类 - 怪物精灵
    │
    ├── systems/                 # 游戏系统模块
    │   ├── __init__.py
    │   │
    │   ├── citymap/            # 地图系统
    │   │   ├── __init__.py
    │   │   ├── citymap.py      # 地图加载和管理
    │   │   └── config.py       # 地图配置
    │   │
    │   ├── inventory/          # 背包系统
    │   │   ├── __init__.py
    │   │   ├── config.py       # 背包配置
    │   │   ├── inventory_gui.py    # 背包界面
    │   │   ├── item_generator.py   # 物品生成器
    │   │   ├── player_stats.py     # 玩家属性计算
    │   │   ├── ui_elements.py      # UI元素
    │   │   └── utils.py            # 工具函数
    │   │
    │   └── monsters/           # 怪物系统
    │       ├── __init__.py
    │       ├── config.py       # 怪物配置
    │       └── monster_logic.py    # 怪物逻辑和生成
    │
    └── tests/                   # 测试/演示脚本
        ├── __init__.py
        ├── test_game.py        # 完整游戏测试（地图移动等） ⭐
        ├── test_inventory.py   # 背包系统测试 ⭐
        └── test_monsters.py    # 怪物系统测试 ⭐
```

## 三个测试入口点

重构后，项目有三个可独立运行的测试入口点：

### 1. 完整游戏测试 (src/tests/test_game.py) ⭐
完整的僵尸生存游戏，包含所有功能（地图、玩家移动、怪物等）。

**运行方式：**
```bash
cd src/tests
python test_game.py
```

**功能：**
- 完整的游戏循环
- 玩家控制（WASD移动，鼠标瞄准射击）
- 怪物生成和AI
- 地图系统和相机跟随
- 碰撞检测
- UI和小地图

### 2. 背包系统测试 (src/tests/test_inventory.py) ⭐
独立的背包系统测试界面。

**运行方式：**
```bash
cd src/tests
python test_inventory.py
```

**功能：**
- 背包界面测试
- 物品生成（普通/精良/史诗/传奇）
- 装备拖拽和旋转
- 属性面板显示
- 物品管理（精炼/销毁）

### 3. 怪物系统测试 (src/tests/test_monsters.py) ⭐
怪物生成系统的命令行测试工具。

**运行方式：**
```bash
cd src/tests
python test_monsters.py
```

**功能：**
- 按天数生成怪物
- 显示怪物详细信息
- 测试怪物平衡性

## 主要改进

### 1. 清晰的模块分离
- **core/**: 核心游戏引擎（游戏循环、渲染、摄像机）
- **entities/**: 游戏实体（玩家、子弹、怪物精灵）
- **systems/**: 独立的游戏系统（地图、背包、怪物）
- **tests/**: 测试和演示脚本

### 2. 一致的导入策略
所有模块使用统一的路径添加方式，确保无论从哪里运行都能正确导入。

### 3. 配置统一
- 主游戏配置：`src/config.py`（原`settings.py`）
- 各系统保留独立配置文件

### 4. 更好的可维护性
- 每个系统可以独立测试和开发
- 清晰的依赖关系
- 便于扩展和修改

## 开发指南

### 添加新功能
1. **新实体**: 在 `src/entities/` 中创建新文件
2. **新系统**: 在 `src/systems/` 中创建新文件夹
3. **修改配置**: 编辑 `src/config.py` 或对应系统的 `config.py`

### 测试
- 完整游戏测试: `cd src/tests && python test_game.py`
- 背包系统测试: `cd src/tests && python test_inventory.py`
- 怪物系统测试: `cd src/tests && python test_monsters.py`

### 注意事项
- 确保所有新文件都添加路径设置代码
- 使用相对于 `src/` 的完整导入路径
- 保持每个系统的独立性

## 迁移说明

原有的 `games/` 目录已保留作为参考，但建议使用新的 `src/` 目录进行开发。

旧代码与新代码的对应关系：
- `games/main.py` → `src/tests/test_game.py`（游戏测试）
- `games/game.py` → `src/core/game.py`
- `games/settings.py` → `src/config.py`
- `games/player.py` → `src/entities/player.py`
- `games/inventory/main.py` → `src/tests/test_inventory.py`
- `games/monsters/main.py` → `src/tests/test_monsters.py`

**注意：** `src/main.py` 暂时不存在，真正的游戏主入口将在未来添加。

## 常见问题

**Q: 为什么要重构？**
A: 原项目结构混乱，文件分散在不同位置，导入关系复杂。重构后层次清晰，便于维护和扩展。

**Q: 旧代码还能用吗？**
A: 可以，`games/` 目录保留了原有代码，但建议迁移到新结构。

**Q: 如何添加新怪物？**
A: 编辑 `src/systems/monsters/config.py` 和 `monster_logic.py`。

**Q: 如何修改背包大小？**
A: 编辑 `src/systems/inventory/config.py` 中的网格配置。

---

## 地图贴图系统

### 贴图资源
项目使用PNG图片作为地图瓷砖贴图，位于 `assets/tiles/` 目录：

| 文件名 | 地图符号 | 用途 | 备用颜色 |
|--------|---------|------|---------|
| road.png | `.` | 道路 | 棕色 |
| river.png | `~` | 河流 | 深蓝色 |
| house.png | `#` | 建筑/墙体 | 深灰色 |
| tree.png | `T` | 树木 | 深绿色 |
| pipe.png | `S` | 下水道入口 | 浅灰色 |

### 加载机制
游戏启动时，`src/core/drawing.py` 中的 `load_tile_images()` 函数会：
1. 首先尝试从 `assets/tiles/` 加载PNG文件
2. 如果文件存在，加载并缩放到配置的瓷砖大小（默认50x50像素）
3. 如果文件不存在或加载失败，自动使用纯色占位符

### 贴图要求
- **格式**：PNG（支持透明通道）
- **尺寸**：任意（会自动缩放到TILE_SIZE）
- **命名**：必须与上表中的文件名一致

### 替换贴图
1. 准备新的PNG文件
2. 使用相同文件名替换 `assets/tiles/` 中的对应文件
3. 重新启动游戏即可看到效果

**注意**：PNG文件的iCCP色彩配置警告不影响使用。

---

**重构完成日期**: 2025-11-16
**重构目标**: ✅ 三个测试入口点均能正常运行
**当前状态**: src/main.py 暂时不存在，将在未来实现完整的游戏主入口
