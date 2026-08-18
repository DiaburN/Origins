BEGIN;

ALTER TABLE content.magic_definitions
    ADD COLUMN delay_base_ms integer,
    ADD COLUMN delay_reduction_ms integer,
    ADD CONSTRAINT magic_delay_base_nonnegative CHECK (delay_base_ms IS NULL OR delay_base_ms >= 0),
    ADD CONSTRAINT magic_delay_reduction_nonnegative CHECK (delay_reduction_ms IS NULL OR delay_reduction_ms >= 0);

ALTER TABLE player.characters
    ADD COLUMN gold bigint NOT NULL DEFAULT 0,
    ADD CONSTRAINT characters_gold_nonnegative CHECK (gold >= 0);

-- Persistent/base/allocated stats only. Runtime totals remain calculated by the
-- game server from class progression, equipment, buffs and other sources.
CREATE TABLE player.character_stats (
    character_id    uuid NOT NULL REFERENCES player.characters(id) ON DELETE CASCADE,
    stat_code       varchar(64) NOT NULL,
    amount          integer NOT NULL DEFAULT 0,
    source          varchar(32) NOT NULL DEFAULT 'base',
    PRIMARY KEY (character_id, stat_code, source)
);

CREATE INDEX character_stats_character_idx ON player.character_stats(character_id);

COMMIT;
