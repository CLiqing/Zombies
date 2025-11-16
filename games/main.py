# main.py
from game import Game

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