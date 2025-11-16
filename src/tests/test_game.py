# test_game.py
# 完整游戏测试入口 - 包含地图、玩家移动、怪物系统等
import sys
import os
import io

# 设置标准输出为UTF-8编码，避免中文显示问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加父目录到路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.game import Game
from systems.monsters.monster_logic import Monster

# 创建一个 10x10 的测试地图（全部为可通行的空地 '.'）
TEST_MAP_10x10 = """
##########
#..###...#
#..###...#
#........#
#...~~...#
#...~~...#
#...~~...#
#...~~...#
#.S....S.#
#........#
##########
""".strip()

WANDERER_NUM = 3
GHOUL_NUM = 2
BUCKET_NUM = 2

# WANDERER_NUM = 50
# GHOUL_NUM = 30
# BUCKET_NUM = 20

def test_monster_generator(city_map, current_day):
    """
    测试专用的怪物生成函数
    生成少量怪物便于测试
    允许多个怪物共享同一出生点
    """
    import random
    monsters = []
        
    # 生成 3 个普通游荡者（允许重复位置）
    wanderer_points = city_map.get_wanderer_spawn_points()
    if wanderer_points:
        for i in range(WANDERER_NUM):
            pos = random.choice(wanderer_points)  # 允许重复
            monster = Monster("Wanderer", current_day, False, pos)
            monsters.append(monster)
            print(f"[TEST] Created Wanderer #{i+1} at {pos}")
    
    # 生成 2 个普通食尸鬼（允许重复位置）
    ghoul_points = city_map.get_ghoul_spawn_points()
    if ghoul_points:
        for i in range(GHOUL_NUM):
            pos = random.choice(ghoul_points)  # 允许重复
            monster = Monster("Ghoul", current_day, False, pos)
            monsters.append(monster)
            print(f"[TEST] Created Ghoul #{i+1} at {pos}")
    
    # # 生成 2 个普通铁桶（允许重复位置）
    bucket_points = city_map.get_bucket_spawn_points()
    if bucket_points:
        for i in range(BUCKET_NUM):
            pos = random.choice(bucket_points)  # 允许重复
            monster = Monster("Bucket", current_day, False, pos)
            monsters.append(monster)
            print(f"[TEST] Created Bucket #{i+1} at {pos}")
    
    print(f"[TEST] Generated {len(monsters)} test monsters total")
    return monsters

if __name__ == "__main__":
    try:
        # 传入测试地图和测试怪物生成函数
        g = Game(custom_map=TEST_MAP_10x10, monster_generator=test_monster_generator)
        
        # 测试用：增加玩家攻击力10倍
        original_attack = g.player.logic.total_stats.get("攻击力", 10)
        g.player.logic.total_stats["攻击力"] = original_attack * 10
        print(f"[TEST] 玩家攻击力增强: {original_attack} -> {g.player.logic.total_stats['攻击力']}")
        
        g.run()
    except Exception as e:
        print(f"游戏运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'g' in locals() and g:
            g.quit()
