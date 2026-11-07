# Linux 小试入口

算法锚点是冻结完整 `SHARE_CTX_GOM`。公共生产代码不改；`build_sources.py` 只派生三个隔离覆盖类，`src/algorithms/diagnostics/pilot/` 提供观察与入口。不存在无人值守后台调度器。

Windows 开发端使用 `prepare_bundle.py` 打包已冻结类、依赖、源码、输入；`pack_update.py` 只打包明确列出的本轮模块。通过已有 `aic-inspur-home` 传输，在 Linux 校验 manifest 后解包。不要改写已完成运行目录。

Linux 环境路径：

```text
/home/inspur/codex-workspace/projects/limingzhegaijin/runtime/jdk17
/home/inspur/codex-workspace/projects/limingzhegaijin/runtime/py311
```

构建与数学夹具：

```bash
python scripts/build_kernel.py --payload "$PAYLOAD" --output "$BUILD" --javac "$JDK/bin/javac"
python -m research.pilot_evaluation check
```

集中诊断由 `run_pilot.py --action engineering` 和 `--action science` 两步执行；都要求 `--payload --output --build --java`。科学批次前检查工程记录、数学夹具、构建类身份和冻结协议。新批次不能通过覆盖目录恢复；失败记录和实际费用保留，再制定明确恢复方案。

单条隔离入口（只在另有任务授权时使用）：

```bash
python scripts/run_isolated.py --method SHARE_CTX_GOM \
  --global-search --no-local-search --instance 20_8_5_1 --seed 16110003 \
  --fe-limit 500000 --payload "$PAYLOAD" --build "$BUILD" \
  --java "$JDK/bin/java" --output "$NEW_RUN"
```

`--no-global-search --local-search` 为 LOCAL_ONLY；两阶段都开为 FULL。`--time-seconds` 是实际 TIME_LIMIT，`--fe-limit` 此时为安全上限。没有未接入的方法别名，不把任何增强版伪装成普通经典算法。

`audit_results.py` 独立核对每条付费行、准入前沿时序、出生 FE、初始四向量、类身份和不同轴 HV。`analyze.py` 使用批次共同参考集离线生成报告。所有执行入口的统计、绘图与搜索限 Linux；Windows 只查看导出的文件。

完整搜索时间包含观察；观察纳秒、离线完整解码、统计、绘图和进程墙钟另列。离线分析结果不能反馈搜索。三seed不画50%达成面；模块支持在独立批准的五seed批次使用相同规则。
