## Diagramme de classes

```mermaid
classDiagram
    class JiraReports {
        -auth: HTTPBasicAuth
        +get_current_users() List[str]
        +get_department_availability() float
        +get_estimated_time(start_date: str, end_date: str, user_name: str) DataFrame
        +get_department_total_time_spent(start_date: str, end_date: str) float
        +get_department_estimated_time(start_date: str, end_date: str) float
    }

    class TempoReport {
        -base_url: str
        -access_token: str
        -session: Session
        +get_worklogs(start_date: str, end_date: str, user_name: str) List[Dict]
        +get_logged_time(start_date: str, end_date: str, user_name: str) DataFrame
        +get_department_logged_time(start_date: str, end_date: str, department_users: List[str]) float
    }

    class JiraTempoReport {
        -jira_report: JiraReports
        -tempo_report: TempoReport
        +get_merged_report(start_date: str, end_date: str, user_id: str) DataFrame
        +get_logged_time(start_date: str, end_date: str, user_id: str) float
        +get_leaked_time(start_date: str, end_date: str, user_id: str) float
        +get_billable_time(start_date: str, end_date: str, user_id: str) float
        +get_billable_ratio(start_date: str, end_date: str, user_id: str) float
        +get_department_leaked_time(start_date: str, end_date: str) float
        +calculate_weekly_billable_hours(start_date: str, end_date: str) DataFrame
    }

    class DataProcessor {
        +get_date_range() Tuple[datetime, datetime]
        +process_data(start_date: datetime, end_date: datetime)
    }

    class DatabaseOperations {
        +get_db_connection() Connection
        +insert_data_to_db(data: DataFrame)
        +verify_data_in_db(start_date: datetime, end_date: datetime)
    }

    class StreamlitApp {
        +load_data() DataFrame
        +main()
    }

    JiraTempoReport --> JiraReports
    JiraTempoReport --> TempoReport
    DataProcessor --> JiraTempoReport
    DataProcessor --> DatabaseOperations
    StreamlitApp --> DatabaseOperations
    ```
