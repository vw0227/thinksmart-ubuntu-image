"""Offline regression checks; run with the gateway's existing Python environment."""
import asyncio
import importlib
import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

ROOT = os.environ.get("THINKSMART_HUB_ROOT", "/home/ubuntu/xiaozhi-hub-server/main/xiaozhi-server")
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import config.logger as logging_config
from loguru import logger

logger.remove()
logging_config._logger_initialized = True
PATCH_DIR = os.environ.get("THINKSMART_PATCH_DIR")
if PATCH_DIR:
    for name, filename in [("core.utils.open_meteo_weather", "open_meteo_weather.py"), ("core.providers.tts.edge", "edge.py"), ("plugins_func.functions.get_weather", "get_weather.py"), ("core.providers.llm.openai.openai", "openai_provider.py")]:
        spec = importlib.util.spec_from_file_location(name, os.path.join(PATCH_DIR, filename))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
edge = importlib.import_module("core.providers.tts.edge")
weather = importlib.import_module("plugins_func.functions.get_weather")
llm_module = importlib.import_module("core.providers.llm.openai.openai")


class VoiceToolsTests(unittest.IsolatedAsyncioTestCase):
    def test_explicit_weather_uses_required_tool(self):
        class EmptyStream:
            def __iter__(self):
                return iter(())

            def close(self):
                pass

        with patch.object(llm_module.openai, "OpenAI") as client:
            client.return_value.chat.completions.create.return_value = EmptyStream()
            provider = llm_module.LLMProvider({"api_key": "unit-test-placeholder", "base_url": "https://example.invalid/v1", "model_name": "test", "weather_tool_first": True})
            list(provider.response_with_functions("test", [{"role": "user", "content": "北京明天天气怎么样"}], [weather.GET_WEATHER_FUNCTION_DESC]))
            self.assertEqual(client.return_value.chat.completions.create.call_args.kwargs.get("tool_choice"), {"type": "function", "function": {"name": "get_weather"}})

    def test_weather_routing_does_not_force_unrelated_or_recursive_calls(self):
        class EmptyStream:
            def __iter__(self):
                return iter(())

            def close(self):
                pass

        cases = [
            ([{"role": "user", "content": "给我一条新闻"}], [weather.GET_WEATHER_FUNCTION_DESC], True),
            ([{"role": "user", "content": "为什么不能查天气"}], [weather.GET_WEATHER_FUNCTION_DESC], True),
            ([{"role": "user", "content": "不要查明天天气"}], [weather.GET_WEATHER_FUNCTION_DESC], True),
            ([{"role": "tool", "content": "天气数据"}], [weather.GET_WEATHER_FUNCTION_DESC], True),
            ([{"role": "user", "content": "北京明天天气怎么样"}], [], True),
            ([{"role": "user", "content": "北京明天天气怎么样"}], [weather.GET_WEATHER_FUNCTION_DESC], False),
        ]
        for dialogue, functions, enabled in cases:
            with self.subTest(dialogue=dialogue, enabled=enabled), patch.object(llm_module.openai, "OpenAI") as client:
                client.return_value.chat.completions.create.return_value = EmptyStream()
                provider = llm_module.LLMProvider({"api_key": "unit-test-placeholder", "base_url": "https://example.invalid/v1", "model_name": "test", "weather_tool_first": enabled})
                list(provider.response_with_functions("test", dialogue, functions))
                self.assertNotIn("tool_choice", client.return_value.chat.completions.create.call_args.kwargs)

    async def test_edge_passes_proxy_and_timeouts(self):
        seen = {}

        class FakeCommunicate:
            def __init__(self, text, **kwargs):
                seen.update(kwargs)

            async def stream(self):
                yield {"type": "audio", "data": b"mp3"}

        provider = edge.TTSProvider({"voice": "zh-CN-XiaoxiaoNeural", "proxy": "http://127.0.0.1:18080", "connect_timeout": 4, "receive_timeout": 8}, True)
        with patch.object(edge.edge_tts, "Communicate", FakeCommunicate):
            self.assertEqual(await provider.text_to_speak("测试", None), b"mp3")
        self.assertEqual(seen.get("proxy"), "http://127.0.0.1:18080")
        self.assertEqual(seen.get("connect_timeout"), 4)
        self.assertEqual(seen.get("receive_timeout"), 8)

    async def test_keyless_weather_uses_default_city_not_ip(self):
        conn = types.SimpleNamespace(config={"plugins": {"get_weather": {"provider": "open_meteo", "default_location": "北京"}}}, client_ip="127.0.0.1")
        fake = AsyncMock(return_value="您查询的位置是：北京\n当前天气: 晴\n数据来源：Open-Meteo")
        with patch.object(weather, "fetch_open_meteo_report", fake, create=True), patch.object(weather, "get_ip_info", side_effect=AssertionError("must not geolocate")):
            result = await weather.get_weather(conn)
        self.assertIn("Open-Meteo", result.result)
        fake.assert_awaited_once_with("北京")

    async def test_keyless_failure_does_not_claim_city_missing(self):
        conn = types.SimpleNamespace(config={"plugins": {"get_weather": {"provider": "open_meteo", "default_location": "北京"}}}, client_ip=None)
        with patch.object(weather, "fetch_open_meteo_report", AsyncMock(side_effect=TimeoutError()), create=True), patch.object(weather, "fetch_city_info", AsyncMock(return_value=None)):
            result = await weather.get_weather(conn, location="测试超时城市")
        self.assertIn("暂时无法获取", result.result)
        self.assertNotIn("未找到相关的城市", result.result)

    def test_local_weather_tool_not_forbidden(self):
        desc = weather.GET_WEATHER_FUNCTION_DESC["function"]["description"]
        self.assertNotIn("绝对不要调用", desc)

    def weather_fixture(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        return {"utc_offset_seconds": 28800, "timezone": "Asia/Shanghai", "current": {"time": now.isoformat(timespec="minutes"), "temperature_2m": 10, "apparent_temperature": 8, "weather_code": 0, "relative_humidity_2m": 45, "wind_speed_10m": 8}, "daily": {"time": [now.date().isoformat()], "weather_code": [0], "temperature_2m_min": [5], "temperature_2m_max": [15], "precipitation_probability_max": [0]}}

    def test_weather_report_has_units_time_source(self):
        from core.utils.open_meteo_weather import format_report
        text = format_report("北京", self.weather_fixture())
        for marker in ["北京", "10℃", "数据有效时间", "Open-Meteo", "非现场气象站实测"]:
            self.assertIn(marker, text)

    def test_stale_weather_rejected(self):
        from core.utils.open_meteo_weather import format_report
        fixture = self.weather_fixture()
        fixture["current"]["time"] = "2000-01-01T00:00"
        with self.assertRaises(ValueError):
            format_report("北京", fixture)

    def test_missing_forecast_rejected(self):
        from core.utils.open_meteo_weather import format_report
        fixture = self.weather_fixture()
        fixture["daily"]["temperature_2m_min"] = [None]
        with self.assertRaises(ValueError):
            format_report("北京", fixture)


if __name__ == "__main__":
    unittest.main(verbosity=2)
