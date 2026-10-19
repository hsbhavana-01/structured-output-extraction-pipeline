import argparse, json, sys
from pathlib import Path
from .extractors import build_extractor
from .pipeline import ExtractionPipeline


def main():
    parser = argparse.ArgumentParser(description="Extract invoice fields into validated JSON")
    parser.add_argument("file", nargs="?", help="UTF-8 text file; reads stdin when omitted")
    parser.add_argument("--extractor", choices=["regex", "openai"], default="regex")
    parser.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args()
    text = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    result = ExtractionPipeline(build_extractor(args.extractor), args.max_attempts).run(text)
    print(json.dumps(asdict(result), indent=2, default=str))
    if result.status != "accepted": sys.exit(2)

if __name__ == "__main__": main()
