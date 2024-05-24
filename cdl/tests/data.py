# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Test data functions

Functions creating test data: curves, images, ...
"""

# pylint: disable=invalid-name  # Allows short reference names like x, y, ...
# guitest: skip

from __future__ import annotations

import guidata.dataset as gds
import numpy as np

import cdl.obj
from cdl.config import _
from cdl.env import execenv
from cdl.utils.tests import get_test_fnames


def get_test_signal(filename: str) -> cdl.obj.SignalObj:
    """Return test signal

    Args:
        filename: Filename

    Returns:
        Signal object
    """
    return cdl.obj.read_signal(get_test_fnames(filename)[0])


def get_test_image(filename: str) -> cdl.obj.ImageObj:
    """Return test image

    Args:
        filename: Filename

    Returns:
        Image object
    """
    return cdl.obj.read_image(get_test_fnames(filename)[0])


def __array_to_str(data: np.ndarray) -> str:
    """Return a compact description of the array properties"""
    dims = "×".join(str(dim) for dim in data.shape)
    return f"{dims},{data.dtype},{data.min():.2g}→{data.max():.2g},µ={data.mean():.2g}"


def check_array_result(
    title: str,
    res: np.ndarray,
    exp: np.ndarray,
    rtol: float = 1.0e-5,
    atol: float = 1.0e-8,
) -> None:
    """Assert that two arrays are almost equal."""
    restxt = f"{title}: {__array_to_str(res)} (expected: {__array_to_str(exp)})"
    execenv.print(restxt)
    assert np.allclose(res, exp, rtol=rtol, atol=atol), restxt


def check_scalar_result(
    title: str, res: float, exp: float, rtol: float = 1.0e-5, atol: float = 1.0e-8
) -> None:
    """Assert that two scalars are almost equal."""
    restxt = f"{title}: {res} (expected: {exp})"
    execenv.print(restxt)
    assert np.isclose(res, exp, rtol=rtol, atol=atol), restxt


def create_paracetamol_signal(
    size: int | None = None, title: str | None = None
) -> cdl.obj.SignalObj:
    """Create test signal (Paracetamol molecule spectrum)

    Args:
        size: Size of the data. Defaults to None.
        title: Title of the signal. Defaults to None.

    Returns:
        Signal object
    """
    obj = cdl.obj.read_signal(get_test_fnames("paracetamol.txt")[0])
    if title is not None:
        obj.title = title
    if size is not None:
        x0, y0 = obj.xydata
        x1 = np.linspace(x0[0], x0[-1], size)
        y1 = np.interp(x1, x0, y0)
        obj.set_xydata(x1, y1)
    return obj


class GaussianNoiseParam(gds.DataSet):
    """Gaussian noise parameters"""

    mu = gds.FloatItem(
        _("Mean"),
        default=0.0,
        min=-100.0,
        max=100.0,
        help=_("Mean of the Gaussian distribution"),
    )
    sigma = gds.FloatItem(
        _("Standard deviation"),
        default=0.1,
        min=0.0,
        max=100.0,
        help=_("Standard deviation of the Gaussian distribution"),
    )
    seed = gds.IntItem(
        _("Seed"),
        default=1,
        min=0,
        max=1000000,
        help=_("Seed for random number generator"),
    )


def add_gaussian_noise_to_signal(
    signal: cdl.obj.SignalObj, p: GaussianNoiseParam | None = None
) -> None:
    """Add Gaussian (Normal-law) random noise to data

    Args:
        signal: Signal object
        p: Gaussian noise parameters.
    """
    if p is None:
        p = GaussianNoiseParam()
    rng = np.random.default_rng(p.seed)
    signal.data += rng.normal(p.mu, p.sigma, size=signal.data.shape)
    signal.title = f"GaussNoise({signal.title}, µ={p.mu}, σ={p.sigma})"


def create_noisy_signal(
    noiseparam: GaussianNoiseParam | None = None,
    newparam: cdl.obj.NewSignalParam | None = None,
    addparam: cdl.obj.GaussLorentzVoigtParam | None = None,
    title: str | None = None,
    noised: bool | None = None,
) -> cdl.obj.SignalObj:
    """Create curve data, optionally noised

    Args:
        noiseparam: Noise parameters. Default: None: No noise
        newparam: New signal parameters.
         Default: Gaussian, size=500, xmin=-10, xmax=10
        addparam: Additional parameters.
         Default: a=1.0, sigma=1.0, mu=0.0, ymin=0.0
        title: Title of the signal. Default: None
         If not None, overrides the title in newparam
        noised: If True, add noise to the signal.
         Default: None (use noiseparam)
         If True, eventually creates a new noiseparam if None

    Returns:
        cdl.obj.Signal object
    """
    if newparam is None:
        newparam = cdl.obj.NewSignalParam()
        newparam.stype = cdl.obj.SignalTypes.GAUSS
    if title is not None:
        newparam.title = title
    newparam.title = "Test signal (noisy)" if newparam.title is None else newparam.title
    if addparam is None:
        addparam = cdl.obj.GaussLorentzVoigtParam()
    if noised is not None and noiseparam is None:
        noiseparam = GaussianNoiseParam()
        noiseparam.sigma = 5.0
    sig = cdl.obj.create_signal_from_param(newparam, addparam)
    if noiseparam is not None:
        add_gaussian_noise_to_signal(sig, noiseparam)
    return sig


def create_periodic_signal(
    shape: cdl.obj.SignalTypes, freq: float = 50.0, size: int = 10000
) -> cdl.obj.SignalObj:
    """Create a periodic signal

    Args:
        shape: Shape of the signal
        freq: Frequency of the signal. Defaults to 50.0.
        size: Size of the signal. Defaults to 10000.

    Returns:
        Signal object
    """
    newparam = cdl.obj.new_signal_param(stype=shape, size=size)
    addparam = cdl.obj.PeriodicParam.create(freq=freq)
    return cdl.obj.create_signal_from_param(newparam, addparam)


def create_2d_steps_data(size: int, width: int, dtype: np.dtype) -> np.ndarray:
    """Creating 2D steps data for testing purpose

    Args:
        size: Size of the data
        width: Width of the steps
        dtype: Data type

    Returns:
        2D data
    """
    data = np.zeros((size, size), dtype=dtype)
    value = 1
    for col in range(0, size - width + 1, width):
        data[:, col : col + width] = np.array(value).astype(dtype)
        value *= 10
    data2 = np.zeros_like(data)
    value = 1
    for row in range(0, size - width + 1, width):
        data2[row : row + width, :] = np.array(value).astype(dtype)
        value *= 10
    data += data2
    return data


def create_2d_random(
    size: int, dtype: np.dtype, level: float = 0.1, seed: int = 1
) -> np.ndarray:
    """Creating 2D Uniform-law random image

    Args:
        size: Size of the data
        dtype: Data type
        level: Level of the random noise. Defaults to 0.1.
        seed: Seed for random number generator. Defaults to 1.

    Returns:
        2D data
    """
    rng = np.random.default_rng(seed)
    amp = np.iinfo(dtype).max * level
    return np.array(rng.random((size, size)) * amp, dtype=dtype)


def create_2d_gaussian(
    size: int,
    dtype: np.dtype,
    x0: float = 0,
    y0: float = 0,
    mu: float = 0.0,
    sigma: float = 2.0,
    amp: float | None = None,
) -> np.ndarray:
    """Creating 2D Gaussian (-10 <= x <= 10 and -10 <= y <= 10)

    Args:
        size: Size of the data
        dtype: Data type
        x0: x0. Defaults to 0.
        y0: y0. Defaults to 0.
        mu: mu. Defaults to 0.0.
        sigma: sigma. Defaults to 2.0.
        amp: Amplitude. Defaults to None.

    Returns:
        2D data
    """
    xydata = np.linspace(-10, 10, size)
    x, y = np.meshgrid(xydata, xydata)
    if amp is None:
        try:
            amp = np.iinfo(dtype).max * 0.5
        except ValueError:
            # dtype is not integer
            amp = 1.0
    return np.array(
        amp
        * np.exp(
            -((np.sqrt((x - x0) ** 2 + (y - y0) ** 2) - mu) ** 2) / (2.0 * sigma**2)
        ),
        dtype=dtype,
    )


def get_laser_spot_data() -> list[np.ndarray]:
    """Return a list of NumPy arrays containing images which are relevant for
    testing laser spot image processing features

    Returns:
        List of NumPy arrays
    """
    znoise = create_2d_random(2000, np.uint16)
    zgauss = create_2d_gaussian(2000, np.uint16, x0=2.0, y0=-3.0)
    return [zgauss + znoise] + [
        cdl.obj.read_image(fname).data for fname in get_test_fnames("*.scor-data")
    ]


class PeakDataParam(gds.DataSet):
    """Peak data test image parameters"""

    size = gds.IntItem(_("Size"), default=2000, min=1)
    n_points = gds.IntItem(_("Number"), default=4, min=1, help=_("Number of points"))
    sigma_gauss2d = gds.FloatItem(
        "σ<sub>Gauss2D</sub>", default=0.06, help=_("Sigma of the 2D Gaussian")
    )
    amp_gauss2d = gds.IntItem(
        "A<sub>Gauss2D</sub>", default=1900, help=_("Amplitude of the 2D Gaussian")
    )
    mu_noise = gds.IntItem(
        "μ<sub>noise</sub>", default=845, help=_("Mean of the Gaussian distribution")
    )
    sigma_noise = gds.IntItem(
        "σ<sub>noise</sub>",
        default=25,
        help=_("Standard deviation of the Gaussian distribution"),
    )
    dx0 = gds.FloatItem("dx0", default=0.0)
    dy0 = gds.FloatItem("dy0", default=0.0)
    att = gds.FloatItem(_("Attenuation"), default=1.0)


def get_peak2d_data(
    p: PeakDataParam | None = None, seed: int | None = None, multi: bool = False
) -> np.ndarray:
    """Return a list of NumPy arrays containing images which are relevant for
    testing 2D peak detection or similar image processing features

    Args:
        p: Peak data test image parameters. Defaults to None.
        seed: Seed for random number generator. Defaults to None.
        multi: If True, multiple peaks are generated.
         Defaults to False.

    Returns:
        2D data
    """
    if p is None:
        p = PeakDataParam()
    delta = 0.1
    rng = np.random.default_rng(seed)
    coords = (rng.random((p.n_points, 2)) - 0.5) * 10 * (1 - delta)
    data = rng.normal(p.mu_noise, p.sigma_noise, size=(p.size, p.size))
    multi_nb = 2 if multi else 1
    for x0, y0 in coords:
        for idx in range(multi_nb):
            if idx != 0:
                p.dx0 = 0.08 + rng.random() * 0.08
                p.dy0 = 0.08 + rng.random() * 0.08
                p.att = 0.2 + rng.random() * 0.8
            data += create_2d_gaussian(
                p.size,
                np.uint16,
                x0=x0 + p.dx0,
                y0=y0 + p.dy0,
                sigma=p.sigma_gauss2d,
                amp=p.amp_gauss2d / multi_nb * p.att,
            )
    return data


def __set_default_size_dtype(
    p: cdl.obj.NewImageParam | None = None,
) -> cdl.obj.NewImageParam:
    """Set default shape and dtype

    Args:
        p: Image parameters. Defaults to None. If None, a new object is created.

    Returns:
        Image parameters
    """
    if p is None:
        p = cdl.obj.NewImageParam()
    p.height = 2000 if p.height is None else p.height
    p.width = 2000 if p.width is None else p.width
    p.dtype = cdl.obj.ImageDatatypes.UINT16 if p.dtype is None else p.dtype
    return p


def add_gaussian_noise_to_image(
    image: cdl.obj.ImageObj, param: cdl.obj.NormalRandomParam
) -> None:
    """Add Gaussian noise to image

    Args:
        src: Source image
        param: Parameters for the normal distribution
    """
    newparam = cdl.obj.new_image_param(
        height=image.data.shape[0],
        width=image.data.shape[1],
        dtype=cdl.obj.ImageDatatypes.from_dtype(image.data.dtype),
        itype=cdl.obj.ImageTypes.NORMALRANDOM,
    )
    noise = cdl.obj.create_image_from_param(newparam, param)
    image.data = image.data + noise.data


def create_2dstep_image(
    p: cdl.obj.NewImageParam | None = None,
) -> cdl.obj.ImageObj:
    """Creating 2D step image

    Args:
        p: Image parameters. Defaults to None.

    Returns:
        Image object
    """
    p = __set_default_size_dtype(p)
    p.title = "Test image (2D step)" if p.title is None else p.title
    obj = cdl.obj.create_image_from_param(p)
    obj.data = create_2d_steps_data(p.height, p.height // 10, p.dtype.value)
    return obj


class RingParam(gds.DataSet):
    """Parameters for creating a ring image"""

    size = gds.IntItem(_("Size"), default=1000)
    ring_x0 = gds.IntItem(_("X<sub>center</sub>"), default=500)
    ring_y0 = gds.IntItem(_("Y<sub>center</sub>"), default=500)
    ring_width = gds.IntItem(_("Width"), default=10)
    ring_radius = gds.IntItem(_("Radius"), default=250)
    ring_intensity = gds.IntItem(_("Intensity"), default=1000)


def create_ring_data(
    size: int, x0: int, y0: int, width: int, radius: int, intensity: int
) -> np.ndarray:
    """Create 2D ring data

    Args:
        size: Size of the image
        x0: Center x coordinate
        y0: Center y coordinate
        width: Width of the ring
        radius: Radius of the ring
        intensity: Intensity of the ring

    Returns:
        2D data
    """
    data = np.zeros((size, size), dtype=np.uint16)
    for x in range(data.shape[0]):
        for y in range(data.shape[1]):
            if (x - x0) ** 2 + (y - y0) ** 2 >= (radius - width) ** 2 and (
                x - x0
            ) ** 2 + (y - y0) ** 2 <= (radius + width) ** 2:
                data[x, y] = intensity
    return data


def create_ring_image(p: RingParam | None = None) -> cdl.obj.ImageObj:
    """Creating 2D ring image

    Args:
        p: Ring image parameters. Defaults to None.

    Returns:
        Image object
    """
    if p is None:
        p = RingParam()
    obj = cdl.obj.create_image(
        f"Ring(size={p.size},x0={p.ring_x0},y0={p.ring_y0},width={p.ring_width},"
        f"radius={p.ring_radius},intensity={p.ring_intensity})"
    )
    obj.data = create_ring_data(
        p.size,
        p.ring_x0,
        p.ring_y0,
        p.ring_width,
        p.ring_radius,
        p.ring_intensity,
    )
    return obj


def create_peak2d_image(
    p: cdl.obj.NewImageParam | None = None,
) -> cdl.obj.ImageObj:
    """Creating 2D peak image

    Args:
        p: Image parameters. Defaults to None.

    Returns:
        Image object
    """
    p = __set_default_size_dtype(p)
    p.title = "Test image (2D peaks)" if p.title is None else p.title
    obj = cdl.obj.create_image_from_param(p)
    param = PeakDataParam()
    if p.height is not None and p.width is not None:
        param.size = max(p.height, p.width)
    obj.data = get_peak2d_data(param)
    return obj


def create_sincos_image(
    p: cdl.obj.NewImageParam | None = None,
) -> cdl.obj.ImageObj:
    """Creating test image (sin(x)+cos(y))

    Args:
        p: Image parameters. Defaults to None.

    Returns:
        Image object
    """
    p = __set_default_size_dtype(p)
    p.title = "Test image (sin(x)+cos(y))" if p.title is None else p.title
    dtype = p.dtype.value
    x, y = np.meshgrid(np.linspace(0, 10, p.width), np.linspace(0, 10, p.height))
    raw_data = 0.5 * (np.sin(x) + np.cos(y)) + 0.5
    dmin = np.iinfo(dtype).min * 0.95
    dmax = np.iinfo(dtype).max * 0.95
    obj = cdl.obj.create_image_from_param(p)
    obj.data = np.array(raw_data * (dmax - dmin) + dmin, dtype=dtype)
    return obj


def create_noisygauss_image(
    p: cdl.obj.NewImageParam | None = None,
    center: tuple[float, float] | None = None,
    level: float = 0.1,
    add_annotations: bool = False,
) -> cdl.obj.ImageObj:
    """Create test image (2D noisy gaussian)

    Args:
        p: Image parameters. Defaults to None.
        center: Center of the gaussian. Defaults to None.
        level: Level of the random noise. Defaults to 0.1.
        add_annotations: If True, add annotations. Defaults to False.

    Returns:
        Image object
    """
    p = __set_default_size_dtype(p)
    p.title = "Test image (noisy 2D Gaussian)" if p.title is None else p.title
    dtype = p.dtype.value
    size = p.width
    obj = cdl.obj.create_image_from_param(p)
    if center is None:
        # Default center
        x0, y0 = 2.0, 3.0
    else:
        x0, y0 = center
    obj.data = create_2d_gaussian(size, dtype=dtype, x0=x0, y0=y0)
    if level:
        obj.data += create_2d_random(size, dtype, level)
    if add_annotations:
        obj.add_annotations_from_file(get_test_fnames("annotations.json")[0])
    return obj


def create_multigauss_image(
    p: cdl.obj.NewImageParam | None = None,
) -> cdl.obj.ImageObj:
    """Create test image (multiple 2D-gaussian peaks)

    Args:
        p: Image parameters. Defaults to None.

    Returns:
        Image object
    """
    p = __set_default_size_dtype(p)
    p.title = "Test image (multi-2D-gaussian)" if p.title is None else p.title
    dtype = p.dtype.value
    size = p.width
    obj = cdl.obj.create_image_from_param(p)
    obj.data = (
        create_2d_gaussian(size, dtype, x0=0.5, y0=3.0)
        + create_2d_gaussian(size, dtype, x0=-1.0, y0=-1.0, sigma=1.0)
        + create_2d_gaussian(size, dtype, x0=7.0, y0=8.0)
    )
    return obj


def create_annotated_image(title: str | None = None) -> cdl.obj.ImageObj:
    """Create test image with annotations

    Returns:
        Image object
    """
    data = create_2d_gaussian(600, np.uint16, x0=2.0, y0=3.0)
    title = "Test image (with metadata)" if title is None else title
    image = cdl.obj.create_image(title, data)
    image.add_annotations_from_file(get_test_fnames("annotations.json")[0])
    return image


def create_resultshapes() -> tuple[cdl.obj.ResultShape, ...]:
    """Create test result shapes (core.model.base.ResultShape test objects)

    Returns:
        Tuple of ResultShape objects
    """
    RShape, SType = cdl.obj.ResultShape, cdl.obj.ShapeTypes
    return (
        RShape(
            "circle",
            [[0, 250, 250, 200], [0, 250, 250, 140]],
            SType.CIRCLE,
        ),
        RShape("rectangle", [0, 300, 200, 700, 700], SType.RECTANGLE),
        RShape("segment", [0, 50, 250, 400, 400], SType.SEGMENT),
        RShape("point", [[0, 500, 500], [0, 15, 400]], SType.POINT),
        RShape(
            "polygon",
            [0, 100, 100, 150, 100, 150, 150, 200, 100, 250, 50],
            SType.POLYGON,
        ),
    )
