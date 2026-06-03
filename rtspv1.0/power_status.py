# 라즈베리파이 UPS Plus 전원 상태 조회 파일입니다.
# 52Pi EP-0136 전력 모듈의 I2C 레지스터에서 배터리 잔량과 입력 전압을 읽습니다.
# UPS가 없거나 I2C 접근이 실패해도 API 서버가 중단되지 않도록 실패 상태를 반환합니다.

from dataclasses import dataclass
from datetime import datetime
import os
import threading
import time


DEFAULT_I2C_BUS = 1
UPS_PLUS_I2C_ADDRESS = 0x17
BATTERY_REMAINING_LOW_REGISTER = 0x13
BATTERY_REMAINING_HIGH_REGISTER = 0x14
USB_C_INPUT_LOW_REGISTER = 0x07
USB_C_INPUT_HIGH_REGISTER = 0x08
MICRO_USB_INPUT_LOW_REGISTER = 0x09
MICRO_USB_INPUT_HIGH_REGISTER = 0x0A
POWER_STATUS_REGISTER = 0x17
DEFAULT_EXTERNAL_POWER_THRESHOLD_MILLIVOLT = 4000


@dataclass(frozen=True)
class PowerStatusSnapshot:
    """UPS Plus 전원 상태 한 번의 측정값을 표현합니다.

    인자:
        captured_at: 측정 시각 ISO 문자열입니다.
        available: UPS 값을 정상적으로 읽었는지 여부입니다.
        battery_remaining_percent: 배터리 잔량 백분율입니다.
        external_power_connected: 외부 전원 연결 여부입니다.
        type_c_input_millivolt: USB-C 입력 전압입니다.
        micro_usb_input_millivolt: MicroUSB 입력 전압입니다.
        power_status_raw: UPS 전원 상태 원본 레지스터 값입니다.
        error_code: 실패 원인을 분류하는 코드입니다.
        error: 실패 원인 설명입니다.
    반환값:
        PowerStatusSnapshot 인스턴스를 반환합니다.
    """

    captured_at: str
    available: bool
    battery_remaining_percent: int | None = None
    external_power_connected: bool | None = None
    type_c_input_millivolt: int | None = None
    micro_usb_input_millivolt: int | None = None
    power_status_raw: int | None = None
    error_code: str | None = None
    error: str | None = None

    def to_dict(self):
        """전원 상태 측정값을 JSON 직렬화 가능한 딕셔너리로 변환합니다.

        인자:
            없음.
        반환값:
            전원 상태 필드를 담은 딕셔너리를 반환합니다.
        """

        return {
            "captured_at": self.captured_at,
            "available": self.available,
            "battery_remaining_percent": self.battery_remaining_percent,
            "external_power_connected": self.external_power_connected,
            "type_c_input_millivolt": self.type_c_input_millivolt,
            "micro_usb_input_millivolt": self.micro_usb_input_millivolt,
            "power_status_raw": self.power_status_raw,
            "error_code": self.error_code,
            "error": self.error,
        }

    @classmethod
    def unavailable(cls, error_code, error):
        """UPS 값을 읽을 수 없을 때 사용할 실패 스냅샷을 생성합니다.

        인자:
            error_code: 실패 원인 분류 코드입니다.
            error: 실패 원인 설명입니다.
        반환값:
            available 값이 False인 PowerStatusSnapshot 인스턴스를 반환합니다.
        """

        return cls(
            captured_at=datetime.now().isoformat(timespec="seconds"),
            available=False,
            error_code=error_code,
            error=str(error),
        )


class UpsPlusPowerReader:
    """52Pi EP-0136 UPS Plus 보드의 I2C 레지스터를 읽습니다.

    인자:
        bus_number: Raspberry Pi에서 사용할 I2C 버스 번호입니다.
        device_address: UPS Plus I2C 장치 주소입니다.
        external_power_threshold_millivolt: 외부 전원 판단 전압 기준입니다.
    반환값:
        UpsPlusPowerReader 인스턴스를 반환합니다.
    """

    def __init__(
        self,
        bus_number=DEFAULT_I2C_BUS,
        device_address=UPS_PLUS_I2C_ADDRESS,
        external_power_threshold_millivolt=DEFAULT_EXTERNAL_POWER_THRESHOLD_MILLIVOLT,
    ):
        """UPS Plus 레지스터 읽기 설정을 초기화합니다.

        인자:
            bus_number: Raspberry Pi에서 사용할 I2C 버스 번호입니다.
            device_address: UPS Plus I2C 장치 주소입니다.
            external_power_threshold_millivolt: 외부 전원 판단 전압 기준입니다.
        반환값:
            없음.
        """

        self.bus_number = bus_number
        self.device_address = device_address
        self.external_power_threshold_millivolt = external_power_threshold_millivolt

    def read_snapshot(self):
        """UPS Plus에서 배터리 잔량과 입력 전원 상태를 읽습니다.

        인자:
            없음.
        반환값:
            PowerStatusSnapshot 인스턴스를 반환합니다.
        """

        bus = None
        try:
            self._ensure_i2c_device_exists()
            bus = self._open_bus()
            battery_remaining_percent = self._read_percent(bus)
            type_c_input_millivolt = self._read_word(
                bus,
                USB_C_INPUT_LOW_REGISTER,
                USB_C_INPUT_HIGH_REGISTER,
            )
            micro_usb_input_millivolt = self._read_word(
                bus,
                MICRO_USB_INPUT_LOW_REGISTER,
                MICRO_USB_INPUT_HIGH_REGISTER,
            )
            power_status_raw = self._read_byte(bus, POWER_STATUS_REGISTER)
            threshold = self.external_power_threshold_millivolt
            external_power_connected = (
                type_c_input_millivolt >= threshold
                or micro_usb_input_millivolt >= threshold
            )
            return PowerStatusSnapshot(
                captured_at=datetime.now().isoformat(timespec="seconds"),
                available=True,
                battery_remaining_percent=battery_remaining_percent,
                external_power_connected=external_power_connected,
                type_c_input_millivolt=type_c_input_millivolt,
                micro_usb_input_millivolt=micro_usb_input_millivolt,
                power_status_raw=power_status_raw,
            )
        except Exception as error:
            return PowerStatusSnapshot.unavailable(
                self._classify_error(error),
                error,
            )
        finally:
            if bus is not None and hasattr(bus, "close"):
                try:
                    bus.close()
                except Exception:
                    pass

    def _ensure_i2c_device_exists(self):
        """리눅스 I2C 장치 파일이 있는지 확인합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if os.name != "posix":
            return

        device_path = f"/dev/i2c-{self.bus_number}"
        if not os.path.exists(device_path):
            raise FileNotFoundError(
                f"{device_path}가 없습니다. I2C 활성화 여부를 확인하세요."
            )

    def _open_bus(self):
        """SMBus 인스턴스를 열어 I2C 통신을 준비합니다.

        인자:
            없음.
        반환값:
            SMBus 인스턴스를 반환합니다.
        """

        smbus_class = _load_smbus_class()
        return smbus_class(self.bus_number)

    def _read_percent(self, bus):
        """UPS Plus 배터리 잔량 레지스터를 백분율로 읽습니다.

        인자:
            bus: 열린 SMBus 인스턴스입니다.
        반환값:
            0부터 100 사이의 정수 배터리 잔량을 반환합니다.
        """

        raw_percent = self._read_word(
            bus,
            BATTERY_REMAINING_LOW_REGISTER,
            BATTERY_REMAINING_HIGH_REGISTER,
        )
        return max(0, min(100, raw_percent))

    def _read_word(self, bus, low_register, high_register):
        """연속된 저위/고위 바이트 레지스터를 16비트 정수로 읽습니다.

        인자:
            bus: 열린 SMBus 인스턴스입니다.
            low_register: 저위 바이트 레지스터 주소입니다.
            high_register: 고위 바이트 레지스터 주소입니다.
        반환값:
            16비트 정수 값을 반환합니다.
        """

        low_byte = self._read_byte(bus, low_register)
        high_byte = self._read_byte(bus, high_register)
        return (high_byte << 8) | low_byte

    def _read_byte(self, bus, register_address):
        """UPS Plus의 단일 레지스터 바이트 값을 읽습니다.

        인자:
            bus: 열린 SMBus 인스턴스입니다.
            register_address: 읽을 레지스터 주소입니다.
        반환값:
            0부터 255 사이의 정수 값을 반환합니다.
        """

        return int(bus.read_byte_data(self.device_address, register_address))

    def _classify_error(self, error):
        """I2C 읽기 실패 원인을 API용 코드로 분류합니다.

        인자:
            error: 발생한 예외 객체입니다.
        반환값:
            실패 원인 코드 문자열을 반환합니다.
        """

        if isinstance(error, ImportError):
            return "smbus_missing"
        if isinstance(error, FileNotFoundError):
            return "i2c_device_missing"
        if isinstance(error, PermissionError):
            return "i2c_permission_denied"
        if isinstance(error, OSError):
            return "i2c_access_error"
        return "power_read_error"


class CachedPowerStatusProvider:
    """UPS Plus 전원 상태를 일정 시간 캐시해 반복 I2C 조회를 줄입니다.

    인자:
        reader: 실제 UPS Plus 값을 읽는 객체입니다.
        cache_seconds: 캐시 유지 시간입니다.
    반환값:
        CachedPowerStatusProvider 인스턴스를 반환합니다.
    """

    def __init__(self, reader=None, cache_seconds=2.0):
        """전원 상태 캐시 저장소와 읽기 객체를 초기화합니다.

        인자:
            reader: 실제 UPS Plus 값을 읽는 객체이며 없으면 기본 리더를 사용합니다.
            cache_seconds: 캐시 유지 시간입니다.
        반환값:
            없음.
        """

        self.reader = reader if reader is not None else UpsPlusPowerReader()
        self.cache_seconds = cache_seconds
        self.cached_snapshot = None
        self.cached_at_monotonic = 0.0
        self.lock = threading.Lock()

    def get_snapshot(self):
        """캐시가 유효하면 캐시값을, 아니면 새 전원 상태를 반환합니다.

        인자:
            없음.
        반환값:
            PowerStatusSnapshot 인스턴스를 반환합니다.
        """

        now = time.monotonic()
        with self.lock:
            if self.cached_snapshot is not None:
                if now - self.cached_at_monotonic < self.cache_seconds:
                    return self.cached_snapshot

            self.cached_snapshot = self.reader.read_snapshot()
            self.cached_at_monotonic = now
            return self.cached_snapshot


def _load_smbus_class():
    """설치된 SMBus 구현체를 찾아 반환합니다.

    인자:
        없음.
    반환값:
        smbus2.SMBus 또는 smbus.SMBus 클래스를 반환합니다.
    """

    try:
        from smbus2 import SMBus

        return SMBus
    except ImportError:
        try:
            from smbus import SMBus

            return SMBus
        except ImportError as smbus_error:
            raise ImportError(
                "smbus2 또는 smbus가 설치되어 있지 않아 UPS Plus 값을 읽을 수 없습니다."
            ) from smbus_error

