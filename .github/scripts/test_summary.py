#!/usr/bin/env python3
"""Résumé des résultats de tests JUnit XML dans le Job Summary de GitHub Actions."""
import argparse, glob, os
import xml.etree.ElementTree as ET


def main() -> None:
    args = parse_args()
    cases = [case
             for path in glob.glob(os.path.join(args.folder, "**", "*.xml"), recursive=True)
             for case in ET.parse(path).getroot().iter("testcase")]

    failed = [c for c in cases if c.find("failure") is not None or c.find("error") is not None]
    skipped = [c for c in cases if c.find("skipped") is not None]
    passed = len(cases) - len(failed) - len(skipped)
    status = "❌" if failed else ("✅" if cases else "⚠️")

    lines = [f"### {status} {args.title}", "",
             "| Total | Réussis | Échecs | Ignorés |", "| ---: | ---: | ---: | ---: |",
             f"| {len(cases)} | {passed} | {len(failed)} | {len(skipped)} |", ""]
    lines += [f"- ❌ `{c.get('classname')} › {c.get('name')}`" for c in failed]

    with open(os.environ.get("GITHUB_STEP_SUMMARY", "/dev/stdout"), "a", encoding="utf-8") as out:
        out.write("\n".join(lines) + "\n\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title", help="titre du résumé, par exemple « Tests back-end »")
    parser.add_argument("folder", help="dossier contenant les rapports JUnit XML (parcouru récursivement)")
    return parser.parse_args()


if __name__ == "__main__":
    main()
