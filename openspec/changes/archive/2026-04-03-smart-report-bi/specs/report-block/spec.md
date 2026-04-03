# Report Block (预制件)

## ADDED Requirements

### Requirement: Block SHALL store verified prompt-to-tool mapping

A block SHALL contain the complete verified mapping:
- `id`: unique block identifier
- `original_prompt`: user's original prompt text
- `rewritten_prompt`: standardized prompt after rewriting (used as alias)
- `tool_chain`: array of tool invocations with parameters
- `result_type`: expected output format
- `created_at`: timestamp of creation
- `created_by`: user identifier

#### Scenario: Block creation after successful debug
- **WHEN** user completes debugging and clicks "Save as Block"
- **THEN** system creates block with complete mapping

### Requirement: Block SHALL support few-shot usage

Blocks SHALL be usable as few-shot examples to guide model behavior in similar scenarios.

#### Scenario: Block as few-shot example
- **WHEN** executing a new prompt similar to existing block
- **THEN** system uses block's tool_chain as reference

### Requirement: Block SHALL enable dynamic tool binding

When a block is selected for execution, the system SHALL only bind the tools referenced in that block's tool_chain to the relevant agents.

#### Scenario: Selective tool binding
- **WHEN** block references only asset_attacks tool
- **THEN** query agent is bound only to asset_attacks (not all tools)

### Requirement: Block SHALL support CRUD operations

Users SHALL be able to:
- Create: save new blocks after debugging
- Read: view block details and usage history
- Update: modify block parameters (with version tracking)
- Delete: remove blocks (with confirmation)

#### Scenario: Block deletion
- **WHEN** user deletes a block
- **THEN** system confirms deletion and removes block permanently

### Requirement: Block SHALL support categorization

Blocks SHALL support categorization for organization:
- personal: private to the creating user
- shared: available to all users in organization

#### Scenario: Shared block visibility
- **WHEN** user creates block with category "shared"
- **THEN** other users can see and use the block
