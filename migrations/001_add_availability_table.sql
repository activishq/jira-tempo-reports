-- Création de la table availability si elle n'existe pas
CREATE TABLE IF NOT EXISTS availability (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    week_start_date DATE NOT NULL,
    budget_hours DECIMAL(5, 2) NOT NULL
);

-- Ajout de la contrainte de clé étrangère si elle n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_employee' AND table_name = 'availability'
    ) THEN
        ALTER TABLE availability
        ADD CONSTRAINT fk_employee
        FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id);
    END IF;
END $$;

-- Ajout de la contrainte d'unicité si elle n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'unique_employee_week' AND table_name = 'availability'
    ) THEN
        ALTER TABLE availability
        ADD CONSTRAINT unique_employee_week
        UNIQUE (employee_id, week_start_date);
    END IF;
END $$;

-- Création de l'index s'il n'existe pas déjà
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'idx_availability_employee_week'
    ) THEN
        CREATE INDEX idx_availability_employee_week
        ON availability (employee_id, week_start_date);
    END IF;
END $$;
