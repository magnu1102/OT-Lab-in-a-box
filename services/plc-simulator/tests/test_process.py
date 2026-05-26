from app.process import WaterTankProcess


def test_high_tank_scenario_sets_alarm_state():
    process = WaterTankProcess()

    process.set_high_tank_scenario()

    assert process.tank_level > process.HIGH_ALARM
    assert process.alarm is True
    assert process.pump_running is True


def test_reset_restores_normal_state_after_high_tank_scenario():
    process = WaterTankProcess()
    process.set_high_tank_scenario()

    process.reset()

    assert process.tank_level == 50.0
    assert process.pump_running is True
    assert process.inflow_rate == 2.0
    assert process.outflow_rate == 1.2
    assert process.temperature == 18.5
    assert process.alarm is False
