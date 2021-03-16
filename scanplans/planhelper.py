import bluesky.plan_stubs as bps
import bluesky.plans as bp
import math
import typing

import xpdacq.beamtime as xb


def configure_area_det(det: typing.Any, exposure: float, acq_time: float):
    """Configure exposure time of a detector in continuous acquisition mode.

    Parameters
    ----------
    det :
        The area detector to be configured.

    exposure :
        The total exposure time. One exposure contains one or multiple frames.

    acq_time :
        The frame acquisition time. The exposure time per frame.

    Returns
    -------
    num_frame :
        Number of frames.

    real_acq_time:
        The real frame acquisition time after set.

    computed_exposure :
        The real exposure time after set.
    """
    xb._check_mini_expo(exposure, acq_time)
    yield from bps.mv(det.cam.acquire_time, acq_time)
    res = yield from bps.read(det.cam.acquire_time)
    real_acq_time = res[det.cam.acquire_time.name]["value"] if res else 1
    if hasattr(det, "images_per_set"):
        # compute number of frames
        num_frame = math.ceil(exposure / real_acq_time)
        yield from bps.mv(det.images_per_set, num_frame)
    else:
        # The dexela detector does not support `images_per_set` so we just
        # use whatever the user asks for as the thing
        num_frame = 1
    computed_exposure = num_frame * real_acq_time

    # print exposure time
    print(
        "INFO: requested exposure time = {} - > computed exposure time"
        "= {}".format(exposure, computed_exposure)
    )
    return num_frame, real_acq_time, computed_exposure


def xpdacq_trigger_and_read(detectors: list, name: str = "primary") -> typing.Generator:
    """Open shutter, wait, trigger and read detectors, close shutter."""
    yield from bps.checkpoint()
    yield from xb.open_shutter_stub()
    yield from bps.sleep(xb.glbl["shutter_sleep"])
    yield from bps.trigger_and_read(detectors, name=name)
    yield from xb.close_shutter_stub()


def xpdacq_per_step(detectors: list, step: dict, pos_cache: dict,
                    take_reading: typing.Callable = xpdacq_trigger_and_read) -> typing.Generator:
    """
    Inner loop of an N-dimensional step scan

    This is the default function for ``per_step`` param`` in ND plans.

    Parameters
    ----------
    detectors : iterable
        devices to read

    step : dict
        mapping motors to positions in this step

    pos_cache : dict
        mapping motors to their last-set positions

    take_reading : plan, optional
        function to do the actual acquisition ::

           def take_reading(dets, name='primary'):
                yield from ...

        Callable[List[OphydObj], Optional[str]] -> Generator[Msg], optional

        Defaults to `xpdacq_trigger_and_read`
    """
    yield from bps.one_nd_step(detectors, step, pos_cache, take_reading=take_reading)


def xpdacq_grid_scan(detectors: list, *args, snake_axes: typing.Union[bool, typing.Iterable[bool], None] = None,
                     per_step: typing.Callable = xpdacq_per_step,
                     md: typing.Union[dict, None] = None) -> typing.Generator:
    """
    Scan over a mesh; each motor is on an independent trajectory.

    Parameters
    ----------
    detectors: list
        list of 'readable' objects
    ``*args``
        patterned like (``motor1, start1, stop1, num1,``
                        ``motor2, start2, stop2, num2,``
                        ``motor3, start3, stop3, num3,`` ...
                        ``motorN, startN, stopN, numN``)

        The first motor is the "slowest", the outer loop. For all motors
        except the first motor, there is a "snake" argument: a boolean
        indicating whether to following snake-like, winding trajectory or a
        simple left-to-right trajectory.
    snake_axes: boolean or iterable, optional
        which axes should be snaked, either ``False`` (do not snake any axes),
        ``True`` (snake all axes) or a list of axes to snake. "Snaking" an axis
        is defined as following snake-like, winding trajectory instead of a
        simple left-to-right trajectory. The elements of the list are motors
        that are listed in `args`. The list must not contain the slowest
        (first) motor, since it can't be snaked.
    per_step: callable, optional
        hook for customizing action of inner loop (messages per step).
        See docstring of `xpdacq_per_step` (the default)
        for details.
    md: dict, optional
        metadata
    """
    yield from bp.grid_scan(detectors, *args, snake_axes=snake_axes, per_step=per_step, md=md)


def xpdacq_count(detectors: list, num: int = 1, delay: float = None, *,
                 per_shot: typing.Callable = xpdacq_trigger_and_read, md: dict = None) -> typing.Generator:
    """
    Take one or more readings from detectors.

    Parameters
    ----------
    detectors : list
        list of 'readable' objects
    num : integer, optional
        number of readings to take; default is 1

        If None, capture data until canceled
    delay : iterable or scalar, optional
        Time delay in seconds between successive readings; default is 0.
    per_shot : callable, optional
        hook for customizing action of inner loop (messages per step)
        Expected signature ::

           def f(detectors: Iterable[OphydObj]) -> Generator[Msg]:
               ...
    md : dict, optional
        metadata

    Notes
    -----
    If ``delay`` is an iterable, it must have at least ``num - 1`` entries or
    the plan will raise a ``ValueError`` during iteration.
    """
    yield from bp.count(detectors, num, delay, per_shot=per_shot, md=md)


def xpdacq_ramp_count(detectors: list, motor: typing.Any, value: typing.Any, take_pre_data=True, timeout=None,
                      period=None, md=None) -> typing.Generator:
    """
    Take data while ramping one or more motors.

    Parameters
    ----------
    detectors : list
        A list of 'readable' objects.

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

    def inner_plan():
        yield from xpdacq_trigger_and_read(detectors)

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


def xpdacq_list_grid_scan(detectors: list, *args,
                          snake_axes: typing.Union[bool, typing.Iterable[bool], None] = None,
                          per_step: typing.Callable = xpdacq_per_step,
                          md: typing.Union[dict, None] = None) -> typing.Generator:
    """
    Scan over a mesh; each motor is on an independent trajectory.

    Parameters
    ----------
    detectors: list
        list of 'readable' objects
    args: list
        patterned like (``motor1, position_list1,``
                        ``motor2, position_list2,``
                        ``motor3, position_list3,``
                        ``...,``
                        ``motorN, position_listN``)

        The first motor is the "slowest", the outer loop. ``position_list``'s
        are lists of positions, all lists must have the same length. Motors
        can be any 'settable' object (motor, temp controller, etc.).
    snake_axes: boolean or iterable, optional
        which axes should be snaked, either ``False`` (do not snake any axes),
        ``True`` (snake all axes) or a list of axes to snake. "Snaking" an axis
        is defined as following snake-like, winding trajectory instead of a
        simple left-to-right trajectory.The elements of the list are motors
        that are listed in `args`. The list must not contain the slowest
        (first) motor, since it can't be snaked.
    per_step: callable, optional
        hook for customizing action of inner loop (messages per step).
        See docstring of :func:`bluesky.plan_stubs.one_nd_step` (the default)
        for details.
    md: dict, optional
        metadata
    """
    yield from bp.list_grid_scan(detectors, *args, snake_axes=snake_axes, per_step=per_step, md=md)


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


def xpdacq_grid_scan_with_dark(detectors: list, *args,
                               snake_axes: typing.Union[bool, typing.Iterable[bool], None] = None,
                               per_step: typing.Callable = xpdacq_per_step,
                               md: typing.Union[dict, None] = None) -> typing.Generator:
    """
    Scan over a mesh; each motor is on an independent trajectory. If there is a change in the position of the
    slow motor, take a dark image.

    Parameters
    ----------
    detectors: list
        list of 'readable' objects
    ``*args``
        patterned like (``motor1, start1, stop1, num1,``
                        ``motor2, start2, stop2, num2,``
                        ``motor3, start3, stop3, num3,`` ...
                        ``motorN, startN, stopN, numN``)

        The first motor is the "slowest", the outer loop. For all motors
        except the first motor, there is a "snake" argument: a boolean
        indicating whether to following snake-like, winding trajectory or a
        simple left-to-right trajectory.
    snake_axes: boolean or iterable, optional
        which axes should be snaked, either ``False`` (do not snake any axes),
        ``True`` (snake all axes) or a list of axes to snake. "Snaking" an axis
        is defined as following snake-like, winding trajectory instead of a
        simple left-to-right trajectory. The elements of the list are motors
        that are listed in `args`. The list must not contain the slowest
        (first) motor, since it can't be snaked.
    per_step: callable, optional
        hook for customizing action of inner loop (messages per step).
        See docstring of `xpdacq_per_step` (the default)
        for details.
    md: dict, optional
        metadata
    """
    if args:
        slow_motor = args[0]
        per_step = slow_dark_wrapper(per_step, slow_motor)
    yield from bp.grid_scan(detectors, *args, snake_axes=snake_axes, per_step=per_step, md=md)


def xpdacq_list_grid_scan_with_dark(detectors: list, *args,
                                    snake_axes: typing.Union[bool, typing.Iterable[bool], None] = None,
                                    per_step: typing.Callable = xpdacq_per_step,
                                    md: typing.Union[dict, None] = None):
    """
    Scan over a mesh; each motor is on an independent trajectory. If there is a change in the position of the
    slow motor, take a dark image.

    Parameters
    ----------
    detectors: list
        list of 'readable' objects
    args: list
        patterned like (``motor1, position_list1,``
                        ``motor2, position_list2,``
                        ``motor3, position_list3,``
                        ``...,``
                        ``motorN, position_listN``)

        The first motor is the "slowest", the outer loop. ``position_list``'s
        are lists of positions, all lists must have the same length. Motors
        can be any 'settable' object (motor, temp controller, etc.).
    snake_axes: boolean or iterable, optional
        which axes should be snaked, either ``False`` (do not snake any axes),
        ``True`` (snake all axes) or a list of axes to snake. "Snaking" an axis
        is defined as following snake-like, winding trajectory instead of a
        simple left-to-right trajectory.The elements of the list are motors
        that are listed in `args`. The list must not contain the slowest
        (first) motor, since it can't be snaked.
    per_step: callable, optional
        hook for customizing action of inner loop (messages per step).
        See docstring of :func:`bluesky.plan_stubs.one_nd_step` (the default)
        for details.
    md: dict, optional
        metadata
    """
    if args:
        slow_motor = args[0]
        per_step = slow_dark_wrapper(per_step, slow_motor)
    yield from bp.list_grid_scan(detectors, *args, snake_axes=snake_axes, per_step=per_step, md=md)


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
