"""ClickHouse client for spatial results."""
from __future__ import annotations

import logging
import os

import pandas as pd

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """Thin wrapper around clickhouse-driver Client."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
    ) -> None:
        """Initialize the ClickHouse client configuration.

        Connection is lazy — no socket is opened until the first query.

        Args:
            host: ClickHouse host; falls back to CH_HOST env var (empty = disabled).
            port: ClickHouse native protocol port; falls back to CH_PORT env var (default 9000).
            database: Database name; falls back to CH_DB env var (default "lahaina").

        Attributes:
            _host: Resolved host string.
            _port: Resolved port integer.
            _database: Resolved database name.
            _client: Lazily initialized clickhouse_driver.Client instance (None until first use).
        """
        self._host = host or os.environ.get("CH_HOST", "")
        self._port = int(port or os.environ.get("CH_PORT", "9000"))
        self._database = database or os.environ.get("CH_DB", "lahaina")
        self._client = None

    def _get_client(self):
        """Return the clickhouse_driver Client, creating it on first call.

        Returns:
            Initialized clickhouse_driver.Client connected to self._host.

        Raises:
            RuntimeError: If CH_HOST is not configured.
        """
        if not self._host:
            raise RuntimeError("CH_HOST not set; ClickHouse unavailable.")
        if self._client is None:
            from clickhouse_driver import Client
            self._client = Client(
                host=self._host,
                port=self._port,
                database=self._database,
            )
        return self._client

    def connect(self) -> None:
        """Eagerly initialize the ClickHouse connection.

        Raises:
            RuntimeError: If CH_HOST is not set.
        """
        self._get_client()

    def create_tables(self) -> None:
        """Create lisa_results, gwr_surfaces, and model_comparison tables if absent.

        All tables use MergeTree with a run_date partition. Safe to call repeatedly
        (CREATE TABLE IF NOT EXISTS semantics).

        Raises:
            RuntimeError: If CH_HOST is not configured.
        """
        client = self._get_client()
        client.execute(
            """
            CREATE TABLE IF NOT EXISTS lisa_results (
              parcel_id String,
              lat Float64,
              lon Float64,
              y_raw Float64,
              y_residual Float64,
              I_local Float64,
              p_value Float64,
              cluster_label LowCardinality(String),
              run_date Date DEFAULT today()
            ) ENGINE = MergeTree() ORDER BY (run_date, cluster_label, parcel_id)
            """
        )
        client.execute(
            """
            CREATE TABLE IF NOT EXISTS gwr_surfaces (
              parcel_id String,
              lat Float64,
              lon Float64,
              bandwidth_km Float64,
              beta_intercept Float64,
              beta_dist_to_fire Float64,
              beta_wui Float64,
              y_hat Float64,
              residual Float64,
              run_date Date DEFAULT today()
            ) ENGINE = MergeTree() ORDER BY (run_date, parcel_id)
            """
        )
        client.execute(
            """
            CREATE TABLE IF NOT EXISTS model_comparison (
              model_name LowCardinality(String),
              spatial_param Float64,
              log_likelihood Float64,
              aic Float64,
              bic Float64,
              p_value_spatial Float64,
              run_date Date DEFAULT today()
            ) ENGINE = MergeTree() ORDER BY (run_date, model_name)
            """
        )

    def insert_lisa(self, df: pd.DataFrame) -> None:
        """Bulk-insert LISA results into the lisa_results table.

        Args:
            df: DataFrame whose columns match the lisa_results schema.
        """
        client = self._get_client()
        rows = df.to_dict(orient="records")
        client.execute("INSERT INTO lisa_results VALUES", rows)

    def insert_gwr(self, df: pd.DataFrame) -> None:
        """Bulk-insert GWR surface rows into the gwr_surfaces table.

        Args:
            df: DataFrame whose columns match the gwr_surfaces schema.
        """
        client = self._get_client()
        rows = df.to_dict(orient="records")
        client.execute("INSERT INTO gwr_surfaces VALUES", rows)

    def insert_model_comparison(self, df: pd.DataFrame) -> None:
        """Bulk-insert model comparison rows into the model_comparison table.

        Args:
            df: DataFrame whose columns match the model_comparison schema.
        """
        client = self._get_client()
        rows = df.to_dict(orient="records")
        client.execute("INSERT INTO model_comparison VALUES", rows)

    def query(self, sql: str, parameters: dict | None = None) -> pd.DataFrame:
        """Execute an arbitrary SQL query and return the results as a DataFrame.

        Args:
            sql: SQL string; use %(name)s placeholders for parameters.
            parameters: Dict of bind parameters (optional).

        Returns:
            DataFrame with column names derived from the query result metadata.

        Raises:
            RuntimeError: If CH_HOST is not configured.
        """
        client = self._get_client()
        result = client.execute(sql, params=parameters or {}, with_column_types=True)
        data, columns = result
        col_names = [c[0] for c in columns]
        return pd.DataFrame(data, columns=col_names)
