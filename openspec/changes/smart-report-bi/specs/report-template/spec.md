# Report Template

## ADDED Requirements

### Requirement: Template SHALL define report structure

A template SHALL define a complete report structure containing:
- `id`: unique template identifier
- `name`: template name (e.g., "安全周报")
- `description`: template description
- `chapters`: array of chapter definitions
- `created_at`: creation timestamp
- `updated_at`: last modification timestamp
- `is_public`: whether template is available to all users

#### Scenario: Built-in security weekly report template
- **WHEN** system loads built-in templates
- **THEN** security weekly report template is available with predefined chapters

### Requirement: Chapter SHALL contain data parts

Each chapter SHALL contain:
- `id`: unique chapter identifier
- `title`: chapter title (e.g., "威胁事件分析")
- `data_parts`: array of data part IDs
- `order`: display order within report

#### Scenario: Chapter with multiple data parts
- **WHEN** chapter "威胁分析" includes data parts for threat type table and trend chart
- **THEN** both data parts execute and render in order

### Requirement: Template SHALL support data part reference

Data parts in a chapter MAY reference pre-built blocks by their block_id.

#### Scenario: Chapter referencing blocks
- **WHEN** chapter references block "threat-type-distribution"
- **THEN** system uses the block's verified tool_chain for execution

### Requirement: Template SHALL support JSON format

Templates SHALL be stored and exchanged in JSON format.

#### Scenario: Template export
- **WHEN** user exports a template
- **THEN** system downloads a JSON file with complete template structure

### Requirement: Template SHALL support built-in templates

System SHALL ship with 3-5 built-in templates for common security report types:

- 安全周报 (Security Weekly Report)
- 安全月报 (Security Monthly Report)
- 漏洞分析报告 (Vulnerability Analysis Report)
- 威胁态势报告 (Threat Posture Report)
- 资产风险报告 (Asset Risk Report)

#### Scenario: Built-in template availability
- **WHEN** user creates new template
- **THEN** system offers built-in templates as starting point
