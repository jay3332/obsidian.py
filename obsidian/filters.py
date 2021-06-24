from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, List, Optional, overload


_FILTERS: tuple = (
    'volume',
    'timescale',
    'karaoke',
    'channel_mix',
    'vibrato',
    'rotation',
    'low_pass',
    'tremolo',
    'equalizer',
    'distortion'
)

__all__: tuple = (
    'FilterSink',
    'BaseFilter',
    'VolumeFilter',
    'TimescaleFilter',
    'RotationFilter',
    'Equalizer',
    'VibratoFilter',
    'TremoloFilter',
    'KaraokeFilter',
    'ChannelMixFilter',
    'LowPassFilter',
    'DistortionFilter'
)


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

    @property
    def distortion(self) -> Optional[DistortionFilter]:
        return self.filters.get('distortion')

    @property
    def karaoke(self) -> Optional[KaraokeFilter]:
        return self.filters.get('karaoke')

    @property
    def channel_mix(self) -> Optional[ChannelMixFilter]:
        return self.filters.get('channel_mix')

    @property
    def low_pass(self) -> Optional[LowPassFilter]:
        return self.filters.get('low_pass')

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


class DistortionFilter(BaseFilter):
    def __init__(
            self,
            *,
            sin_offset: int = 0,
            sin_scale: int = 1,
            cos_offset: int = 0,
            cos_scale: int = 1,
            tan_offset: int = 0,
            tan_scale: int = 1,
            offset: int = 0,
            scale: int = 1
    ):
        self.__sin_offset: int = sin_offset
        self.__sin_scale: int = sin_scale
        self.__cos_offset: int = cos_offset
        self.__cos_scale: int = cos_scale
        self.__tan_offset: int = tan_offset
        self.__tan_scale: int = tan_scale
        self.__offset: int = offset
        self.__scale: int = scale

    def __repr__(self) -> str:
        return '<DistortionFilter>'

    @property
    def scale(self) -> int:
        return self.__scale

    @scale.setter
    def scale(self, new: int) -> None:
        self.__scale = new

    @property
    def offset(self) -> int:
        return self.__offset

    @offset.setter
    def offset(self, new: int) -> None:
        self.__offset = new

    @property
    def sin_scale(self) -> int:
        return self.__sin_scale

    @sin_scale.setter
    def sin_scale(self, new: int) -> None:
        self.__sin_scale = new

    @property
    def sin_offset(self) -> int:
        return self.__sin_offset

    @sin_offset.setter
    def sin_offset(self, new: int) -> None:
        self.__sin_offset = new

    @property
    def cos_scale(self) -> int:
        return self.__cos_scale

    @cos_scale.setter
    def cos_scale(self, new: int) -> None:
        self.__cos_scale = new

    @property
    def cos_offset(self) -> int:
        return self.__cos_offset

    @cos_offset.setter
    def cos_offset(self, new: int) -> None:
        self.__cos_offset = new

    @property
    def tan_scale(self) -> int:
        return self.__tan_scale

    @tan_scale.setter
    def tan_scale(self, new: int) -> None:
        self.__tan_scale = new

    @property
    def tan_offset(self) -> int:
        return self.__tan_offset

    @tan_offset.setter
    def tan_offset(self, new: int) -> None:
        self.__tan_offset = new

    @property
    def identifier(self) -> str:
        return 'distortion'

    @classmethod
    def from_raw(cls, data: Dict[str, int]) -> DistortionFilter:
        data = {
            ''.join('_' + c.lower() if c.isupper() else c for c in k).lstrip('_'): v
            for k, v in data.items()
        }
        return cls(**data)

    def to_raw(self) -> Dict[str, int]:
        return {
            'sinOffset': self.sin_offset,
            'sinScale': self.sin_scale,
            'cosOffset': self.cos_offset,
            'cosScale': self.cos_scale,
            'tanOffset': self.tan_offset,
            'tanScale': self.tan_scale,
            'offset': self.offset,
            'scale': self.scale
        }


class KaraokeFilter(BaseFilter):
    def __init__(
            self,
            level: float = 1.0,
            mono_level: float = 1.0,
            *,
            filter_band: float = 220.0,
            filter_width: float = 100.0
    ):
        self.__level: float = level
        self.__mono_level: float = mono_level

        self.__filter_band: float = filter_band
        self.__filter_width: float = filter_width

    def __repr__(self) -> str:
        return f'<KaraokeFilter level={self.level:.2f}>'

    @property
    def level(self) -> float:
        return self.__level

    @level.setter
    def level(self, new: float) -> None:
        self.__level = new

    @property
    def mono_level(self) -> float:
        return self.__mono_level

    @mono_level.setter
    def mono_level(self, new: float) -> None:
        self.__mono_level = new

    @property
    def filter_band(self) -> float:
        return self.__filter_band

    @filter_band.setter
    def filter_band(self, new: float) -> None:
        self.__filter_band = new

    @property
    def filter_width(self) -> float:
        return self.__filter_width

    @filter_width.setter
    def filter_width(self, new: float) -> None:
        self.__filter_width = new

    @property
    def identifier(self) -> str:
        return 'karaoke'

    @classmethod
    def from_raw(cls, data: Dict[str, float]) -> KaraokeFilter:
        return cls(**data)

    def to_raw(self) -> Dict[str, float]:
        return {
            'level': self.level,
            'mono_level': self.mono_level,
            'filter_band': self.filter_band,
            'filter_width': self.filter_width
        }


class ChannelMixFilter(BaseFilter):
    def __init__(
            self,
            *,
            left_to_left: float = 1,
            right_to_right: float = 1,
            left_to_right: float = 0,
            right_to_left: float = 0
    ) -> None:
        self.__left_to_left: float = None
        self.__right_to_right: float = None
        self.__left_to_right: float = None
        self.__right_to_left: float = None

        # Let setters handle
        self.left_to_left = left_to_left
        self.right_to_right = right_to_right
        self.left_to_right = left_to_right
        self.right_to_left = right_to_left

    def __repr__(self) -> str:
        return '<ChannelMixFilter>'

    @property
    def left_to_left(self) -> float:
        return self.__left_to_left

    @left_to_left.setter
    def left_to_left(self, new: float) -> None:
        if not 0 <= new <= 1:
            raise ValueError('left_to_left value must be between 0 and 1.')

        self.__left_to_left = new

    @property
    def right_to_right(self) -> float:
        return self.__right_to_right

    @right_to_right.setter
    def right_to_right(self, new: float) -> None:
        if not 0 <= new <= 1:
            raise ValueError('right_to_right value must be between 0 and 1.')

        self.__right_to_right = new

    @property
    def left_to_right(self) -> float:
        return self.__left_to_right

    @left_to_right.setter
    def left_to_right(self, new: float) -> None:
        if not 0 <= new <= 1:
            raise ValueError('left_to_right value must be between 0 and 1.')

        self.__left_to_right = new

    @property
    def right_to_left(self) -> float:
        return self.__right_to_left

    @right_to_left.setter
    def right_to_left(self, new: float) -> None:
        if not 0 <= new <= 1:
            raise ValueError('right_to_left value must be between 0 and 1.')

        self.__right_to_left = new

    @property
    def identifier(self) -> str:
        return 'channel_mix'

    @classmethod
    def from_raw(cls, data: Dict[str, float]) -> ChannelMixFilter:
        return cls(**data)

    def to_raw(self) -> Dict[str, float]:
        return {
            'left_to_left': self.left_to_left,
            'right_to_right': self.right_to_right,
            'left_to_right': self.left_to_right,
            'right_to_left': self.right_to_left
        }


class LowPassFilter(BaseFilter):
    def __init__(self, smoothing: float = 20) -> None:
        self.__smoothing: float = smoothing

    def __repr__(self) -> str:
        return f'<LowPassFilter smoothing={self.__smoothing:.1f}>'

    @property
    def smoothing(self) -> float:
        return self.__smoothing

    @smoothing.setter
    def smoothing(self, new: float) -> None:
        self.__smoothing = new

    @property
    def identifier(self) -> str:
        return 'low_pass'

    @classmethod
    def from_raw(cls, data: float) -> LowPassFilter:
        return cls(smoothing=data)

    def to_raw(self) -> float:
        return self.smoothing
