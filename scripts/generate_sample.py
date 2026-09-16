"""Offline generator. Truth and expected labels are intentionally separate files."""
import argparse
import json
from pathlib import Path
from backend.app.data.sample import generate_bundle

parser = argparse.ArgumentParser()
parser.add_argument("--size", choices=["fixture", "full"], default="fixture")
parser.add_argument("--seed", type=int, default=97)
parser.add_argument("--output", type=Path, default=Path("artifacts/sample"))
args = parser.parse_args()
bundle = generate_bundle(args.size, args.seed)
args.output.mkdir(parents=True, exist_ok=True)
(args.output / "runtime-inputs.json").write_text(bundle.inputs.model_dump_json(indent=2))
(args.output / "offline-truth.json").write_text(json.dumps(bundle.truth))
(args.output / "offline-labels.json").write_text(json.dumps(bundle.validation_labels, indent=2))
print(f"Generated {len(bundle.inputs.products)} SKUs and {len(bundle.inputs.demand_history)} historical rows. Oracle files are offline only.")
