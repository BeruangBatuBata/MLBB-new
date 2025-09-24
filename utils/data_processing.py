import pandas as pd
import json

# --- HERO PROFILES DICTIONARY (Complete) ---
HERO_PROFILES = {
    # A
    'Aamon':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['Burst', 'Magic Damage', 'Conceal', 'Pick-off']}],
    'Akai':     [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Tank'], 'tags': ['Initiator', 'Control', 'Set-up', 'Front-line', 'Forced Movement']}],
    'Aldous':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Late Game', 'Carry', 'Burst', 'Global Presence']}],
    'Alice':    [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Mage'], 'tags': ['Sustain', 'Dive', 'Magic Damage', 'AoE Damage']}],
    'Alpha':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Control', 'AoE Damage', 'Stun']}],
    'Alucard':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Carry', 'Early Game']}],
    'Angela':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Utility', 'Heal', 'Shield', 'Peel', 'Global Presence', 'Slow']}],
    'Argus':    [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Carry', 'Late Game', 'Immunity', 'Push']}],
    'Arlott': [
        {'build_name': 'Damage', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Burst', 'Dive', 'Pick-off', 'Carry', 'Stun']},
        {'build_name': 'Tank', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Tank'], 'tags': ['Sustain', 'Control', 'Front-line', 'Set-up']}
    ],
    'Atlas':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Initiator', 'Set-up', 'AoE Damage', 'Front-line', 'Airborne']}],
    'Aulus':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Carry', 'Late Game', 'High Mobility', 'Sustain Damage']}],
    'Aurora':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'AoE Damage', 'Control', 'Magic Damage', 'Freeze']}],
    # B
    'Badang':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Burst', 'Control', 'Set-up', 'Airborne']}],
    'Balmond':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Early Game', 'AoE Damage']}],
    'Bane':     [{'build_name': 'Magic', 'primary_role': 'Jungle', 'sub_role': ['Fighter', 'Mage'], 'tags': ['Poke', 'AoE Damage', 'Push', 'Magic Damage']}],
    'Barats':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Tank', 'Fighter'], 'tags': ['Sustain', 'Front-line', 'Control', 'Carry', 'AoE Damage']}],
    'Baxia':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Tank'], 'tags': ['Sustain', 'High Mobility', 'Anti-Heal', 'Short Dash']}],
    'Beatrix':  [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Poke', 'Burst', 'Sustain Damage']}],
    'Belerick': [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Control', 'Front-line', 'Peel', 'Taunt']}],
    'Benedetta':[{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Assassin'], 'tags': ['High Mobility', 'Sustain', 'Immunity', 'Split Push', 'Multi-Dash']}],
    'Brody':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Early Game', 'Burst', 'Poke']}],
    'Bruno':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Burst', 'Sustain Damage']}],
    # C
    'Carmilla': [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Control', 'Set-up', 'Sustain', 'Slow']}],
    'Cecilion': [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Late Game', 'Poke', 'Burst', 'AoE Damage']}],
    "Chang'e":  [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'AoE Damage', 'High Mobility', 'Sustain Damage']}],
    'Chip':     [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank', 'Support'], 'tags': ['Utility', 'Global Presence', 'Peel', 'Wall Pass']}],
    'Chou': [
        {'build_name': 'Damage', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Burst', 'Pick-off', 'High Mobility', 'Immunity', 'Airborne']},
        {'build_name': 'Utility', 'primary_role': 'Roam', 'sub_role': ['Fighter', 'Tank'], 'tags': ['Peel', 'Control', 'Initiator', 'Vision', 'Airborne']}
    ],
    'Cici':     [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'High Mobility', 'Poke', 'Sustain Damage']}],
    'Claude':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'AoE Damage', 'High Mobility', 'Multi-Dash']}],
    'Clint':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Early Game', 'Burst', 'Poke']}],
    'Cyclops':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Mage'], 'tags': ['Burst', 'Magic Damage', 'Single Target CC', 'Immobilize']}],
    # D
    'Diggie':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Utility', 'Disengage', 'Peel', 'Vision', 'Anti-CC']}],
    'Dyrroth':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Burst', 'Early Game', 'Dive', 'Anti-Tank']}],
    # E
    'Edith':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank', 'Marksman'], 'tags': ['Control', 'Front-line', 'Carry', 'Magic Damage', 'Airborne']}],
    'Esmeralda':[{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Mage', 'Tank'], 'tags': ['Sustain', 'Front-line', 'High Mobility', 'Sustain Damage']}],
    'Estes':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Heal', 'Sustain', 'Utility', 'Peel']}],
    'Eudora':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'Magic Damage', 'Pick-off', 'Stun']}],
    # F
    'Fanny':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['High Mobility', 'Burst', 'Carry', 'Split Push', 'Unlimited Dash', 'Wall Pass']}],
    'Faramis':  [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Support', 'Mage'], 'tags': ['Utility', 'AoE Damage', 'Magic Damage', 'Objective Control']}],
    'Floryn':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Heal', 'Sustain', 'Utility', 'Global Presence']}],
    'Franco':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Pick-off', 'Single Target CC', 'Control', 'Suppress']}],
    'Fredrinn': [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Tank', 'Fighter'], 'tags': ['Sustain', 'Control', 'Front-line', 'Utility', 'Taunt']}],
    'Freya':    [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Burst', 'AoE Damage']}],
    # G
    'Gatotkaca':[{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Tank', 'Fighter'], 'tags': ['Initiator', 'Control', 'Front-line', 'Taunt']}],
    'Gloo':     [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Tank'], 'tags': ['Sustain', 'Control', 'Dive', 'Immobilize']}],
    'Gord':     [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'AoE Damage', 'Magic Damage', 'Sustain Damage']}],
    'Granger':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Marksman'], 'tags': ['Burst', 'Early Game']}],
    'Grock':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Initiator', 'Set-up', 'Front-line', 'Burst', 'Petrify']}],
    'Guinevere':[{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter', 'Mage'], 'tags': ['Burst', 'Set-up', 'Magic Damage', 'Airborne', 'Charm']}],
    'Gusion':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin', 'Mage'], 'tags': ['Burst', 'High Mobility', 'Magic Damage', 'Pick-off']}],
    # H
    'Hanabi':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'AoE Damage', 'Immunity']}],
    'Hanzo':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['Carry', 'Late Game']}],
    'Harith':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Mage'], 'tags': ['Sustain', 'High Mobility', 'Magic Damage', 'Carry', 'Sustain Damage']}],
    'Harley':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Mage', 'Assassin'], 'tags': ['Burst', 'Pick-off', 'Magic Damage']}],
    'Hayabusa': [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['High Mobility', 'Burst', 'Pick-off', 'Split Push', 'Multi-Dash']}],
    'Helcurt':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['Burst', 'Pick-off', 'Map Control', 'Silence']}],
    'Hilda':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank', 'Fighter'], 'tags': ['Sustain', 'Early Game', 'High Mobility']}],
    'Hylos':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Sustain', 'Front-line', 'Control', 'Stun']}],
    # I
    'Irithel':  [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'AoE Damage', 'Sustain Damage']}],
    'Ixia':     [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['AoE Damage', 'Sustain', 'Late Game', 'Sustain Damage']}],
    # J
    'Jawhead':  [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Fighter', 'Tank'], 'tags': ['Pick-off', 'Single Target CC', 'Burst', 'Forced Movement']}],
    'Johnson':  [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Global Presence', 'Set-up', 'Burst', 'Long Dash']}],
    'Joy':      [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Assassin', 'Mage'], 'tags': ['High Mobility', 'Immunity', 'Dive', 'Magic Damage', 'Multi-Dash']}],
    'Julian':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Mage'], 'tags': ['Burst', 'Control', 'Sustain', 'AoE Damage']}],
    # K
    'Kadita':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Mage'], 'tags': ['Burst', 'Initiator', 'Immunity', 'Airborne']}],
    'Kagura':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'Poke', 'High Mobility']}],
    'Kaja':     [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support', 'Fighter'], 'tags': ['Pick-off', 'Single Target CC', 'Control', 'Suppress']}],
    'Karina':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin', 'Mage'], 'tags': ['Burst', 'Magic Damage', 'Carry']}],
    'Karrie':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Burst', 'Anti-Tank']}],
    'Khaleed':  [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Early Game', 'AoE Damage']}],
    'Khufra':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Initiator', 'Set-up', 'Control', 'Anti-Mobility', 'Airborne']}],
    'Kimmy':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman', 'Mage'], 'tags': ['Poke', 'Late Game', 'Hybrid Damage', 'Sustain Damage']}],
    # L
    'Lancelot': [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['High Mobility', 'Burst', 'Carry', 'Immunity', 'Multi-Dash']}],
    'Lapu-Lapu':[{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['AoE Damage', 'Sustain', 'Dive']}],
    'Layla':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Long Range']}],
    'Leomord':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'High Mobility', 'Carry']}],
    'Lesley':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Burst', 'Poke']}],
    'Ling':     [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['High Mobility', 'Burst', 'Carry', 'Late Game', 'Wall Pass']}],
    'Lolita':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank', 'Support'], 'tags': ['Peel', 'Set-up', 'Initiator', 'Front-line', 'Stun']}],
    'Lunox':    [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'Sustain', 'Magic Damage', 'Anti-Tank']}],
    'Luo Yi':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Set-up', 'AoE Damage', 'Global Presence', 'Forced Movement']}],
    'Lylia':    [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'AoE Damage', 'Magic Damage', 'High Mobility', 'Slow']}],
    # M
    'Martis':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Carry', 'Early Game', 'Immunity', 'Airborne']}],
    'Masha':    [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Split Push', 'Sustain', 'Anti-Tank']}],
    'Mathilda': [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support', 'Assassin'], 'tags': ['Utility', 'High Mobility', 'Dive', 'Peel', 'Long Dash']}],
    'Melissa':  [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Peel']}],
    'Minotaur': [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank', 'Support'], 'tags': ['Initiator', 'Set-up', 'Heal', 'Front-line', 'Airborne']}],
    'Minsitthar':[{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Fighter', 'Support'], 'tags': ['Initiator', 'Control', 'Anti-Mobility', 'Immobilize']}],
    'Miya':     [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'AoE Damage']}],
    'Moskov':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'AoE Damage']}],
    # N
    'Nana':     [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage', 'Support'], 'tags': ['Poke', 'Control', 'Set-up', 'Polymorph']}],
    'Natalia':  [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Assassin'], 'tags': ['Pick-off', 'Conceal', 'Vision', 'Silence']}],
    'Natan':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman', 'Mage'], 'tags': ['Late Game', 'Carry', 'Magic Damage', 'Sustain Damage']}],
    'Nolan':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['Burst', 'High Mobility', 'Carry']}],
    'Novaria':  [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'Long Range', 'Vision', 'Map Control', 'Wall Pass']}],
    # O
    'Obsidia':  [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'Control', 'AoE Damage', 'Set-up', 'Magic Damage']}],
    'Odette':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['AoE Damage', 'Burst', 'Set-up']}],
    # P
    'Paquito':  [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Burst', 'Early Game', 'Short Dash']}],
    'Pharsa':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['AoE Damage', 'Poke', 'Long Range', 'Global Presence', 'High Ground Defense']}],
    'Phoveus':  [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Mage'], 'tags': ['Anti-Mobility', 'Dive', 'Sustain']}],
    'Popol and Kupa': [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman', 'Support'], 'tags': ['Control', 'Push', 'Vision', 'Stun']}],
    # R
    'Rafaela':  [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Heal', 'Utility', 'High Mobility']}],
    'Roger':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter', 'Marksman'], 'tags': ['Carry', 'Burst', 'Late Game']}],
    'Ruby':     [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Tank'], 'tags': ['Sustain', 'Control', 'Peel']}],
    # S
    'Saber':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['Pick-off', 'Burst', 'Single Target CC']}],
    'Selena':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Assassin', 'Mage'], 'tags': ['Pick-off', 'Vision', 'Burst', 'Control', 'Stun']}],
    'Silvanna': [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Mage'], 'tags': ['Pick-off', 'Single Target CC', 'Magic Damage']}],
    'Sun':      [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Split Push', 'Carry', 'Late Game']}],
    # T
    'Terizla':  [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'AoE Damage', 'Set-up']}],
    'Thamuz':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Early Game', 'Dive']}],
    'Tigreal':  [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Initiator', 'Set-up', 'Front-line', 'Peel']}],
    # U
    'Uranus':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Tank'], 'tags': ['Sustain', 'Front-line', 'Split Push']}],
    # V
    'Vale':     [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'AoE Damage', 'Set-up']}],
    'Valentina':[{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'Utility', 'Magic Damage', 'High Mobility']}],
    'Valir':    [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'Control', 'Disengage']}],
    'Vexana':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['AoE Damage', 'Burst', 'Control']}],
    # W
    'Wanwan':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'High Mobility', 'Immunity']}],
    # X
    'X.Borg':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Poke', 'AoE Damage']}],
    'Xavier':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'AoE Damage', 'Long Range', 'High Ground Defense']}],
    # Y
    'Yi Sun-shin': [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Marksman', 'Assassin'], 'tags': ['Carry', 'Late Game', 'Global Presence', 'Vision']}],
    'Yin':      [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Pick-off', 'Single Target CC', 'Burst']}],
    'Yu Zhong': [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Initiator', 'Dive', 'AoE Damage', 'Sustain']}],
    'Yve':      [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['AoE Damage', 'Control', 'Poke', 'Set-up', 'High Ground Defense']}],
    # Z
    'Zhask':    [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Push', 'Poke', 'AoE Damage']}],
    'Zhuxin':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'AoE Damage', 'Sustain']}],
    'Zilong':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Assassin'], 'tags': ['Split Push', 'Pick-off', 'Late Game']}]
}

# --- HERO DAMAGE TYPE DICTIONARY (Complete) ---
HERO_DAMAGE_TYPE = {
    'Aamon': ['Magic'], 'Akai': ['Physical'], 'Aldous': ['Physical'], 'Alice': ['Magic'], 'Alpha': ['Physical'],
    'Alucard': ['Physical'], 'Angela': ['Magic'], 'Argus': ['Physical'], 'Arlott': ['Physical'], 'Atlas': ['Magic'],
    'Aulus': ['Physical'], 'Aurora': ['Magic'], 'Badang': ['Physical'], 'Balmond': ['Physical', 'True'], 'Bane': ['Physical', 'Magic'],
    'Barats': ['Physical'], 'Baxia': ['Magic'], 'Beatrix': ['Physical'], 'Belerick': ['Magic'], 'Benedetta': ['Physical'],
    'Brody': ['Physical'], 'Bruno': ['Physical'], 'Carmilla': ['Magic'], 'Cecilion': ['Magic'], "Chang'e": ['Magic'],
    'Chip': ['Magic'], 'Chou': ['Physical'], 'Cici': ['Physical'], 'Claude': ['Physical'], 'Clint': ['Physical'],
    'Cyclops': ['Magic'], 'Diggie': ['Magic'], 'Dyrroth': ['Physical'], 'Edith': ['Magic'], 'Esmeralda': ['Magic'],
    'Estes': ['Magic'], 'Eudora': ['Magic'], 'Fanny': ['Physical'], 'Faramis': ['Magic'], 'Floryn': ['Magic'],
    'Franco': ['Physical'], 'Fredrinn': ['Physical'], 'Freya': ['Physical'], 'Gatotkaca': ['Magic'], 'Gloo': ['Magic'],
    'Gord': ['Magic'], 'Granger': ['Physical'], 'Grock': ['Physical'], 'Guinevere': ['Magic'], 'Gusion': ['Magic'],
    'Hanabi': ['Physical'], 'Hanzo': ['Physical'], 'Harith': ['Magic'], 'Harley': ['Magic'], 'Hayabusa': ['Physical'],
    'Helcurt': ['Physical'], 'Hilda': ['Physical'], 'Hylos': ['Magic'], 'Irithel': ['Physical'], 'Ixia': ['Physical'],
    'Jawhead': ['Physical'], 'Johnson': ['Magic'], 'Joy': ['Magic'], 'Julian': ['Magic'], 'Kadita': ['Magic'], 'Kagura': ['Magic'],
    'Kaja': ['Magic'], 'Karina': ['Magic', 'True'], 'Karrie': ['Physical', 'True'], 'Khaleed': ['Physical'], 'Khufra': ['Physical'],
    'Kimmy': ['Physical', 'Magic'], 'Lancelot': ['Physical'], 'Lapu-Lapu': ['Physical'], 'Layla': ['Physical'], 'Leomord': ['Physical'],
    'Lesley': ['Physical', 'True'], 'Ling': ['Physical'], 'Lolita': ['Physical'], 'Lunox': ['Magic'], 'Luo Yi': ['Magic'],
    'Lylia': ['Magic'], 'Martis': ['Physical', 'True'], 'Masha': ['Physical'], 'Mathilda': ['Magic'], 'Melissa': ['Physical'],
    'Minotaur': ['Physical'], 'Minsitthar': ['Physical'], 'Miya': ['Physical'], 'Moskov': ['Physical'],
    'Nana': ['Magic'], 'Natalia': ['Physical'], 'Natan': ['Magic'], 'Nolan': ['Physical'], 'Novaria': ['Magic'],
    'Obsidia': ['Magic'], 'Odette': ['Magic'], 'Paquito': ['Physical'], 'Pharsa': ['Magic'], 'Phoveus': ['Magic'], 'Popol and Kupa': ['Physical'],
    'Rafaela': ['Magic'], 'Roger': ['Physical'], 'Ruby': ['Physical'], 'Saber': ['Physical'], 'Selena': ['Magic'],
    'Silvanna': ['Magic'], 'Sun': ['Physical'], 'Terizla': ['Physical'], 'Thamuz': ['Physical', 'True'], 'Tigreal': ['Physical'],
    'Uranus': ['Magic'], 'Vale': ['Magic'], 'Valentina': ['Magic'], 'Valir': ['Magic'], 'Vexana': ['Magic'],
    'Wanwan': ['Physical'], 'X.Borg': ['Physical', 'True'], 'Xavier': ['Magic'], 'Yi Sun-shin': ['Physical'], 'Yin': ['Physical'],
    'Yu Zhong': ['Physical'], 'Yve': ['Magic'], 'Zhask': ['Magic'], 'Zhuxin': ['Magic'], 'Zilong': ['Physical']
}

# --- TEAM NORMALIZATION AND PARSING FUNCTIONS ---
TEAM_NORMALIZATION = {
    "AP.Bren": "Falcons AP.Bren",
    "Falcons AP.Bren": "Falcons AP.Bren",
    "ECHO": "Team Liquid PH",
    "Team Liquid PH": "Team Liquid PH",
}
def normalize_team(n):
    return TEAM_NORMALIZATION.get((n or "").strip(), (n or "").strip())

def parse_matches(matches_raw):
    out=[]
    for m in matches_raw:
        if isinstance(m, str):
            try:
                m = json.loads(m)
            except:
                continue
        if not isinstance(m, dict):
            continue

        if "opponents" in m and not "match2opponents" in m:
            opps = m.get("opponents", [])
            if len(opps) != 2: continue
            teamA = opps[0].get("name", "") if isinstance(opps[0], dict) else str(opps[0])
            teamB = opps[1].get("name", "") if isinstance(opps[1], dict) else str(opps[1])
            games = m.get("games", [])
            scoreA = sum(1 for g in games if str(g.get("winner", "")) == "1")
            scoreB = sum(1 for g in games if str(g.get("winner", "")) == "2")
            if scoreA > scoreB:
                winner = "1"
            elif scoreB > scoreA:
                winner = "2"
            else:
                winner = ""

        elif "match2opponents" in m:
            opps = m.get("match2opponents", [])
            if len(opps) != 2: continue
            teamA = opps[0].get("name", "")
            teamB = opps[1].get("name", "")
            scoreA = int(opps[0].get("score", 0))
            scoreB = int(opps[1].get("score", 0))
            winner = str(m.get("winner", ""))
        else:
            continue

        if not teamA or not teamB:
            continue

        dt = pd.to_datetime(m.get("date") or m.get("datetime") or m.get("timestamp"), errors="coerce")
        if pd.isnull(dt): continue

        bestof = int(m.get("bestof", 3))
        pagename = m.get("pagename", "")
        section = m.get("section", "")

        is_regular_season = any([
            section != "Playoffs",
            "/Stage 1" in pagename,
            "/Regular_Season" in pagename,
            "/Group Stage" in pagename,
            "/Swiss Stage" in pagename,
            "/Week " in pagename,
            "Regular" in section,
            "Week" in section,
        ])

        is_playoff = any([
            section == "Playoffs",
            "/Playoffs" in pagename,
            "/Finals" in pagename,
            "/Knockouts" in pagename,
            "/Elimination" in pagename,
            "Playoff" in section,
            "Final" in section,
        ])

        out.append({
            "date": dt.date(),
            "teamA": normalize_team(teamA),
            "teamB": normalize_team(teamB),
            "bestof": bestof,
            "winner": winner,
            "scoreA": scoreA,
            "scoreB": scoreB,
            "is_regular_season": is_regular_season,
            "is_playoff": is_playoff,
            "pagename": pagename,
            "tournament": m.get("tournament", ""),
            "section": section,
            "match_id": m.get("match2id", m.get("matchid", ""))
        })

    return sorted(out, key=lambda x:x["date"])
