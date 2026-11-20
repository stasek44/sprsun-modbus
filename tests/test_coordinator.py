"""Unit tests for SPRSUNDataUpdateCoordinator."""
import time
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from tests.conftest import setup_mocks
setup_mocks()

from custom_components.sprsun_modbus import SPRSUNDataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed


class TestSPRSUNCoordinator(unittest.IsolatedAsyncioTestCase):
    """Test suite for SPRSUNDataUpdateCoordinator."""

    def setUp(self):
        """Set up coordinator test fixtures."""
        self.hass = MagicMock()
        async def async_add_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)
        self.hass.async_add_executor_job = async_add_executor_job

        self.coordinator = SPRSUNDataUpdateCoordinator(
            hass=self.hass,
            host="192.168.1.100",
            port=502,
            device_address=1,
            scan_interval=10,
            controller_type="chico",
        )

    def test_init_properties(self):
        """Test coordinator initialization attributes."""
        self.assertEqual(self.coordinator.host, "192.168.1.100")
        self.assertEqual(self.coordinator.port, 502)
        self.assertEqual(self.coordinator.device_address, 1)
        self.assertEqual(self.coordinator.controller_type, "chico")
        self.assertEqual(self.coordinator.cache_staleness_seconds, 20)  # 2 * scan_interval
        self.assertEqual(self.coordinator.controller.name, "CHICO")

    def test_create_and_close_modbus_client(self):
        """Test creating and safely closing modbus client."""
        client = self.coordinator._create_modbus_client()
        self.assertEqual(client.host, "192.168.1.100")
        self.assertEqual(client.port, 502)

        self.coordinator.client = client
        self.coordinator._close_client()
        self.assertIsNone(self.coordinator.client)

    def test_ensure_connection_already_connected(self):
        """Test _ensure_connection returns True if client already connected."""
        client = MagicMock()
        client.connected = True
        self.coordinator.client = client
        self.assertTrue(self.coordinator._ensure_connection())
        client.connect.assert_not_called()

    def test_ensure_connection_reconnect_success(self):
        """Test _ensure_connection reconnects when client disconnected."""
        client = MagicMock()
        client.connected = False
        client.connect.return_value = True
        self.coordinator.client = client
        self.assertTrue(self.coordinator._ensure_connection())
        client.connect.assert_called_once()

    def test_ensure_connection_failure(self):
        """Test _ensure_connection returns False when reconnect fails."""
        client = MagicMock()
        client.connected = False
        client.connect.return_value = False
        self.coordinator.client = client
        self.assertFalse(self.coordinator._ensure_connection())
        self.assertIsNone(self.coordinator.client)

    def test_ensure_connection_exception(self):
        """Test _ensure_connection handles exceptions gracefully."""
        client = MagicMock()
        client.connected = False
        client.connect.side_effect = OSError("Network unreachable")
        self.coordinator.client = client
        self.assertFalse(self.coordinator._ensure_connection())
        self.assertIsNone(self.coordinator.client)

    def test_sync_update_success_and_caching(self):
        """Test _sync_update populates cache with timestamps."""
        client = MagicMock()
        client.connected = True
        self.coordinator.client = client

        # Mock controller returning fresh registers
        fresh_data = {
            "inlet_temp": 24.5,
            "unit_mode": 3,
            "heating_setpoint": 40.0,
        }
        self.coordinator.controller.read_all_registers = MagicMock(return_value=fresh_data)

        data = self.coordinator._sync_update()
        self.assertIn("inlet_temp", data)
        self.assertEqual(data["inlet_temp"]["value"], 24.5)
        self.assertIsInstance(data["inlet_temp"]["updated_at"], float)
        self.assertEqual(data["unit_mode"]["value"], 3)
        self.assertTrue(self.coordinator._rw_loaded)

    def test_sync_update_cache_staleness_preserves_recent_writes(self):
        """Test recently written values are preserved against revert glitches."""
        client = MagicMock()
        client.connected = True
        self.coordinator.client = client

        now = time.time()
        # Simulated recently written heating setpoint (written 5s ago, staleness is 20s)
        self.coordinator.data = {
            "heating_setpoint": {"value": 42.0, "updated_at": now - 5},
        }

        # Device returns old value (38.0) because hardware hasn't committed/updated yet
        fresh_data = {
            "heating_setpoint": 38.0,
        }
        self.coordinator.controller.read_all_registers = MagicMock(return_value=fresh_data)

        updated_data = self.coordinator._sync_update()
        # Should preserve the cached 42.0 value!
        self.assertEqual(updated_data["heating_setpoint"]["value"], 42.0)

    def test_sync_update_stale_cache_is_overwritten(self):
        """Test stale cached values older than window are overwritten with device values."""
        client = MagicMock()
        client.connected = True
        self.coordinator.client = client

        now = time.time()
        # Cached value written 50s ago (stale, staleness window is 20s)
        self.coordinator.data = {
            "heating_setpoint": {"value": 42.0, "updated_at": now - 50},
        }

        fresh_data = {
            "heating_setpoint": 39.5,
        }
        self.coordinator.controller.read_all_registers = MagicMock(return_value=fresh_data)

        updated_data = self.coordinator._sync_update()
        # Should use the fresh device reading
        self.assertEqual(updated_data["heating_setpoint"]["value"], 39.5)

    def test_sync_update_connection_failure_raises(self):
        """Test _sync_update raises UpdateFailed when connection fails."""
        client = MagicMock()
        client.connected = False
        client.connect.return_value = False
        self.coordinator.client = client

        with patch("time.sleep"):  # Speed up retry delay
            with self.assertRaises(UpdateFailed):
                self.coordinator._sync_update()

    def test_sync_write_register_success(self):
        """Test _sync_write_register writes and updates cached timestamp."""
        client = MagicMock()
        client.connected = True
        res_write = MagicMock(isError=lambda: False)
        client.write_register.return_value = res_write

        self.coordinator.client = client
        self.coordinator.data = {}

        success = self.coordinator._sync_write_register(
            address=0x00CC,
            value=76,  # 38.0 * 2
            key="heating_setpoint",
            scale=2,
        )

        self.assertTrue(success)
        client.write_register.assert_called_once_with(
            address=0x00CC, value=76, device_id=1
        )
        self.assertIn("heating_setpoint", self.coordinator.data)
        self.assertEqual(self.coordinator.data["heating_setpoint"]["value"], 38.0)
        self.assertAlmostEqual(self.coordinator.data["heating_setpoint"]["updated_at"], time.time(), delta=2)

    def test_sync_write_register_retry_on_disconnect(self):
        """Test _sync_write_register retries once if write error occurs."""
        client = MagicMock()
        client.connected = True

        # First write fails, second succeeds after reconnect
        res_err = MagicMock(isError=lambda: True)
        res_ok = MagicMock(isError=lambda: False)

        def mock_connect():
            client.connected = True
            return True

        client.connect.side_effect = mock_connect
        client.write_register.side_effect = [res_err, res_ok]

        self.coordinator._create_modbus_client = MagicMock(return_value=client)
        self.coordinator.client = client
        self.coordinator.data = {}

        with patch("time.sleep"):
            success = self.coordinator._sync_write_register(
                address=0x00CC, value=80, key="heating_setpoint", scale=2
            )
        self.assertTrue(success)
        self.assertEqual(client.write_register.call_count, 2)

    def test_sync_write_register_fails_after_retry(self):
        """Test _sync_write_register raises ValueError if retry also fails."""
        client = MagicMock()
        client.connected = True
        res_err = MagicMock(isError=lambda: True)
        client.write_register.return_value = res_err
        client.connect.return_value = True

        self.coordinator._create_modbus_client = MagicMock(return_value=client)
        self.coordinator.client = client

        with patch("time.sleep"):
            with self.assertRaises(ValueError):
                self.coordinator._sync_write_register(
                    address=0x9999, value=1, key="invalid_reg", scale=1
                )

    def test_sync_write_bit_success(self):
        """Test atomic bit modification in _sync_write_bit."""
        client = MagicMock()
        client.connected = True

        # Read returns current value 0b00000000 (bit 0 is 0)
        read_res = MagicMock(isError=lambda: False, registers=[0b00000000])
        client.read_holding_registers.return_value = read_res
        write_res = MagicMock(isError=lambda: False)
        client.write_register.return_value = write_res

        self.coordinator.client = client
        self.coordinator.data = {}

        # Set bit 0 to True on address 0x0032
        success = self.coordinator._sync_write_bit(
            address=0x0032,
            bit=0,
            value=True,
            reg_key="_control_0032"
        )

        self.assertTrue(success)
        client.write_register.assert_called_once_with(
            address=0x0032,
            value=1,  # 0b00000001
            device_id=1
        )
        self.assertEqual(self.coordinator.data["_control_0032"]["value"], 1)

    async def test_async_write_register(self):
        """Test async wrapper applies scaling factor and updates data."""
        self.coordinator._sync_write_register = MagicMock(return_value=True)

        await self.coordinator.async_write_register(
            address=0x00CC,
            value=45.5,
            key="heating_setpoint",
            scale=2,  # 45.5 * 2 = 91
        )

        self.coordinator._sync_write_register.assert_called_once_with(
            0x00CC, 91, "heating_setpoint", 2
        )

    async def test_async_write_bit(self):
        """Test async wrapper for bit writes."""
        self.coordinator._sync_write_bit = MagicMock(return_value=True)

        await self.coordinator.async_write_bit(
            address=0x0032,
            bit=0,
            value=True,
            reg_key="_control_0032"
        )

        self.coordinator._sync_write_bit.assert_called_once_with(
            0x0032, 0, True, "_control_0032"
        )

    async def test_async_shutdown(self):
        """Test coordinator shutdown closes client socket."""
        client = MagicMock()
        self.coordinator.client = client

        await self.coordinator.async_shutdown()
        client.close.assert_called_once()
        self.assertIsNone(self.coordinator.client)


if __name__ == "__main__":
    unittest.main()
