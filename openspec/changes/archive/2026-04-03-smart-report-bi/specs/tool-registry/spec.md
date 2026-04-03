# Tool Registry

## ADDED Requirements

### Requirement: Tool Registry SHALL store available tools

The tool registry SHALL maintain a catalog of all available tools with their metadata including:
- tool_id: unique identifier
- tool_name: human-readable name
- description: semantic description for matching
- params_schema: JSON schema for tool parameters
- result_format: expected output format (table, chart, text)

#### Scenario: Tool registration
- **WHEN** system initializes
- **THEN** tool registry contains all defined tools with complete metadata

### Requirement: Tool Registry SHALL support semantic search

The registry SHALL provide semantic search capability using vector embeddings to match user prompts to tools.

#### Scenario: Semantic similarity search
- **WHEN** searching for "资产被攻击情况"
- **THEN** registry returns asset_attacks tool with similarity score

#### Scenario: Search returns ranked results
- **WHEN** search query matches multiple tools
- **THEN** results are ranked by similarity score descending

### Requirement: Tool Registry SHALL maintain clean state

The registry SHALL NOT be modified by user debugging activities. User-specific aliases and mappings are stored in blocks, not in the registry.

#### Scenario: Alias isolation
- **WHEN** user creates a block with custom rewritten_prompt
- **THEN** tool registry description remains unchanged

### Requirement: Tool Registry SHALL validate tool parameters

The registry SHALL validate that tool invocations match the defined params_schema.

#### Scenario: Valid parameter submission
- **WHEN** tool is invoked with parameters matching schema
- **THEN** invocation proceeds

#### Scenario: Invalid parameter rejection
- **WHEN** tool is invoked with missing required parameter
- **THEN** system returns validation error with missing field details
