# test_game.py
# 完整游戏测试入口 - 包含地图、玩家移动、怪物系统等
import sys
import os

# 添加父目录到路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.game import Game

if __name__ == "__main__":
    try:
        g = Game()
        g.run()
    except Exception as e:
        print(f"游戏运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'g' in locals() and g:
            g.quit()
