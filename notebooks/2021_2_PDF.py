import functools
import bluesky.plan_stubs as bps
from bluesky.simulators import summarize_plan
import bluesky.plans as bp
from bluesky.preprocessors import pchain
from xpdacq.xpdacq import open_shutter_stub, close_shutter_stub
from xpdacq.xpdacq_conf import xpd_configuration
from xpdacq.beamtime import configure_area_det

"""
from xpdacq.simulation import pe1c, shctl1, cs700
from ophyd.sim import hw

motor = hw().motor
xpd_configuration['shutter'] = shctl1
"""

def my_take_reading(devices: list):
    yield from open_shutter_stub()
    sts = yield from bps.trigger_and_read(devices, name="primary")
    yield from close_shutter_stub()
    return sts


def my_per_step(detectors, step, pos_cache, take_reading=my_take_reading):
    sts = yield from bps.one_nd_step(detectors, step, pos_cache, take_reading=take_reading)
    return sts


def gen_per_step(delay: float):

    @functools.wraps(bps.one_nd_step)
    def _per_step(detectors, step, pos_cache, take_reading=my_take_reading):
        yield from bps.sleep(delay)
        sts = yield from bps.one_nd_step(detectors, step, pos_cache, take_reading=take_reading)
        return sts
    
    return _per_step


# Mandy's samples
per_step7 = gen_per_step(60 * 5)
plan42 = pchain(
    configure_area_det(pe1c, 60 * 5, 0.2),
    bp.list_scan([pe1c], cs700, [300, 433, 465], per_step=per_step7),
    configure_area_det(pe1c, 60, 0.2),
    bp.grid_scan([pe1c], cs700, 465, 300, 34, per_step=my_per_step)
)
plan43 = pchain(
    configure_area_det(pe1c, 60 * 5, 0.2),
    bp.list_scan([pe1c], cs700, [300, 433], per_step=per_step7),
    bps.mv(cs700, 300)
)
plan44 = pchain(
    configure_area_det(pe1c, 60 * 5, 0.2),
    bp.list_scan([pe1c], cs700, [300], per_step=my_per_step),
    configure_area_det(pe1c, 60, 0.2),
    bp.grid_scan([pe1c], cs700, 300, 455, 32, per_step=my_per_step),
    configure_area_det(pe1c, 60 * 5, 0.2),
    bp.list_scan([pe1c], cs700, [455], per_step=per_step7),
    configure_area_det(pe1c, 60, 0.2),
    bp.grid_scan([pe1c], cs700, 455, 300, 32, per_step=my_per_step),
)
plan45 = pchain(
    bp.list_scan([pe1c], cs700, [300, 413], per_step=per_step7),
    bps.mv(cs700, 300)
)

# Sandra's samples
configure1 = configure_area_det(pe1c, 120, 0.2)
per_step1 = gen_per_step(60 * 5)
plan5 = pchain(
    bp.list_scan([pe1c], cs700, [80, 250, 400], per_step=per_step1),
    bps.mv(cs700, 300)
)
plan6 = pchain(
    bp.list_scan([pe1c], cs700, [150, 240, 350, 420], per_step=per_step1),
    bps.mv(cs700, 300)
)
plan7 = pchain(
    bp.list_scan([pe1c], cs700, [200, 295], per_step=per_step1),
    bps.mv(cs700, 300)
)
plan8 = pchain(
    bp.list_scan([pe1c], cs700, [100, 300], per_step=per_step1),
    bps.mv(cs700, 300)
)
# Wendy's sample
configure2 = configure_area_det(pe1c, 60, 0.2)
plan9 = bp.grid_scan([pe1c], cs700, 90, 500, 42, per_step=my_per_step)

# Wilson's samples
confgiure3 = configure_area_det(pe1c, 120, 0.2)
plan10 = bp.count([pe1c], per_shot=my_take_reading)
plan11 = bp.count([pe1c], per_shot=my_take_reading)
plan12 = bp.count([pe1c], per_shot=my_take_reading)
plan13 = bp.count([pe1c], per_shot=my_take_reading)
plan14 = bp.count([pe1c], per_shot=my_take_reading)
plan15 = bp.count([pe1c], per_shot=my_take_reading)
plan16 = bp.count([pe1c], per_shot=my_take_reading)
plan17 = bp.count([pe1c], per_shot=my_take_reading)
plan18 = bp.count([pe1c], per_shot=my_take_reading)
plan19 = bp.count([pe1c], per_shot=my_take_reading)

# Yevgeny's samples
configure4 = configure_area_det(pe1c, 120, 0.2)
plan20 = bp.rel_grid_scan([pe1c], motor, -3, 3, 3, per_step=my_per_step)
plan21 = bp.rel_grid_scan([pe1c], motor, -3, 3, 3, per_step=my_per_step)
plan22 = bp.rel_grid_scan([pe1c], motor, -3, 3, 3, per_step=my_per_step)
plan23 = bp.rel_grid_scan([pe1c], motor, -3, 3, 3, per_step=my_per_step)
plan24 = bp.rel_grid_scan([pe1c], motor, -3, 3, 3, per_step=my_per_step)

# Hunter's samples
configure5 = configure_area_det(pe1c, 120, 0.2)
plan25 = bp.rel_grid_scan([pe1c], motor, -3, 3, 3, per_step=my_per_step)
plan26 = bp.rel_grid_scan([pe1c], motor, -3, 3, 3, per_step=my_per_step)
plan27 = bp.rel_grid_scan([pe1c], motor, -3, 3, 3, per_step=my_per_step)
plan28 = bp.rel_grid_scan([pe1c], motor, -3, 3, 3, per_step=my_per_step)

# Wenhu's samples
configure6 = configure_area_det(pe1c, 120, 0.2)
plan29 = bp.count([pe1c], 3, 5, per_shot=my_take_reading)
plan30 = bp.count([pe1c], 3, 5, per_shot=my_take_reading)
plan31 = bp.count([pe1c], 3, 5, per_shot=my_take_reading)
plan32 = bp.count([pe1c], 3, 5, per_shot=my_take_reading)

# Eric's samples
configure6 = configure_area_det(pe1c, 120, 0.2)
plan33 = bp.count([pe1c], 10, 5, per_shot=my_take_reading)
plan34 = bp.count([pe1c], 10, 5, per_shot=my_take_reading)
plan35 = bp.count([pe1c], 10, 5, per_shot=my_take_reading)
plan36 = bp.count([pe1c], 10, 5, per_shot=my_take_reading)
