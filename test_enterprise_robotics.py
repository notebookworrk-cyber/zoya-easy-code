import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
import json
import math
from unittest.mock import patch

from zoya.enterprise import (
    EnterpriseError, Tenant, RBACManager, AuditLog, AuditLogger,
    FeatureFlags, SSOProvider, SSOManager, TenantManager,
)
from zoya.robotics import (
    RoboticsError, Motor, UltrasonicSensor, TemperatureSensor,
    Gyroscope, GPSModule, Servo, RobotController, DroneController,
    SimulationEnvironment, create_wheeled_robot, create_quadcopter,
    calculate_odometry,
)


class TestRBACManager(unittest.TestCase):
    def setUp(self):
        self.rbac = RBACManager()
        self.user_id = "user_001"
        self.tenant_id = "tenant_001"

    def test_create_role_with_permissions(self):
        self.rbac.create_role("analyst", ["read", "export"])
        role = self.rbac.get_role("analyst")
        self.assertIsNotNone(role)
        self.assertEqual(role["name"], "analyst")
        self.assertIn("read", role["permissions"])
        self.assertIn("export", role["permissions"])

    def test_get_role_returns_role(self):
        role = self.rbac.get_role("admin")
        self.assertIsNotNone(role)
        self.assertEqual(role["name"], "admin")
        self.assertTrue(role["built_in"])

    def test_get_role_nonexistent_returns_none(self):
        role = self.rbac.get_role("ghost")
        self.assertIsNone(role)

    def test_update_role_changes_permissions(self):
        self.rbac.create_role("beta_tester", ["read"])
        self.rbac.update_role("beta_tester", ["read", "write", "delete"])
        role = self.rbac.get_role("beta_tester")
        self.assertIn("delete", role["permissions"])

    def test_delete_role_removes(self):
        self.rbac.create_role("tmp", ["read"])
        self.rbac.delete_role("tmp")
        self.assertIsNone(self.rbac.get_role("tmp"))

    def test_delete_built_in_role_raises(self):
        with self.assertRaises(EnterpriseError):
            self.rbac.delete_role("admin")

    def test_assign_role_to_user(self):
        self.rbac.assign_role(self.user_id, "editor", self.tenant_id)
        roles = self.rbac.get_user_roles(self.user_id)
        self.assertIn("editor", roles)

    def test_assign_role_nonexistent_raises(self):
        with self.assertRaises(EnterpriseError):
            self.rbac.assign_role(self.user_id, "nope", self.tenant_id)

    def test_get_user_roles_returns_assigned(self):
        self.rbac.assign_role(self.user_id, "viewer", self.tenant_id)
        self.rbac.assign_role(self.user_id, "editor", "tenant_002")
        roles = self.rbac.get_user_roles(self.user_id)
        self.assertEqual(len(roles), 2)

    def test_get_user_roles_empty(self):
        roles = self.rbac.get_user_roles("unknown")
        self.assertEqual(roles, [])

    def test_check_permission_granted(self):
        self.rbac.assign_role(self.user_id, "editor", self.tenant_id)
        self.assertTrue(self.rbac.check_permission(self.user_id, "write", self.tenant_id))

    def test_check_permission_denied(self):
        self.rbac.assign_role(self.user_id, "viewer", self.tenant_id)
        self.assertFalse(self.rbac.check_permission(self.user_id, "delete", self.tenant_id))

    def test_check_permission_no_role_returns_false(self):
        self.assertFalse(self.rbac.check_permission("no_user", "read", self.tenant_id))

    def test_check_permission_admin_wildcard(self):
        self.rbac.assign_role(self.user_id, "admin", self.tenant_id)
        self.assertTrue(self.rbac.check_permission(self.user_id, "anything", self.tenant_id))

    def test_list_roles_includes_built_in(self):
        roles = self.rbac.list_roles()
        self.assertIn("admin", roles)
        self.assertIn("editor", roles)
        self.assertIn("viewer", roles)

    def test_duplicate_role_raises(self):
        with self.assertRaises(EnterpriseError):
            self.rbac.create_role("admin", [])

    def test_remove_role(self):
        self.rbac.assign_role(self.user_id, "viewer", self.tenant_id)
        self.rbac.remove_role(self.user_id, self.tenant_id)
        self.assertEqual(self.rbac.get_user_roles(self.user_id), [])

    def test_update_nonexistent_role_raises(self):
        with self.assertRaises(EnterpriseError):
            self.rbac.update_role("phantom", [])


class TestAuditLogger(unittest.TestCase):
    def setUp(self):
        self.logger = AuditLogger()

    def test_log_creates_entry(self):
        entry = self.logger.log("login", "u1", "t1", "login", "session")
        self.assertIsInstance(entry, AuditLog)
        self.assertEqual(entry.event, "login")
        self.assertEqual(entry.user_id, "u1")

    def test_query_with_filters(self):
        self.logger.log("login", "u1", "t1", "login", "session")
        self.logger.log("logout", "u1", "t1", "logout", "session")
        self.logger.log("login", "u2", "t2", "login", "session")
        results = self.logger.query({"user_id": "u1"})
        self.assertEqual(len(results), 2)

    def test_query_multiple_filters(self):
        self.logger.log("login", "u1", "t1", "login", "session")
        self.logger.log("login", "u1", "t2", "login", "session")
        results = self.logger.query({"user_id": "u1", "tenant_id": "t1"})
        self.assertEqual(len(results), 1)

    def test_query_severity_filter(self):
        self.logger.log("login", "u1", "t1", "login", "session", severity="info")
        self.logger.log("error", "u1", "t1", "crash", "system", severity="critical")
        results = self.logger.query({"severity": "critical"})
        self.assertEqual(len(results), 1)

    def test_query_action_filter(self):
        self.logger.log("login", "u1", "t1", "login", "session")
        self.logger.log("delete", "u1", "t1", "delete", "file")
        results = self.logger.query({"action": "delete"})
        self.assertEqual(len(results), 1)

    def test_query_event_filter(self):
        self.logger.log("login_event", "u1", "t1", "login", "session")
        results = self.logger.query({"event": "login_event"})
        self.assertEqual(len(results), 1)

    def test_query_resource_filter(self):
        self.logger.log("access", "u1", "t1", "read", "report.pdf")
        results = self.logger.query({"resource": "report.pdf"})
        self.assertEqual(len(results), 1)

    def test_get_by_user_returns_user_events(self):
        self.logger.log("login", "u1", "t1", "login", "session")
        self.logger.log("login", "u2", "t2", "login", "session")
        results = self.logger.get_by_user("u1")
        self.assertEqual(len(results), 1)

    def test_get_by_tenant_returns_tenant_events(self):
        self.logger.log("login", "u1", "t1", "login", "session")
        self.logger.log("login", "u2", "t2", "login", "session")
        self.logger.log("login", "u3", "t1", "login", "session")
        results = self.logger.get_by_tenant("t1")
        self.assertEqual(len(results), 2)

    def test_get_recent_returns_latest(self):
        for i in range(10):
            self.logger.log(f"e{i}", "u1", "t1", f"a{i}", "r")
        recent = self.logger.get_recent(3)
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[-1].event, "e9")

    def test_export_returns_json(self):
        self.logger.log("login", "u1", "t1", "login", "session")
        exported = self.logger.export()
        data = json.loads(exported)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["event"], "login")

    def test_clear_removes_all(self):
        self.logger.log("login", "u1", "t1", "login", "session")
        self.logger.clear()
        self.assertEqual(len(self.logger.get_recent()), 0)


class TestFeatureFlags(unittest.TestCase):
    def setUp(self):
        self.ff = FeatureFlags()
        self.tenant_id = "tenant_xyz"

    def test_set_flag_enables_disables(self):
        self.ff.set_flag("dark_mode", False)
        self.assertFalse(self.ff.is_enabled("dark_mode"))
        self.ff.set_flag("dark_mode", True)
        self.assertTrue(self.ff.is_enabled("dark_mode"))

    def test_is_enabled_checks_default(self):
        self.assertTrue(self.ff.is_enabled("dark_mode"))
        self.assertFalse(self.ff.is_enabled("beta_features"))

    def test_get_all_returns_all_flags(self):
        flags = self.ff.get_all()
        self.assertIn("dark_mode", flags)
        self.assertIn("analytics", flags)
        self.assertEqual(len(flags), 5)

    def test_per_tenant_flag_isolation(self):
        self.ff.set_flag("beta_features", True, tenant_id=self.tenant_id)
        self.assertTrue(self.ff.is_enabled("beta_features", tenant_id=self.tenant_id))
        self.assertFalse(self.ff.is_enabled("beta_features"))

    def test_delete_flag_removes(self):
        self.ff.set_flag("custom_flag", True)
        self.ff.delete_flag("custom_flag")
        self.assertFalse(self.ff.is_enabled("custom_flag"))

    def test_list_flags_returns_names(self):
        names = self.ff.list_flags()
        self.assertIn("dark_mode", names)
        self.assertIn("export_pdf", names)
        self.assertEqual(len(names), 5)

    def test_reset_clears_tenant_flags(self):
        self.ff.set_flag("dark_mode", False, tenant_id=self.tenant_id)
        self.ff.reset(tenant_id=self.tenant_id)
        flags = self.ff.get_all(tenant_id=self.tenant_id)
        self.assertTrue(flags["dark_mode"])

    def test_reset_global_clears_everything(self):
        self.ff.set_flag("beta_features", True)
        self.ff.set_flag("custom_flag", True)
        self.ff.reset()
        self.assertFalse(self.ff.is_enabled("beta_features"))
        self.assertNotIn("custom_flag", self.ff.list_flags())

    def test_get_all_with_tenant_includes_overrides(self):
        self.ff.set_flag("dark_mode", False, tenant_id=self.tenant_id)
        flags = self.ff.get_all(tenant_id=self.tenant_id)
        self.assertFalse(flags["dark_mode"])

    def test_is_enabled_unknown_flag(self):
        self.assertFalse(self.ff.is_enabled("nonexistent_flag"))

    def test_delete_flag_also_from_tenant(self):
        self.ff.set_flag("beta_features", True, tenant_id=self.tenant_id)
        self.ff.delete_flag("beta_features")
        self.assertFalse(self.ff.is_enabled("beta_features", tenant_id=self.tenant_id))


class TestSSOManager(unittest.TestCase):
    def setUp(self):
        self.sso = SSOManager()

    def test_add_provider(self):
        provider = SSOProvider("google", {"client_id": "abc", "client_secret": "secret"})
        self.sso.add_provider(provider)
        self.assertIsNotNone(self.sso.get_provider("google"))

    def test_get_provider_returns_provider(self):
        provider = SSOProvider("github", {"client_id": "x", "client_secret": "y"})
        self.sso.add_provider(provider)
        got = self.sso.get_provider("github")
        self.assertEqual(got.name, "github")

    def test_get_provider_nonexistent_returns_none(self):
        self.assertIsNone(self.sso.get_provider("nonexistent"))

    def test_list_providers(self):
        self.sso.add_provider(SSOProvider("google", {"client_id": "a", "client_secret": "b"}))
        self.sso.add_provider(SSOProvider("github", {"client_id": "c", "client_secret": "d"}))
        self.assertEqual(len(self.sso.list_providers()), 2)

    def test_remove_provider(self):
        provider = SSOProvider("okta", {"client_id": "x", "client_secret": "y", "issuer": "https://okta.example.com"})
        self.sso.add_provider(provider)
        self.sso.remove_provider("okta")
        self.assertIsNone(self.sso.get_provider("okta"))

    def test_generate_auth_url_returns_url(self):
        provider = SSOProvider("google", {"client_id": "abc", "client_secret": "secret", "issuer": "https://accounts.google.com"})
        self.sso.add_provider(provider)
        url = self.sso.generate_auth_url("google", "https://myapp.com/callback")
        self.assertIn("accounts.google.com", url)
        self.assertIn("client_id=abc", url)
        self.assertIn("redirect_uri=https://myapp.com/callback", url)
        self.assertIn("response_type=code", url)

    def test_generate_auth_url_unconfigured_raises(self):
        with self.assertRaises(EnterpriseError):
            self.sso.generate_auth_url("google", "https://myapp.com/callback")

    def test_handle_callback_returns_dict(self):
        provider = SSOProvider("github", {"client_id": "x", "client_secret": "y", "issuer": "https://github.com"})
        self.sso.add_provider(provider)
        result = self.sso.handle_callback("github", "auth_code_123")
        self.assertIn("access_token", result)
        self.assertIn("user", result)
        self.assertEqual(result["provider"], "github")
        self.assertEqual(result["token_type"], "Bearer")

    def test_handle_callback_unconfigured_raises(self):
        with self.assertRaises(EnterpriseError):
            self.sso.handle_callback("google", "code")

    def test_is_sso_enabled_false(self):
        self.assertFalse(self.sso.is_sso_enabled())

    def test_is_sso_enabled_true(self):
        provider = SSOProvider("google", {"client_id": "a", "client_secret": "b"})
        self.sso.add_provider(provider)
        self.assertTrue(self.sso.is_sso_enabled())

    def test_invalid_provider_name_raises(self):
        with self.assertRaises(EnterpriseError):
            SSOProvider("invalid_provider")


class TestTenantManager(unittest.TestCase):
    def setUp(self):
        self.tm = TenantManager()

    def test_create_tenant_free(self):
        tenant = self.tm.create_tenant("Test Corp", plan="free")
        self.assertEqual(tenant.name, "Test Corp")
        self.assertEqual(tenant.plan, "free")
        self.assertTrue(tenant.is_active)

    def test_create_tenant_pro(self):
        tenant = self.tm.create_tenant("Pro Corp", plan="pro")
        self.assertEqual(tenant.plan, "pro")

    def test_create_tenant_enterprise(self):
        tenant = self.tm.create_tenant("Enterprise Inc", plan="enterprise")
        self.assertEqual(tenant.plan, "enterprise")

    def test_create_tenant_invalid_plan_raises(self):
        with self.assertRaises(EnterpriseError):
            self.tm.create_tenant("Bad", plan="platinum")

    def test_get_tenant(self):
        tenant = self.tm.create_tenant("Test")
        got = self.tm.get_tenant(tenant.id)
        self.assertEqual(got.id, tenant.id)
        self.assertEqual(got.name, "Test")

    def test_get_tenant_nonexistent(self):
        self.assertIsNone(self.tm.get_tenant("nonexistent"))

    def test_update_tenant(self):
        tenant = self.tm.create_tenant("Old Name")
        self.tm.update_tenant(tenant.id, {"name": "New Name", "is_active": False})
        updated = self.tm.get_tenant(tenant.id)
        self.assertEqual(updated.name, "New Name")
        self.assertFalse(updated.is_active)

    def test_update_tenant_settings(self):
        tenant = self.tm.create_tenant("Test")
        self.tm.update_tenant(tenant.id, {"settings": {"theme": "dark"}})
        updated = self.tm.get_tenant(tenant.id)
        self.assertEqual(updated.settings["theme"], "dark")

    def test_update_nonexistent_raises(self):
        with self.assertRaises(EnterpriseError):
            self.tm.update_tenant("invalid", {"name": "X"})

    def test_delete_tenant(self):
        tenant = self.tm.create_tenant("ToDelete")
        self.tm.delete_tenant(tenant.id)
        self.assertIsNone(self.tm.get_tenant(tenant.id))

    def test_list_tenants(self):
        self.tm.create_tenant("A")
        self.tm.create_tenant("B")
        self.tm.create_tenant("C")
        self.assertEqual(len(self.tm.list_tenants()), 3)

    def test_set_max_users(self):
        tenant = self.tm.create_tenant("Test")
        self.tm.set_max_users(tenant.id, 50)
        self.assertEqual(self.tm.get_tenant(tenant.id).max_users, 50)

    def test_set_max_users_nonexistent_raises(self):
        with self.assertRaises(EnterpriseError):
            self.tm.set_max_users("invalid", 50)

    def test_set_max_storage(self):
        tenant = self.tm.create_tenant("Test")
        self.tm.set_max_storage(tenant.id, 100)
        self.assertEqual(self.tm.get_tenant(tenant.id).max_storage_gb, 100)

    def test_set_max_storage_nonexistent_raises(self):
        with self.assertRaises(EnterpriseError):
            self.tm.set_max_storage("invalid", 100)

    def test_get_usage_returns_dict(self):
        tenant = self.tm.create_tenant("Test")
        usage = self.tm.get_usage(tenant.id)
        self.assertIn("user_count", usage)
        self.assertIn("storage_gb", usage)
        self.assertIn("api_calls", usage)
        self.assertIn("tenant_id", usage)
        self.assertEqual(usage["user_count"], 0)

    def test_get_usage_nonexistent_raises(self):
        with self.assertRaises(EnterpriseError):
            self.tm.get_usage("invalid")


class TestMotor(unittest.TestCase):
    def test_set_speed_get_speed(self):
        motor = Motor(channel=0)
        motor.set_speed(0.75)
        self.assertEqual(motor.get_speed(), 0.75)

    def test_set_speed_out_of_range_raises(self):
        motor = Motor(channel=0)
        with self.assertRaises(RoboticsError):
            motor.set_speed(1.5)

    def test_set_speed_negative(self):
        motor = Motor(channel=1)
        motor.set_speed(-0.5)
        self.assertEqual(motor.get_speed(), -0.5)

    def test_stop_sets_speed_to_zero(self):
        motor = Motor(channel=0)
        motor.set_speed(0.8)
        motor.stop()
        self.assertEqual(motor.get_speed(), 0.0)

    def test_is_running_true_when_moving(self):
        motor = Motor(channel=0)
        motor.set_speed(0.5)
        self.assertTrue(motor.is_running())

    def test_is_running_false_when_stopped(self):
        motor = Motor(channel=0)
        motor.stop()
        self.assertFalse(motor.is_running())

    def test_is_running_threshold(self):
        motor = Motor(channel=0)
        motor.set_speed(0.0005)
        self.assertFalse(motor.is_running())

    def test_channel_assignment(self):
        motor = Motor(channel=5)
        self.assertEqual(motor.channel, 5)


class TestSensors(unittest.TestCase):
    def test_ultrasonic_read_returns_float(self):
        sensor = UltrasonicSensor(trigger_pin=2, echo_pin=3)
        value = sensor.read()
        self.assertIsInstance(value, float)
        self.assertGreaterEqual(value, 2.0)

    def test_ultrasonic_calibrate(self):
        sensor = UltrasonicSensor(trigger_pin=2, echo_pin=3)
        sensor.calibrate()
        self.assertTrue(sensor.is_calibrated())

    def test_temperature_read_returns_float(self):
        sensor = TemperatureSensor(pin=5)
        value = sensor.read()
        self.assertIsInstance(value, float)

    def test_gyroscope_read_returns_float_magnitude(self):
        sensor = Gyroscope()
        value = sensor.read()
        self.assertIsInstance(value, float)
        self.assertGreaterEqual(value, 0.0)

    def test_gyroscope_get_value_returns_dict(self):
        sensor = Gyroscope()
        result = sensor.get_value()
        self.assertEqual(len(result), 3)

    def test_gps_read_returns_tuple(self):
        gps = GPSModule()
        lat, lng, alt = gps.read()
        self.assertIsInstance(lat, float)
        self.assertIsInstance(lng, float)
        self.assertIsInstance(alt, float)

    def test_gps_get_value_returns_dict(self):
        gps = GPSModule()
        result = gps.get_value()
        self.assertIn("latitude", result)
        self.assertIn("longitude", result)
        self.assertIn("altitude", result)

    def test_gps_base_coordinates(self):
        gps = GPSModule()
        self.assertEqual(gps._base_lat, 37.7749)
        self.assertEqual(gps._base_lng, -122.4194)

    def test_sensor_get_value_fallback(self):
        sensor = UltrasonicSensor(2, 3)
        value = sensor.get_value()
        self.assertIsInstance(value, float)


class TestServo(unittest.TestCase):
    def test_set_angle_get_angle(self):
        servo = Servo(pin=9)
        servo.set_angle(45.0)
        self.assertEqual(servo.get_angle(), 45.0)

    def test_default_angle(self):
        servo = Servo(pin=9)
        self.assertEqual(servo.get_angle(), 90.0)

    def test_angle_clamped_0_180(self):
        servo = Servo(pin=9)
        with self.assertRaises(RoboticsError):
            servo.set_angle(-1)
        with self.assertRaises(RoboticsError):
            servo.set_angle(181)

    def test_sweep_changes_angle(self):
        servo = Servo(pin=9)
        servo.sweep(0, 180)
        self.assertAlmostEqual(servo.get_angle(), 180, delta=1)

    def test_sweep_invalid_range_raises(self):
        servo = Servo(pin=9)
        with self.assertRaises(RoboticsError):
            servo.sweep(-10, 90)

    def test_sweep_reverse(self):
        servo = Servo(pin=9)
        servo.set_angle(180)
        servo.sweep(180, 0)
        self.assertAlmostEqual(servo.get_angle(), 0, delta=1)

    def test_pin_assignment(self):
        servo = Servo(pin=7)
        self.assertEqual(servo.pin, 7)


class TestRobotController(unittest.TestCase):
    def setUp(self):
        self.robot = RobotController("test_bot")
        self.m1 = Motor(channel=0)
        self.m2 = Motor(channel=1)
        self.robot.add_motor(self.m1)
        self.robot.add_motor(self.m2)

    def test_add_motor(self):
        self.assertEqual(len(self.robot.motors), 2)

    def test_add_sensor(self):
        sensor = UltrasonicSensor(2, 3)
        self.robot.add_sensor(sensor)
        self.assertIn(sensor, self.robot.sensors)

    def test_add_servo(self):
        servo = Servo(pin=9)
        self.robot.add_servo(servo)
        self.assertIn(servo, self.robot.servos)

    def test_drive_sets_motor_speeds(self):
        self.robot.drive(0.5, -0.3)
        self.assertEqual(self.m1.get_speed(), 0.5)
        self.assertEqual(self.m2.get_speed(), -0.3)

    def test_drive_insufficient_motors_raises(self):
        solo = RobotController("solo")
        solo.add_motor(Motor(0))
        with self.assertRaises(RoboticsError):
            solo.drive(0.5, 0.5)

    def test_forward(self):
        self.robot.forward(0.7)
        self.assertEqual(self.m1.get_speed(), 0.7)
        self.assertEqual(self.m2.get_speed(), 0.7)

    def test_backward(self):
        self.robot.backward(0.6)
        self.assertEqual(self.m1.get_speed(), -0.6)
        self.assertEqual(self.m2.get_speed(), -0.6)

    def test_turn_left(self):
        self.robot.turn_left(0.4)
        self.assertEqual(self.m1.get_speed(), -0.4)
        self.assertEqual(self.m2.get_speed(), 0.4)

    def test_turn_right(self):
        self.robot.turn_right(0.4)
        self.assertEqual(self.m1.get_speed(), 0.4)
        self.assertEqual(self.m2.get_speed(), -0.4)

    def test_stop_all_resets_motors(self):
        self.robot.drive(0.8, 0.8)
        self.robot.stop_all()
        self.assertEqual(self.m1.get_speed(), 0.0)
        self.assertEqual(self.m2.get_speed(), 0.0)

    def test_read_all_sensors_returns_dict(self):
        sensor = UltrasonicSensor(2, 3)
        self.robot.add_sensor(sensor)
        data = self.robot.read_all_sensors()
        self.assertIn(sensor.name, data)
        self.assertIsInstance(data[sensor.name], float)

    def test_execute_sequence_runs_commands(self):
        commands = [
            {"action": "forward", "speed": 0.5},
            {"action": "turn_left", "speed": 0.3},
        ]
        self.robot.execute_sequence(commands)
        self.assertEqual(self.m1.get_speed(), -0.3)

    def test_execute_sequence_unknown_action_raises(self):
        with self.assertRaises(RoboticsError):
            self.robot.execute_sequence([{"action": "fly"}])


    def test_get_state_returns_full_state(self):
        sensor = UltrasonicSensor(2, 3)
        servo = Servo(pin=9)
        self.robot.add_sensor(sensor)
        self.robot.add_servo(servo)
        state = self.robot.get_state()
        self.assertEqual(state["name"], "test_bot")
        self.assertEqual(len(state["motors"]), 2)
        self.assertEqual(state["sensor_count"], 1)
        self.assertEqual(state["servo_count"], 1)


class TestDroneController(unittest.TestCase):
    def setUp(self):
        self.drone = DroneController("quad")

    def test_arm(self):
        self.drone.arm()
        self.assertTrue(self.drone._armed)

    def test_arm_low_battery_raises(self):
        self.drone._battery = 5.0
        with self.assertRaises(RoboticsError):
            self.drone.arm()

    def test_disarm(self):
        self.drone.arm()
        self.drone.disarm()
        self.assertFalse(self.drone._armed)

    def test_takeoff(self):
        self.drone.arm()
        self.drone.takeoff(height=2.5)
        self.assertEqual(self.drone.get_altitude(), 2.5)

    def test_takeoff_not_armed_raises(self):
        with self.assertRaises(RoboticsError):
            self.drone.takeoff()

    def test_land(self):
        self.drone.arm()
        self.drone.takeoff(2.0)
        self.drone.land()
        self.assertEqual(self.drone.get_altitude(), 0.0)
        self.assertFalse(self.drone._armed)

    def test_hover(self):
        self.drone.arm()
        self.drone.takeoff(1.0)
        self.drone.hover(0.01)
        self.assertGreater(self.drone.get_altitude(), 0)

    def test_hover_on_ground_raises(self):
        with self.assertRaises(RoboticsError):
            self.drone.hover()

    def test_move_changes_position(self):
        self.drone.arm()
        self.drone.move(1.0, 2.0, 1.0)
        self.assertEqual(self.drone._position["x"], 1.0)
        self.assertEqual(self.drone._position["y"], 2.0)
        self.assertEqual(self.drone._position["z"], 1.0)

    def test_move_not_armed_raises(self):
        with self.assertRaises(RoboticsError):
            self.drone.move(1, 1, 1)

    def test_get_altitude(self):
        self.assertEqual(self.drone.get_altitude(), 0.0)

    def test_get_battery_returns_percentage(self):
        self.drone._battery = 50.0
        level = self.drone.get_battery()
        self.assertEqual(level, 50.0)  # first call drains 0.01, round(49.99,1)=50.0

    def test_get_battery_never_below_zero(self):
        self.drone._battery = 0.5
        for _ in range(100):
            self.drone.get_battery()
        self.assertGreaterEqual(self.drone._battery, 0.0)

    def test_return_to_launch(self):
        self.drone.arm()
        self.drone.takeoff(5.0)
        self.drone.return_to_launch()
        self.assertEqual(self.drone._position, {"x": 0.0, "y": 0.0, "z": 0.0})
        self.assertEqual(self.drone.get_altitude(), 0.0)

    def test_rotate(self):
        self.drone.rotate(90.0)
        self.assertEqual(self.drone._yaw, 90.0)

    def test_rotate_wraps(self):
        self.drone.rotate(400.0)
        self.assertEqual(self.drone._yaw, 40.0)

    def test_flip_forward(self):
        self.drone.arm()
        self.drone.takeoff(1.0)
        self.drone.flip("forward")

    def test_flip_low_altitude_raises(self):
        self.drone.arm()
        with self.assertRaises(RoboticsError):
            self.drone.flip("forward")

    def test_flip_invalid_direction_raises(self):
        self.drone.arm()
        self.drone.takeoff(1.0)
        with self.assertRaises(RoboticsError):
            self.drone.flip("sideways")


class TestSimulationEnvironment(unittest.TestCase):
    def setUp(self):
        self.robot = RobotController("sim_bot")
        self.robot.add_motor(Motor(0))
        self.robot.add_motor(Motor(1))
        self.sim = SimulationEnvironment(self.robot)

    def test_start(self):
        self.sim.start()
        self.assertTrue(self.sim._running)

    def test_stop(self):
        self.sim.start()
        self.sim.stop()
        self.assertFalse(self.sim._running)

    def test_set_obstacles(self):
        obs = [{"x": 1.0, "y": 2.0, "radius": 0.5}]
        self.sim.set_obstacles(obs)
        self.assertEqual(len(self.sim._obstacles), 1)

    def test_step_advances_time(self):
        self.sim.start()
        self.sim.step(dt=0.5)
        self.assertEqual(self.sim._time, 0.5)

    def test_step_not_running(self):
        self.sim.step()
        self.assertEqual(self.sim._time, 0.0)

    def test_reset_clears_state(self):
        self.sim.start()
        self.sim.step(1.0)
        self.sim.reset()
        self.assertEqual(self.sim._time, 0.0)
        self.assertFalse(self.sim._running)

    def test_reset_stops_motors(self):
        self.robot.forward(0.8)
        self.sim.reset()
        self.assertEqual(self.robot.motors[0].get_speed(), 0.0)
        self.assertEqual(self.robot.motors[1].get_speed(), 0.0)

    def test_get_simulated_sensor_data(self):
        sensor = UltrasonicSensor(2, 3)
        self.robot.add_sensor(sensor)
        data = self.sim.get_simulated_sensor_data()
        self.assertIn(sensor.name, data)

    def test_drone_auto_land_on_low_battery(self):
        drone = DroneController("test_drone")
        drone.add_motor(Motor(0))
        drone.add_motor(Motor(1))
        drone.add_motor(Motor(2))
        drone.add_motor(Motor(3))
        sim = SimulationEnvironment(drone)
        drone.arm()
        drone.takeoff(2.0)
        drone._battery = 4.0
        sim.start()
        sim.step()
        self.assertFalse(sim._running)
        self.assertEqual(drone.get_altitude(), 0.0)


class TestFactoryHelpers(unittest.TestCase):
    def test_create_wheeled_robot(self):
        robot = create_wheeled_robot("wally")
        self.assertIsInstance(robot, RobotController)
        self.assertEqual(robot.name, "wally")
        self.assertEqual(len(robot.motors), 2)
        self.assertEqual(len(robot.sensors), 3)
        self.assertEqual(len(robot.servos), 1)

    def test_create_quadcopter(self):
        drone = create_quadcopter("flyer")
        self.assertIsInstance(drone, DroneController)
        self.assertEqual(drone.name, "flyer")
        self.assertEqual(len(drone.motors), 4)
        self.assertEqual(len(drone.sensors), 4)

    def test_calculate_odometry_returns_position(self):
        result = calculate_odometry(360, 360, 10.0, 20.0)
        self.assertIn("distance", result)
        self.assertIn("rotation", result)
        self.assertIn("left_distance", result)
        self.assertIn("right_distance", result)

    def test_calculate_odometry_straight_line(self):
        result = calculate_odometry(360, 360, 10.0, 20.0)
        expected_distance = math.pi * 10.0
        self.assertAlmostEqual(result["distance"], expected_distance, places=3)
        self.assertAlmostEqual(result["rotation"], 0.0, places=3)

    def test_calculate_odometry_turning(self):
        result = calculate_odometry(360, 0, 10.0, 20.0)
        self.assertGreater(abs(result["rotation"]), 0)


if __name__ == "__main__":
    unittest.main()
