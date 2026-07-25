"""Compare compact-v3 Chinese text indexes with compact-v4 binary indexes."""

import argparse
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "generate_watch_dict.py"
VALIDATOR_PATH = ROOT / "omo" / "dict_semantic_validator.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_legacy(directory: Path, name: str, prefix: str, generator):
    mappings = {}
    for path in sorted((directory / name).glob(f"{prefix}_*.txt")):
        previous = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            key, value = line.split("\t")
            if name == "cn_index":
                key = generator.decode_front_code(key, previous)
            mappings[key] = tuple(generator.decode_delta_ids(value))
            previous = key
    return mappings


def read_binary(directory: Path, name: str, prefix: str, validator):
    mappings = {}
    for path in sorted((directory / name).glob(f"{prefix}_*.bin")):
        decoded = validator.read_binary_index(path, name)
        if set(mappings) & set(decoded):
            raise RuntimeError(f"duplicate key in {path}")
        mappings.update(decoded)
    return mappings


def prefix_ids(mappings, query):
    exact = mappings.get(query)
    if exact is not None:
        return list(exact[:50])
    ids = []
    seen = set()
    for key in [key for key in mappings if key.startswith(query)][:20]:
        for entry_id in mappings[key][:10]:
            if entry_id not in seen:
                seen.add(entry_id)
                ids.append(entry_id)
    return ids[:50]


def compare_index(legacy, binary, label):
    if legacy != binary:
        missing = sorted(set(legacy) - set(binary))[:1]
        changed = next((key for key in legacy if legacy.get(key) != binary.get(key)), None)
        raise RuntimeError(f"{label} mapping differs: missing={missing}, changed={changed!r}")
    # The complete key-to-ordered-ID mapping is equal. Exact and prefix search
    # are pure functions of that mapping, so this proves every prefix outcome.
    for query in ("不存在", "能力", "能力的", "能"):
        if prefix_ids(legacy, query) != prefix_ids(binary, query):
            raise RuntimeError(f"{label} representative search differs for {query!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-dir", required=True)
    parser.add_argument("--binary-dir", required=True)
    args = parser.parse_args()
    generator = load_module("v3_generator", GENERATOR_PATH)
    validator = load_module("v4_validator", VALIDATOR_PATH)
    legacy_dir = Path(args.legacy_dir)
    binary_dir = Path(args.binary_dir)
    compare_index(read_legacy(legacy_dir, "cn_index", "cn", generator), read_binary(binary_dir, "cn_index", "cn", validator), "cn_index")
    compare_index(read_legacy(legacy_dir, "zh_index", "zh", generator), read_binary(binary_dir, "zh_index", "zh", validator), "zh_index")
    print("Chinese compact-v3 and compact-v4 indexes are behaviorally identical")


if __name__ == "__main__":
    main()
