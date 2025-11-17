# monster_factory.py
"""
怪物工厂模块
提供统一的怪物创建接口，根据参数返回对应的怪物实例
"""
import random
from systems.monsters.monster_types import Wanderer, Bucket, Ghoul
from systems.monsters.elite_monsters import EliteWanderer, EliteBucket, EliteGhoul


def create_monster(monster_type, level, is_elite, position, elite_subtype=None):
    """
    创建怪物实例的工厂函数
    
    Args:
        monster_type: 怪物类型 'Wanderer', 'Bucket', 'Ghoul'
        level: 怪物等级
        is_elite: 是否为精英怪物
        position: 初始位置 (r, c)
        elite_subtype: 精英子类型 (可选)
            - Wanderer: 'summoner' (呼唤者) 或 'undying' (不死者)
            - Bucket: 'titan' (庞然) 或 'thornguard' (荆棘守卫)
            - Ghoul: 'shadow_hunter' (暗影猎手) 或 'silverwing' (银翼猎手)
    
    Returns:
        MonsterBase: 对应的怪物实例
    
    Raises:
        ValueError: 如果monster_type不合法
    """
    if monster_type == "Wanderer":
        if is_elite:
            # 如果没有指定子类型，随机选择
            if elite_subtype is None:
                elite_subtype = random.choice(['summoner', 'undying'])
            return EliteWanderer(level, position, elite_subtype)
        else:
            return Wanderer(level, is_elite=False, position=position)
    
    elif monster_type == "Bucket":
        if is_elite:
            # 如果没有指定子类型，随机选择
            if elite_subtype is None:
                elite_subtype = random.choice(['titan', 'thornguard'])
            return EliteBucket(level, position, elite_subtype)
        else:
            return Bucket(level, is_elite=False, position=position)
    
    elif monster_type == "Ghoul":
        if is_elite:
            # 如果没有指定子类型，随机选择
            if elite_subtype is None:
                elite_subtype = random.choice(['shadow', 'silverwing'])
            return EliteGhoul(level, position, elite_subtype)
        else:
            return Ghoul(level, is_elite=False, position=position)
    
    else:
        raise ValueError(f"未知的怪物类型: {monster_type}")


# 为了向后兼容，保留旧的Monster类名
class Monster:
    """
    向后兼容的Monster类
    实际上是create_monster的包装
    """
    def __new__(cls, monster_type, level, is_elite, position, elite_subtype=None):
        return create_monster(monster_type, level, is_elite, position, elite_subtype)
