BEGIN;

INSERT INTO content.class_definitions (id, code, display_name, source_system, source_repo, source_path)
VALUES
    (1, 'warrior',  'Warrior',  'Crystal',      'Suprcode/Crystal',        'Shared/Enums.cs'),
    (2, 'wizard',   'Wizard',   'Crystal',      'Suprcode/Crystal',        'Shared/Enums.cs'),
    (3, 'taoist',   'Taoist',   'Crystal',      'Suprcode/Crystal',        'Shared/Enums.cs'),
    (4, 'assassin', 'Assassin', 'Crystal',      'Suprcode/Crystal',        'Shared/Enums.cs'),
    (5, 'archer',   'Archer',   'Crystal',      'Suprcode/Crystal',        'Shared/Enums.cs'),
    (6, 'monk',     'Monk',     'Crystal-Monk', 'JevLOMCN/Crystal-Monk',  'Common.cs')
ON CONFLICT (id) DO UPDATE SET
    code = EXCLUDED.code,
    display_name = EXCLUDED.display_name,
    source_system = EXCLUDED.source_system,
    source_repo = EXCLUDED.source_repo,
    source_path = EXCLUDED.source_path;

COMMIT;
