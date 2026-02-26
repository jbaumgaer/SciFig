import numpy as np
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Union

    
def cm2inch(*size: Union[float, tuple[float, ...]]) -> tuple[float, ...]:
    inch = 2.54
    if isinstance(size[0], tuple):
        return tuple(i / inch for i in size[0])
    return tuple(i / inch for i in size)


class NoiseLevel(Enum):
    NONE = 0
    LOW = 0.01
    MEDIUM = 0.05
    HIGH = 0.2


def add_noise(y: np.ndarray, noise_level: NoiseLevel):
    y_diff = np.abs(np.diff([y.min(), y.max()]))
    return np.random.normal(0, noise_level.value * y_diff, len(y))


class Distribution(ABC):

    @abstractmethod
    def get_peak(self, x):
        pass


@dataclass
class Gaussian(Distribution):
    scale: float
    center: float
    width: float

    def get_peak(self, x):
        return self.scale * np.exp(-((x - self.center)**2) / (2 * self.width**2))


@dataclass
class DataSet(ABC):
    x: np.ndarray
    y: np.ndarray = field(init=False)

    @abstractmethod
    def get_data(self) -> tuple[np.ndarray, np.ndarray]:
        pass


@dataclass
class IRDataSet(DataSet):
    x: np.ndarray
    peak_set: list[Gaussian]
    baseline: float
    noise_level: Optional[NoiseLevel] = NoiseLevel.LOW
    slope: Optional[float] = None
    y: np.ndarray = field(init=False)

    def __post_init__(self):
        self.y = np.full_like(self.x, self.baseline)
        if self.slope is not None:
            self.y += self.slope * (self.x - self.x.min())
        for peak in self.peak_set:
            self.y += peak.get_peak(self.x)
        if self.noise_level and self.noise_level != NoiseLevel.NONE:
            self.y += add_noise(self.y, self.noise_level)

    def get_data(self) -> tuple[np.ndarray, np.ndarray]:
        return self.x, self.y


class CharacterizationMethod(Enum):
    IR = "IR"
    

ir_data_set_1 = IRDataSet(
    x=np.linspace(3500, 2800, 500),
    peak_set=[
        Gaussian(-20, 3350, 60),
        Gaussian(-45, 2970, 5),
        Gaussian(-15, 2930, 10),
        Gaussian(-10, 2880, 10)
    ],
    baseline=100,
    noise_level=NoiseLevel.LOW
)

ir_data_set_2 = IRDataSet(
    x=np.linspace(3500, 2800, 500),
    peak_set=[
        Gaussian(-25, 3320, 60),
        Gaussian(-40, 2970, 5),
        Gaussian(-12, 2930, 8),
        Gaussian(-8, 2880, 8)
    ],
    baseline=100,
    slope=-0.02,
    noise_level=NoiseLevel.LOW
)

ir_data_set_3 = IRDataSet(
    x=np.linspace(3500, 2800, 500),
    peak_set=[
        Gaussian(-35, 3380, 50),
        Gaussian(-5, 3050, 20),
        Gaussian(-5, 2950, 40)
    ],
    baseline=100,
    noise_level=NoiseLevel.LOW
)

ir_data_set_4 = IRDataSet(
    x=np.linspace(3500, 2800, 500),
    peak_set=[
        Gaussian(-30, 3400, 60),
        Gaussian(-15, 3150, 80),
        Gaussian(-10, 2850, 40)
    ],
    baseline=100,
    slope=-0.03,
    noise_level=NoiseLevel.LOW
)


data_sets = {
    CharacterizationMethod.IR: [ir_data_set_1, ir_data_set_2, ir_data_set_3, ir_data_set_4],
}