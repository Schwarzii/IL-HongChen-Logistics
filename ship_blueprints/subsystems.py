import time


class TechPoint:
    def __init__(self, system_property, idx, limit=5):
        self.property = system_property
        self.idx = idx
        self.limit = limit

    def __get__(self, instance, owner):
        if self.idx < len(instance):
            return self.property * (1 + sum(instance))
        else:
            raise KeyError('no upgrade')

    def __set__(self, instance, correction):
        if self.idx < len(instance):
            instance[self.idx] = correction
        else:
            instance.append(correction)


class TechSlot:
    def __init__(self, name, description, point):
        self.name = name
        self.description = description
        self.point = point
        self._limit = len(self.point)

        self.upgraded = 0  # Count of upgrade
        self.step = 0
        self._effect = 0

    def upgrade_effect(self, sys_property):
        sys_property[0].append(self)
        self.step = sys_property[1]  # Integer [%]

    def change_point(self, count):
        clamping = sorted([0, self.upgraded + count, self._limit])[1]
        self.upgraded = clamping
        self._effect = clamping * self.step

    def spent_points(self):
        return sum(self.point[:self.upgraded])

    @property
    def effect(self):
        return 0.01 * self._effect

    def __str__(self):
        return self.description.format(abs(self._effect))


class MultiTechSlot(TechSlot):
    def __init__(self, name, description, point):
        super().__init__(name, description, point)
        self.sub_tech_slot = []

    def upgrade_effect(self, sys_properties):
        for sp in sys_properties:  # sp -> sub property
            sub_tech_slot = TechSlot(self.name, self.description, self.point)
            sub_tech_slot.upgrade_effect(sp)
            self.sub_tech_slot.append(sub_tech_slot)

    def change_point(self, count):
        for t in self.sub_tech_slot:
            t.change_point(count)

    def __str__(self):
        return self.description.format(*(t for t in self.sub_tech_slot))


class Strategy:
    pass


class Weapon:
    # {'Weapon_type': (direct T/F, energy T/F, basic_accuracy)}
    weapons = {'generic_battery': (True, False), 'cannon': (True, False), 'rail_gun': (True, False),
               'ion_cannon': (True, True), 'pulse_cannon': (True, True),
               'missile': (False, False), 'torpedo': (False, False), 'energy_torpedo': (False, True)}
    small_ships = ['destroyer', 'frigate']
    large_ships = ['carrier', 'battlecruiser', 'cruiser']
    aircraft = ['corvette', 'fighter']
    air_defense_type = ['self', 'current_row', 'own_side', 'opponent_side']
    system_damage_list = ['weapon', 'propulsion', 'command', 'hangar']

    def __init__(self, name, number, weapon_type, target_priority, unit_damage,
                 interval, targeting, duration=0, cycle=None):
        self.number = number  # Number of weapon modules in the system
        self.name = name  # Name of the weapon module

        self.weapon_type = weapon_type  # Weapon type
        self.direct, self.damage_type = self.weapons[weapon_type]  # Direct/Indirect fire, projectile/energy damage

        self.target = target_priority  # Small ship, large ship or aircraft
        self.target_queue = self._target_queue()

        self._unit_damage = [unit_damage]  # Basic anti-ship damage per fire
        self._air_defense = 0
        self._siege_damage = 0

        self._ss_accuracy = []  # small ship accuracy
        self._ls_accuracy = []  # large ship accuracy
        self._air_accuracy = []  # aircraft accuracy

        if cycle:
            self._cycle = cycle
        else:
            self._cycle = [1, 1]  # Round, fire per round
        self._interval = [interval]
        self._targeting = [targeting]
        self._duration = [duration]

        self.air_defense_type = None
        self.interception = None
        self.system_damage = None
        self.critical_damage = False

    def _target_queue(self):
        if self.target == 'aircraft_f':
            return self.aircraft + self.small_ships
        elif self.target == 'aircraft_c':
            return self.aircraft[::] + self.small_ships
        elif self.target == 'small_ship':
            return self.small_ships
        else:
            return self.large_ships

    def damage_mapping(self, air_multiplier, siege_multiplier):
        pass

    def dpm(self):
        return self.number * self.unit_damage * self.cycle[0] * self.cycle[1] * 60 / (self.interval + self.duration)

    def tech_slot_bonus(self, tech_slot, tech_effect):
        tech = tech_slot
        if len(tech_effect) > 1:
            tech.upgrade_effect([(getattr(self, f'_{p}'), e) for p, e in tech_effect.items()])
        else:
            unpacked_tech = list(tech_effect.items())[0]
            tech.upgrade_effect((getattr(self, f'_{unpacked_tech[0]}'), unpacked_tech[1]))

    @staticmethod
    def get_property(attribute):
        return round(attribute[0] * (1 + sum(t.effect for t in attribute[1:])), 1)

    @property
    def unit_damage(self):
        return self.get_property(self._unit_damage)

    @property
    def cycle(self):
        return self._cycle

    @property
    def interval(self):
        return self.get_property(self._interval)

    @property
    def targeting(self):
        return self.get_property(self._targeting)

    @property
    def duration(self):
        return self.get_property(self._duration)


class MainWeapon:
    def __init__(self, system_weapons, structure):
        self.weapons = system_weapons
        self.structure = structure
        self.system_tech = {}

    def add_system_tech(self, tech_slot, tech_effect):
        for w in self.weapons:
            w.tech_slot_bonus(tech_slot, tech_effect)
            self.system_tech[tech_slot.name] = tech_slot

    @property
    def dpm(self):
        return sum(w.dpm() for w in self.weapons[0])


if __name__ == '__main__':
    torpedo = Weapon('xxx', 2, 'torpedo', 'aircraft_c', 35, 20, 3, 10, [4, 5])
    ws = MainWeapon([torpedo], 4000)
    # ws.add_system_tech(TechSlot('供弹机构强化', '冷却减少{0}%', [1, 1, 2, 2, 2]), {'interval': -3})
    # ws.system_tech['供弹机构强化'].change_point(1)
    # print(ws.weapons.interval)
    print(ws.weapons[0].dpm())
    # ws.add_system_tech(MultiTechSlot('额外充电', '提高轨道炮伤害{0}，冷却时间提高{1}', [10]),
    #                    {'unit_damage': 40, 'interval': 20})
    # print(ws.weapons.unit_damage)
    # print(ws.weapons.interval)
    # ws.system_tech['额外充电'].change_point(1)
    # print(ws.weapons.unit_damage)
    # print(ws.weapons.interval)
