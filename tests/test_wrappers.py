import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.simulators as sim
import xpdsim.movers as movers

import scanplans.wrapper as helper


def test_wrapper_count():
    trigger_and_read = helper.shutter_wrapper(bps.trigger_and_read, movers.shctl1, 0, 100, 0)
    one_shot = helper.take_reading_wrapper(bps.one_shot, trigger_and_read)
    plan = bp.count([movers.cs700], per_shot=one_shot)
    sim.summarize_plan(plan)


def test_grid_scan():
    trigger_and_read = helper.shutter_wrapper(bps.trigger_and_read, movers.shctl1, 0, 100, 0)
    one_nd_step = helper.take_reading_wrapper(bps.one_nd_step, trigger_and_read)
    plan = bp.grid_scan([movers.cs700], movers.cs700, -1, 1, 3, per_step=one_nd_step)
    sim.summarize_plan(plan)
