"""Render complete per-seed joint indicators for the frozen paid-donor experiment."""
import argparse
from pathlib import Path

from run_long_budget_bridge import read


def table(headers, data):
    return ["|" + "|".join(headers) + "|", "|" + "|".join(["---"] * len(headers)) + "|"] + [
        "|" + "|".join(map(str, row)) + "|" for row in data]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    root = parser.parse_args().root
    analysis, audit = read(root / "analysis.json"), read(root / "post-audit.json")
    lines = ["# 已付费联合供体：冻结三指标全表", "",
             "主臂始终为GRAFT_S；以下其他方法不是事后候选。16个逻辑终点复用源前缀及接收分支，不是16次独立运行。", "",
             "每个逻辑终点100000FE；新增科学评价3000000FE，工程137200FE，合计3137200FE/0失败；额外完整QA123751。", "",
             "post-audit已独立核对52条公共入口/4条原生工程运行、18份来源池、类身份、初始化、账目和指标重算；无新增搜索FE。", "",
             "HV越大越好，IGD+越小越好。IGD+对比采用200×(IGD_A−IGD_B)/(IGD_A+IGD_B)，正值表示A较差，不能称通常百分比下降。", "",
             "C(A,B)为A弱支配的B目标去重点比例，相等计覆盖；两个方向分母不同，非互补、非总体排序。", "",
             "A=GRAFT_S。HV效应为100×(HV_A/HV_B−1)；归一化固定，IGD+采用同实例全部登记终点/seed的统一经验ND参考集。", ""]
    assert audit["status"] == "passed"
    for instance in analysis["instances"]:
        lines += ["## " + instance["stem"], "", "### 全部逻辑终点", ""]
        data = [[r["seed"], r["method"], r["frontSize"], f'{r["HV"]["1.25"]:.9f}',
                 f'{r["HV"]["1.5"]:.9f}', f'{r["HV"]["2.0"]:.9f}', f'{r["IGDplus"]:.9f}']
                for r in instance["observations"]]
        lines += table(["seed", "方法", "ND数", "HV1.25", "HV1.5", "HV2.0", "IGD+"], data) + [""]
        lines += ["### 全部预定配对与中位", ""]
        for comparison in instance["comparisons"]:
            lines += ["A相对 " + comparison["control"], ""]
            data = []
            for pair in comparison["pairs"]:
                hv, c = pair["HVEffectPct"], pair["coverage"]
                data.append([pair["seed"], f'{hv["1.25"]:.3f}%', f'{hv["1.5"]:.3f}%', f'{hv["2.0"]:.3f}%',
                             f'{pair["IGDplusSymmetricWorseningPct"]:.3f}%',
                             f'{c["coveredB"]}/{c["totalB"]} ({100*c["C_A_B"]:.3f}%)',
                             f'{c["coveredA"]}/{c["totalA"]} ({100*c["C_B_A"]:.3f}%)', pair["directions"]["label"]])
            hv = comparison["medianHVEffectPct"]
            data.append(["中位", f'{hv["1.25"]:.3f}%', f'{hv["1.5"]:.3f}%', f'{hv["2.0"]:.3f}%',
                         f'{comparison["medianIGDplusSymmetricWorseningPct"]:.3f}%',
                         f'{100*comparison["medianC_A_B"]:.3f}%', f'{100*comparison["medianC_B_A"]:.3f}%',
                         comparison["directions"]["label"]])
            lines += table(["seed", "ΔHV1.25", "ΔHV1.5", "ΔHV2.0", "IGD+对称变差", "C(A,B)", "C(B,A)", "方向描述"], data) + [""]
    lines += ["## 冻结决定", "", analysis["decision"], "",
              "全部八项必要比较在两个实例都未共同通过；其中几项存在正向单项或指标分歧，不能挑控制晋升。没有TIME实验、独立确认或论文性能结论。", "",
              "当前PA为普通联合混合接收器，没有整合原QGS/条件共享；源S/U保留这些机制，U仅统一目标偏好。源局搜覆盖和私有档案限制见source-scope-diagnosis.json。", ""]
    with (root / "report.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    print("PA_PAID_DONOR_REPORT_WRITTEN", root / "report.md")


if __name__ == "__main__":
    main()
