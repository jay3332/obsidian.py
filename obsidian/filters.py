from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, List, Optional, overload


_FILTERS = [
    'volume',
    'timescale',
    'karaoke',
    'channel_mix',
    'vibrato',
    'rotation',
    'low_pass',
    'tremolo',
    'equalizer'
]

__all__: list = [
    'FilterSink',
    'BaseFilter',
    'VolumeFilter',
    'TimescaleFilter',
    'RotationFilter',
    'Equalizer',
    'VibratoFilter',
    'TremoloFilter'
]


# noinspection PyShadowingBuiltins
class FilterSink(object):
    """
    Represents a sink of filters.
    """

    def __init__(self, player) -> None:
        from .player import Player

        self.__player: Player = player
        self.__filters: Dict[str, BaseFilter] = {}

    def __repr__(self) -> str:
        extra = ''.join(f' {key}={filter!r}' for key, filter in self.__filters.items())
        return f'<FilterSink{extra}>'

    @property
    def player(self):
        return self.__player

    @property
    def filters(self) -> Dict[str, BaseFilter]:
        return self.__filters

    @property
    def volume(self) -> Optional[VolumeFilter]:
        return self.filters.get('volume')

    @property
    def timescale(self) -> Optional[TimescaleFilter]:
        return self.filters.get('timescale')

    @property
    def rotation(self) -> Optional[RotationFilter]:
        return self.filters.get('rotation')

    @property
    def equalizer(self) -> Optional[Equalizer]:
        return self.filters.get('equalizer')

    eq = equalizer

    @property
    def vibrato(self) -> Optional[VibratoFilter]:
        return self.filters.get('vibrato')

    @property
    def tremolo(self) -> Optional[TremoloFilter]:
        return self.filters.get('tremolo')

    def add(self, filter: BaseFilter) -> FilterSink:
        if not isinstance(filter, BaseFilter):
            raise TypeError('filter must inherit from BaseFilter.')

        self.__filters[filter.identifier] = filter
        return self

    @overload
    def remove(self, identifier: str) -> None:
        ...

    @overload
    def remove(self, identifier: type) -> None:
        ...

    @overload
    def remove(self, identifier: BaseFilter) -> None:
        ...

    def remove(self, identifier: Any) -> None:
        if isinstance(identifier, str):
            try:
                del self.__filters[identifier]
            except KeyError:
                return
            return

        if isinstance(identifier, type):
            for k, filter in self.__filters.items():
                if filter.__class__ is identifier:
                    del self.__filters[k]
            return

        if isinstance(identifier, BaseFilter):
            for k, filter in self.__filters.items():
                if filter is identifier:
                    del self.__filters[k]
            return

    def reset(self) -> None:
        self.__filters = {}

    def to_json(self, guild_id: Optional[int] = None) -> Dict[str, Any]:
        payload = {}

        for key in _FILTERS:
            try:
                filter = self.__filters[key]
            except KeyError:
                continue
            else:
                payload[key] = filter.to_raw()

        return {'guild_id': str(guild_id), 'filters': payload}

    set = add


class BaseFilter(object):
    @property
    def identifier(self) -> str:
        raise NotImplementedError

    @classmethod
    def from_raw(cls, data: Any) -> BaseFilter:
        return cls()  # Optional method

    def to_raw(self) -> Any:
        raise NotImplementedError

    def __repr__(self) -> str:
        return '<BaseFilter>'


class VolumeFilter(BaseFilter):
    def __init__(self, volume: float = 1.0) -> None:
        self.__volume: float = 1.0
        self.volume = volume  # Let the setter handle it

    @property
    def volume(self) -> float:
        return self.__volume

    @volume.setter
    def volume(self, new: float) -> None:
        if new > 5.0:
            raise ValueError('volume must be under 500%')

        if new < 0.0:
            raise ValueError('volume must be positive')

        self.__volume = new

    @property
    def percent(self) -> int:
        return int(self.volume * 100)

    @percent.setter
    def percent(self, new: float) -> None:
        self.volume = new / 100

    @property
    def identifier(self) -> str:
        return 'volume'

    @classmethod
    def from_raw(cls, data: float) -> BaseFilter:
        return cls(data)

    def to_raw(self) -> float:
        return self.volume

    def __repr__(self) -> str:
        return f'<VolumeFilter volume={self.volume}>'


class TimescaleFilter(BaseFilter):
    @staticmethod
    def __count_not_none(*entities):
        return sum(entity is not None for entity in entities)

    def __init__(
            self,
            *,
            pitch: Optional[float] = None,
            pitch_octaves: Optional[float] = None,
            pitch_semitones: Optional[float] = None,
            rate: Optional[float] = None,
            rate_change: Optional[float] = None,
            speed: Optional[float] = None,
            speed_change: Optional[float] = None
    ):
        if self.__count_not_none(pitch, pitch_octaves, pitch_semitones) > 1:
            raise ValueError('Only one of pitch, pitch_octaves, and pitch_semitones can be used.')

        if self.__count_not_none(rate, rate_change) > 1:
            raise ValueError('Only one of rate and rate_change can be used.')

        if self.__count_not_none(speed, speed_change) > 1:
            raise ValueError('Only one of speed and speed_change can be used.')

        self.__pitch: Optional[float] = pitch
        self.__pitch_octaves: Optional[float] = pitch_octaves
        self.__pitch_semitones: Optional[float] = pitch_semitones
        self.__rate: Optional[float] = rate
        self.__rate_change: Optional[float] = rate_change
        self.__speed: Optional[float] = speed
        self.__speed_change: Optional[float] = speed_change

    @property
    def pitch(self) -> Optional[float]:
        return self.__pitch

    @pitch.setter
    def pitch(self, new: Optional[float]) -> None:
        self.__pitch_octaves = None
        self.__pitch_semitones = None
        self.__pitch = new

    @property
    def pitch_octaves(self) -> Optional[float]:
        return self.__pitch_octaves

    @pitch_octaves.setter
    def pitch_octaves(self, new: Optional[float]) -> None:
        self.__pitch_octaves = new
        self.__pitch_semitones = None
        self.__pitch = None

    @property
    def pitch_semitones(self) -> Optional[float]:
        return self.__pitch_semitones

    @pitch_semitones.setter
    def pitch_semitones(self, new: Optional[float]) -> None:
        self.__pitch_octaves = None
        self.__pitch_semitones = new
        self.__pitch = None

    @property
    def rate(self) -> Optional[float]:
        return self.__rate

    @rate.setter
    def rate(self, new: Optional[float]) -> None:
        self.__rate_change = None
        self.__rate = new

    @property
    def rate_change(self) -> Optional[float]:
        return self.__rate_change

    @rate_change.setter
    def rate_change(self, new: Optional[float]) -> None:
        self.__rate_change = new
        self.__rate = None

    @property
    def speed(self) -> Optional[float]:
        return self.__speed

    @speed.setter
    def speed(self, new: Optional[float]) -> None:
        self.__speed_change = None
        self.__speed = new

    @property
    def speed_change(self) -> Optional[float]:
        return self.__speed_change

    @speed_change.setter
    def speed_change(self, new: Optional[float]) -> None:
        self.__speed_change = new
        self.__speed = None

    @property
    def identifier(self) -> str:
        return 'timescale'

    @classmethod
    def from_raw(cls, data: Dict[str, float]) -> TimescaleFilter:
        data['pitch_semitones'] = data.get('pitch_semi_tones')
        return cls(**data)

    def to_raw(self) -> Dict[str, float]:
        final = {}

        for key in [
            'pitch',
            'pitch_octaves',
            'rate',
            'rate_change',
            'speed',
            'speed_change'
        ]:
            value = getattr(self, key, None)
            if value is not None:
                final[key] = value

        if self.pitch_semitones is not None:
            final['pitch_semi_tones'] = self.pitch_semitones

        return final

    def __repr__(self) -> str:
        entities = ''

        for key in [
            'pitch',
            'pitch_octaves',
            'pitch_semitones',
            'rate',
            'rate_change',
            'speed',
            'speed_change'
        ]:
            value = getattr(self, key, None)
            if value is not None:
                entities += f' {key}={value!r}'

        return f'<TimescaleFilter{entities}>'


class RotationFilter(BaseFilter):
    def __init__(self, hz: float = 5.0) -> None:
        self.__hz: float = None
        self.hz = hz  # Let the setter handle it

    def __repr__(self) -> str:
        return f'<RotationFilter hz={self.__hz:.2f}>'

    @property
    def identifier(self) -> str:
        return 'rotation'

    @property
    def hz(self) -> float:
        return self.__hz

    @hz.setter
    def hz(self, new: float) -> None:
        if new <= 0:
            raise ValueError('hz must be positive.')

        self.__hz = new

    @classmethod
    def from_raw(cls, data: float) -> RotationFilter:
        return cls(data)

    def to_raw(self) -> float:
        return self.__hz


class Equalizer(BaseFilter):
    def __init__(self, *gains: float, name: str = 'custom'):
        if any(gain < -.25 or gain > 1 for gain in gains):
            raise ValueError('All equalizer gains must be between -0.25 and +1.')

        _extend = []
        if len(gains) < 15:
            _extend = [0] * (15 - len(gains))

        if len(gains) > 15:
            gains = gains[:15]

        self.__gains: List[float] = list(gains) + _extend
        self.__name: str = name

    def __repr__(self) -> str:
        return f'<Equalizer name={self.name!r}>'

    def __str__(self) -> str:
        return self.name

    @property
    def gains(self) -> List[float]:
        return self.__gains

    @property
    def name(self) -> str:
        return self.__name

    def set(self, index: int, gain: float) -> None:
        try:
            self.__gains[index] = gain
        except IndexError:
            raise IndexError(f'Invalid index "{index}".')

    @overload
    def reset(self, index: int) -> None:
        ...

    @overload
    def reset(self) -> None:
        ...

    def reset(self, index: Any = None) -> None:
        if index is None:
            self.__gains = [0] * 15
            return

        try:
            self.__gains[index] = 0
        except IndexError:
            raise IndexError(f'Invalid index "{index}".')

    @staticmethod
    def ___factory(func) -> callable:
        @wraps(func)
        def inner(cls, *args, **kwargs):
            gains = func(cls, *args, **kwargs)
            return cls(*gains, name=func.__name__)

        inner.__eq_factory__ = True
        return inner

    __factory = ___factory.__func__

    @classmethod
    @__factory
    def flat(cls) -> Equalizer:
        return ()

    @classmethod
    @__factory
    def boost(cls) -> Equalizer:
        return -.075, .125, .125, .1, .1, .05, .075, 0, 0, 0, 0, 0, .125, .15, .05

    @classmethod
    @__factory
    def metal(cls) -> Equalizer:
        return 0, .1, .1, .15, .13, .1, 0, .125, .175, .175, .125, .125, .1, .075, 0

    @classmethod
    @__factory
    def piano(cls) -> Equalizer:
        return -.25, -.25, -.125, 0, .25, .25, 0, -.25, -.25, 0, 0, .5, .25, -.025

    @classmethod
    @__factory
    def jazz(cls) -> Equalizer:
        return -.13, -.11, .1, -.1, .14, .2, -.18, 0, .24, .22, .2, 0, 0, 0, 0

    @classmethod
    @__factory
    def pop(cls) -> Equalizer:
        return -.02, -.01, .08, .1, .15, .1, .03, -.02, -.035, -.05, -.05, -.05, -.05, -.05, -.05

    @classmethod
    def all_factory(cls) -> Dict[str, Callable[..., Equalizer]]:
        result = {}
        for key in dir(cls):
            func = getattr(cls, key)
            try:
                func = func.__func__
            except AttributeError:
                continue
            else:
                if not hasattr(func, '__eq_factory__'):
                    continue

                result[key] = func

        return result

    @property
    def identifier(self) -> str:
        return 'equalizer'

    @classmethod
    def from_raw(cls, data: List[float]) -> None:
        return cls(*data)

    def to_raw(self) -> List[float]:
        return self.__gains


class VibratoFilter(BaseFilter):
    def __init__(self, frequency: float = 2.0, depth: float = 0.5) -> None:
        self.__frequency: float = None
        self.__depth: float = None

        # Let setters handle checks
        self.frequency = frequency
        self.depth = depth

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} frequency={self.frequency:.2f} depth={self.depth:.2f}>'

    @property
    def frequency(self) -> float:
        return self.__frequency

    @frequency.setter
    def frequency(self, new: float) -> None:
        if not 0 < new <= 14:
            raise ValueError('frequency must be positive and under 14.')

        self.__frequency = new

    @property
    def depth(self) -> float:
        return self.__depth

    @depth.setter
    def depth(self, new: float) -> None:
        if not 0 < new <= 1:
            raise ValueError('depth must be between 0 and 1 (but not 0).')

        self.__depth = new

    @property
    def identifier(self) -> str:
        return 'vibrato'

    @classmethod
    def from_raw(cls, data: Dict[str, float]) -> VibratoFilter:
        return cls(data.get('frequency', 2), data.get('depth', .5))

    def to_raw(self) -> Dict[str, float]:
        return {'frequency': self.frequency, 'depth': self.depth}


class TremoloFilter(VibratoFilter):
    def __init__(self, frequency: float = 2.0, depth: float = 0.5) -> None:
        super().__init__(frequency, depth)

    @property
    def frequency(self) -> float:
        return self.__frequency

    @frequency.setter
    def frequency(self, new: float) -> None:
        if new <= 0:
            raise ValueError('frequency must be positive.')

        self.__frequency = new

    @property
    def identifier(self) -> str:
        return 'tremolo'
