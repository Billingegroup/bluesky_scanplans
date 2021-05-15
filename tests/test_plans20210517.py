from bluesky import RunEngine
from bluesky.simulators import summarize_plan
from ophyd.sim import hw

from scanplans.plans20210517 import my_list_grid_scan
from xpdacq.simulation import xpd_pe1c, shctl1, cs700
from xpdacq.xpdacq_conf import xpd_configuration


def test_my_list_grid_scan1():
    xpd_configuration["shutter"] = shctl1
    motor = hw().motor
    plan = my_list_grid_scan(xpd_pe1c, motor, [1.], cs700, [300., 400., 500.], acquire_time=0.2,
                             images_per_set=300, wait_for_step=20.)
    summarize_plan(plan)


def test_my_list_grid_scan2():
    xpd_configuration["shutter"] = shctl1
    motor = hw().motor
    plan = my_list_grid_scan(xpd_pe1c, motor, [1.], cs700, [300., 400., 500.], acquire_time=0.2, images_per_set=5,
                             wait_for_step=0.)
    RE = RunEngine()
    RE(plan)
