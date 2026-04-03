# Prompt Rewriting Agent

## ADDED Requirements

### Requirement: Prompt Rewriting Agent SHALL decompose user prompts

The prompt rewriting agent SHALL accept a user's natural language prompt and decompose it into a sequence of n query operations and m analysis operations.

#### Scenario: Simple single query
- **WHEN** user submits "最近一周哪些资产被攻击最严重"
- **THEN** agent returns one data part with type="query"

#### Scenario: Multiple queries with analysis
- **WHEN** user submits "最近一周威胁事件有哪些，按类型分布，并分析趋势"
- **THEN** agent returns data_parts containing 2 queries and 1 analysis, with dependency relationships

#### Scenario: Analysis depends on query results
- **WHEN** user submits "查询威胁事件，然后分析一下"
- **THEN** agent returns analysis data part with depends_on referencing the query data part

### Requirement: Prompt Rewriting Agent SHALL route to correct tools

The agent SHALL match rewritten prompts to tools in the tool registry using semantic similarity.

#### Scenario: Direct tool match
- **WHEN** user prompt matches asset_attacks tool with similarity > 0.85
- **THEN** agent selects asset_attacks as the target tool

#### Scenario: Fallback to tool registry search
- **WHEN** user prompt does not directly match any pre-built block
- **THEN** agent searches tool registry semantically and selects best match

### Requirement: Prompt Rewriting Agent SHALL generate structured output

The agent SHALL output a structured data_parts array containing:

- `id`: unique identifier for the data part
- `type`: "query" or "analyze"
- `original_prompt`: user's original input
- `rewritten_prompt`: standardized prompt after rewriting
- `tool_id`: matched tool from registry (for queries)
- `params`: parameters for the tool
- `depends_on`: array of data part IDs this depends on (if any)

#### Scenario: Output structure validation
- **WHEN** agent completes rewriting
- **THEN** output conforms to the data_parts schema with all required fields

### Requirement: Prompt Rewriting Agent SHALL handle time parameters

The agent SHALL parse time expressions in user prompts and convert to concrete time ranges.

#### Scenario: Time parameter extraction
- **WHEN** user says "最近一周"
- **THEN** params.time_range is set to "last_week" with concrete dates

#### Scenario: Supported time expressions
- **WHEN** user uses any of: 今天, 昨天, 最近一周, 上周, 本月, 上月, 最近三月
- **THEN** agent correctly parses and converts to concrete time range
