## Why

当前安全运营报表生成依赖人工编写，效率低且一致性差。用户需要能够通过自然语言快速查询数据、生成图表、分析总结，并能够调试单个数据部分（Data Part）直到满意，然后保存为可复用的预制件（Block）。系统需要支持网安行业标准报表模板，通过语义匹配将用户prompt路由到正确的查询工具。

## What Changes

- **自然语言查询接口**：用户输入自然语言prompt，系统自动解析并查询数据
- **数据可视化转换**：查询结果可转换为表格、柱状图、折线图、饼图等多种图表形式
- **数据分析能力**：支持对查询结果进行归纳、总结、分析
- **报表模板系统**：内置JSON格式模板，支持多章节（Chapter）和数据部分（Data Part）
- **调试模式**：支持单独调试某个Data Part，查看结果是否符合预期
- **预制件机制**：用户调试满意的Data Part可保存为预制件，包含original_prompt + rewritten_prompt + tool_chain
- **Prompt改写Agent**：将用户prompt改写为n个查询调用 + m个分析调用
- **工具注册表**：系统级工具清单，支持语义向量检索（Tool Registry）
- **动态工具绑定**：预制件绑定特定工具组合，确​​定输出稳定性

## Capabilities

### New Capabilities

- `prompt-rewriting-agent`: Prompt改写Agent，将用户原始prompt拆解为查询和分析任务序列
- `tool-registry`: 工具注册表，管理系统所有可用API工具，支持语义向量检索
- `data-part`: 数据部分，单个prompt对应的查询+格式化结果，作为报表的原子组成单元
- `report-block`: 预制件（Block），已验证的prompt+改写prompt+工具链组合，可作为few-shot示例
- `report-template`: 报表模板，JSON格式定义章节和Data Part，支持模板编辑和管理
- `chart-generator`: 图表生成器，将查询结果转换为表格、柱状图、折线图、饼图等
- `debug-mode`: 调试模式，支持单独执行和预览单个Data Part

### Modified Capabilities

- （无）

## Impact

- 新增 `agents/` 目录：包含 Prompt改写Agent、路由Agent、查询Agent、分析Agent
- 新增 `tools/` 目录：工具注册表、图表生成器等
- 新增 `templates/` 目录：内置报表模板（JSON格式）
- 新增 `blocks/` 目录：用户保存的预制件存储
- 数据库新增表：预制件表、模板表、工具注册表
