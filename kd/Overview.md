## Overview

The objective of this flow is to create a high-quality dataset for instruction tuning from previously generated model responses and their evaluation results. This dataset can then be used to fine-tune smaller models. The steps include:

1. **Defining a Scenario**: What generation model, tasks, evaluation tasks, and metrics should we filter by to get high-quality responses.
2. **Fetching High-Quality Responses**: Based on the scenario, query BigQuery for top-scoring model responses from `evaluation_results`.
3. **Retrieving Item Inputs**: Once we have chosen responses, fetch their corresponding item input data (title, descriptions, product type) from `task_input`.
4. **Regenerating Original Prompts**: Using `PromptManager` to reconstruct the original prompt given the item inputs and generation tasks.
5. **Formatting Data**: Convert each (prompt, response) pair into a standardized instruction tuning format (e.g., Alpaca-style JSON).
6. **Storing the Dataset**: Save the final dataset as JSONL or Parquet locally, then upload to GCS.

---

## Key Components

### 1. ScenarioParams (`kd/scenario_params.py`)

**Purpose**: Encapsulate the configuration parameters for the scenario. This includes:

- GCP project and dataset information.
- The generation model name (e.g., `gpt-4o`).
- The generation tasks (e.g., `["title_enhancement"]`).
- The evaluation tasks and metrics to filter on (e.g., `["title_style_guide_compliance_check"]` and `quality_score`).
- Scenario type (e.g., `all_eval_models` means we require all specified eval tasks to be present).
- Optional score thresholds, top-N limits, and specific eval models.

**How It's Used**:
Developers instantiate `ScenarioParams` with their desired configuration. Other classes (like `ScenarioManager`) use this configuration to decide how to query and filter data.

### 2. QueryBuilder (`kd/query_builder.py`)

**Purpose**: Construct BigQuery SQL queries dynamically based on `ScenarioParams`.

- `build_evaluation_query`: Generates SQL to select top model responses from `evaluation_results` table. It applies filters for generation model, tasks, optional evaluation tasks, eval model, min score, and so forth.
- `build_task_input_query`: Generates SQL to fetch item inputs (title, short_desc, long_desc, product_type) from `task_input` table for the selected items.

**How It's Used**:
`ScenarioManager` calls `QueryBuilder` to get the actual SQL strings, which are then run by the BigQuery client.

### 3. ScenarioManager (`kd/scenario_manager.py`)

**Purpose**: Orchestrate the scenario logic and determine which metric to use if not explicitly provided.

- Determines the evaluation metric by inspecting `EvaluationTask` definitions if `eval_task_metric` is not provided.
- Executes the evaluation query and fetches initial high-quality responses.
- Applies scenario-specific logic (e.g., `all_eval_models` scenario might require that each item has responses from all required evaluation tasks).

**How It's Used**:
`InstructionDatasetCreator` uses `ScenarioManager` to get the filtered, final list of high-quality responses that meet the scenario criteria.

### 4. ItemInputFetcher (`kd/item_input_fetcher.py`)

**Purpose**: Once we know which `dataset_id` and `item_id` pairs are needed, this class fetches their input data from `task_input` table in BigQuery.

**How It's Used**:
After `ScenarioManager` selects responses, `InstructionDatasetCreator` calls `ItemInputFetcher` to pull the original input fields needed to reconstruct prompts.

### 5. PromptManager (`prompt_manager.py` - external to `kd` directory)

**Purpose**: Given the item data (product type, title, descriptions) and a family name, `PromptManager` can regenerate the original prompts that were used to create model responses. This relies on templates and logic defined elsewhere. It's a key step since we only have the final model responses in `evaluation_results`; we need the original prompt to create instruction tuning pairs.

**How It's Used**:
`InstructionDatasetCreator` passes the item data and task type to `PromptManager` to get back the exact prompts that were originally given to the model.

### 6. InstructionFormatter (`kd/instruction_formatter.py`)

**Purpose**: Convert a `(prompt, model_response)` pair into the chosen instruction tuning format (e.g., Alpaca-style JSON).

- `format_record`: Takes the original prompt and model response, plus a generic overarching instruction, and returns a dictionary containing `instruction`, `input`, and `output`.

**How It's Used**:
`InstructionDatasetCreator` calls `InstructionFormatter` for each pair to produce final JSON records.

### 7. InstructionDatasetCreator (`kd/instruction_dataset_creator.py`)

**Purpose**: The main orchestrator that:

- Instantiates `ScenarioManager` to get filtered responses.
- Uses `ItemInputFetcher` to get input data.
- Rebuilds prompts via `PromptManager`.
- Uses `InstructionFormatter` to produce final instruction-tuning records.
- Writes these records to a local file and uploads to GCS.

**How It's Used**:
Developers create an instance of `InstructionDatasetCreator` with the chosen scenario, format, and output location. Calling `run()` executes the entire flow.

---

## Detailed Flow

1. **Initialize Scenario Parameters**: A developer sets up `ScenarioParams` with their desired filtering conditions (model, tasks, metric, scenario type, min score, etc.).

2. **ScenarioManager & Metric Determination**: 
   - If no `eval_task_metric` is given, `ScenarioManager` looks up `EvaluationTask` in the SQL DB to find a suitable numeric metric.
   - The chosen metric is used to order and filter the responses from `evaluation_results`.

3. **Fetching High-Quality Responses**:
   - `ScenarioManager` calls `QueryBuilder.build_evaluation_query()` to get a SQL query.
   - Executes the query in BigQuery, returns a list of candidate responses.
   - Applies scenario logic (for example, if `scenario_type` = `all_eval_models`, it ensures each item has responses from all required evaluation tasks).

4. **Retrieve Item Inputs**:
   - From the filtered responses, extract `(dataset_id, item_id)` pairs.
   - `ItemInputFetcher` uses `QueryBuilder.build_task_input_query()` to load the corresponding item data (title, short_desc, long_desc, product_type).

5. **Regenerate Prompts**:
   - For each item, `PromptManager.generate_prompts()` is called with `task_type="generation"` and `family_name` if needed.
   - This returns a list of prompts for defined tasks. Find the prompt matching our `task_name`.

6. **Format Records for Instruction Tuning**:
   - For each `(prompt, model_response)` pair, `InstructionFormatter.format_record()` is used to wrap them in a standardized instruction schema.
   - Records are appended to a JSONL file.

7. **Upload to GCS**:
   - The resulting dataset file is uploaded to the specified GCS bucket and path.

---

## Example Use Case

**Example:**
- We have a generation model `gpt-4o` that improves product titles.
- We want only responses that scored above 80.0 on `quality_score` in the `title_style_guide_compliance_check` evaluation task.
- We require that all eval models considered must have contributed to the score (if `scenario_type`= `all_eval_models`).
- After retrieving these top responses and their input data, we generate the original prompt again, and finally produce Alpaca-style JSON records.
- The final dataset is saved to GCS.

---

## Extensibility

- **Adding New Scenario Types**: 
  Developers can add logic in `ScenarioManager` to handle new scenario types (e.g., requiring multiple evaluation tasks, combining metric conditions, etc.).
  
- **Changing Instruction Format**: 
  If a different instruction tuning format is needed, replace or extend `InstructionFormatter`.

- **Updating Metrics Logic**:
  With the `expected_metrics` field in `EvaluationTask`, developers can handle non-numeric or categorical metrics by adjusting `ScenarioManager` and `QueryBuilder` logic.

---

## Conclusion

This flow provides a modular, extensible pipeline for extracting high-quality instruction-tuning datasets from previously generated and evaluated model responses. By abstracting away scenario configuration, querying logic, item input fetching, prompt generation, and formatting, developers can easily adapt and maintain this system for various use cases and evaluation strategies.