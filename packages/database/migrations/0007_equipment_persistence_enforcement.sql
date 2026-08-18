-- ORIGINS DATA FOUNDATION V1
-- Persistence guard: invalid equipment cannot be stored even if a client/server
-- bug attempts to bypass normal gameplay validation.

BEGIN;

CREATE FUNCTION player.validate_character_item_slot()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_owner uuid;
    v_item_definition_id bigint;
    v_class_id smallint;
    v_slot_code varchar(32);
BEGIN
    SELECT owner_character_id, item_definition_id
      INTO v_owner, v_item_definition_id
      FROM player.item_instances
     WHERE id = NEW.item_instance_id;

    IF v_item_definition_id IS NULL THEN
        RAISE EXCEPTION 'Unknown item instance %', NEW.item_instance_id;
    END IF;

    IF v_owner IS DISTINCT FROM NEW.character_id THEN
        RAISE EXCEPTION 'Item instance % is not owned by character %', NEW.item_instance_id, NEW.character_id;
    END IF;

    IF NEW.slot_group = 'equipment' THEN
        SELECT class_id INTO v_class_id
          FROM player.characters
         WHERE id = NEW.character_id;

        SELECT slot_code INTO v_slot_code
          FROM content.equipment_slot_definitions
         WHERE id = NEW.slot_index;

        IF v_slot_code IS NULL THEN
            RAISE EXCEPTION 'Unknown equipment slot index %', NEW.slot_index;
        END IF;

        IF NOT content.can_class_equip_item_in_slot(v_item_definition_id, v_class_id, v_slot_code) THEN
            RAISE EXCEPTION 'Class % cannot equip item definition % in slot %', v_class_id, v_item_definition_id, v_slot_code;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER character_item_slot_integrity_trigger
BEFORE INSERT OR UPDATE ON player.character_item_slots
FOR EACH ROW
EXECUTE FUNCTION player.validate_character_item_slot();

COMMIT;
