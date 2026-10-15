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

class ComicLanguageTests(unittest.TestCase):
    def value(self):
        import test_manage_run as fixtures
        value = fixtures.assignment()
        value.update(schema_version=20, language='zh-Hans', run_title='逗号工厂', language_resolution={'source':'current-session','reason':'Synthetic Chinese session'})
        value['input']['language'] = 'zh-Hans'
        for image in value['images']:
            image['title'] = '修好这个逗号'
            image['lettering_description'] = '清晰的黑色文字，白色气泡。'
            for a in image['action_plan']: a['action'] = '鲸鱼娘把逗号放在桌上。'
            for e in image['expression_plan']: e['visual_description'] = '她安静地注视桌面。'
            for d in image['dialogue_plan']: d['placement'] = '在说话者上方，气泡指向嘴部'
            for e in image['effects_plan']: e['effect'] = '工厂后方有速度线'
            for r in image['references']: r.pop('instruction', None)
        return fixtures.confirm_fixture_plan(value)

    def test_current_prompt_and_plan_are_localized_and_locked(self):
        import test_manage_run as fixtures
        manager = fixtures.manage
        value = self.value()
        prompt = manager.visual_prompt().render(value, value['images'][0])
        self.assertIn('角色与参考图', prompt)
        self.assertIn('第 1 格', prompt)
        self.assertNotIn('CHARACTERS', prompt)
        self.assertNotIn('Speech balloon', prompt)
        self.assertIn(value['images'][0]['core_text'][0], prompt)
        plan = manager.plan_markdown(value)
        self.assertIn('逗号工厂', plan)
        self.assertIn('档位目标', plan)
        value['language_overrides'] = {'prompt': 'en'}
        with self.assertRaisesRegex(manager.RunError, 'stale'):
            manager.validate_approval(value)

    def test_v20_initialization_and_resume_preserve_language(self):
        import argparse
        import test_manage_run as fixtures
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'assignment.json'
            path.write_text(json.dumps(self.value()))
            result = fixtures.manage.cmd_init(argparse.Namespace(assignment=str(path), root=str(Path(directory)/'runs'), effective_parallelism=1))
            _, frozen, _ = fixtures.manage.load_run(result['run_dir'])
            self.assertEqual(frozen['language'], 'zh-Hans')
            self.assertEqual(frozen['run_title'], '逗号工厂')

    def test_scoped_visible_text_and_prompt_languages_are_independent(self):
        import test_manage_run as fixtures
        value = self.value()
        value['language_overrides'] = {'visible_text': 'ja'}
        value['input']['language'] = 'ja'
        self.assertEqual(lp.effective(value, 'prompt'), 'zh-Hans')
        lp.validate(value, comic=True)
        value['input']['language'] = 'en'
        with self.assertRaisesRegex(ValueError, 'input.language'):
            lp.validate(value, comic=True)

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

class CurrentBatchLanguageTests(unittest.TestCase):
    def test_language_survives_staged_planning_and_batch_start(self):
        import test_priority_selection as fixtures
        case = fixtures.PlanningTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        spec = {'schema_version':20, 'language':'zh-Hans', 'run_title':'中文漫画批次',
                'language_resolution':{'source':'current-session','reason':'Synthetic current session'},
                'sources':[{'id':'source-a','text':'input','target_images':1}],
                'execution':{'batch_id':'synthetic-v20'},
                'availability':{'builtin':{'available':True,'evidence':'Synthetic tool presence'}}}
        case.cli('batch-prepare', '--spec', case.save('spec.json',spec))
        packet = case.cli('task-packet','--task','concepts-source-a')
        self.assertEqual(packet['language_contract']['language'], 'zh-Hans')
        value = case.concepts(1)
        value.update(case.select(value))
        value.update(schema_version=20, run_title='中文素材标题')
        for image in value['images']: image['title']='中文图片标题'
        case.claim('detail-source-a','author')
        detail = case.submit('detail','author',value)
        review = case.save('cross.json',{'review_status':'reviewed','sources':['source-a'],'observation':'Synthetic comparison'})
        proposal = case.cli('batch-proposal','--draft',detail['output'],'--review-json',review)
        self.assertIn('任务语言：zh-Hans',Path(proposal['rendered']).read_text())
        confirmation = case.save('confirmation.json',{'user_reply':'Synthetic approval','summary_sha256':proposal['summary_sha256']})
        result = case.cli('batch-start','--confirmation',confirmation,'--root',case.root/'runs','--slots',1)
        frozen = fixtures.m.load_run(result['runs']['source-a'])[1]
        self.assertEqual(frozen['language'],'zh-Hans')
        self.assertEqual(frozen['run_title'],'中文素材标题')
        case.run_dir = Path(result['runs']['source-a'])
        case.image_spec = frozen['images'][0]
        case.image = case.image_spec['id']
        case.task = 'source-a-gen-' + case.image
        case.claim(case.task)
        case.act('start')
        bad = case.root / 'synthetic-invalid.png'
        bad.write_bytes(b'Synthetic undecodable image; no provider call')
        self.assertEqual(case.act('ingest',candidate=bad)['status'],'technical_blocked')
        collection = 'source-a-collection-0'
        case.claim(collection)
        fixtures.m.invoke(fixtures.m.parser().parse_args(['collection-task','prepare','--run-dir',str(case.run_dir),'--task-id',collection,'--owner','worker']))
        case.claim('delivery-all')
        delivered = case.cli('batch-deliver','--task-id','delivery-all','--owner','worker')
        self.assertEqual(delivered['expected'],1)
        self.assertIn('中文图片标题', (case.batch.parent / 'delivery-index.md').read_text())
        self.assertIn('中文素材标题', Path(delivered['gallery']).read_text())
