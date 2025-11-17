# monster_types.py
"""
定义三种普通怪物类型: Wanderer, Bucket, Ghoul
每个类继承自 MonsterBase 并实现特定的技能和行为
"""
import random
import pygame
from systems.monsters.monster_base import MonsterBase
from systems.monsters import config as mcfg


class Wanderer(MonsterBase):
    """游荡者 - 近战怪物，拥有团结光环和重生技能"""
    
    def __init__(self, level, is_elite, position):
        super().__init__("Wanderer", level, is_elite, position)
    
    def _calculate_base_stats(self):
        """游荡者速度稍快"""
        super()._calculate_base_stats()
        if not self.is_elite:
            self.movement_speed = 1.1
    
    def _get_elite_skills(self):
        """游荡者精英只有召唤技能"""
        if not self.is_elite:
            return []
        return ['召唤']
    
    def _init_skills(self):
        """初始化游荡者技能"""
        self.skills_active['revive_timer'] = 0.0
        self.revive_delay = mcfg.MONSTER_SKILL_PARAMS["Wanderer_Revive_Delay"]
    
    def calculate_damage(self, nearby_monsters):
        """游荡者：团结光环（附近每有一个游荡者，攻击力提升10%）"""
        base_damage = self.damage
        
        wanderer_count = sum(1 for m, dist in nearby_monsters 
                           if m.type == "Wanderer" and dist <= mcfg.MONSTER_SKILL_PARAMS["Wanderer_Aura_Range"])
        if wanderer_count > 0:
            bonus = wanderer_count * mcfg.MONSTER_SKILL_PARAMS["Wanderer_Aura_Factor"]
            base_damage *= (1 + bonus)
        
        return base_damage
    
    def take_damage(self, damage, damage_source="未知"):
        """游荡者受伤：死亡后会复活一次"""
        result = super().take_damage(damage, damage_source)
        
        # 游荡者：复活判定
        if result['died'] and not self.has_revived:
            result['will_revive'] = True
            self.is_reviving = True
            self.revive_timer = mcfg.MONSTER_SKILL_PARAMS['Wanderer_Revive_Delay']
            self.has_revived = True  # 标记已使用复活
        
        return result
    
    def get_base_skill_info(self):
        """返回先天技能信息"""
        return "无"
        
    def get_advanced_skill_info(self):
        """返回进阶技能信息"""
        info = []
        info.append(f"团结光环({mcfg.MONSTER_SKILL_PARAMS['Wanderer_Aura_Factor']*100:.0f}% DMG, 可叠加)")
        info.append(f"重生(3秒后复活)")
        return ", ".join(info)


class Bucket(MonsterBase):
    """铁桶 - AoE怪物，拥有格挡、护甲光环和尸爆技能"""
    
    def __init__(self, level, is_elite, position):
        super().__init__("Bucket", level, is_elite, position)
    
    def _get_elite_skills(self):
        """铁桶精英随机获得烈爆或巨人技能"""
        if not self.is_elite:
            return []
        return random.choice([['烈爆'], ['巨人']])
    
    def _init_skills(self):
        """初始化铁桶技能"""
        self.skills_active['giant_stacks'] = 0
    
    def perform_attack(self, target_pos, nearby_monsters):
        """铁桶：AoE圆环攻击"""
        damage = self.calculate_damage(nearby_monsters)
        
        attack_info = {
            'damage': damage,
            'attacker_name': self.name,
            'attacker_type': self.type,
            'position': target_pos,
            'armor_ignore': 0,
            'type': 'aoe',
            'range': self.attack_range
        }
        
        return attack_info
    
    def take_damage(self, damage, damage_source="未知"):
        """铁桶受伤：15%概率格挡，减少90%伤害"""
        if not self.is_alive or self.is_reviving:
            return {
                'blocked': False,
                'evaded': False,
                'actual_damage': 0,
                'died': False,
                'will_revive': False
            }
        
        blocked = False
        actual_damage = damage
        current_time = pygame.time.get_ticks() / 1000.0
        
        # 铁桶：格挡判定
        block_cd = mcfg.MONSTER_SKILL_PARAMS['Bucket_Block_Cooldown']
        if current_time - self.last_block_time >= block_cd:
            block_chance = mcfg.MONSTER_SKILL_PARAMS['Bucket_Block_Chance']
            if random.random() < block_chance:
                blocked = True
                self.last_block_time = current_time
                reduction = mcfg.MONSTER_SKILL_PARAMS['Bucket_Block_Reduction']
                actual_damage *= (1 - reduction)  # 减少90%伤害
        
        # 扣除生命值
        self.current_hp -= actual_damage
        
        # Debug日志
        import config as game_config
        if game_config.DEBUG_COMBAT_LOG:
            if blocked:
                print(f"[COMBAT] {self.name} 格挡！受到 {actual_damage:.1f} 伤害（原始：{damage:.1f}，减免90%）- HP: {self.current_hp:.1f}/{self.max_hp}", flush=True)
            else:
                print(f"[COMBAT] {self.name} 受到 {actual_damage:.1f} 伤害 - HP: {self.current_hp:.1f}/{self.max_hp}", flush=True)
        
        # 判定死亡
        died = False
        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_alive = False
            died = True
        
        return {
            'blocked': blocked,
            'evaded': False,
            'actual_damage': actual_damage,
            'died': died,
            'will_revive': False
        }
    
    def get_base_skill_info(self):
        """返回先天技能信息"""
        return f"概率格挡({mcfg.MONSTER_SKILL_PARAMS['Bucket_Block_Chance']*100:.0f}%), 范围AoE({mcfg.MONSTER_SKILL_PARAMS['Bucket_AOE_Range']}px)"
        
    def get_advanced_skill_info(self):
        """返回进阶技能信息"""
        info = []
        info.append(f"护甲光环({mcfg.MONSTER_SKILL_PARAMS['Bucket_Armor_Aura_Factor']*100:.0f}% Armor)")
        info.append(f"尸爆({mcfg.MONSTER_SKILL_PARAMS['Bucket_Corpse_Explosion_HP_Dmg']*100:.0f}% MaxHP Dmg)")
        return ", ".join(info)


class Ghoul(MonsterBase):
    """食尸鬼 - 快速近战怪物，拥有迅扑、闪避和独狼技能"""
    
    def __init__(self, level, is_elite, position):
        super().__init__("Ghoul", level, is_elite, position)
    
    def _get_elite_skills(self):
        """食尸鬼精英随机获得暴击或飞天技能"""
        if not self.is_elite:
            return []
        return random.choice([['暴击'], ['飞天']])
    
    def _init_skills(self):
        """初始化食尸鬼技能"""
        self.evade_chance = mcfg.MONSTER_SKILL_PARAMS["Ghoul_Evade_Chance"]
        
        # 所有食尸鬼都有嗜血技能
        self.crit_chance = mcfg.MONSTER_SKILL_PARAMS["Ghoul_Bloodthirst_Crit_Chance"]
        self.crit_damage_mult = mcfg.MONSTER_SKILL_PARAMS["Ghoul_Bloodthirst_Crit_Dmg_Mult"]
        self.lifesteal_factor = mcfg.MONSTER_SKILL_PARAMS["Ghoul_Bloodthirst_Lifesteal"]
        self.last_crit = False  # 标记上次攻击是否暴击
    
    def perform_attack(self, target_pos, nearby_monsters):
        """食尸鬼：近战攻击 + 独狼技能（20%护甲穿透）+ 嗜血技能"""
        base_damage = self.calculate_damage(nearby_monsters)
        
        # 嗜血技能：暴击判定
        is_crit = random.random() < self.crit_chance
        if is_crit:
            base_damage *= self.crit_damage_mult
        
        self.last_crit = is_crit  # 记录暴击状态
        
        attack_info = {
            'damage': base_damage,
            'attacker_name': self.name,
            'attacker_type': self.type,
            'position': target_pos,
            'armor_ignore': mcfg.MONSTER_SKILL_PARAMS['Ghoul_Lone_Wolf_Armor_Ignore'],
            'type': 'melee',
            'is_crit': is_crit,
            'lifesteal_factor': self.lifesteal_factor if is_crit else 0  # 只有暴击才吸血
        }
        
        return attack_info
    
    def take_damage(self, damage, damage_source="未知"):
        """食尸鬼受伤：20%概率完全闪避"""
        if not self.is_alive or self.is_reviving:
            return {
                'blocked': False,
                'evaded': False,
                'actual_damage': 0,
                'died': False,
                'will_revive': False
            }
        
        evaded = False
        actual_damage = damage
        
        # 食尸鬼：闪避判定
        evade_chance = mcfg.MONSTER_SKILL_PARAMS['Ghoul_Evade_Chance']
        if random.random() < evade_chance:
            evaded = True
            actual_damage = 0  # 完全闪避
        
        # 扣除生命值
        self.current_hp -= actual_damage
        
        # Debug日志
        import config as game_config
        if game_config.DEBUG_COMBAT_LOG:
            if evaded:
                print(f"[COMBAT] {self.name} 闪避！完全躲开攻击 - HP: {self.current_hp:.1f}/{self.max_hp}", flush=True)
            else:
                print(f"[COMBAT] {self.name} 受到 {actual_damage:.1f} 伤害 - HP: {self.current_hp:.1f}/{self.max_hp}", flush=True)
        
        # 判定死亡
        died = False
        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_alive = False
            died = True
        
        return {
            'blocked': False,
            'evaded': evaded,
            'actual_damage': actual_damage,
            'died': died,
            'will_revive': False
        }
    
    def get_base_skill_info(self):
        """返回先天技能信息"""
        return f"迅扑(距{mcfg.MONSTER_SKILL_PARAMS['Ghoul_Dash_Min_Range']}~{mcfg.MONSTER_SKILL_PARAMS['Ghoul_Dash_Max_Range']}px)"
        
    def get_advanced_skill_info(self):
        """返回进阶技能信息"""
        info = []
        info.append(f"闪避({mcfg.MONSTER_SKILL_PARAMS['Ghoul_Evade_Chance']*100:.0f}%)")
        info.append(f"独狼(无视{mcfg.MONSTER_SKILL_PARAMS['Ghoul_Lone_Wolf_Armor_Ignore']*100:.0f}%护甲)")
        info.append(f"嗜血({mcfg.MONSTER_SKILL_PARAMS['Ghoul_Bloodthirst_Crit_Chance']*100:.0f}%暴击, {mcfg.MONSTER_SKILL_PARAMS['Ghoul_Bloodthirst_Crit_Dmg_Mult']*100:.0f}%伤害, {mcfg.MONSTER_SKILL_PARAMS['Ghoul_Bloodthirst_Lifesteal']*100:.0f}%吸血)")
        return ", ".join(info)
