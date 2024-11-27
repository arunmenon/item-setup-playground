-- config/schema.sql

-- Providers Table
CREATE TABLE IF NOT EXISTS providers (
    provider_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    provider_name TEXT NOT NULL, -- e.g., 'openai'
    family TEXT NOT NULL,        -- e.g., 'gpt', 'llama'
    model TEXT NOT NULL,
    max_tokens INTEGER NULL,
    temperature REAL NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Templates Table
CREATE TABLE IF NOT EXISTS templates (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    template_type TEXT NOT NULL CHECK (template_type IN ('base', 'model')),
    parent_template_id INTEGER NULL REFERENCES templates(template_id),
    model_family TEXT NULL,
    task_name TEXT NOT NULL,
    content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(template_name, version)
);

-- Placeholders Table
CREATE TABLE IF NOT EXISTS placeholders (
    placeholder_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NULL,
    data_type TEXT NOT NULL,
    default_value TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- TemplatePlaceholders Association Table
CREATE TABLE IF NOT EXISTS template_placeholders (
    template_id INTEGER NOT NULL REFERENCES templates(template_id),
    placeholder_id INTEGER NOT NULL REFERENCES placeholders(placeholder_id),
    PRIMARY KEY (template_id, placeholder_id)
);

-- StylingGuides Table
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

-- Tasks Table
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL UNIQUE,
    max_tokens INTEGER NOT NULL,
    output_format TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- TaskExecutionConfig Table
CREATE TABLE IF NOT EXISTS task_execution_config (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    default_tasks TEXT NOT NULL, -- Stored as JSON array
    conditional_tasks TEXT NOT NULL, -- Stored as JSON object
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- Indexes (Optional)
CREATE INDEX IF NOT EXISTS idx_templates_task_name ON templates(task_name);
CREATE INDEX IF NOT EXISTS idx_templates_model_family ON templates(model_family);
CREATE INDEX IF NOT EXISTS idx_styling_guides_product_task ON styling_guides(product_type, task_name);
