from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'merge-zircon-web-player-assets.py'
spec=importlib.util.spec_from_file_location('merge_player_assets',SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def write_bundle(root:Path,library:str,page_bytes:bytes=b'PNG-A',*,commit:str='pin',atlas:int=2048,source_sha:str='SOURCE') -> Path:
    root.mkdir(parents=True,exist_ok=True)
    lib=root/library; lib.mkdir()
    (lib/'page_000.png').write_bytes(page_bytes)
    manifest={
      'schema':mod.SCHEMA,'libraryFile':library,'sourcePath':f'Data/{library}.Zl','sourceFileName':f'{library}.Zl',
      'sourceSha256':source_sha,'libraryVersion':2,'imageCount':1,'exportedImageCount':1,'atlasSize':atlas,
      'pages':['page_000.png'],'images':[{'index':0,'page':'page_000.png','x':0,'y':0,'width':1,'height':1,'offsetX':0,'offsetY':0}],
    }
    (lib/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    master={'schema':mod.SCHEMA,'zirconCommit':commit,'atlasSize':atlas,'profile':'TEST','libraries':[{'libraryFile':library,'manifest':f'{library}/manifest.json','imageCount':1,'exportedImageCount':1}]}
    (root/'player-assets.json').write_text(json.dumps(master,indent=2)+'\n',encoding='utf-8')
    return root


class MergePlayerAssetsTests(unittest.TestCase):
    def test_merges_distinct_libraries_without_changing_pages(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); a=write_bundle(base/'a','M_Hum',b'body'); b=write_bundle(base/'b','M_Hair',b'hair')
            report=mod.merge([a,b],base/'out')
            self.assertEqual(report['status'],'PASS')
            self.assertEqual(report['libraries'],['M_Hair','M_Hum'])
            self.assertEqual((base/'out/M_Hum/page_000.png').read_bytes(),b'body')
            self.assertEqual((base/'out/M_Hair/page_000.png').read_bytes(),b'hair')
            master=json.loads((base/'out/player-assets.json').read_text())
            self.assertEqual(master['profile'],mod.MERGED_PROFILE)

    def test_identical_duplicate_is_deduplicated(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); a=write_bundle(base/'a','M_Hum',b'same'); b=write_bundle(base/'b','M_Hum',b'same')
            report=mod.merge([a,b],base/'out')
            self.assertEqual(report['libraryCount'],1)
            self.assertEqual(report['deduplicatedCount'],1)
            self.assertEqual(report['duplicates'][0]['libraryFile'],'M_Hum')

    def test_same_manifest_but_different_atlas_bytes_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); a=write_bundle(base/'a','M_Hum',b'A'); b=write_bundle(base/'b','M_Hum',b'B')
            with self.assertRaisesRegex(ValueError,'Conflicting duplicate library M_Hum'):
                mod.merge([a,b],base/'out')

    def test_mismatched_zircon_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); a=write_bundle(base/'a','M_Hum',commit='one'); b=write_bundle(base/'b','M_Hair',commit='two')
            with self.assertRaisesRegex(ValueError,'Zircon commit mismatch'):
                mod.merge([a,b],base/'out')

    def test_manifest_path_cannot_escape_input_root(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); root=write_bundle(base/'a','M_Hum')
            master=json.loads((root/'player-assets.json').read_text())
            master['libraries'][0]['manifest']='../outside/manifest.json'
            (root/'player-assets.json').write_text(json.dumps(master),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'escapes bundle root'):
                mod.merge([root],base/'out')


if __name__=='__main__':
    unittest.main()
