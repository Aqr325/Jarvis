"""
J.A.R.V.I.S. Agent Modules
-------------------------------
Built-in modules for real-world capabilities.
"""

import asyncio
import json
import os
import random
import hashlib
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class WeatherModule:
    """Real weather module integrated with OpenWeatherMap API."""

    def __init__(self):
        self.cache = {}
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.geocode_url = "https://api.openweathermap.org/geo/1.0/direct"

    async def _geocode_city(self, city: str) -> Optional[Dict]:
        """Convert city name to coordinates."""
        if not self.api_key:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                url = (
                    f"{self.geocode_url}"
                    f"?q={city}&limit=1&appid={self.api_key}"
                )
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data:
                            return {"lat": data[0]["lat"], "lon": data[0]["lon"], "name": data[0]["name"]}
        except Exception:
            return None
        return None

    async def _fetch_from_api(self, city_or_coords: Dict) -> Optional[Dict]:
        """Fetch real weather data from OpenWeatherMap."""
        if not self.api_key:
            return None
        try:
            if "lat" in city_or_coords:
                url = (
                    f"{self.base_url}/weather"
                    f"?lat={city_or_coords['lat']}"
                    f"&lon={city_or_coords['lon']}"
                    f"&units=metric"
                    f"&lang=zh_cn"
                    f"&appid={self.api_key}"
                )
            else:
                url = (
                    f"{self.base_url}/weather"
                    f"?q={city_or_coords['name']}"
                    f"&units=metric"
                    f"&lang=zh_cn"
                    f"&appid={self.api_key}"
                )
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception:
            return None
        return None

    async def get_weather(self, city: str) -> Dict[str, Any]:
        """Get real weather for a city. Falls back to simulation if no API key."""
        if city in self.cache:
            return self.cache[city]

        result = None

        # Try to fetch real weather
        if self.api_key:
            coords = await self._geocode_city(city)
            if coords:
                result = await self._fetch_from_api(coords)

        # Fallback: simulate if API failed
        if not result:
            conditions = ["晴", "多云", "阴", "小雨", "雷阵雨", "雾霾"]
            temp = random.uniform(10, 35)
            humidity = random.uniform(30, 90)
            result = {
                "city": city,
                "temperature": round(temp, 1),
                "humidity": round(humidity, 1),
                "condition": random.choice(conditions),
                "aqi": random.randint(20, 200),
                "forecast": [
                    {"day": "明天", "high": round(temp + 2), "low": round(temp - 5)},
                    {"day": "后天", "high": round(temp + 1), "low": round(temp - 3)},
                ],
                "_mode": "simulated" if self.api_key else "demo (no API key)",
            }
        else:
            # Parse real API response
            result = {
                "city": result.get("name", city),
                "temperature": result.get("main", {}).get("temp", 0),
                "feels_like": result.get("main", {}).get("feels_like", 0),
                "humidity": result.get("main", {}).get("humidity", 0),
                "pressure": result.get("main", {}).get("pressure", 0),
                "wind_speed": result.get("wind", {}).get("speed", 0),
                "condition": result.get("weather", [{}])[0].get("description", ""),
                "condition_cn": result.get("weather", [{}])[0].get("main", ""),
                "aqi": "N/A",
                "icon": result.get("weather", [{}])[0].get("icon", ""),
                "forecast": [],
                "_mode": "real",
            }

        self.cache[city] = result
        return result


class DataAnalysisModule:
    """Basic data analysis and statistics module."""

    def __init__(self):
        self.datasets: Dict[str, List[float]] = {}

    def register_dataset(self, name: str, data: List[float]):
        self.datasets[name] = data

    async def analyze(self, dataset_name: str) -> Dict[str, Any]:
        data = self.datasets.get(dataset_name)
        if not data:
            return {"error": f"Dataset '{dataset_name}' not found"}

        sorted_data = sorted(data)
        n = len(data)
        result = {
            "name": dataset_name,
            "count": n,
            "mean": round(sum(data) / n, 2),
            "median": round(sorted_data[n // 2], 2) if n % 2 == 1 else round((sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2, 2),
            "std_dev": round((sum((x - sum(data) / n) ** 2 for x in data) / n) ** 0.5, 2),
            "min": min(data),
            "max": max(data),
        }
        return result

    async def generate_sample(self, name: str, n: int = 100) -> dict:
        data = [random.gauss(50, 15) for _ in range(n)]
        self.register_dataset(name, data)
        return {"status": "generated", "name": name, "size": n}


class SchedulerModule:
    """Task scheduling and reminder module."""

    def __init__(self):
        self.tasks: List[Dict[str, Any]] = []
        self.reminders: List[Dict[str, Any]] = []

    async def create_task(self, title: str, due_date: str, priority: str = "medium") -> Dict[str, Any]:
        task = {
            "id": hashlib.md5(f"{title}{datetime.now()}".encode()).hexdigest()[:8],
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        self.tasks.append(task)
        return task

    async def list_tasks(self, status: str = None) -> List[Dict[str, Any]]:
        if status:
            return [t for t in self.tasks if t["status"] == status]
        return self.tasks

    async def set_reminder(self, message: str, delay_seconds: int = 5) -> Dict[str, Any]:
        reminder = {
            "id": hashlib.md5(f"{message}{datetime.now()}".encode()).hexdigest()[:8],
            "message": message,
            "triggered": False,
        }
        self.reminders.append(reminder)

        async def trigger():
            await asyncio.sleep(delay_seconds)
            reminder["triggered"] = True

        asyncio.create_task(trigger())
        return reminder

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "total_tasks": len(self.tasks),
            "pending": sum(1 for t in self.tasks if t["status"] == "pending"),
            "completed": sum(1 for t in self.tasks if t["status"] == "completed"),
            "reminders_pending": sum(1 for r in self.reminders if not r["triggered"]),
        }


class FileModule:
    """Basic file operations module."""

    async def create_file(self, path: str, content: str = "") -> Dict[str, Any]:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "created", "path": path, "size": len(content)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def read_file(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"status": "success", "path": path, "content": content, "lines": content.count("\n") + 1}
        except FileNotFoundError:
            return {"status": "error", "message": f"File not found: {path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def list_directory(self, path: str) -> Dict[str, Any]:
        import os
        try:
            entries = os.listdir(path)
            return {"status": "success", "path": path, "entries": entries, "count": len(entries)}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class ReportModule:
    """Report generation module."""

    async def generate_report(self, title: str, sections: List[Dict[str, str]]) -> Dict[str, Any]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        report = {
            "title": title,
            "generated_at": now,
            "sections": sections,
            "section_count": len(sections),
            "id": hashlib.md5(f"{title}{now}".encode()).hexdigest()[:8],
        }
        return report

    async def export_csv(self, data: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        import csv
        import io
        try:
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            return {
                "status": "success",
                "filename": filename,
                "size": len(output.getvalue()),
                "preview": output.getvalue()[:500],
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
