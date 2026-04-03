# Debug Mode

## ADDED Requirements

### Requirement: Debug Mode SHALL allow single data part execution

Users SHALL be able to execute and preview a single data part in isolation without running the entire report template.

#### Scenario: Single data part debug
- **WHEN** user selects a data part in debug mode
- **THEN** only that data part executes and displays result

### Requirement: Debug Mode SHALL display result preview

Debug mode SHALL show the rendered result (table, chart, or text) immediately after execution.

#### Scenario: Result preview display
- **WHEN** data part execution completes
- **THEN** system displays result in preview panel

### Requirement: Debug Mode SHALL allow prompt adjustment

Users SHALL be able to modify the prompt text and re-execute to iterate on the result.

#### Scenario: Prompt iteration
- **WHEN** user modifies prompt and clicks "Re-run"
- **THEN** system re-executes with new prompt and shows updated result

### Requirement: Debug Mode SHALL save verified data parts

When user is satisfied with the debug result, they SHALL be able to save the data part configuration to a block.

#### Scenario: Save verified data part
- **WHEN** user clicks "Save as Block" on satisfactory result
- **THEN** system creates new block with original_prompt, rewritten_prompt, and tool_chain

### Requirement: Debug Mode SHALL show execution history

Debug mode SHALL display the sequence of executions during a debug session for traceability.

#### Scenario: Execution history display
- **WHEN** user completes multiple debug iterations
- **THEN** system shows history with timestamps and results

### Requirement: Debug Mode SHALL support comparison

Users SHALL be able to compare results from different prompt versions side by side.

#### Scenario: Side-by-side comparison
- **WHEN** user has 2+ debug iterations
- **THEN** user can select two versions to compare
