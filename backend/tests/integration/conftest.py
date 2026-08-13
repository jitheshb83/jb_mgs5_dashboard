"""Shared fixtures for integration tests.

Uses a temp-file SQLite DB per test (via DATABASE_PATH env var, which
app.config.get_settings() reads fresh -- no caching) and a fake SaicApi class
so tests never call the real SAIC API.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.fixtures.synthetic_saic_responses import (
    synthetic_charging_management_data,
    synthetic_vehicle_status,
)


@pytest.fixture
def temp_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "test_mgs5.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("SAIC_USERNAME", "test@example.com")
    monkeypatch.setenv("SAIC_PASSWORD", "super-secret-test-password")
    monkeypatch.setenv("SAIC_REGION", "eu")
    return db_path


class FakeVinInfo:
    vin = "TESTVIN0000000001"


class FakeVehicleListResp:
    def __init__(self) -> None:
        self.vinList = [FakeVinInfo()]  # matches real library's field naming


class FakeSaicApi:
    """Stands in for saic_ismart_client_ng.SaicApi -- no network calls."""

    login_call_count = 0

    def __init__(self, _config: object) -> None:
        pass

    async def login(self) -> None:
        FakeSaicApi.login_call_count += 1

    async def vehicle_list(self) -> FakeVehicleListResp:
        return FakeVehicleListResp()

    async def get_vehicle_status(self, _vin: str) -> object:
        return synthetic_vehicle_status()

    async def get_vehicle_charging_management_data(self, _vin: str) -> object:
        return synthetic_charging_management_data()


class FakeSaicApiWithScheduleAndObc(FakeSaicApi):
    """Same as FakeSaicApi, but with scheduled-charging reservation and
    on-board AC charger input fields set -- matches a real captured vehicle
    response (2026-08-13), see test_advanced.py's
    test_advanced_scheduled_charging_and_obc_ac_input."""

    async def get_vehicle_charging_management_data(self, _vin: str) -> object:
        return synthetic_charging_management_data(
            bms_reser_ctrl_dsp_cmd=2,  # ScheduledChargingMode.DISABLED
            bms_reser_st_hour_dsp_cmd=22,
            bms_reser_st_mintue_dsp_cmd=0,
            bms_reser_sp_hour_dsp_cmd=6,
            bms_reser_sp_mintue_dsp_cmd=0,
            on_bd_chrgr_altr_crnt_inpt_crnt=80,  # -> 16.0 A
            on_bd_chrgr_altr_crnt_inpt_vol=115,  # -> 230.0 V
        )


class FakeSaicApiAuthFailure:
    """A fake SaicApi whose login always fails, for testing the 502 path."""

    def __init__(self, _config: object) -> None:
        pass

    async def login(self) -> None:
        from saic_ismart_client_ng.exceptions import SaicLogoutException

        raise SaicLogoutException("invalid credentials", 401)


@pytest.fixture
def mock_saic_success(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeSaicApi.login_call_count = 0
    monkeypatch.setattr("app.services.saic_client.SaicApi", FakeSaicApi)


@pytest.fixture
def mock_saic_success_with_schedule_and_obc(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeSaicApiWithScheduleAndObc.login_call_count = 0
    monkeypatch.setattr("app.services.saic_client.SaicApi", FakeSaicApiWithScheduleAndObc)


@pytest.fixture
def mock_saic_auth_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.saic_client.SaicApi", FakeSaicApiAuthFailure)


@pytest.fixture
def client(temp_db_path: Path) -> Iterator[TestClient]:
    # Imported here (after env vars are set by temp_db_path) to ensure a fresh
    # app.main import path is unnecessary -- get_settings() re-reads env every call.
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
