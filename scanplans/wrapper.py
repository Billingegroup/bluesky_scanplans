import bluesky.plan_stubs as bps
import bluesky.plans as bp
import functools
import typing


def shutter_wrapper(func: typing.Callable, shutter, open_state, close_state, delay: float) -> typing.Callable:
    """Wrap the generator function with shutter open, shutter close and delay."""

    @functools.wraps(func)
    def _func(*args, **kwargs):
        yield from bps.mv(shutter, open_state)
        yield from bps.sleep(delay)
        yield from func(*args, **kwargs)
        yield from bps.mv(shutter, close_state)

    _func.__doc__ = func.__doc__

    return _func


def take_reading_wrapper(func: typing.Callable, take_reading_func: typing.Callable) -> typing.Callable:
    @functools.wraps(func)
    def _func(*args, take_reading=take_reading_func, **kwargs):
        return func(*args, take_reading=take_reading, **kwargs)

    _func.__doc__ = func.__doc__

    return _func


def xpdacq_ramp_count(motor: typing.Any, value: typing.Any, inner_plan: typing.Callable, take_pre_data=True,
                      timeout=None,
                      period=None, md=None) -> typing.Generator:
    """
    Take data while ramping one or more motors.

    Parameters
    ----------
    inner_plan :
        The plan to repeat in loop. It returns a generator inner_plan().

    motor :
        A positioner to ramp up.

    value:
        A value to ramp up to.

    timeout : float, optional
        If not None, the maximum time the ramp can run.

        In seconds

    take_pre_data: Bool, optional
        If True, add a pre data at beginning

    period : float, optional
        If not None, take data no faster than this.  If None, take
        data as fast as possible

        If running the inner plan takes longer than `period` than take
        data with no dead time.

        In seconds.

    md : dict
        The metadata of this plan.
    """
    for detector in detectors:
        yield from bps.stage(detector)

    def go_plan():
        status, = yield from bps.mv(motor, value)
        return status

    yield from bp.ramp_plan(
        go_plan(),
        motor,
        inner_plan,
        take_pre_data=take_pre_data,
        timeout=timeout,
        period=period,
        md=md
    )

    for detector in detectors:
        yield from bps.unstage(detector)


def slow_dark_wrapper(per_step: typing.Callable, slow_motor: object) -> typing.Callable:
    """
    Decorate the per step function so that it will take a dark image if the slow motor changes its position.

    Parameters
    ----------
    per_step :
        The per step function, like ``f(detectors, step, pos_cache, take_reading)``.

    slow_motor :
        The slow motor in a grid scan.

    Returns
    -------
    _per_step :
        The decorated per_step function.
    """

    def _per_step(detectors: list, step: dict, pos_cache: dict,
                  take_reading: typing.Callable = xpdacq_trigger_and_read):
        # if the slow motor moves to another position in this step, take a dark
        if pos_cache.get(slow_motor) != step.get(slow_motor):
            yield from take_reading(detectors + list(step.keys()), name="dark")
        yield from per_step(detectors, step, pos_cache, take_reading)

    return _per_step


def calc_velocity(start: float, end: float, exposure: float, num: int):
    """Calculate the velocity of the motor.

    Parameters
    ----------
    start :
        The start position of a motor.

    end :
        The end position of a motor.

    exposure :
        The time per exposure.

    num :
        The number of exposure.

    Returns
    -------
    velocity :
        The velocity suggested for the motor.
    """
    return abs(end - start) / (exposure * num)
