"""Language contracts use synthetic sessions and never inspect real user history."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]

def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

lp = module('language_policy')
detect = module('detect-language')

class LanguageTests(unittest.TestCase):
    def test_scope_and_original_tags(self):
        value = {'language': 'zh-Hans', 'language_overrides': {'visible_text': 'ja'}}
        self.assertEqual(lp.effective(value, 'prompt'), 'zh-Hans')
        self.assertEqual(lp.effective(value, 'visible_text'), 'ja')
        self.assertEqual(lp.tag('zh-TW'), 'zh-Hant')
        self.assertEqual(detect.classify('مرحبا كيف حالك'), 'other')
        with self.assertRaises(ValueError): lp.tag('../../en')
        locked = {'language':'zh-Hans','run_title':'原文保留',
                  'language_resolution':{'source':'explicit','reason':'Synthetic exact wording','preserved_text':['Permission denied']},
                  'images':[{'title':'原文','text':{'content':'Permission denied','languages':['en']}}]}
        lp.validate(locked)
        locked['language_resolution'].pop('preserved_text')
        with self.assertRaisesRegex(ValueError, 'text.languages'): lp.validate(locked)

    def test_dictionary_validates_nested_keys_and_placeholders(self):
        english = lp.locale({}, 'en', 'gallery')
        bad = copy.deepcopy(english)
        bad['warnings']['image_missing'] = 'Lost {wrong}'
        with self.assertRaisesRegex(ValueError, 'placeholders'):
            lp.check_dictionary(bad, english)
        bad = copy.deepcopy(english); del bad['zoomIn']
        with self.assertRaisesRegex(ValueError, 'keys'):
            lp.check_dictionary(bad, english)
        with self.assertRaisesRegex(ValueError, 'Missing ja'):
            lp.locale({}, 'ja', 'gallery')

    def test_recent_session_precedes_daily_majority_and_filters_noise(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); sessions = root / '.codex/sessions/2026/10/15'
            sessions.mkdir(parents=True)
            now = datetime.now(timezone.utc)
            for name, messages, offset, source in [('older', ['这是中文消息'] * 8, 2, 'cli'), ('newer', ['日本語で漫画を作ってください', 'OK', '> quoted source'], 1, 'cli'), ('tool', ['English tool instructions'], 0, 'exec')]:
                records = [{'type': 'session_meta', 'payload': {'source': source}}]
                for i, text in enumerate(messages):
                    records.append({'type': 'response_item', 'timestamp': (now-timedelta(hours=offset, seconds=i)).isoformat(), 'payload': {'role': 'user', 'content': [{'type':'input_text','text':text}]}})
                (sessions / f'rollout-{name}.jsonl').write_text('\n'.join(json.dumps(x) for x in records))
            result = detect.detect(24, root, 5)
            self.assertTrue(result['sessions'][0]['session'].endswith('newer.jsonl'))
            self.assertEqual(result['leading'], 'ja')
            self.assertEqual(result['sessions'][0]['by_script'], {'ja': 1})
            self.assertEqual(len(result['sessions']), 2)

import helpers

class CharacterLanguageTests(helpers.FixtureCase):
    def test_v7_freezes_language_and_visible_titles(self):
        value = self.assignment()
        value.update(schema_version=7, language='zh-Hans', run_title='挥手问好', language_resolution={'source':'current-session','reason':'Synthetic Chinese session'})
        for image in value['images']: image['title'] = '轻轻挥手'
        helpers.confirm_fixture(value)
        result = self.initialize(value)
        _, saved, _ = helpers.manage_run.load_run(str(result))
        self.assertEqual(saved['language'], 'zh-Hans')
        self.assertEqual(saved['images'][0]['title'], '轻轻挥手')
        saved['language'] = 'en'
        with self.assertRaisesRegex(helpers.manage_run.RunError, 'stale'):
            helpers.manage_run.validate_approval(saved, result / 'assignment.json')

class GalleryLanguageTests(unittest.TestCase):
    def test_custom_locale_titles_and_scoped_default(self):
        import test_gallery as fixtures
        with tempfile.TemporaryDirectory() as directory:
            run = fixtures.make_run(Path(directory))
            value = fixtures.gallery.read_json(run / 'assignment.json')
            # Synthetic complete dictionary tests wiring, not translation quality.
            custom = {'name':'日本語（テスト）', 'direction':'ltr', 'gallery':lp.locale({}, 'en', 'gallery')}
            custom['gallery']['titleComic'] = '漫画ギャラリー'
            custom['gallery']['titleCharacter'] = 'キャラクターギャラリー'
            value.update(language='zh-Hans', language_overrides={'interface':'ja'}, run_title='记录的中文标题', localizations={'ja':custom})
            value['images'][0]['title'] = '图片中文标题'
            fixtures.write_json(run / 'assignment.json', value)
            manifest = fixtures.gallery.read_json(run / 'manifest.json')
            manifest['assignment_sha256'] = fixtures.gallery.digest(run / 'assignment.json')
            fixtures.write_json(run / 'manifest.json', manifest)
            exported = fixtures.gallery.export_gallery([run])
            data = fixtures.payload(exported['gallery'])
            self.assertEqual(data['language'], 'ja')
            self.assertEqual(list(data['locales']), ['zh-Hans', 'en', 'ja'])
            self.assertEqual(data['groups'][0]['title'], '记录的中文标题')
            self.assertEqual(data['groups'][0]['proposals'][0]['images'][0]['name'], '图片中文标题')
            again = fixtures.gallery.export_gallery([run])
            self.assertNotEqual(data['gallery_id'], fixtures.payload(again['gallery'])['gallery_id'])
            self.assertIn('lang="ja"', Path(exported['gallery']).read_text())

    def test_browser_language_preference_is_per_gallery(self):
        import subprocess
        source = (ROOT / 'assets/gallery/gallery.js').read_text()
        prefix = source[source.index('const STRINGS ='):source.index('let activeGroup')]
        script = '''const vm = require('node:vm');
const code = JSON.parse(process.argv[1]);
function language(id, saved) {
 const ctx = {data:{locales:{'zh-Hans':{},en:{},ja:{}},gallery_id:id,language:'ja'},localStorage:{getItem:k=>saved[k]}};
 vm.createContext(ctx);vm.runInContext(code,ctx);return vm.runInContext('language',ctx);
}
const saved = {'whalechan-gallery-language':'en', 'whalechan-gallery-language:first':'en'};
if (language('first',saved)!=='en' || language('second',saved)!=='ja') throw Error('cross-gallery preference leak');
'''
        subprocess.run(['node','-e',script,json.dumps(prefix)],check=True,capture_output=True)
