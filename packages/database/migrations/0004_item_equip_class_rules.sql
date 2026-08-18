-- ORIGINS DATA FOUNDATION V1
-- Authoritative equipment restrictions. Client UI may hide invalid equipment,
-- but the server/database contract remains the source of truth.

BEGIN;

ALTER TABLE content.item_definitions
    ADD COLUMN class_restriction_mode varchar(16) NOT NULL DEFAULT 'all',
    ADD CONSTRAINT item_class_restriction_mode_check
        CHECK (class_restriction_mode IN ('all','restricted','none'));

-- Explicit allow-list for class-restricted items. This avoids extending Zircon's
-- four-class RequiredClass bit mask and works natively with Archer + Monk.
CREATE TABLE content.item_allowed_classes (
    item_definition_id  bigint NOT NULL REFERENCES content.item_definitions(id) ON DELETE CASCADE,
    class_id            smallint NOT NULL REFERENCES content.class_definitions(id) ON DELETE CASCADE,
    source_system       varchar(32),
    source_item_id      integer,
    source_repo         text,
    source_path         text,
    source_commit       varchar(64),
    metadata            jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (item_definition_id, class_id)
);

CREATE INDEX item_allowed_classes_class_idx
    ON content.item_allowed_classes(class_id, item_definition_id);

-- Equipment slot allow-list. Inventory/ground/storage placement is not governed
-- by this table; this only describes where an item may be equipped.
CREATE TABLE content.item_equip_slots (
    item_definition_id  bigint NOT NULL REFERENCES content.item_definitions(id) ON DELETE CASCADE,
    slot_code           varchar(32) NOT NULL,
    PRIMARY KEY (item_definition_id, slot_code),
    CHECK (slot_code IN (
        'weapon','armour','helmet','torch','necklace','bracelet_left','bracelet_right',
        'ring_left','ring_right','shoes','belt','poison','amulet','flower','horse_armour',
        'emblem','shield','costume','hook','float','bait','finder','reel'
    ))
);

CREATE INDEX item_equip_slots_slot_idx
    ON content.item_equip_slots(slot_code, item_definition_id);

-- One server-side predicate for every equip attempt.
CREATE FUNCTION content.can_class_equip_item(p_item_definition_id bigint, p_class_id smallint)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT CASE i.class_restriction_mode
        WHEN 'all' THEN true
        WHEN 'none' THEN false
        WHEN 'restricted' THEN EXISTS (
            SELECT 1
            FROM content.item_allowed_classes a
            WHERE a.item_definition_id = i.id
              AND a.class_id = p_class_id
        )
        ELSE false
    END
    FROM content.item_definitions i
    WHERE i.id = p_item_definition_id;
$$;

-- Runtime-friendly resolved equipment policy.
CREATE VIEW content.item_class_equip_policy AS
SELECT
    i.id AS item_definition_id,
    i.game_key,
    c.id AS class_id,
    c.code AS class_code,
    content.can_class_equip_item(i.id, c.id) AS can_equip
FROM content.item_definitions i
CROSS JOIN content.class_definitions c;

COMMIT;
