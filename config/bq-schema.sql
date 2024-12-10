CREATE OR REPLACE TABLE `my_project.my_dataset.task_input` (
  item_id INT64 NOT NULL,
  dataset_id INT64 NOT NULL,
  item_data STRING,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY RANGE_BUCKET(dataset_id, GENERATE_ARRAY(1, 100000, 1000))
CLUSTER BY dataset_id;

CREATE OR REPLACE TABLE `my_project.my_dataset.evaluation_results` (
  item_id INT64 NOT NULL,
  item_product_type STRING,
  generation_task STRING,
  evaluation_task STRING,
  model_name STRING,
  model_version STRING,
  evaluator_type STRING,
  evaluator_id STRING,
  evaluation_data STRING, -- JSON
  raw_evaluation_data STRING,
  is_winner BOOL,
  comments STRING,
  dataset_id INT64 NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY RANGE_BUCKET(dataset_id, GENERATE_ARRAY(1, 100000, 1000))
CLUSTER BY dataset_id;

CREATE OR REPLACE TABLE `my_project.my_dataset.aggregated_evaluations` (
  item_id INT64 NOT NULL,
  item_product_type STRING,
  generation_task STRING,
  evaluation_task STRING,
  model_name STRING,
  model_version STRING,
  evaluator_type STRING,
  evaluator_id STRING,
  metric_name STRING,
  metric_mean FLOAT64,
  metric_variance FLOAT64,
  metric_confidence STRING,
  dataset_id INT64 NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY RANGE_BUCKET(dataset_id, GENERATE_ARRAY(1, 100000, 1000))
CLUSTER BY dataset_id;

