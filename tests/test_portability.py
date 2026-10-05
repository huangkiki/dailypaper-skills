"""Exercise the installed bundle and real config consumers in isolated workspaces."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills' / '_shared'))
import user_config


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load_module('bundle_installer', ROOT / 'install.py')


class IsolatedWorkspace(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        env = {**os.environ, 'HOME': str(self.home), 'USERPROFILE': str(self.home),
               'XDG_CONFIG_HOME': str(self.home / '.config'), 'PYTHONIOENCODING': 'utf-8'}
        for key in ('DAILYPAPER_CONFIG', 'DAILYPAPER_TEMP_DIR', 'OBSIDIAN_VAULT_PATH'):
            env.pop(key, None)
        self.environment = patch.dict(os.environ, env, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        user_config.load_user_config.cache_clear()
        self.addCleanup(user_config.load_user_config.cache_clear)

    def write_json(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        user_config.load_user_config.cache_clear()
        return path

    def run_python(self, *args):
        return subprocess.run([sys.executable, *map(str, args)], cwd=self.root,
                              text=True, encoding='utf-8', capture_output=True)


class InstallerTests(IsolatedWorkspace):
    def test_each_agent_installs_complete_runnable_bundle(self):
        for agent, directory in installer.AGENT_DIRS.items():
            with self.subTest(agent=agent):
                result = self.run_python(ROOT / 'install.py', '--agent', agent)
                self.assertEqual(result.returncode, 0, result.stderr)
                destination = self.home / directory
                self.assertEqual(len(list(destination.glob('*/SKILL.md'))), 7)
                self.assertTrue((destination / '_shared/agent-runtime.md').is_file())
                config = self.run_python(destination / '_shared/user_config.py')
                self.assertEqual(config.returncode, 0, config.stderr)
                self.assertEqual(json.loads(config.stdout)['paths']['obsidian_vault'],
                                 str(self.home / 'ObsidianVault'))

    def test_custom_path_runs_indexer_from_unrelated_working_directory(self):
        destination = self.root / 'skills with spaces 技能'
        self.assertEqual(self.run_python(ROOT / 'install.py', '--target', destination).returncode, 0)
        vault = self.root / 'notes with spaces 笔记'
        note = vault / '论文笔记' / 'Robotics' / 'Method.md'
        note.parent.mkdir(parents=True)
        note.write_text('# My method\n', encoding='utf-8')
        os.environ['OBSIDIAN_VAULT_PATH'] = str(vault)
        result = self.run_python(destination / '_shared/generate_paper_mocs.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('[[论文笔记/Robotics/Method|Method]]', (note.parent / 'Robotics.md').read_text(encoding='utf-8'))

    def test_update_preserves_personal_config_and_unrelated_files(self):
        destination = self.root / 'skills'
        installer.install([destination])
        main = destination / '_shared/user-config.json'
        local = destination / '_shared/user-config.local.json'
        mapping = destination / 'paper-reader/assets/collection_mapping.json'
        for path in (main, local, mapping):
            self.write_json(path, {'personal': path.name})
        unrelated = destination / 'another-skill/SKILL.md'
        unrelated.parent.mkdir()
        unrelated.write_text('Mine', encoding='utf-8')
        skill = destination / 'daily-papers/SKILL.md'
        skill.write_text('Old bundle', encoding='utf-8')
        installer.install([destination], update=True)
        for path in (main, local, mapping):
            self.assertEqual(json.loads(path.read_text()), {'personal': path.name})
        self.assertEqual(unrelated.read_text(), 'Mine')
        self.assertEqual(skill.read_bytes(), (installer.SOURCE / 'daily-papers/SKILL.md').read_bytes())
        self.assertEqual(installer.install([destination], update=True), 0)

    def test_conflict_is_detected_before_any_target_is_written(self):
        clean, occupied = self.root / 'clean', self.root / 'occupied'
        existing = occupied / 'paper-reader/SKILL.md'
        existing.parent.mkdir(parents=True)
        existing.write_text('User edits', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Existing file differs'):
            installer.install([clean, occupied])
        self.assertFalse(clean.exists())
        self.assertEqual(existing.read_text(), 'User edits')
        self.assertFalse((occupied / '_shared').exists())

    def test_dry_run_writes_nothing(self):
        destination = self.root / 'dry run'
        result = self.run_python(ROOT / 'install.py', '--target', destination, '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(destination.exists())

    def test_source_overlap_is_rejected(self):
        for destination in (installer.SOURCE, installer.SOURCE / 'child', ROOT):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                installer.install([destination], update=True)

    def test_symlinked_destination_is_not_overwritten(self):
        destination = self.root / 'skills'
        destination.mkdir()
        victim = self.root / 'other-skills'
        victim.mkdir()
        try:
            (destination / 'paper-reader').symlink_to(victim, target_is_directory=True)
        except OSError:
            self.skipTest('Symlink creation is not permitted on this host')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            installer.install([destination], update=True)
        self.assertEqual(list(victim.iterdir()), [])
        self.assertFalse((destination / '_shared').exists())


class ConfigurationTests(IsolatedWorkspace):
    def test_precedence_and_deep_merge(self):
        config_dir = self.root / 'config'
        self.write_json(config_dir / 'user-config.json', {'daily_papers': {'keywords': ['bundle'], 'top_n': 12}})
        self.write_json(config_dir / 'user-config.local.json', {'daily_papers': {'keywords': ['local']}})
        self.write_json(user_config.shared_config_path(), {'daily_papers': {'keywords': ['shared']}})
        explicit = self.write_json(self.root / 'explicit.json', {'daily_papers': {'keywords': ['explicit']}})
        os.environ['DAILYPAPER_CONFIG'] = str(explicit)
        os.environ['OBSIDIAN_VAULT_PATH'] = str(self.root / 'vault')
        config = user_config.load_user_config(config_dir)
        self.assertEqual(config['daily_papers']['keywords'], ['explicit'])
        self.assertEqual(config['daily_papers']['top_n'], 12)
        self.assertEqual(config['paths']['obsidian_vault'], str(self.root / 'vault'))
        self.assertFalse(config['automation']['git_push'])

    def test_explicit_path_has_priority_even_if_already_loaded(self):
        config_dir = self.root / 'config'
        base = self.write_json(config_dir / 'user-config.json', {'daily_papers': {'top_n': 5}})
        self.write_json(config_dir / 'user-config.local.json', {'daily_papers': {'top_n': 10}})
        os.environ['DAILYPAPER_CONFIG'] = str(base)
        self.assertEqual(user_config.load_user_config(config_dir)['daily_papers']['top_n'], 5)

    def test_invalid_or_missing_explicit_config_fails(self):
        explicit = self.root / 'explicit.json'
        os.environ['DAILYPAPER_CONFIG'] = str(explicit)
        with self.assertRaises(FileNotFoundError):
            user_config.load_user_config()
        for value in ([], {'paths': 'wrong type'}):
            self.write_json(explicit, value)
            with self.assertRaises(ValueError):
                user_config.load_user_config()

    def test_shared_config_and_environment_are_used_by_viewer(self):
        viewer = load_module('portable_viewer', ROOT / 'web-viewer/app.py')
        legacy = self.home / '.claude/skills/_shared/user-config.json'
        self.write_json(legacy, {'paths': {'obsidian_vault': str(self.home)}})
        vault = self.root / 'shared-vault'
        vault.mkdir()
        self.write_json(user_config.shared_config_path(), {'paths': {'obsidian_vault': str(vault)}})
        self.assertEqual(viewer.load_config()['paths']['obsidian_vault'], str(vault))
        os.environ['OBSIDIAN_VAULT_PATH'] = str(self.root)
        user_config.load_user_config.cache_clear()
        self.assertEqual(viewer.load_config()['paths']['obsidian_vault'], str(self.root))
        os.environ['DAILYPAPER_CONFIG'] = str(self.root / 'missing.json')
        user_config.load_user_config.cache_clear()
        with self.assertRaises(FileNotFoundError):
            viewer.load_config()

    def test_viewer_keeps_legacy_local_override(self):
        viewer = load_module('legacy_viewer', ROOT / 'web-viewer/app.py')
        legacy = self.home / '.claude/skills/_shared'
        self.write_json(legacy / 'user-config.json', {'paths': {'obsidian_vault': str(self.home)}})
        self.write_json(legacy / 'user-config.local.json', {'paths': {'obsidian_vault': str(self.root)}})
        self.assertEqual(viewer.load_config()['paths']['obsidian_vault'], str(self.root))

    def test_init_migrates_local_config_without_overwriting_shared_config(self):
        destination = self.root / 'skills'
        installer.install([destination])
        self.write_json(destination / '_shared/user-config.local.json', {'daily_papers': {'keywords': ['my topic']}})
        command = destination / '_shared/user_config.py'
        first = self.run_python(command, '--init')
        self.assertEqual(first.returncode, 0, first.stderr)
        shared = user_config.shared_config_path()
        original = shared.read_bytes()
        self.assertEqual(json.loads(original)['daily_papers']['keywords'], ['my topic'])
        self.assertEqual(self.run_python(command, '--init').returncode, 0)
        self.assertEqual(shared.read_bytes(), original)

    def test_temp_override_and_git_guard(self):
        temporary = self.root / 'run with spaces'
        os.environ['DAILYPAPER_TEMP_DIR'] = str(temporary)
        self.assertEqual(user_config.temp_file_path('papers.json'), temporary / 'papers.json')
        self.assertTrue(temporary.is_dir())
        self.write_json(user_config.shared_config_path(), {'automation': {'git_push': True, 'git_commit': False}})
        self.assertFalse(user_config.git_push_enabled())
        self.assertTrue(user_config.load_user_config()['automation']['git_push'])


class JsonOutputTests(IsolatedWorkspace):
    def test_fetch_writes_utf8_json_without_shell_redirection(self):
        fetch = load_module('portable_fetch', ROOT / 'skills/daily-papers/fetch_and_score.py')
        output = self.root / '论文 output.json'
        papers = [{'id': '2601.00001', 'title': '机器人论文'}]
        with patch.object(sys, 'argv', ['fetch', '--ranker', 'keyword', '--usage-output', str(self.root / 'usage.json'), '--output', str(output)]), \
                patch.object(fetch, 'fetch_hf_papers', return_value=[]), \
                patch.object(fetch, 'fetch_arxiv_papers', return_value=[]), \
                patch.object(fetch, 'merge_and_dedup', return_value=papers):
            fetch.main()
        self.assertEqual(json.loads(output.read_text(encoding='utf-8')), papers)

    def test_trending_keeps_stdout_and_supports_utf8_file(self):
        trending = load_module('portable_trending', ROOT / 'skills/github-trending/fetch_trending.py')
        repo = {'repo': 'owner/robot', 'description': '机器人', 'language': 'Python', 'stars_period': 42}
        output = self.root / '榜单 output.json'
        with patch.object(trending, 'fetch_html', return_value=''), \
                patch.object(trending, 'parse_trending', return_value=[repo]), \
                patch.object(sys, 'argv', ['trending', '--output', str(output)]):
            self.assertEqual(trending.main(), 0)
        self.assertEqual(json.loads(output.read_text(encoding='utf-8'))[0]['description'], '机器人')
        stream = io.StringIO()
        with patch.object(trending, 'fetch_html', return_value=''), \
                patch.object(trending, 'parse_trending', return_value=[repo]), \
                patch.object(sys, 'argv', ['trending']), contextlib.redirect_stdout(stream):
            trending.main()
        self.assertEqual(json.loads(stream.getvalue())[0]['rank'], 1)


if __name__ == '__main__':
    unittest.main()
