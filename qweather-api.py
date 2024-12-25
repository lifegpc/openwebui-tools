"""
title: 和风天气
description: 和风天气接口
author: lifegpc
author_url: https://github.com/lifegpc
github: https://git.lifegpc.com/lifegpc/openwebui-tools
requirements: httpx
version: 0.0.1
license: MIT
"""

import json
import httpx
from pydantic import BaseModel, Field
from typing import Any, Callable, Tuple, Union


def dump_json(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


class EventEmitter:
    def __init__(self, event_emitter: Callable[[dict], Any] = None):
        self.event_emitter = event_emitter

    async def progress_update(self, description):
        await self.emit(description)

    async def error_update(self, description):
        await self.emit(description, "error", True)

    async def success_update(self, description):
        await self.emit(description, "success", True)

    async def emit(self, description="Unknown State", status="in_progress", done=False):
        if self.event_emitter:
            await self.event_emitter(
                {
                    "type": "status",
                    "data": {
                        "status": status,
                        "description": description,
                        "done": done,
                    },
                }
            )


class Tools:
    class Valves(BaseModel):
        DEVAPI: bool = Field(False, description="免费订阅请设置成true")
        API_KEY: str = Field("", description="API Key")

    def __init__(self):
        self.valves = self.Valves()

    async def _request(self, method, url, params):
        headers = {'X-QW-Api-Key': self.valves.API_KEY}
        client = httpx.AsyncClient()
        res = await client.request(method, url, params=params, headers=headers)
        data = res.json()
        if 'code' in data and data['code'] != '200':
            raise Exception(f"Failed to process request: {data['code']}.")
        return data

    async def lookupCity(self, location: Union[str, Tuple[float, float]],
                         number: int = 10,
                         __event_emitter__: Callable[[dict], Any] = None):
        """
        搜索城市
        `location` - 需要查询地区的名称，支持文字或者经纬度（最多支持小数点后两位）
        `number` - 返回结果的数量，取值范围1-20
        """
        emitter = EventEmitter(__event_emitter__)

        if isinstance(location, tuple):
            location = f"{round(location[0], 2)},{round(location[1], 2)}"
        await emitter.progress_update("搜索城市……")
        try:
            data = await self._request(
                "GET",
                "https://geoapi.qweather.com/v2/city/lookup",
                {
                    "location": location,
                    "number": number,
                },
            )
            await emitter.success_update("搜索城市成功")
            return dump_json(data)
        except Exception as e:
            errmsg = f"搜索城市失败：{e}"
            await emitter.error_update(errmsg)
            return errmsg

    async def getWeatherNow(self, location: Union[str, Tuple[float, float]],
                            unit: str = 'm',
                            __event_emitter__: Callable[[dict], Any] = None):
        """
        获取实时天气
        `location` - 需要查询地区的LocationID或经纬度（最多支持小数点后两位），LocationID可通过搜索城市得到
        `unit` - 单位选择，m为公制，i为英制
        """
        emitter = EventEmitter(__event_emitter__)

        if isinstance(location, tuple):
            location = f"{round(location[0], 2)},{round(location[1], 2)}"
        prefix = 'devapi' if self.valves.DEVAPI else 'api'
        await emitter.progress_update("获取实时天气……")
        try:
            data = await self._request(
                "GET",
                f"https://{prefix}.qweather.com/v7/weather/now",
                {
                    "location": location,
                    "unit": unit,
                },
            )
            await emitter.success_update("获取实时天气成功")
            return dump_json(data)
        except Exception as e:
            errmsg = f"获取实时天气失败：{e}"
            await emitter.error_update(errmsg)
            return errmsg
