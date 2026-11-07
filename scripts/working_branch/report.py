"""Render the frozen outcome and its limitations from completed Linux evidence."""
import csv
from common import *


def table(headers, values):
    return '\n'.join(['|'+'|'.join(headers)+'|', '|'+'|'.join(['---']*len(headers))+'|']+
                     ['|'+'|'.join(map(str, row))+'|' for row in values])


def csv_rows(path):
    with path.open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def render(root):
    result = read(root/'analysis/decision.json'); audit = read(root/'independent-audit.json')
    cost = read(root/'analysis/cost.json'); pairs = csv_rows(root/'analysis/paired.csv')
    measured = csv_rows(root/'analysis/metrics.csv'); programs = csv_rows(root/'analysis/programs.csv')
    q = [p for p in programs if p['arm'] == 'BRANCH' and p['branch'] == '1']
    primary = [r for r in pairs if r['kind'] == 'ALL_PAID' and r['control'] == 'CURRENT']
    endpoints = [r for r in pairs if r['kind'] == 'COMMIT_ENDPOINTS' and r['control'] == 'CURRENT']
    cases = {c['id']: c for c in read(root/'prepared/cases.json')}
    text = ['# 工作分支续搜小试结果（2026-11-07）',
        f"冻结决定：**{result['decision']}**。质量关：{result['qualityGate']}；Q支路合格新终点："
        f"{result['QendpointGate']['qualifiedCount']}/12。停止这份固定短分支方案，不延长程序、重选Q或新增seed追正。四职责、QGS、家族、原共享与默认主线保持，未扩量、未创建或恢复Goal。",
        '## 范围与公平口径',
        'Linux同一实例100_2_3_1、来源seed14910003，三个已付费入口104540/179120/228840；每入口四职责，共12组固定P/Q/R。Q来自上轮POST_FA付费反事实查询，不能将其可供数量当原生500k的事件频率。R为同职责第二个自由成员。所有起点及上轮三臂结果均已纳入共同A0，不能以复评已知好解获得免费收益。',
        table(['臂','起点/程序','每组FE','本轮FE'], [
            ['ONE','P：1次起点＋31次混合',32,384],
            ['RESTART','P/P：各1＋15',32,384],
            ['CURRENT','P/R：各1＋15',32,384],
            ['BRANCH','P/Q：各1＋15',32,384]]),
        '原POST模型、80份供体快照、PaMixingMove、原职责接受规则和每条私有档案固定。三个双支路的第二支使用同一组随机索引；起点/接受不同后候选自然不同。ONE的前16条付费结果与其他臂P支路完全一致。Q只在私有分支作为当前工作态，不替换原P或向其他支路写回。',
        '## 主对照：全部付费发现，BRANCH相对普通双起点CURRENT',
        'HV变化和IGD+对称改善均以正值为好；C(B,C)为BRANCH覆盖CURRENT，C(C,B)方向相反，相等计覆盖。',
        table(['入口','HV变化%','IGD+对称改善%','C(B,C)','C(C,B)'], [
            [r['context'],f"{float(r['HVpct']):+.9f}",f"{float(r['IGDplusSymPct']):+.6f}",
             f"{r['C_BC_covered']}/{r['C_BC_denominator']} ({100*float(r['C_BC']):.4f}%)",
             f"{r['C_CB_covered']}/{r['C_CB_denominator']} ({100*float(r['C_CB']):.4f}%)"] for r in primary]),
        '三个入口均未达到HV至少0.1%或IGD+改善至少5%的信号。晚入口IGD+显著比例反向，超过预定5%小试止损线；这里的“超过止损线”不是统计显著性。HV参考点改为1.25或2.0时三处方向不翻转。C在共同A0背景下多数相等覆盖，不能只凭接近100%宣布方法等价。',
        table(['入口','对ONE HV%','对ONE IGD+改善%','对RESTART HV%','对RESTART IGD+改善%'], [
            [context, *[f"{float(next(r for r in pairs if r['kind']=='ALL_PAID' and r['context']==context and r['control']==control)[field]):+.6f}"
                       for control in ('ONE','RESTART') for field in ('HVpct','IGDplusSymPct')]]
            for context in ('104540','179120','228840')]),
        '## Q工作态与可提交终点',
        f"12条Q支路中{sum(p['fromSuccessor']=='True' for p in q)}条至少接受过一次后继，"
        f"共{sum(int(p['acceptedSuccessors']) for p in q)}次接受；并非没有执行或完全不接收。"
        f"相对共同A0新鲜的付费记录共{sum(int(p['freshPaidPoints']) for p in q)}条（不冒称唯一新解），"
        f"末点新鲜{sum(p['freshToA0']=='True' for p in q)}条，但相对原P可提交{sum(p['wouldCommit']=='True' for p in q)}条。",
        table(['入口','职责','接受后继数','末点来自后继','末点不被A0覆盖','原职责允许提交'], [
            [p['context'],p['role'],p['acceptedSuccessors'],p['fromSuccessor'],p['freshToA0'],p['wouldCommit']] for p in q]),
        '两个新鲜末点的专业目标对比如下。支路内部相对Q可以进步，但仍没有修复相对原P的专业目标损失；这不是日志漏写或接受公式实现错误。',
        table(['case','专业目标','P','起点Q','末工作态'], [
            [p['case'], 'TEC' if p['role']=='ENERGY' else 'TWC',
             f"{cases[p['case']]['P']['objectives'][1 if p['role']=='ENERGY' else 2]:.9f}",
             f"{cases[p['case']]['Q']['objectives'][1 if p['role']=='ENERGY' else 2]:.9f}",
             f"{float(p['terminalTEC' if p['role']=='ENERGY' else 'terminalTWC']):.9f}"]
            for p in q if p['freshToA0']=='True']),
        '可提交终点前沿使用A0＋所有按原职责合格的各支末点。它不实现额外终点选择器；以下BRANCH的收益可来自共有P支路，不能替Q终点关凑数。',
        table(['入口','终点前沿HV变化%','终点IGD+对称改善%','C覆盖差pp'], [
            [r['context'],f"{float(r['HVpct']):+.9f}",f"{float(r['IGDplusSymPct']):+.6f}",f"{float(r['CdiffPP']):+.6f}"] for r in endpoints]),
        '## 绝对指标与实际目标',
        '同一经验参考集为ND(三份A0＋本轮全部1536付费目标)，只用于离线评分。归一化下界为0，尺度与旧协议一致，主HV参考1.5。传统IGD同时公开。',
        table(['入口','臂/口径','前沿大小','HV','IGD+','IGD'], [
            [r['context'],r['arm']+'/'+r['kind'],r['n'],f"{float(r['HV']):.12f}",
             f"{float(r['IGDplus']):.12g}",f"{float(r['IGD']):.12g}"]
            for r in measured if r['kind'] in ('ALL_PAID','A0')]),
        'Cmax、TEC、TWC各自极值对应的完整三目标向量见analysis/extreme-vectors.json，不把不同解的极值拼成一个解。所有可提交终点的绝对指标在analysis/metrics.csv；每条程序的终点、接受数和费用见analysis/programs.csv。',
        '## 工程核验、实际计费与成本',
        f"实际搜索尝试/成功/失败为1536/1536/0，其中84次起点评价、1452次后继混合；额外QA36/36成功，目标逐位一致。总1572份时间轴、{audit['operationRecords']}条工序独立核对，聚合误差{audit['maxAggregationError']}；{audit['loadedClassChecks']}次实际加载类来源及SHA核查通过。",
        '1,656个初始基因混合夹具无解码；原接受公式、CENTER相等行为、私有档案隔离、全部父代—供体—FOS索引、逐次私有档案Flags、接受状态及84个末工作态均复核。27个解集做81次独立HV、27次IGD+、27次传统IGD和36次覆盖分子检查；指标数学方向/相等/互不覆盖夹具通过。审计没有增加解码。',
        '首次隔离编译因EDHHFSPW构造器的IOException声明遗漏而停止，发生在0FE/0QA。原source/build/失败日志保留；仅在source-02与build-02修复异常声明，未覆盖旧文件或调整科学协议。源、输入及依赖身份见build-02/identity.json和science/receipt.json。',
        table(['阶段','完整进程秒数'], [[name,f"{meta['seconds']:.6f}"] for name,meta in cost['phases'].items()]),
        f"科学JVM完整进程{cost['phases']['science']['seconds']:.6f}秒，包括原生验证和完整时间轴写盘；解码器累计{cost['fullDecoderNanos']/1e9:.6f}秒。离线指标计算另用{cost['offlineAnalysisSeconds']:.6f}秒。独立审计总墙钟没有单列捕获，明确记缺失；本轮不作同时间优势结论。每臂都独立实际全解码，918种物理日程中重复出现的评价同样收费。",
        '## 解释与停止边界',
        '这次检验的是“原规则拒绝的权衡邻居，在固定模型/供体和短预算内成为独立工作态后有无额外可用价值”。观察到少量新点和内部改进，却未胜普通双起点，也未产生可返回原职责的新末点。因此被拒但互不支配这一条件本身不足以支持保留分支；不能再把缺口简单归为没有多pbest、没有Q工作态或接受规则没接通。',
        '结论只否定这份冻结短程序，不证明所有多状态搜索无效，更不否定四职责与原共享的旧条件收益。共同A0较成熟，整体HV变化很小；晚入口BRANCH IGD+约2.68e-5，比例差也要结合绝对距离看。三个时点属于同一来源seed，不能作为三个独立seed；本轮也没有NSGA/PA全算法对照，不能扩大为完整算法优劣。',
        '不自动改接受公式、不延长Q支、不增加状态数、不晋升普通双起点、不启动新实例或完整500k实验。若以后提出新方向，先复用已付费数据确定结构缺口和能推翻它的普通控制，再另行讨论；本轮没有启动后续实验。',
        '## 复算入口与产物',
        'protocol.md为评价前冻结协议；prepared/为输入与随机索引；science/为全部1536付费轨迹和84个终点；qa/为36QA；independent-audit.json为独立轨迹与时间轴验收；analysis/为共同参考、全部指标、C分子分母、原始前沿、极值向量及冻结决定。',
        'code-02/为有效Python入口；source/保留初版Java，source-02仅替换WorkingBranchRun.java；有效classpath为build-02/classpath.txt。冻结依赖仍引用同一Linux项目的历史运行目录，source-references.json列出路径和身份；交付包不是脱离历史依赖的独立安装包。复核已有日志不需新评价，禁止为复算指标重跑science或qa。']
    (root/'summary.md').write_text('\n\n'.join(text)+'\n', encoding='utf-8')
    print('REPORT_WRITTEN', flush=True)


if __name__ == '__main__':
    linux(); render(Path(sys.argv[1]))
