"""Load a small demo data set through the application use cases."""

from django.core.management.base import BaseCommand
from django.db import transaction

from cardcraft.container import get_container
from cardcraft.domain.queries import ListQuery

DEMO = {
    "system": {
        "name": "Ironvale Fantasy",
        "description": "A classic sword-and-sorcery system with d20 checks and gritty resource management.",
    },
    "campaigns": [
        {"name": "The Ashen Crown", "description": "A dethroned king's heir gathers allies among the ruins of the old capital."},
        {"name": "Tides of Saltmere", "description": "Smugglers, sea witches and a drowned lighthouse that still shines at night."},
    ],
    "items": [
        {"name": "Longsword", "item_type": "Weapon", "rarity": "common", "cost": "15 gp", "weight": "3 lb",
         "description": "Versatile steel blade. Deals 1d8 slashing damage, or 1d10 when wielded with two hands."},
        {"name": "Healing Draught", "item_type": "Potion", "rarity": "common", "cost": "50 gp", "weight": "0.5 lb",
         "description": "A bitter red tonic. Drinking it restores 2d4 + 2 hit points."},
        {"name": "Cloak of Embers", "item_type": "Wondrous", "rarity": "rare", "cost": "4,000 gp", "weight": "1 lb",
         "description": "While wearing this charred cloak you resist fire damage. Once per day you can wreathe yourself in harmless flames, gaining advantage on Intimidation checks for 1 minute.",
         "campaign": 0},
        {"name": "Saltmere Compass", "item_type": "Wondrous", "rarity": "uncommon", "cost": "600 gp", "weight": "—",
         "description": "Its needle points to the nearest submerged wreck within one mile.", "campaign": 1},
        {"name": "Crown of the Last King", "item_type": "Artifact", "rarity": "legendary", "cost": "Priceless", "weight": "2 lb",
         "description": "The wearer can issue a one-word command to any creature that can hear them. Each use adds a point of Corruption.",
         "campaign": 0},
    ],
    "races": [
        {"name": "Human", "description": "Adaptable and ambitious, humans thrive wherever they settle.",
         "skills": [
             {"name": "Versatile", "kind": "passive", "description": "Gain proficiency in one extra skill of your choice."},
             {"name": "Second Wind", "kind": "active", "cost": "1/rest", "description": "As a bonus action regain hit points equal to your level."},
         ]},
        {"name": "Elf", "description": "Long-lived wanderers with keen senses and a deep bond with the wild.",
         "skills": [
             {"name": "Darkvision", "kind": "passive", "description": "See in dim light within 60 ft as if it were bright light."},
             {"name": "Trance", "kind": "passive", "description": "Rest for 4 hours in meditation to gain the benefits of a long rest."},
         ]},
        {"name": "Dwarf", "description": "Stout mountain folk, famed smiths and stubborn allies.",
         "skills": [
             {"name": "Stonecunning", "kind": "passive", "description": "Double your proficiency bonus on checks related to stonework."},
             {"name": "Iron Gut", "kind": "reaction", "description": "When poisoned, roll a d6. On 4+ the effect ends immediately."},
         ]},
    ],
    "classes": [
        {"name": "Warrior", "description": "Masters of arms and armor who hold the front line.",
         "skills": [
             {"name": "Cleave", "kind": "active", "level": 1, "cost": "2 stamina", "description": "Strike up to two adjacent enemies with a single melee attack."},
             {"name": "Shield Wall", "kind": "reaction", "level": 3, "cost": "1 stamina", "description": "Reduce damage taken by an adjacent ally by 1d10 + your level."},
         ]},
        {"name": "Mage", "description": "Scholars who bend arcane energy through study and willpower.",
         "skills": [
             {"name": "Arcane Bolt", "kind": "active", "level": 1, "cost": "1 mana", "description": "Ranged spell attack, 120 ft. Deals 1d10 force damage."},
             {"name": "Counterspell", "kind": "reaction", "level": 5, "cost": "3 mana", "description": "Interrupt a creature casting a spell within 60 ft. Spells of level 3 or lower fail."},
         ]},
        {"name": "Rogue", "description": "Cunning specialists who strike from the shadows.",
         "skills": [
             {"name": "Sneak Attack", "kind": "passive", "level": 1, "description": "Once per turn, deal an extra 1d6 damage to a target you have advantage against."},
             {"name": "Vanish", "kind": "active", "level": 7, "cost": "1/rest", "description": "Become invisible until the end of your next turn."},
         ]},
    ],
}


class Command(BaseCommand):
    help = "Create a demo RPG system with campaigns, items, races, classes and skills."

    @transaction.atomic
    def handle(self, *args, **options):
        container = get_container()
        existing = container.systems.list.execute(ListQuery(search=DEMO["system"]["name"]))
        if existing.total:
            self.stdout.write(self.style.WARNING("Demo data already present; nothing to do."))
            return

        system = container.systems.create.execute(DEMO["system"])
        campaigns = [
            container.campaigns.create.execute({**data, "system_id": system.id}) for data in DEMO["campaigns"]
        ]

        for data in DEMO["items"]:
            data = dict(data)
            campaign_index = data.pop("campaign", None)
            campaign_id = campaigns[campaign_index].id if campaign_index is not None else None
            container.items.create.execute({**data, "system_id": system.id, "campaign_id": campaign_id})

        for data in DEMO["races"]:
            race = container.races.create.execute(
                {"name": data["name"], "description": data["description"], "system_id": system.id}
            )
            for skill in data["skills"]:
                container.race_skills.create.execute({**skill, "race_id": race.id})

        for data in DEMO["classes"]:
            character_class = container.classes.create.execute(
                {"name": data["name"], "description": data["description"], "system_id": system.id}
            )
            for skill in data["skills"]:
                container.class_skills.create.execute({**skill, "class_id": character_class.id})

        self.stdout.write(self.style.SUCCESS(f"Demo system '{system.name}' created."))
