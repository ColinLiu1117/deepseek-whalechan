"""Check browser filter collections against exported records, including legacy gaps."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_gallery import ROOT, gallery, make_run, payload, write_json


@unittest.skipUnless(shutil.which('node'), 'JavaScript collection checks require Node.js')
class GalleryFilterTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.run = make_run(self.root)

    def collections(self):
        result = gallery.export_gallery([self.run])
        group = payload(result['gallery'])['groups'][0]
        script = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
const context = {group: JSON.parse(fs.readFileSync(0, 'utf8'))};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function comicCollections('),
                            source.indexOf('function renderComicImages(')), context);
process.stdout.write(JSON.stringify(vm.runInContext('comicCollections(group)', context)));
'''
        check = subprocess.run(['node', '-e', script, str(ROOT / 'assets/gallery/gallery.js')],
                               input=json.dumps(group), capture_output=True, text=True, check=True)
        return json.loads(check.stdout)

    def mutate(self, change):
        manifest = gallery.read_json(self.run / 'manifest.json')
        change(manifest['images']['01_same'])
        write_json(self.run / 'manifest.json', manifest)

    def test_unselected_pass_is_an_attempt_not_an_extra_final(self):
        sets = self.collections()
        self.assertEqual([len(sets[key]) for key in ('finals', 'attempts', 'all')], [1, 1, 2])
        self.assertEqual(sets['finals'][0]['attempt']['id'], 'attempt-01')
        self.assertEqual(sets['attempts'][0]['attempt']['id'], 'attempt-02')
        self.assertEqual(sets['attempts'][0]['attempt']['verdict'], 'PASS')

    def test_ambiguous_final_has_one_card_without_inventing_prompt_ownership(self):
        shutil.copyfile(self.run / 'candidates/one.png', self.run / 'candidates/two.png')
        def change(state):
            state['attempts'][1]['candidate_sha256'] = state['final_sha256']
        self.mutate(change)
        sets = self.collections()
        self.assertEqual([len(sets[key]) for key in ('finals', 'attempts', 'all')], [1, 2, 2])
        self.assertTrue(sets['finals'][0]['origin_ambiguous'])
        self.assertIsNone(sets['finals'][0]['attempt'])
        self.assertEqual(len({item['attempt']['id'] for item in sets['attempts']}), 2)

    def test_final_without_attempt_records_is_still_available(self):
        self.mutate(lambda state: state.update(attempts=[]))
        sets = self.collections()
        self.assertEqual([len(sets[key]) for key in ('finals', 'attempts', 'all')], [1, 0, 1])
        self.assertIsNone(sets['finals'][0]['attempt'])
        self.assertFalse(sets['finals'][0]['origin_ambiguous'])

    def test_missing_final_file_uses_the_matching_recorded_candidate(self):
        (self.run / 'final/01_same.png').unlink()
        sets = self.collections()
        self.assertEqual(len(sets['finals']), 1)
        self.assertTrue(sets['finals'][0]['picture']['src'])
        self.assertEqual(sets['finals'][0]['attempt']['id'], 'attempt-01')

    def test_pass_components_are_not_full_comic_finals(self):
        self.run = make_run(self.root, 'composite', composite=True)
        sets = self.collections()
        self.assertEqual([len(sets[key]) for key in ('finals', 'attempts', 'all')], [1, 2, 3])
        self.assertEqual(sets['finals'][0]['attempt']['role'], 'composite')
        self.assertTrue(all(item['attempt']['role'] == 'component' for item in sets['attempts']))

    def test_partial_run_keeps_empty_finals_and_all_failed_versions(self):
        def change(state):
            state.update(status='pending', final_path=None, final_sha256=None)
            for record in state['attempts']:
                record['verdict'] = 'FAIL'
        self.mutate(change)
        sets = self.collections()
        self.assertEqual([len(sets[key]) for key in ('finals', 'attempts', 'all')], [0, 2, 2])
        self.assertTrue(all(item['attempt']['verdict'] == 'FAIL' for item in sets['attempts']))


if __name__ == '__main__':
    unittest.main()
