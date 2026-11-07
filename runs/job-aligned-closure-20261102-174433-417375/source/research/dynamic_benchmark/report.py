"""Render exploratory evidence with the frozen interpretation limits."""
import json

def write_report(rows, comparisons, audit, output):
    report=["# 第四、第五步完整算法开发初筛","",f"{len(rows)}次完整运行；6实例×5seed×9版本×2预算。主目标Cmax/TEC/TWC，strong_fast合成疲劳参数。",
            "归一化在正式运行前冻结；IGD+参考集为全部九版本末期有效档案的经验并集，不是真前沿。时间结果使用截止时间内完成的档案；离线重放不反馈搜索。",
            "", "## 实例层平均HV差", "", "|步骤|预算|比较|平均HV差|平均相对%|实例胜/平/负|95%探索性区间|Holm p|", "|---|---|---|---:|---:|---|---|---:|"]
    for c in comparisons:
        report.append(f"|{c['step']}|{c['budget']}|{c['comparison']}|{c['meanDelta']:.6f}|{c.get('meanRelativePercent',float('nan')):.3f}|{c['wins']}/{c['ties']}/{c['losses']}|[{c['bootstrap95'][0]:.6f},{c['bootstrap95'][1]:.6f}]|{c['holmP']:.4f}|")
    report += ["", "## 解释边界", "", "这是开发实例初筛，5个seed是同一实例内的重复，配对单位只有6个实例。区间、单侧符号翻转检验与Holm校正仅用于探索性判断；不能替代第六步独立确认。",
               "四个FA家族在本轮固定不刷新，各占5粒子，80粒子保持自由。SYNC控制含相同配额、资源重绑定和固定FA限制，但不开池组合。共享组合按有限池精确可分解目标选厂方案；不声称全局最优或工资预算等价。",
               "完整基线和联合生成器的本轮结果不能用于倒推v1-v10局部机制，也不能由一个组件无优势否定四子群方向。",
               "", "## 费用审计", "", "```json",json.dumps(audit,ensure_ascii=False,indent=2),"```",""]
    (output/"report.md").write_text("\n".join(report),encoding="utf-8")
