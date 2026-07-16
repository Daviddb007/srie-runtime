from srie.sdk.client import SDK


def cmd(
    project_path: str = ".",
):
    sdk = SDK(project_path)
    report = sdk.indicators()

    print(f"SRIE Score: {report.srie_score:.1f}")
    print(f"Maturity Level: {report.maturity_level}")
    print(f"Confidence: {report.confidence:.2f}")
    print(f"\nPer-Domain Scores:")
    for domain, score in sorted(report.by_domain.items()):
        bar = chr(9608) * int(score / 10) + chr(9617) * (10 - int(score / 10))
        print(f"  {domain:20s} {score:5.1f} {bar}")
