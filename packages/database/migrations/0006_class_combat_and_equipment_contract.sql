-- ORIGINS DATA FOUNDATION V1
-- Canonical class combat roles and Zircon-compatible equipment slots.

BEGIN;

CREATE TABLE content.class_combat_profiles (
    class_id                smallint PRIMARY KEY REFERENCES content.class_definitions(id) ON DELETE CASCADE,
    primary_offense_stat    varchar(16) NOT NULL,
    secondary_offense_stat  varchar(16),
    physical_stat           varchar(16),
    skill_stat              varchar(16),
    notes                   text,
    CHECK (primary_offense_stat IN ('DC','MC','SC')),
    CHECK (secondary_offense_stat IS NULL OR secondary_offense_stat IN ('DC','MC','SC')),
    CHECK (physical_stat IS NULL OR physical_stat IN ('DC','MC','SC')),
    CHECK (skill_stat IS NULL OR skill_stat IN ('DC','MC','SC'))
);

INSERT INTO content.class_combat_profiles
    (class_id, primary_offense_stat, secondary_offense_stat, physical_stat, skill_stat, notes)
VALUES
    (1, 'DC', NULL, 'DC', 'DC', 'Warrior: DC drives physical/offensive skills.'),
    (2, 'MC', NULL, 'DC', 'MC', 'Wizard: MC drives magic; basic physical attack may still use DC.'),
    (3, 'SC', NULL, 'DC', 'SC', 'Taoist: SC drives Taoist magic; basic physical attack may still use DC.'),
    (4, 'DC', NULL, 'DC', 'DC', 'Assassin: Crystal combat is primarily DC.'),
    (5, 'DC', 'MC', 'DC', 'MC', 'Archer: DC physical/ranged base plus MC for elemental/trap skill power.'),
    (6, 'DC', 'SC', 'DC', 'SC', 'Monk: DC physical techniques plus SC spiritual/skill scaling.');

-- Mirrors Zircon EquipmentSlot numbering so imported equipment can retain slot IDs.
CREATE TABLE content.equipment_slot_definitions (
    id          smallint PRIMARY KEY,
    slot_code   varchar(32) NOT NULL UNIQUE,
    display_name varchar(64) NOT NULL,
    equip_group varchar(32) NOT NULL DEFAULT 'character'
);

INSERT INTO content.equipment_slot_definitions (id, slot_code, display_name, equip_group) VALUES
    (0, 'weapon', 'Weapon', 'character'),
    (1, 'armour', 'Armour', 'character'),
    (2, 'helmet', 'Helmet', 'character'),
    (3, 'torch', 'Torch', 'character'),
    (4, 'necklace', 'Necklace', 'character'),
    (5, 'bracelet_left', 'Bracelet Left', 'character'),
    (6, 'bracelet_right', 'Bracelet Right', 'character'),
    (7, 'ring_left', 'Ring Left', 'character'),
    (8, 'ring_right', 'Ring Right', 'character'),
    (9, 'shoes', 'Shoes', 'character'),
    (10, 'poison', 'Poison', 'character'),
    (11, 'amulet', 'Amulet', 'character'),
    (12, 'flower', 'Flower', 'character'),
    (13, 'horse_armour', 'Horse Armour', 'character'),
    (14, 'emblem', 'Emblem', 'character'),
    (15, 'shield', 'Shield', 'character'),
    (16, 'costume', 'Costume', 'character'),
    (17, 'hook', 'Hook', 'fishing'),
    (18, 'float', 'Float', 'fishing'),
    (19, 'bait', 'Bait', 'fishing'),
    (20, 'finder', 'Finder', 'fishing'),
    (21, 'reel', 'Reel', 'fishing');

-- Normalised view of the legacy mask retained on item_definitions. The new
-- authoritative rule is item_allowed_classes; this view is for import/debug only.
CREATE VIEW content.class_offense_stats AS
SELECT
    c.id AS class_id,
    c.code AS class_code,
    p.primary_offense_stat,
    p.secondary_offense_stat,
    p.physical_stat,
    p.skill_stat
FROM content.class_definitions c
JOIN content.class_combat_profiles p ON p.class_id = c.id;

CREATE FUNCTION content.can_class_equip_item_in_slot(
    p_item_definition_id bigint,
    p_class_id smallint,
    p_slot_code varchar
)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT
        content.can_class_equip_item(p_item_definition_id, p_class_id)
        AND (
            NOT EXISTS (
                SELECT 1 FROM content.item_equip_slots s
                WHERE s.item_definition_id = p_item_definition_id
            )
            OR EXISTS (
                SELECT 1 FROM content.item_equip_slots s
                WHERE s.item_definition_id = p_item_definition_id
                  AND s.slot_code = p_slot_code
            )
        );
$$;

COMMIT;
