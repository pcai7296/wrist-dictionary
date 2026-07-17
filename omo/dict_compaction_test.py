"""Unit tests for the compact dictionary wire format."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "generate_watch_dict.py"
DICT_DIR = ROOT / "src" / "common" / "dict"
VALIDATOR_PATH = ROOT / "omo" / "dict_semantic_validator.py"
ACTIVE_CONSUMERS = (
    ROOT / "omo" / "coverage_test_v2.py",
    ROOT / "omo" / "analyze_cccedict.py",
    ROOT / "omo" / "_check_sizes.py",
    VALIDATOR_PATH,
    ROOT / "omo" / "dict_coverage_test.py",
)


class GeneratorLoadError(RuntimeError):
    """Raised when the generator module cannot be loaded for unit tests."""


def load_generator() -> ModuleType:
    """Load the generator without executing its CLI entry point."""
    spec = importlib.util.spec_from_file_location("generate_watch_dict", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise GeneratorLoadError(f"cannot load generator: {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_module(name: str, path: Path) -> ModuleType:
    """Load a Python module from a repository path."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise GeneratorLoadError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_script(path: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run a repository Python script with captured UTF-8 output."""
    return subprocess.run(
        [sys.executable, str(path), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class CompactDictionaryFormatTest(unittest.TestCase):
    """Exercise compact encoding at its serialization boundary."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()

    def test_delta_base36_round_trip_when_ids_are_sorted(self) -> None:
        # Given
        entry_ids = [0, 21, 1844, 1849, 14_941]
        encode: Callable[[list[int]], str] | None = getattr(
            self.generator, "encode_delta_base36", None
        )
        decode: Callable[[str], list[int]] | None = getattr(
            self.generator, "decode_delta_base36", None
        )

        # When / Then
        self.assertIsNotNone(encode, "generator must expose encode_delta_base36")
        self.assertIsNotNone(decode, "generator must expose decode_delta_base36")
        assert encode is not None and decode is not None
        self.assertEqual(decode(encode(entry_ids)), entry_ids)

    def test_delta_base36_rejects_malformed_token(self) -> None:
        # Given
        decode: Callable[[str], list[int]] | None = getattr(
            self.generator, "decode_delta_base36", None
        )

        # When / Then
        self.assertIsNotNone(decode, "generator must expose decode_delta_base36")
        assert decode is not None
        with self.assertRaises(ValueError):
            decode("l,!,2")

    def test_delta_base36_rejects_non_increasing_ids(self) -> None:
        # Given
        encode: Callable[[list[int]], str] | None = getattr(
            self.generator, "encode_delta_base36", None
        )

        # When / Then
        self.assertIsNotNone(encode, "generator must expose encode_delta_base36")
        assert encode is not None
        with self.assertRaises(ValueError):
            encode([21, 21])


class CompactDictionaryConsumerTest(unittest.TestCase):
    """Keep every active offline consumer on the compact word schema."""

    def test_coverage_v2_loads_all_compact_headwords(self) -> None:
        # Given / When
        result = run_script(ROOT / "omo" / "coverage_test_v2.py")
        report = json.loads((ROOT / ".omo" / "coverage_test_v2.json").read_text(encoding="utf-8"))

        # Then
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["english"], {"total": 99, "exact": 99, "prefix": 0, "miss": 0, "rate": 100.0})
        self.assertEqual(report["chinese"]["exact"], 85)
        self.assertEqual(report["chinese"]["miss"], 14)

    def test_analyze_cccedict_loads_all_compact_headwords(self) -> None:
        # Given
        env = os.environ.copy()
        env["TEMP"] = str(ROOT / "data")
        env["PYTHONUTF8"] = "1"

        # When
        result = run_script(ROOT / "omo" / "analyze_cccedict.py", env=env)

        # Then
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Existing English words: 14942", result.stdout)

    def test_size_checker_reports_compact_word_index(self) -> None:
        # Given / When
        result = run_script(ROOT / "omo" / "_check_sizes.py")

        # Then
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"Compact word index: 14,942 entries, [\d,]+ bytes")

    def test_active_consumers_have_no_legacy_dictionary_references(self) -> None:
        # Given
        legacy_reference = re.compile(r'dict_\*\.txt|index_en\.txt|english_suggestions(?:\.js|\.json)?')

        # When
        violations = {
            str(path.relative_to(ROOT)): legacy_reference.findall(path.read_text(encoding="utf-8"))
            for path in ACTIVE_CONSUMERS
            if legacy_reference.search(path.read_text(encoding="utf-8"))
        }

        # Then
        self.assertEqual(violations, {})


class SemanticValidatorRegressionTest(unittest.TestCase):
    """Pin semantic validation to trusted corpus invariants."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module("dict_semantic_validator_test", VALIDATOR_PATH)

    def copy_dictionary(self, destination: Path) -> Path:
        """Copy the generated dictionary for isolated corruption tests."""
        shutil.copytree(DICT_DIR, destination)
        return destination

    def test_validator_exposes_pinned_baseline_counts(self) -> None:
        # Given / When
        actual = {
            "headwords": getattr(self.validator, "EXPECTED_HEADWORDS", None),
            "cn_phrases": getattr(self.validator, "EXPECTED_CN_PHRASES", None),
            "cn_links": getattr(self.validator, "EXPECTED_CN_LINKS", None),
            "zh_chars": getattr(self.validator, "EXPECTED_ZH_CHARS", None),
            "zh_links": getattr(self.validator, "EXPECTED_ZH_LINKS", None),
            "inflect": getattr(self.validator, "EXPECTED_INFLECT_LINKS", None),
            "reverse": getattr(self.validator, "EXPECTED_REVERSE_INFLECT_LINKS", None),
        }

        # Then
        self.assertEqual(
            actual,
            {
                "headwords": 14_942,
                "cn_phrases": 122_067,
                "cn_links": 324_516,
                "zh_chars": 3_731,
                "zh_links": 135_638,
                "inflect": 26_225,
                "reverse": 26_225,
            },
        )

    def test_validator_rejects_data_and_meta_that_share_a_wrong_link_count(self) -> None:
        # Given
        with tempfile.TemporaryDirectory() as temp_dir:
            dictionary = self.copy_dictionary(Path(temp_dir) / "dict")
            cn_file = next((dictionary / "cn_index").glob("cn_*.txt"))
            rows = cn_file.read_text(encoding="utf-8").splitlines()
            row_index = next(index for index, row in enumerate(rows) if "," in row.split("\t", 1)[1])
            phrase, encoded = rows[row_index].split("\t")
            rows[row_index] = f"{phrase}\t{encoded.rsplit(',', 1)[0]}"
            cn_file.write_text("\n".join(rows) + "\n", encoding="utf-8")
            meta_path = dictionary / "meta.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["cnIndexLinks"] -= 1
            meta_path.write_text(json.dumps(meta), encoding="utf-8")
            original = self.validator.DICT_DIR
            self.validator.DICT_DIR = dictionary

            # When / Then
            try:
                with self.assertRaises(self.validator.DictionaryValidationError):
                    self.validator.validate(require_compact=True)
            finally:
                self.validator.DICT_DIR = original

    def test_validator_stays_active_under_python_optimized_mode(self) -> None:
        # Given
        with tempfile.TemporaryDirectory() as temp_dir:
            dictionary = self.copy_dictionary(Path(temp_dir) / "dict")
            word_file = dictionary / "words" / "word_a.txt"
            rows = word_file.read_text(encoding="utf-8").splitlines()
            word_file.write_text("\n".join(rows[1:]) + "\n", encoding="utf-8")
            command = (
                "import importlib.util,pathlib,sys;"
                f"p=pathlib.Path({str(VALIDATOR_PATH)!r});"
                "s=importlib.util.spec_from_file_location('validator_opt',p);"
                "m=importlib.util.module_from_spec(s);sys.modules['validator_opt']=m;s.loader.exec_module(m);"
                f"m.DICT_DIR=pathlib.Path({str(dictionary)!r});"
                "m.validate(require_compact=True)"
            )

            # When
            result = subprocess.run(
                [sys.executable, "-O", "-c", command],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            # Then
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("DictionaryValidationError", result.stderr)


class CoverageFailureGateTest(unittest.TestCase):
    """Make coverage regressions visible to build and release automation."""

    def test_main_coverage_exits_nonzero_for_forced_miss(self) -> None:
        # Given / When
        result = run_script(ROOT / "omo" / "dict_coverage_test.py", "--force-miss")

        # Then
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("coverage validation failed", result.stderr)


if __name__ == "__main__":
    unittest.main()
