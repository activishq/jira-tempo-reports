CREATE TABLE IF NOT EXISTS target (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    week_start_date DATE NOT NULL,
    target_hours DECIMAL(5, 2) NOT NULL,
    CONSTRAINT fk_employee_target
        FOREIGN KEY(employee_id)
        REFERENCES employees(employee_id),
    CONSTRAINT unique_employee_week_target
        UNIQUE (employee_id, week_start_date)
);

CREATE INDEX IF NOT EXISTS idx_target_employee_week
ON target (employee_id, week_start_date);
