import base64
import json
import tempfile
import unittest
from pathlib import Path
from fashion_flats_full_pipeline import prepare_job, read_observations, main

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.photo = self.root / 'private.png'
        self.photo.write_bytes(PNG)
        self.obs = self.root / 'observations.json'
        self.data = dict(target='Coat', view='front', observed_features=['Standing collar'],
                         invariants=['Long straight body'], observed_colors=['Cream'],
                         surface_appearance='Smooth appearance; fiber unknown', unknowns=['Back'],
                         evidence=['Source 1 front'], example_only=False)
        self.save()

    def save(self):
        self.obs.write_text(json.dumps(self.data), encoding='utf-8')

    def prepare(self, **kwargs):
        return prepare_job([self.photo], self.obs, self.root / 'job', **kwargs)

    def test_no_master_blocks_color_and_no_fake_output(self):
        job = self.prepare()
        self.assertEqual(job['color_task']['status'], 'blocked_missing_line_master')
        self.assertEqual(job['generated_images'], [])
        text = (self.root / 'job' / 'line_prompt.txt').read_text()
        self.assertIn('Standing collar', text)
        self.assertNotIn('Structured Sleeveless Bow Mini Dress', text)
        self.assertFalse((self.root / 'job' / 'color_prompt.txt').exists())
        manifest = (self.root / 'job' / 'manifest.json').read_text()
        self.assertNotIn(str(self.root), manifest)
        self.assertEqual((self.root / 'job/inputs/source-01.png').read_bytes(), PNG)

    def test_master_is_copied_and_hashed(self):
        job = self.prepare(line_master=self.photo, style_references=[self.photo])
        self.assertEqual(job['color_task']['status'], 'ready_for_host')
        self.assertEqual([r['role'] for r in job['references']], ['source', 'style', 'line-master'])
        self.assertTrue(all(len(r['sha256']) == 64 for r in job['references']))
        self.assertTrue((self.root / 'job/color_prompt.txt').is_file())

    def test_missing_and_fake_images_fail_before_writing(self):
        for value in ('missing.png', 'fake.png'):
            if value == 'fake.png':
                (self.root / value).write_text('not an image')
            with self.assertRaises(ValueError):
                prepare_job([self.root / value], self.obs, self.root / 'job')
        self.assertFalse((self.root / 'job').exists())

    def test_examples_and_invalid_schema_are_rejected(self):
        for key, value in [('example_only', True), ('view', 'imagined'),
                           ('invariants', []), ('observed_features', 'not a list')]:
            original = self.data[key]
            self.data[key] = value
            self.save()
            with self.assertRaises(ValueError):
                read_observations(self.obs)
            self.data[key] = original

    def test_second_run_never_overwrites(self):
        self.prepare()
        marker = self.root / 'job/keep.txt'
        marker.write_text('keep')
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual(marker.read_text(), 'keep')

    def test_different_garment_changes_prompts(self):
        self.prepare()
        first = (self.root / 'job/line_prompt.txt').read_text()
        self.data.update(target='Skirt', observed_features=['Pleated hem'])
        self.save()
        prepare_job([self.photo], self.obs, self.root / 'second')
        second = (self.root / 'second/line_prompt.txt').read_text()
        self.assertNotEqual(first, second)
        self.assertIn('Pleated hem', second)

    def test_cli_returns_error_for_unreviewed_example(self):
        self.data['example_only'] = True
        self.save()
        self.assertEqual(main(['--image', str(self.photo), '--observations', str(self.obs),
                               '--out', str(self.root / 'job')]), 2)


if __name__ == '__main__':
    unittest.main()
