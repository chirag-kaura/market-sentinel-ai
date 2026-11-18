"""Unit tests for Apache Airflow DAG Integrity and Dependency Validation."""
import importlib.util
import os
import pytest

AIRFLOW_DAGS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "orchestration", "airflow", "dags")


def test_airflow_dags_directory_exists():
    """Verify that the Airflow DAGs directory exists."""
    assert os.path.exists(AIRFLOW_DAGS_DIR)


def test_daily_market_ingestion_dag_integrity():
    """Test importing and verifying the daily market ingestion DAG structure."""
    dag_path = os.path.join(AIRFLOW_DAGS_DIR, "daily_market_ingestion_dag.py")
    assert os.path.exists(dag_path)

    try:
        from airflow.models import DAG
        spec = importlib.util.spec_from_file_location("daily_market_ingestion_dag", dag_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        dag = getattr(module, "dag", None)
        assert isinstance(dag, DAG)
        assert dag.dag_id == "daily_market_ingestion_dag"
        assert len(dag.tasks) == 5

        # Verify task IDs
        task_ids = {t.task_id for t in dag.tasks}
        expected_tasks = {
            "fetch_nse_bhavcopy",
            "fetch_nse_delivery",
            "validate_and_quarantine",
            "upsert_to_postgresql",
            "append_to_parquet_store",
        }
        assert task_ids == expected_tasks

        # Verify task dependencies
        t_validate = dag.get_task("validate_and_quarantine")
        t_bhavcopy = dag.get_task("fetch_nse_bhavcopy")
        t_delivery = dag.get_task("fetch_nse_delivery")
        assert t_bhavcopy in t_validate.upstream_list
        assert t_delivery in t_validate.upstream_list

    except ImportError:
        # If airflow is not locally installed on the development host, verify file contents and syntax
        with open(dag_path, "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, dag_path, "exec")
        assert "daily_market_ingestion_dag" in code
        assert "schedule_interval" in code


def test_intraday_news_ingestion_dag_integrity():
    """Test importing and verifying the intraday news ingestion DAG structure."""
    dag_path = os.path.join(AIRFLOW_DAGS_DIR, "intraday_news_ingestion_dag.py")
    assert os.path.exists(dag_path)

    try:
        from airflow.models import DAG
        spec = importlib.util.spec_from_file_location("intraday_news_ingestion_dag", dag_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        dag = getattr(module, "dag", None)
        assert isinstance(dag, DAG)
        assert dag.dag_id == "intraday_news_ingestion_dag"
        assert len(dag.tasks) == 4

        task_ids = {t.task_id for t in dag.tasks}
        expected_tasks = {
            "fetch_financial_rss_news",
            "fetch_corporate_filings",
            "deduplicate_and_sanitize",
            "persist_news_to_database",
        }
        assert task_ids == expected_tasks
    except ImportError:
        with open(dag_path, "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, dag_path, "exec")
        assert "intraday_news_ingestion_dag" in code
