# 世界流通钱币图像数据集

> 文档语言：简体中文。默认入口：[README.md](README.md)。

**Legal Tender Currency Image Dataset**

面向钱币收藏、展示与资料整理，系统收集当前法定流通纸币和硬币的正反面图像，并按“国家/发行地区 -> 货币类型 -> 面额/版别”归档。

> **当前阶段：持续收集。** 项目尚未完成全球覆盖，现阶段重点是持续补充符合清晰度、完整性和来源可追溯要求的钱币数据，同时保持已有数据可验证、可复现。

## 项目目标

- 收集当前法定流通的纸币与硬币，优先采用最新标准发行版和现行设计。
- 为每个条目保存正反面图像，并提供统一尺寸的展示版本。
- 保留原始图像、来源页面、原图 URL、发行年份和图像质量信息，便于核验与追溯。
- 以结构化索引和稳定目录结构，支持收藏浏览、资料检索以及后续的网页或应用展示。
- 通过可复现的收集脚本和校验工具，降低人工整理带来的路径错误、尺寸不一致和来源缺失。

## 当前状态

截至 **2026-10-29**，根据 `currencies.json` 核对：

| 指标 | 当前值 |
| --- | ---: |
| 国家/发行地区 | 22 |
| 硬币条目 | 129 |
| 纸币条目 | 122 |
| 面额/版别条目合计 | 251 |
| 同时覆盖硬币与纸币 | 20 |
| 仅覆盖纸币 | 2 |
| 数据校验 | `Validation passed.` |

当前仅有纸币的国家/发行地区为卡塔尔（QAR）和文莱（BND）；其硬币来源尚未满足完整正反面或清晰度要求。条目数按“面额/版别”统计，因此同一面额的不同现行设计会分别计数。

## 覆盖概览

| 国家/发行地区 | 目录 | 代码 | 硬币 | 纸币 | 合计 |
| --- | --- | --- | ---: | ---: | ---: |
| 中国 | [China](./China/) | CNY | 3 | 6 | 9 |
| 日本 | [Japan](./Japan/) | JPY | 6 | 4 | 10 |
| 澳大利亚 | [Australia](./Australia/) | AUD | 6 | 5 | 11 |
| 新加坡 | [Singapore](./Singapore/) | SGD | 5 | 7 | 12 |
| 加拿大 | [Canada](./Canada/) | CAD | 6 | 5 | 11 |
| 挪威 | [Norway](./Norway/) | NOK | 4 | 5 | 9 |
| 瑞典 | [Sweden](./Sweden/) | SEK | 4 | 6 | 10 |
| 瑞士 | [Switzerland](./Switzerland/) | CHF | 7 | 6 | 13 |
| 菲律宾 | [Philippines](./Philippines/) | PHP | 7 | 6 | 13 |
| 丹麦 | [Denmark](./Denmark/) | DKK | 6 | 4 | 10 |
| 智利 | [Chile](./Chile/) | CLP | 4 | 5 | 9 |
| 哥斯达黎加 | [Costa_Rica](./Costa_Rica/) | CRC | 20 | 5 | 25 |
| 乌拉圭 | [Uruguay](./Uruguay/) | UYU | 4 | 7 | 11 |
| 阿联酋 | [United_Arab_Emirates](./United_Arab_Emirates/) | AED | 6 | 8 | 14 |
| 巴林 | [Bahrain](./Bahrain/) | BHD | 5 | 5 | 10 |
| 科威特 | [Kuwait](./Kuwait/) | KWD | 6 | 6 | 12 |
| 格鲁吉亚 | [Georgia](./Georgia/) | GEL | 8 | 5 | 13 |
| 台湾 | [Taiwan](./Taiwan/) | TWD | 6 | 5 | 11 |
| 乌克兰 | [Ukraine](./Ukraine/) | UAH | 10 | 6 | 16 |
| 摩洛哥 | [Morocco](./Morocco/) | MAD | 6 | 4 | 10 |
| 卡塔尔 | [Qatar](./Qatar/) | QAR | 0 | 7 | 7 |
| 文莱 | [Brunei](./Brunei/) | BND | 0 | 5 | 5 |

各国家/发行地区已收录的具体面额与版别见 [docs/COVERAGE.md](docs/COVERAGE.md)。完整字段、路径和逐条来源以 [currencies.json](currencies.json) 为准。

## 目录结构

```text
.
|-- currencies.json              # 数据集主索引，记录全部条目和本地路径
|-- collection_log.json          # 收集批次、来源和处理记录
|-- <Country>/
|   |-- coin/
|   |   `-- <denomination>/
|   |       |-- front_original.<ext>
|   |       |-- back_original.<ext>
|   |       |-- front.jpg
|   |       `-- back.jpg
|   `-- banknote/
|       `-- <denomination>/
|           |-- front_original.<ext>
|           |-- back_original.<ext>
|           |-- front.jpg
|           `-- back.jpg
|-- docs/                        # 收录明细、来源说明、候选调研
|-- tools/                       # 可复现收集脚本与数据校验器
`-- tmp/                         # 临时调研文件，不属于正式数据
```

每个面额/版别目录至少包含正反面原图和正反面展示图。部分来源提供合并图时，还会保留 `combined_original.<ext>`，并在索引中记录拆分方式。

## 数据约定

- `currencies.json` 是唯一主索引，顶层为数组，按国家/发行地区记录硬币和纸币条目。
- 每条记录包含本地正反面路径、来源页面、原图 URL、发行年份、面额值和 `image_quality`。
- `front_original.*` / `back_original.*` 保留来源图像；`front.jpg` / `back.jpg` 是用于展示的处理版本。
- 同一面额的正反面展示图会被放在相同尺寸的白色画布上，确保像素宽高完全一致。
- 原始来源图可能包含透明通道、合并正反面、网页裁切区域或多个现行设计，处理方式记录在 `image_quality.transform` 或 `source_split` 中。
- `collection_log.json` 记录批次状态、来源和特殊处理；详细来源说明见 [docs/SOURCES.md](docs/SOURCES.md)。

## 收录标准

1. **现行法定流通**：只收录当前仍具法定流通地位的纸币或硬币，并优先使用最新标准发行版。
2. **正反面完整**：每个条目必须同时具备可核验的正反两面图像；缺一面的条目暂不收录。
3. **展示可用**：图像应达到展示所需清晰度，不应被强 `SPECIMEN` 水印、页码、年份标签或大面积安全特征标注遮挡。
4. **来源优先**：优先使用中央银行、储备银行、造币厂或官方货币博物馆来源；官方正反面不可得时，可使用有明确正反面标注的 Numista 详情页。
5. **允许部分覆盖**：国家/发行地区可以只收录纸币、只收录硬币或部分面额；不合格条目不使用替代图勉强补位。
6. **版别独立**：发行机构明确列为现行设计的不同版别，分别建立条目和目录。
7. **可追溯与可复现**：保留来源 URL、原图 URL、处理参数和收集脚本；无法稳定复现的来源不进入正式数据。

## 使用方式

读取主索引并访问某个条目的正反面图片：

```python
import json
from pathlib import Path

root = Path(".")
records = json.loads((root / "currencies.json").read_text(encoding="utf-8"))
china = next(country for country in records if country["code"] == "CNY")

for item in china["coin"]:
    print(item["name"])
    print(root / item["front_view_image"])
    print(root / item["back_view_image"])
```

## 校验

校验脚本依赖 Python 3 和 Pillow。首次使用时安装依赖：

```sh
python3 -m pip install Pillow
```

运行校验：

```sh
python3 tools/validate_dataset.py
```

校验内容包括：

- `currencies.json` 是否为合法 JSON，并包含必需字段。
- 所有引用的正反面原图和处理图是否存在。
- 同一面额的正反面展示图尺寸是否一致。
- `image_quality` 中的尺寸是否与实际文件一致。

成功输出为 `Validation passed.`。本机 Codex 运行时也可直接使用：

```sh
/Users/kw/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 tools/validate_dataset.py
```

## 文档导航

| 文件 | 内容 |
| --- | --- |
| [currencies.json](currencies.json) | 数据集主索引与逐条来源元数据 |
| [collection_log.json](collection_log.json) | 收集批次、来源和处理日志 |
| [docs/COVERAGE.md](docs/COVERAGE.md) | 各国家/发行地区的面额与版别明细 |
| [docs/SOURCES.md](docs/SOURCES.md) | 官方来源、备用来源和特殊图像处理说明 |
| [docs/CANDIDATE_SOURCES.md](docs/CANDIDATE_SOURCES.md) | 已调研但暂未收录的候选来源及原因 |
| [OPERATION_GUIDE.md](OPERATION_GUIDE.md) | 新增国家/面额的操作流程、脚本规范和视觉检查方法 |
| [tools/render_coverage.py](tools/render_coverage.py) | 根据主索引重新生成收录明细 |
| [tools/validate_dataset.py](tools/validate_dataset.py) | 数据集结构与图像质量校验器 |

## 后续方向

- 继续按收录标准调研并补充新的国家/发行地区。
- 在找到合格官方来源后，补齐卡塔尔和文莱的硬币数据。
- 定期复核法定流通状态、停止流通日期和新版发行情况。
- 检查失效来源链接、异常低分辨率图像和展示图裁切质量。
- 在数据规模稳定后，再建设面向收藏浏览的网页展示层或检索界面。

新增国家或面额前，请先阅读 [OPERATION_GUIDE.md](OPERATION_GUIDE.md)，并参考 `tools/add_<country>.py` 中最接近的来源处理模式。

## 来源与版权

来源机构和逐条来源 URL 已记录在 `currencies.json` 与 `collection_log.json` 中。本项目当前未声明统一的开放许可；钱币图像及相关资料的版权和使用条件归原发行机构或图片来源方所有，引用、再分发或商业使用前请核对对应来源页面的条款。
