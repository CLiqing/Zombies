# test_monsters.py
# 怪物系统测试入口
import sys
import os
from typing import List

# 添加父目录到路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from systems.citymap.citymap import CityMap 
    from systems.monsters.monster_logic import Monster, generate_monsters
except ImportError as e:
    print(f"导入错误：请确保 'citymap' 和 'monsters' 文件夹结构正确。错误信息: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def display_monster_list(monsters: List[Monster]):
    """格式化并打印怪物列表信息。"""
    if not monsters:
        print("未生成任何怪物。")
        return

    print(f"--- 👾 怪物生成结果 (总数: {len(monsters)}) ---")

    # 按怪物类型和精英/普通分组
    grouped = {}
    for m in monsters:
        key = f"{m.type} ({'精英' if m.is_elite else '普通'})"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(m)

    # 打印分组信息
    for group_key, m_list in grouped.items():
        print(f"\n## {group_key} ({m_list[0].name}，数量: {len(m_list)})")
        
        # 打印详细信息（取前5个作为示例）
        for i, m in enumerate(m_list[:5]):
            info = m.get_info()
            print(f"  [{i+1}] {info['名称']} (Lv {info['等级(a)']})")
            print(f"    位置: {info['位置(r, c)']} | 移速: {info['移动速度']}")
            print(f"    HP: {info['Max HP']} | 护甲: {info['护甲(Armor)']} | 攻击力: {info['攻击力(DMG)']}")
            print(f"    基础技能: {info['基础技能']}")
            print(f"    进阶技能: {info['进阶技能']}")
            print(f"    精英/分支技能: {info['精英技能']}")
            
        if len(m_list) > 5:
            print(f"    ... (省略了 {len(m_list) - 5} 个同类怪物)")
            
def run_main():
    """主测试函数，用于接收天数输入并生成怪物。"""
    
    try:
        days_input = input("请输入要测试的游戏天数 (例如: 10, 50, 100): ")
        current_day = int(days_input)
    except ValueError:
        print("输入无效，请确保输入一个整数。")
        return

    if current_day <= 0:
        print("天数必须大于 0。")
        return
    
    print(f"\n--- ⏳ 正在模拟第 {current_day} 天的怪物生成 ---")
    
    try:
        # 1. 初始化地图
        game_map = CityMap()
        width, height = game_map.get_dimensions()
        map_area = width * height
        print(f"地图加载成功。尺寸: {width}x{height} = {map_area} 格。")
        
        # 2. 生成怪物列表
        active_monsters = generate_monsters(game_map, current_day)
        
        # 3. 显示结果
        display_monster_list(active_monsters)

    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print(f"\n致命错误：地图或配置加载失败。错误信息: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_main()
