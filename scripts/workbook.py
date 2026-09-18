"""Generate blank, fixture or full XLSX without including withheld demand truth."""
import argparse
from pathlib import Path
import json
from backend.app.data.sample import generate_sample
from backend.app.data.workbook import template, parse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', choices=['blank', 'fixture', 'full'], default='fixture')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = None if args.size == 'blank' else generate_sample(args.size)
    content = template(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(content)
    print(json.dumps({'size': args.size, 'xlsx_bytes': len(content)}))
    if data:
        restored, _, measurements = parse(content)
        assert restored == data, 'Workbook must round-trip without loss'
        print(json.dumps(measurements))

if __name__ == '__main__': main()
