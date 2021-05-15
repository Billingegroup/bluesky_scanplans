import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
import typing as tp
from bluesky.callbacks.core import LiveTable

from xpdacq.beamtime import close_shutter_stub, open_shutter_stub


def configure_cam_detector(detector: tp.Any, acquire_time: float, images_per_set: int) -> tp.Generator:
    """Configure the acquire_time of the cam opponent in detector and the images_per_set of the detector."""
    print("acquire_time -> {}; images_per_set -> {}; exposure -> {}".format(acquire_time, images_per_set,
                                                                            acquire_time * images_per_set))
    yield from bps.abs_set(detector.cam.acquire_time, acquire_time, wait=True)
    yield from bps.abs_set(detector.images_per_set, images_per_set, wait=True)


def my_move_per_step(step: dict, pos_cache: dict):
    yield from bps.checkpoint()
    for motor, pos in step.items():
        if pos == pos_cache[motor]:
            continue
        yield from bps.mv(motor, pos)
        pos_cache[motor] = pos


def my_list_grid_scan(detector: tp.Any, *args, acquire_time: float, images_per_set: int, wait_for_step: float = 0.,
                      wait_for_shutter: float = 0.5, md: dict = None) -> tp.Generator:
    """Configure detector and run a list_grid_scan with shutter control and wait for seconds at each step."""
    if not md:
        md = {}

    def per_step(detectors, step: dict, pos_cache: dict):
        _motors = step.keys()
        yield from my_move_per_step(step, pos_cache)
        yield from bps.sleep(wait_for_step)
        yield from open_shutter_stub()
        yield from bps.sleep(wait_for_shutter)
        yield from bps.trigger_and_read(list(detectors) + list(_motors))
        yield from close_shutter_stub()

    plan = bp.list_grid_scan([detector], *args, per_step=per_step, md=md)
    motors = list(args[::2])
    plan = bpp.subs_wrapper(plan, LiveTable([detector] + motors))

    yield from configure_cam_detector(detector, acquire_time, images_per_set)
    return (yield from plan)
