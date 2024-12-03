-- config/schema.sql

-- Model Families Table
CREATE TABLE IF NOT EXISTS model_families (
    model_family_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Generation Tasks Table
CREATE TABLE IF NOT EXISTS generation_tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL UNIQUE,
    description TEXT,
    max_tokens INTEGER,
    output_format TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Evaluation Tasks Table
CREATE TABLE IF NOT EXISTS evaluation_tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Association table between generation_tasks and evaluation_tasks
CREATE TABLE IF NOT EXISTS generation_task_evaluation_tasks (
    generation_task_id INTEGER NOT NULL,
    evaluation_task_id INTEGER NOT NULL,
    PRIMARY KEY (generation_task_id, evaluation_task_id),
    FOREIGN KEY (generation_task_id) REFERENCES generation_tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (evaluation_task_id) REFERENCES evaluation_tasks(task_id) ON DELETE CASCADE
);

-- Association table between generation_tasks and providers
CREATE TABLE IF NOT EXISTS generation_task_providers (
    generation_task_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    PRIMARY KEY (generation_task_id, provider_id),
    FOREIGN KEY (generation_task_id) REFERENCES generation_tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id) ON DELETE CASCADE
);

-- Generation Prompt Templates Table
CREATE TABLE IF NOT EXISTS generation_prompt_templates (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    model_family_id INTEGER NOT NULL,
    template_text TEXT NOT NULL,
    version INTEGER NOT NULL,
    placeholders TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES generation_tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (model_family_id) REFERENCES model_families(model_family_id)
);

-- Evaluation Prompt Templates Table
CREATE TABLE IF NOT EXISTS evaluation_prompt_templates (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    model_family_id INTEGER NOT NULL,
    template_text TEXT NOT NULL,
    version INTEGER NOT NULL,
    placeholders TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES evaluation_tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (model_family_id) REFERENCES model_families(model_family_id)
);

-- Providers Table
CREATE TABLE IF NOT EXISTS providers (
    provider_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    provider_name TEXT NOT NULL, -- e.g., 'openai'
    family TEXT NOT NULL,        -- e.g., 'gpt', 'llama'
    model TEXT NOT NULL,
    version TEXT NOT NULL,
    api_base TEXT NOT NULL,
    max_tokens INTEGER NULL,
    temperature REAL NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Styling Guides Table
CREATE TABLE IF NOT EXISTS styling_guides (
    styling_guide_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_type TEXT NOT NULL,
    task_name TEXT NOT NULL,
    content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_type, task_name, version)
);

-- Task Execution Config Table
CREATE TABLE IF NOT EXISTS task_execution_config (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    default_tasks TEXT NOT NULL, -- Stored as JSON array
    conditional_tasks TEXT NOT NULL, -- Stored as JSON object
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Prompt Templates
CREATE INDEX IF NOT EXISTS idx_generation_prompt_templates_task_id ON generation_prompt_templates(task_id);
CREATE INDEX IF NOT EXISTS idx_generation_prompt_templates_model_family_id ON generation_prompt_templates(model_family_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_prompt_templates_task_id ON evaluation_prompt_templates(task_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_prompt_templates_model_family_id ON evaluation_prompt_templates(model_family_id);

-- Indexes for Styling Guides
CREATE INDEX IF NOT EXISTS idx_styling_guides_product_task ON styling_guides(product_type, task_name);

-- Indexes for Association Tables
CREATE INDEX IF NOT EXISTS idx_gen_task_eval_tasks_gen_task_id ON generation_task_evaluation_tasks(generation_task_id);
CREATE INDEX IF NOT EXISTS idx_gen_task_eval_tasks_eval_task_id ON generation_task_evaluation_tasks(evaluation_task_id);

CREATE INDEX IF NOT EXISTS idx_gen_task_providers_gen_task_id ON generation_task_providers(generation_task_id);
CREATE INDEX IF NOT EXISTS idx_gen_task_providers_provider_id ON generation_task_providers(provider_id);
