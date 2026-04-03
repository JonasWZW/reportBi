# Data Part

## ADDED Requirements

### Requirement: Data Part SHALL represent atomic query or analysis unit

A data part SHALL represent the smallest executable unit in a report section, corresponding to a single user's prompt after rewriting.

#### Scenario: Query data part structure
- **WHEN** data part is of type "query"
- **THEN** it contains tool_id and params for execution

#### Scenario: Analysis data part structure
- **WHEN** data part is of type "analyze"
- **THEN** it contains depends_on references to source data parts

### Requirement: Data Part SHALL support result types

Data parts SHALL support the following result types:
- table: tabular data display
- chart: graphical visualization (bar, line, pie)
- text: textual summary or analysis

#### Scenario: Table result type
- **WHEN** data part is configured with result_type "table"
- **THEN** output renders as a data table

#### Scenario: Chart result type
- **WHEN** data part is configured with result_type "chart"
- **THEN** output renders as specified chart type

### Requirement: Data Part SHALL track execution state

Each data part SHALL track its execution state:
- pending: not yet executed
- running: currently executing
- completed: successfully finished
- failed: execution error

#### Scenario: Execution state transition
- **WHEN** data part execution starts
- **THEN** state changes from pending to running

#### Scenario: Execution failure handling
- **WHEN** data part execution fails
- **THEN** state changes to failed with error message
