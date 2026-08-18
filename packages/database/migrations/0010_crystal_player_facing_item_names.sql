-- ORIGINS DATA FOUNDATION V1
-- Crystal ItemInfo.FriendlyName hides trailing internal class/level suffix digits
-- and square-bracket tags. ORIGINS stores that player-facing source name while
-- preserving the exact Server.MirDB name in metadata.source_name_raw.
--
-- IMPORTANT: this migration is applied AFTER the generated Crystal equipment
-- seed in CI/deployment order.

BEGIN;

UPDATE content.item_definitions
SET
    metadata = jsonb_set(
        metadata,
        '{source_name_raw}',
        to_jsonb(item_name),
        true
    ),
    item_name = regexp_replace(
        regexp_replace(item_name, E'\\d+$', '', 'g'),
        E'\\[[^\\]]*\\]',
        '',
        'g'
    )
WHERE source_system = 'crystal';

UPDATE content.equipment_progression p
SET original_name = i.item_name
FROM content.item_definitions i
WHERE i.id = p.item_definition_id
  AND i.source_system = 'crystal';

COMMIT;
