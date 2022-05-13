import argparse
import collections
import os
from typing import Dict

import requests


def aggregate(args: argparse.Namespace):
    url = f"https://sentry.io/api/0/projects/{args.organization}/{args.project}/issues/?query={args.query}&sort={args.sort}&statsPeriod={args.period}"
    res = requests.get(url, headers=dict(Authorization=f"Bearer {args.token}"))

    issues_by_cause: Dict[str, Dict[str, dict]] = {}
    for issue in res.json():
        cause = issue["metadata"]["value"]
        if cause not in issues_by_cause:
            issues_by_cause[cause] = {}
        issues_by_cause[cause][issue["id"]] = issue

    cause_total_counts: Dict[str, int] = {}
    for cause, issues in issues_by_cause.items():
        cause_total_counts[cause] = sum([int(issue["count"]) for issue in issues.values()])

    if args.markdown:
        print("| Total | Count | Info | At |")
        print("|:-----:|:-----:|:-----|:---|")

    for cause, total in collections.Counter(cause_total_counts).most_common():
        if args.markdown:
            print(f"| {total} | | {cause} |")
        else:
            print(f"{total}\t{cause}")

        cause_issues = issues_by_cause[cause]
        cause_counts = {issue["id"]: int(issue["count"]) for issue in cause_issues.values()}
        for issue_id, count in collections.Counter(cause_counts).most_common():
            culprit = cause_issues[issue_id]["culprit"]
            link = cause_issues[issue_id]["permalink"]
            if args.markdown:
                print(f"| | {count} | [{culprit}]({link}) |")
            else:
                print(f"\t{count}\t{culprit}: {link}")


def main():
    parser = argparse.ArgumentParser("sentry", description="tools for sentry issue access")
    subparsers = parser.add_subparsers(help="commands")

    aggregator_parser = subparsers.add_parser("aggregate", help="aggregate sentry issues by its root cause")
    aggregator_parser.add_argument("organization", type=str, help="organization slug")
    aggregator_parser.add_argument("project", type=str, help="project slug")
    aggregator_parser.add_argument("query", type=str, help="issue query string")
    aggregator_parser.add_argument("--sort", type=str, choices=["date", "new", "priority", "freq", "user"], default="date", help="sort order")
    aggregator_parser.add_argument("--period", type=str, choices=["", "24h", "14d"], default="", help="stats period")
    aggregator_parser.add_argument("--token", type=str, default=os.getenv("SENTRY_AUTH_TOKEN"), help="sentry auth token")
    aggregator_parser.add_argument("--markdown", action="store_true", help="export as markdown table")
    aggregator_parser.set_defaults(func=aggregate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
