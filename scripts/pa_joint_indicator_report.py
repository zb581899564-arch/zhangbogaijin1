"""Complete raw and paired three-indicator tables for a registered isolated comparison."""


def table(headers, rows):
    return ["|" + "|".join(headers) + "|", "|" + "|".join(["---"] * len(headers)) + "|"] + [
        "|" + "|".join(map(str, row)) + "|" for row in rows]


def write_report(root, title, analysis):
    lines = ["# " + title, "", "HV越大、IGD+越小越好；双向C采用精确弱支配，相等计覆盖，两方向分母不同、不互补。", "",
             "ΔHV=100×(HV_A/HV_B−1)%。IGD+对称变差=200×(IGD_A−IGD_B)/(IGD_A+IGD_B)%，正值表示A较差，非通常相对变化。", "",
             "全部预定方法/seed共同构造每实例经验ND参考集；指标分歧不以加权总分或多数表决处理。", ""]
    for instance in analysis["instances"]:
        lines += ["## " + instance["stem"], "", "### 原始终点", ""]
        values = [[p["seed"], p["method"], p["frontSize"], f'{p["HV"]["1.25"]:.9f}', f'{p["HV"]["1.5"]:.9f}',
                   f'{p["HV"]["2.0"]:.9f}', f'{p["IGDplus"]:.9f}'] for p in instance["observations"]]
        lines += table(["seed", "方法", "ND数", "HV1.25", "HV1.5", "HV2.0", "IGD+"], values) + [""]
        for comparison in instance["comparisons"]:
            lines += ["### A=" + comparison["A"] + "，B=" + comparison["B"], ""]
            values = []
            for p in comparison["pairs"]:
                hv, c = p["HVEffectPct"], p["coverage"]
                values.append([p["seed"], f'{hv["1.25"]:.3f}%', f'{hv["1.5"]:.3f}%', f'{hv["2.0"]:.3f}%',
                               f'{p["IGDplusSymmetricWorseningPct"]:.3f}%',
                               f'{c["coveredB"]}/{c["totalB"]} ({100*c["C_A_B"]:.3f}%)',
                               f'{c["coveredA"]}/{c["totalA"]} ({100*c["C_B_A"]:.3f}%)'])
            hv = comparison["medianHVEffectPct"]
            values.append(["中位", f'{hv["1.25"]:.3f}%', f'{hv["1.5"]:.3f}%', f'{hv["2.0"]:.3f}%',
                           f'{comparison["medianIGDplusSymmetricWorseningPct"]:.3f}%',
                           f'{100*comparison["medianC_A_B"]:.3f}%', f'{100*comparison["medianC_B_A"]:.3f}%'])
            lines += table(["seed", "ΔHV1.25", "ΔHV1.5", "ΔHV2.0", "IGD+对称变差", "C(A,B)", "C(B,A)"], values) + [""]
    lines += ["## 冻结决定", "", str(analysis["decision"]), "",
              "方法能力、机制归因、完整算法资格及创新性需分开；本轮没有同时间或独立确认结论，默认主线未改。", ""]
    with (root / "report.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
