# test_elite.py
# 精英怪物测试入口 - 创建每种精英怪物各一只
import sys
import os
import io

# 设置标准输出为UTF-8编码，避免中文显示问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加父目录到路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.game import Game
from systems.monsters.monster_factory import Monster

# 创建一个测试地图
TEST_MAP_ELITE = """
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


def test_elite_monster_generator(city_map, current_day):
    """
    精英怪物测试专用生成函数
    创建每种精英怪物各一只
    """
    monsters = []
    
    # 获取出生点
    wanderer_points = city_map.get_wanderer_spawn_points()
    ghoul_points = city_map.get_ghoul_spawn_points()
    bucket_points = city_map.get_bucket_spawn_points()
    
    # 创建精英游荡者·呼唤者（使用更安全的位置）
    if len(wanderer_points) > 2:
        pos = wanderer_points[2]  # 使用第3个点，避免边缘
        monster = Monster("Wanderer", current_day, True, pos, elite_subtype='summoner')
        monsters.append(monster)
        print(f"[TEST] Created {monster.name} at {pos}")
    
    # 创建精英游荡者·不死者
    if len(wanderer_points) > 3:
        pos = wanderer_points[3]  # 使用第4个点
        monster = Monster("Wanderer", current_day, True, pos, elite_subtype='undying')
        monsters.append(monster)
        print(f"[TEST] Created {monster.name} at {pos}")
    
    # 创建精英铁桶·泰坦巨尸
    if len(bucket_points) > 0:
        pos = bucket_points[0]
        monster = Monster("Bucket", current_day, True, pos, elite_subtype='titan')
        monsters.append(monster)
        print(f"[TEST] Created {monster.name} at {pos}")
    
    # 创建精英铁桶·荆棘守卫
    if len(bucket_points) > 1:
        pos = bucket_points[1]
        monster = Monster("Bucket", current_day, True, pos, elite_subtype='thornguard')
        monsters.append(monster)
        print(f"[TEST] Created {monster.name} at {pos}")
    
    # 创建精英食尸鬼·暗影猎手
    if ghoul_points:
        pos = ghoul_points[0]
        monster = Monster("Ghoul", current_day, True, pos, elite_subtype='shadow')
        monsters.append(monster)
        print(f"[TEST] Created {monster.name} at {pos}")
    
    # 创建精英食尸鬼·银翼猎手（暂时使用基础实现）
    if len(ghoul_points) > 1:
        pos = ghoul_points[1]
        monster = Monster("Ghoul", current_day, True, pos, elite_subtype='silverwing')
        monsters.append(monster)
        print(f"[TEST] Created {monster.name} at {pos}")
    
    print(f"[TEST] Generated {len(monsters)} elite monsters total")
    return monsters


if __name__ == "__main__":
    try:
        # 传入测试地图和精英怪物生成函数
        g = Game(custom_map=TEST_MAP_ELITE, monster_generator=test_elite_monster_generator)
        
        # 测试用：增加玩家攻击力500倍（精英怪物血量更高）
        original_attack = g.player.logic.total_stats.get("攻击力", 10)
        g.player.logic.total_stats["攻击力"] = original_attack * 500
        print(f"[TEST] 玩家攻击力增强: {original_attack} -> {g.player.logic.total_stats['攻击力']}")
        
        g.run()
    except Exception as e:
        print(f"游戏运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'g' in locals() and g:
            g.quit()
