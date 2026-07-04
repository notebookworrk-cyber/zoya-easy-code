__version__ = "0.1.0"

import math
import random
import time
from abc import ABC, abstractmethod
from typing import Any


class RoboticsError(Exception):
    pass


class RobotHardware(ABC):
    def __init__(self, name: str):
        self.name: str = name
        self._connected: bool = False

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    def is_connected(self) -> bool:
        return self._connected

    @abstractmethod
    def get_status(self) -> dict[str, Any]: ...

    @abstractmethod
    def emergency_stop(self) -> None: ...


class Motor:
    def __init__(self, channel: int):
        self.channel: int = channel
        self.speed: float = 0.0
        self._running: bool = False

    def set_speed(self, speed: float) -> None:
        if not -1.0 <= speed <= 1.0:
            raise RoboticsError(f"Speed must be between -1.0 and 1.0, got {speed}")
        self.speed = speed
        self._running = abs(speed) > 0.001

    def stop(self) -> None:
        self.speed = 0.0
        self._running = False

    def get_speed(self) -> float:
        return self.speed

    def is_running(self) -> bool:
        return self._running


class Sensor(ABC):
    def __init__(self, name: str, unit: str = ""):
        self.name: str = name
        self.unit: str = unit
        self._calibrated: bool = False
        self._offset: float = 0.0

    @abstractmethod
    def read(self) -> float: ...

    def get_value(self) -> float:
        return self.read()

    def calibrate(self) -> None:
        self._calibrated = True

    def is_calibrated(self) -> bool:
        return self._calibrated


class UltrasonicSensor(Sensor):
    def __init__(self, trigger_pin: int, echo_pin: int):
        super().__init__(name=f"Ultrasonic_{trigger_pin}_{echo_pin}", unit="cm")
        self.trigger_pin: int = trigger_pin
        self.echo_pin: int = echo_pin
        self._distance: float = 0.0

    def read(self) -> float:
        self._distance = max(2.0, 400.0 - abs(hash(f"{time.time():.1f}")) % 398.0)
        if self._calibrated:
            self._distance *= 1.0 + self._offset
        return round(self._distance, 2)

    def calibrate(self) -> None:
        raw = abs(hash(str(time.time()))) % 10 / 100
        self._offset = -raw
        self._calibrated = True


class InfraredSensor(Sensor):
    def __init__(self, pin: int):
        super().__init__(name=f"Infrared_{pin}", unit="binary")
        self.pin: int = pin
        self._detected: int = 0

    def read(self) -> float:
        self._detected = (
            1 if (abs(hash(f"ir_{int(time.time() * 2)}")) % 100 > 70) else 0
        )
        return float(self._detected)


class TemperatureSensor(Sensor):
    def __init__(self, pin: int):
        super().__init__(name=f"Temp_{pin}", unit="celsius")
        self.pin: int = pin
        self._temperature: float = 22.0

    def read(self) -> float:
        drift = random.uniform(-1.5, 1.5)
        self._temperature = round(22.0 + drift, 1)
        return self._temperature


class Gyroscope(Sensor):
    def __init__(self):
        super().__init__(name="Gyroscope", unit="deg/s")
        self.x: float = 0.0
        self.y: float = 0.0
        self.z: float = 0.0

    def read(self) -> float:
        self.x = random.uniform(-5.0, 5.0)
        self.y = random.uniform(-5.0, 5.0)
        self.z = random.uniform(-5.0, 5.0)
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def get_value(self) -> tuple[float, float, float]:
        self.read()
        return (round(self.x, 2), round(self.y, 2), round(self.z, 2))


class Accelerometer(Sensor):
    def __init__(self):
        super().__init__(name="Accelerometer", unit="m/s^2")
        self.x: float = 0.0
        self.y: float = 0.0
        self.z: float = 9.81

    def read(self) -> float:
        self.x = random.uniform(-2.0, 2.0)
        self.y = random.uniform(-2.0, 2.0)
        self.z = 9.81 + random.uniform(-0.5, 0.5)
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def get_value(self) -> tuple[float, float, float]:
        self.read()
        return (round(self.x, 2), round(self.y, 2), round(self.z, 2))


class LightSensor(Sensor):
    def __init__(self, pin: int):
        super().__init__(name=f"Light_{pin}", unit="lux")
        self.pin: int = pin
        self._lux: float = 0.0

    def read(self) -> float:
        base = (
            random.uniform(100, 900)
            if abs(hash(str(int(time.time()))[:2])) % 2 == 0
            else random.uniform(0, 50)
        )
        self._lux = round(base, 1)
        return self._lux


class GPSModule:
    def __init__(self):
        self.latitude: float = 37.7749
        self.longitude: float = -122.4194
        self.altitude: float = 0.0
        self._base_lat: float = 37.7749
        self._base_lng: float = -122.4194

    def read(self) -> tuple[float, float, float]:
        self.latitude = self._base_lat + random.uniform(-0.001, 0.001)
        self.longitude = self._base_lng + random.uniform(-0.001, 0.001)
        self.altitude = max(0.0, self.altitude + random.uniform(-0.5, 0.5))
        return (
            round(self.latitude, 6),
            round(self.longitude, 6),
            round(self.altitude, 2),
        )

    def get_value(self) -> dict[str, float]:
        self.read()
        return {
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "altitude": round(self.altitude, 2),
        }


class Servo:
    def __init__(self, pin: int):
        self.pin: int = pin
        self.angle: float = 90.0

    def set_angle(self, angle: float) -> None:
        if not 0.0 <= angle <= 180.0:
            raise RoboticsError(f"Angle must be between 0 and 180, got {angle}")
        self.angle = angle

    def get_angle(self) -> float:
        return self.angle

    def sweep(self, start: float, end: float, delay: float = 0.01) -> None:
        if not (0 <= start <= 180 and 0 <= end <= 180):
            raise RoboticsError("Sweep angles must be between 0 and 180")
        step = 1.0 if end >= start else -1.0
        angle = start
        while abs(angle - end) > 0.5:
            self.angle = round(angle, 1)
            angle += step


class RobotController:
    def __init__(self, name: str):
        self.name: str = name
        self.motors: list[Motor] = []
        self.sensors: list[Sensor] = []
        self.servos: list[Servo] = []

    def add_motor(self, motor: Motor) -> None:
        self.motors.append(motor)

    def add_sensor(self, sensor: Sensor) -> None:
        self.sensors.append(sensor)

    def add_servo(self, servo: Servo) -> None:
        self.servos.append(servo)

    def drive(self, left_speed: float, right_speed: float) -> None:
        if len(self.motors) < 2:
            raise RoboticsError("Need at least 2 motors for differential drive")
        self.motors[0].set_speed(left_speed)
        self.motors[1].set_speed(right_speed)

    def forward(self, speed: float = 0.5) -> None:
        self.drive(speed, speed)

    def backward(self, speed: float = 0.5) -> None:
        self.drive(-speed, -speed)

    def turn_left(self, speed: float = 0.5) -> None:
        self.drive(-speed, speed)

    def turn_right(self, speed: float = 0.5) -> None:
        self.drive(speed, -speed)

    def stop_all(self) -> None:
        for motor in self.motors:
            motor.stop()

    def read_all_sensors(self) -> dict[str, float]:
        data: dict[str, float] = {}
        for sensor in self.sensors:
            data[sensor.name] = sensor.read()
        return data

    def execute_sequence(self, commands: list[dict[str, Any]]) -> None:
        for cmd in commands:
            action = cmd.get("action")
            params = {k: v for k, v in cmd.items() if k != "action"}
            if hasattr(self, action):
                getattr(self, action)(**params)
            else:
                raise RoboticsError(f"Unknown command action: {action}")

    def get_state(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "motors": [{"channel": m.channel, "speed": m.speed} for m in self.motors],
            "sensor_count": len(self.sensors),
            "servo_count": len(self.servos),
        }


class DroneController(RobotController):
    def __init__(self, name: str):
        super().__init__(name=name)
        self._armed: bool = False
        self._altitude: float = 0.0
        self._battery: float = 100.0
        self._home_lat: float = 37.7749
        self._home_lng: float = -122.4194
        self._position: dict[str, float] = {"x": 0.0, "y": 0.0, "z": 0.0}
        self._yaw: float = 0.0

    def arm(self) -> None:
        if self._battery < 10:
            raise RoboticsError("Battery too low to arm")
        self._armed = True

    def disarm(self) -> None:
        self._armed = False

    def takeoff(self, height: float = 1.0) -> None:
        if not self._armed:
            raise RoboticsError("Cannot takeoff: drone not armed")
        self._altitude = height
        self._position["z"] = height

    def land(self) -> None:
        self._altitude = 0.0
        self._position["z"] = 0.0
        self._armed = False

    def hover(self, duration: float = 1.0) -> None:
        if self._altitude <= 0:
            raise RoboticsError("Cannot hover: drone is on the ground")
        time.sleep(min(duration, 0.05))

    def move(self, x: float, y: float, z: float, speed: float = 0.5) -> None:
        if not self._armed:
            raise RoboticsError("Cannot move: drone not armed")
        self._position["x"] += x
        self._position["y"] += y
        self._position["z"] = max(0.0, self._position["z"] + z)
        self._altitude = self._position["z"]

    def rotate(self, yaw: float) -> None:
        self._yaw = (self._yaw + yaw) % 360.0

    def flip(self, direction: str = "forward") -> None:
        if self._altitude < 0.5:
            raise RoboticsError("Altitude too low for flip")
        valid = ("forward", "backward", "left", "right")
        if direction not in valid:
            raise RoboticsError(f"Invalid flip direction: {direction}. Valid: {valid}")

    def get_altitude(self) -> float:
        return self._altitude

    def get_battery(self) -> float:
        self._battery = max(0.0, self._battery - 0.01)
        return round(self._battery, 1)

    def return_to_launch(self) -> None:
        self._position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self._altitude = 0.0

    def set_home(self) -> None:
        self._home_lat = 37.7749 + random.uniform(-0.0005, 0.0005)
        self._home_lng = -122.4194 + random.uniform(-0.0005, 0.0005)


class SimulationEnvironment:
    def __init__(self, robot: RobotController):
        self.robot: RobotController = robot
        self._running: bool = False
        self._time: float = 0.0
        self._obstacles: list[dict[str, Any]] = []

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def set_obstacles(self, obstacles: list[dict[str, Any]]) -> None:
        self._obstacles = list(obstacles)

    def get_simulated_sensor_data(self) -> dict[str, float]:
        data: dict[str, float] = {}
        for sensor in self.robot.sensors:
            data[sensor.name] = sensor.read()
        return data

    def step(self, dt: float = 0.1) -> None:
        if not self._running:
            return
        self._time += dt
        if isinstance(self.robot, DroneController) and self.robot.get_battery() < 5:
            self.robot.return_to_launch()
            self.stop()

    def reset(self) -> None:
        self._time = 0.0
        self._running = False
        self.robot.stop_all()
        for servo in self.robot.servos:
            servo.set_angle(90.0)


def create_wheeled_robot(name: str) -> RobotController:
    robot = RobotController(name=name)
    robot.add_motor(Motor(channel=0))
    robot.add_motor(Motor(channel=1))
    robot.add_sensor(UltrasonicSensor(trigger_pin=2, echo_pin=3))
    robot.add_sensor(InfraredSensor(pin=4))
    robot.add_sensor(TemperatureSensor(pin=5))
    robot.add_servo(Servo(pin=6))
    return robot


def create_quadcopter(name: str) -> DroneController:
    drone = DroneController(name=name)
    drone.add_motor(Motor(channel=0))
    drone.add_motor(Motor(channel=1))
    drone.add_motor(Motor(channel=2))
    drone.add_motor(Motor(channel=3))
    drone.add_sensor(Gyroscope())
    drone.add_sensor(Accelerometer())
    drone.add_sensor(TemperatureSensor(pin=0))
    drone.add_sensor(GPSModule())
    return drone


def calculate_odometry(
    left_ticks: int,
    right_ticks: int,
    wheel_diameter: float,
    wheel_base: float,
) -> dict[str, float]:
    ticks_per_revolution = 360
    left_rev = left_ticks / ticks_per_revolution
    right_rev = right_ticks / ticks_per_revolution
    wheel_circumference = math.pi * wheel_diameter
    left_dist = left_rev * wheel_circumference
    right_dist = right_rev * wheel_circumference
    distance = (left_dist + right_dist) / 2.0
    rotation = (right_dist - left_dist) / wheel_base
    return {
        "distance": round(distance, 4),
        "rotation": round(rotation, 4),
        "left_distance": round(left_dist, 4),
        "right_distance": round(right_dist, 4),
    }


__all__ = [
    "RoboticsError",
    "RobotHardware",
    "Motor",
    "Sensor",
    "UltrasonicSensor",
    "InfraredSensor",
    "TemperatureSensor",
    "Gyroscope",
    "Accelerometer",
    "LightSensor",
    "GPSModule",
    "Servo",
    "RobotController",
    "DroneController",
    "SimulationEnvironment",
    "create_wheeled_robot",
    "create_quadcopter",
    "calculate_odometry",
]
