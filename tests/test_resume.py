import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile
import yaml
import docx

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load('build_resume')
checker = load('check_resume')


class ResumeTests(unittest.TestCase):
    def test_bilingual_builds_and_metadata(self):
        for filename, expected in [('example_resume.yaml', 'Alex Chen'),
                                   ('example_resume_zh.yaml', '陈示例')]:
            source = ROOT / 'examples' / filename
            data = yaml.safe_load(source.read_text())
            with tempfile.TemporaryDirectory() as folder:
                target = Path(folder) / 'resume.docx'
                builder.build(data, builder.resolve_template(data, None, str(source)), target)
                document = docx.Document(target)
                self.assertIn(expected, '\n'.join(p.text for p in document.sections[0].header.paragraphs))
                self.assertTrue(any(data['sections'][0]['title'] in p.text for p in document.paragraphs))
                with zipfile.ZipFile(target) as archive:
                    self.assertNotIn('docProps/custom.xml', archive.namelist())
                    xml = b'\n'.join(archive.read(n) for n in archive.namelist() if n.endswith('.xml'))
                    for forbidden in (b'{{NAME}}', b'{{SECTION}}', b'KSOTemplateDocerSaveRecord', b'Liu, D.'):
                        self.assertNotIn(forbidden, xml)

    def test_invalid_data(self):
        for data in (None, {'sections': [{'title': 'Test', 'type': 'typo'}]},
                     {'header': {'phone': 123}},
                     {'sections': [{'title': 'Test', 'entries': [{'title': 'Role', 'date': 2026}]}]}):
            with self.assertRaises(ValueError):
                builder.validate_data(data)

    def test_dates(self):
        self.assertGreater(checker.end_key('Sep 2026'), checker.end_key('Jan 2026'))
        self.assertEqual(checker.end_key('Jan 2025-May 2026'), (2026, 5))
        self.assertEqual(checker.end_key('2025.01-2026.05'), (2026, 5))
        self.assertGreater(checker.end_key('2025.01-至今'), checker.end_key('12/2026'))


if __name__ == '__main__':
    unittest.main()
