# 完整文件与Release原始证据

[Release下载页](https://github.com/zb581899564-arch/zhangbogaijin1/releases/tag/research-snapshot-20261107)

PROJECT_FILES.jsonl逐行记录全部收录文件：原项目相对路径path、原大小bytes、原字节SHA-256、Release资产asset、资产内member，以及可直接浏览的gitPath。相同内容只存一份对象，不丢弃原路径；原始证据字节不做脱敏改写或截断。SNAPSHOT.json列出资产大小和SHA、总量及明确排除规则。

Git目录便于网页审核，优先收录当前代码、研究文档、协议、审计、分析和较小结构化记录。大型逐次轨迹、完整数组、冻结字节码和二进制保存在Release。Git中没有直接镜像的文件仍在完整清单内；少量旧审核快照保留文件可能不在当前PROJECT_FILES清单，MANIFEST会注明其为历史保留项，当前项目身份以PROJECT_FILES为准。

恢复方式（Python 3.11或更新版本，只用标准库，不启动研究）：

```sh
gh release download research-snapshot-20261107 --repo zb581899564-arch/zhangbogaijin1 --pattern 'project-objects-*.zip' --dir evidence-assets
python review_tools/restore_snapshot.py --assets evidence-assets --output restored-project
```

只恢复最近工作分支运行，可加：

```sh
python review_tools/restore_snapshot.py --assets evidence-assets --output restored-working-branch --prefix runs/linux-working-branch-probe-20261107-01/
```

目标必须为新目录。恢复器先核对清单和所需资产SHA，再逐文件核对原字节；不会覆盖现有目录。完整材料需要相应磁盘容量，具体原大小见SNAPSHOT.json。若只查看结果，请先读Git中的报告，不必恢复所有轨迹。

本次公开范围不包括原李明哲材料兄弟目录、项目规则明确排除的私密作者/参考包、论文全文与提取页面、本地导出目录、临时文件、可重建缓存和运行库下载。原始研究目录与历史Git提交未改写。SHA表示文件身份，不能替代科学正确性；已有工程和指标审计见各运行目录。部分入口仍需历史Linux冻结依赖，本归档不保证异机一键从零重跑。
