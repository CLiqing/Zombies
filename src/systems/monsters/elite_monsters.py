# elite_monsters.py
"""
定义精英怪物类型
每个精英类继承自对应的普通怪物类，并添加精英特有的技能
"""
import random
import pygame
from systems.monsters.monster_types import Wanderer, Bucket, Ghoul
from systems.monsters import config as mcfg


class EliteWanderer(Wanderer):
    """精英游荡者 - 拥有召唤或不死技能"""
    
    def __init__(self, level, position, elite_type='summoner'):
        """
        Args:
            elite_type: 'summoner' (呼唤者) 或 'undying' (不死者)
        """
        self.elite_type = elite_type
        super().__init__(level, is_elite=True, position=position)
        
        # 初始化精英技能状态
        if elite_type == 'summoner':
            self.last_summon_time = -999.0  # 召唤冷却
            self.summon_cooldown = mcfg.MONSTER_SKILL_PARAMS['Wanderer_Summoner_Cooldown']
        elif elite_type == 'undying':
            self.undying_active = False
            self.undying_start_time = 0.0
            self.undying_duration = mcfg.MONSTER_SKILL_PARAMS['Wanderer_Undying_Duration']
    
    def _get_elite_skills(self):
        """返回精英技能列表"""
        if self.elite_type == 'summoner':
            return ['呼唤者']
        elif self.elite_type == 'undying':
            return ['不死者']
        return []
    
    def _get_display_name(self):
        """返回更友好的名称"""
        if self.elite_type == 'summoner':
            return "精英游荡者·呼唤者"
        elif self.elite_type == 'undying':
            return "精英游荡者·不死者"
        return "精英游荡者"
    
    def can_summon(self, current_time):
        """检查是否可以召唤"""
        if self.elite_type != 'summoner':
            return False
        return (current_time - self.last_summon_time) >= self.summon_cooldown
    
    def perform_summon(self, current_time):
        """执行召唤，返回需要召唤的数量"""
        if not self.can_summon(current_time):
            return 0
        
        self.last_summon_time = current_time
        min_count = mcfg.MONSTER_SKILL_PARAMS['Wanderer_Summoner_Count_Min']
        max_count = mcfg.MONSTER_SKILL_PARAMS['Wanderer_Summoner_Count_Max']
        return random.randint(min_count, max_count)
    
    def take_damage(self, damage, damage_source="未知"):
        """
        游荡者受伤：
        1. 优先处理重生（基类技能）
        2. 如果没有重生，且是不死者，则进入残躯状态
        """
        # 如果已经在残躯状态，不受伤害
        if self.elite_type == 'undying' and self.undying_active:
            return {
                'blocked': False,
                'evaded': False,
                'actual_damage': 0,
                'died': False,
                'will_revive': False,
                'undying_active': True
            }
        
        # 调用基类处理（包括重生逻辑）
        result = super().take_damage(damage, damage_source)
        
        # 如果死亡且没有触发重生，检查不死者技能
        if result['died'] and not result.get('will_revive', False):
            if self.elite_type == 'undying' and not self.undying_active:
                # 激活残躯状态
                self.undying_active = True
                self.undying_start_time = pygame.time.get_ticks() / 1000.0
                self.is_alive = True  # 保持存活
                self.current_hp = 1  # 保持1点血
                result['died'] = False
                result['undying_triggered'] = True
                
                import config as game_config
                if game_config.DEBUG_COMBAT_LOG:
                    print(f"[COMBAT] {self.name} 触发不死者！进入残躯状态 {self.undying_duration}秒", flush=True)
        
        return result
    
    def update_undying(self, current_time):
        """更新残躯状态，返回是否应该死亡"""
        if not self.undying_active:
            return False
        
        # 检查残躯时间是否结束
        if current_time - self.undying_start_time >= self.undying_duration:
            self.undying_active = False
            self.is_alive = False
            self.current_hp = 0
            
            import config as game_config
            if game_config.DEBUG_COMBAT_LOG:
                print(f"[COMBAT] {self.name} 残躯时间结束，真正死亡", flush=True)
            return True
        
        return False


class EliteBucket(Bucket):
    """精英铁桶 - 拥有庞然或荆棘守卫技能"""
    
    def __init__(self, level, position, elite_type='titan'):
        """
        Args:
            elite_type: 'titan' (庞然) 或 'thornguard' (荆棘守卫)
        """
        self.elite_type = elite_type
        super().__init__(level, is_elite=True, position=position)
        
        # 初始化精英技能状态
        if elite_type == 'thornguard':
            self.last_thornguard_time = -999.0
            self.thornguard_cooldown = mcfg.MONSTER_SKILL_PARAMS['Bucket_Thornguard_Cooldown']
            self.thornguard_active = False
    
    def _get_elite_skills(self):
        """返回精英技能列表"""
        if self.elite_type == 'titan':
            return ['庞然']
        elif self.elite_type == 'thornguard':
            return ['荆棘守卫']
        return []
    
    def _get_display_name(self):
        """返回更友好的名称"""
        if self.elite_type == 'titan':
            return "精英铁桶·泰坦巨尸"
        elif self.elite_type == 'thornguard':
            return "精英铁桶·荆棘守卫"
        return "精英铁桶"
    
    def _calculate_base_stats(self):
        """精英铁桶属性计算"""
        super()._calculate_base_stats()
        
        # 庞然技能不影响格挡
        if self.elite_type == 'thornguard':
            # 荆棘守卫取消格挡能力
            pass
    
    def get_size_multiplier(self):
        """获取体型缩放倍数"""
        if self.elite_type == 'titan':
            return mcfg.MONSTER_SKILL_PARAMS['Bucket_Titan_Size_Mult']
        return 1.0
    
    def get_range_bonus(self):
        """获取范围加成"""
        if self.elite_type == 'titan':
            return mcfg.MONSTER_SKILL_PARAMS['Bucket_Titan_Range_Bonus']
        return 0
    
    def _get_attack_range(self):
        """获取攻击范围（庞然有额外加成）"""
        base_range = super()._get_attack_range()
        return base_range + self.get_range_bonus()
    
    def perform_attack(self, target_pos, nearby_monsters):
        """精英铁桶攻击"""
        attack_info = super().perform_attack(target_pos, nearby_monsters)
        
        # 庞然技能：范围加成已在_get_attack_range中处理
        if self.elite_type == 'titan':
            # AoE范围也增加
            attack_info['range'] = mcfg.MONSTER_SKILL_PARAMS['Bucket_AOE_Range'] + self.get_range_bonus()
        
        return attack_info
    
    def can_thornguard_reflect(self, current_time):
        """检查荆棘守卫是否可以反弹"""
        if self.elite_type != 'thornguard':
            return False
        return (current_time - self.last_thornguard_time) >= self.thornguard_cooldown
    
    def activate_thornguard(self, current_time):
        """激活荆棘守卫反弹"""
        self.last_thornguard_time = current_time
        self.thornguard_active = True
    
    def take_damage(self, damage, damage_source="未知"):
        """
        铁桶受伤：
        - 庞然：正常格挡
        - 荆棘守卫：取消格挡，改为反弹伤害
        """
        if not self.is_alive or self.is_reviving:
            return {
                'blocked': False,
                'evaded': False,
                'actual_damage': 0,
                'died': False,
                'will_revive': False,
                'reflected_damage': 0
            }
        
        current_time = pygame.time.get_ticks() / 1000.0
        
        # 荆棘守卫：纯反弹，不格挡
        if self.elite_type == 'thornguard':
            reflected_damage = 0
            if self.can_thornguard_reflect(current_time):
                reflect_factor = mcfg.MONSTER_SKILL_PARAMS['Bucket_Thornguard_Reflect_Factor']
                reflected_damage = damage * reflect_factor
                self.activate_thornguard(current_time)
                
                import config as game_config
                if game_config.DEBUG_COMBAT_LOG:
                    print(f"[COMBAT] {self.name} 荆棘守卫反弹 {reflected_damage:.1f} 伤害！", flush=True)
            
            # 受到全额伤害
            self.current_hp -= damage
            
            import config as game_config
            if game_config.DEBUG_COMBAT_LOG:
                print(f"[COMBAT] {self.name} 受到 {damage:.1f} 伤害 - HP: {self.current_hp:.1f}/{self.max_hp}", flush=True)
            
            # 判定死亡
            died = False
            if self.current_hp <= 0:
                self.current_hp = 0
                self.is_alive = False
                died = True
            
            return {
                'blocked': False,
                'evaded': False,
                'actual_damage': damage,
                'died': died,
                'will_revive': False,
                'reflected_damage': reflected_damage,
                'reflect_source': self.position if reflected_damage > 0 else None
            }
        
        # 庞然或普通：使用基类的格挡逻辑
        return super().take_damage(damage, damage_source)


class EliteGhoul(Ghoul):
    """精英食尸鬼 - 拥有暗影猎手或银翼猎手技能"""
    
    def __init__(self, level, position, elite_type='shadow'):
        """
        Args:
            elite_type: 'shadow' (暗影猎手) 或 'silverwing' (银翼猎手)
        """
        self.elite_type = elite_type
        super().__init__(level, is_elite=True, position=position)
    
    def _get_elite_skills(self):
        """返回精英技能列表"""
        if self.elite_type == 'shadow':
            return ['暗影猎手']
        elif self.elite_type == 'silverwing':
            return ['银翼猎手']
        return []
    
    def _get_display_name(self):
        """返回更友好的名称"""
        if self.elite_type == 'shadow':
            return "精英食尸鬼·暗影猎手"
        elif self.elite_type == 'silverwing':
            return "精英食尸鬼·银翼猎手"
        return "精英食尸鬼"
    
    def _calculate_base_stats(self):
        """精英食尸鬼属性计算"""
        super()._calculate_base_stats()
        
        # 暗影猎手：速度提升20%
        if self.elite_type == 'shadow':
            speed_mult = mcfg.MONSTER_SKILL_PARAMS['Ghoul_ShadowHunter_Speed_Mult']
            self.movement_speed *= speed_mult
        
        # 银翼猎手：远程攻击范围
        if self.elite_type == 'silverwing':
            self.attack_range = mcfg.MONSTER_SKILL_PARAMS['Ghoul_Silverwing_Attack_Range']
    
    def _get_attack_cooldown(self):
        """获取攻击冷却时间"""
        # 暗影猎手：固定0.7秒冷却
        if self.elite_type == 'shadow':
            return mcfg.MONSTER_SKILL_PARAMS['Ghoul_ShadowHunter_Attack_Cooldown']
        return super()._get_attack_cooldown()
    
    def perform_attack(self, target_pos, nearby_monsters):
        """
        食尸鬼攻击
        - 暗影猎手：近战攻击
        - 银翼猎手：远程弹道攻击（TODO: 需要实现弹道系统）
        """
        attack_info = super().perform_attack(target_pos, nearby_monsters)
        
        # 银翼猎手：标记为远程攻击
        if self.elite_type == 'silverwing':
            attack_info['type'] = 'projectile'
            attack_info['projectile_speed'] = mcfg.MONSTER_SKILL_PARAMS['Ghoul_Silverwing_Projectile_Speed']
        
        return attack_info

