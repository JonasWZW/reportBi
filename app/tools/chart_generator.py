"""图表生成器"""
from abc import ABC, abstractmethod
from typing import Any

from app.schemas.data_part import DataPart, DataPartResult, DataPartState


class ChartRenderer(ABC):
    """图表渲染器基类"""

    @abstractmethod
    def render(self, data: Any, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """渲染图表，返回图表定义"""
        ...


class TableRenderer(ChartRenderer):
    """表格渲染器"""

    def render(self, data: Any, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """渲染表格"""
        options = options or {}

        if not isinstance(data, list):
            data = [data]

        # 提取列名
        if data and isinstance(data[0], dict):
            columns = list(data[0].keys())
        else:
            columns = [f"Column_{i}" for i in range(len(data[0]) if data else 0))]

        return {
            "type": "table",
            "data": data,
            "columns": columns,
            "options": {
                "pagination": options.get("pagination", True),
                "page_size": options.get("page_size", 10),
            }
        }


class BarChartRenderer(ChartRenderer):
    """柱状图渲染器"""

    def render(self, data: Any, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """渲染柱状图"""
        options = options or {}

        # ECharts 配置
        return {
            "type": "bar",
            "echarts_option": {
                "tooltip": {"trigger": "axis"},
                "xAxis": {
                    "type": "category",
                    "data": options.get("x_axis_data", [])
                },
                "yAxis": {"type": "value"},
                "series": [{
                    "type": "bar",
                    "data": options.get("series_data", []),
                    "itemStyle": {
                        "color": options.get("color", "#5470C6")
                    }
                }],
                "title": {
                    "text": options.get("title", ""),
                    "left": "center"
                }
            }
        }


class LineChartRenderer(ChartRenderer):
    """折线图渲染器"""

    def render(self, data: Any, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """渲染折线图"""
        options = options or {}

        return {
            "type": "line",
            "echarts_option": {
                "tooltip": {"trigger": "axis"},
                "xAxis": {
                    "type": "category",
                    "data": options.get("x_axis_data", [])
                },
                "yAxis": {"type": "value"},
                "series": [{
                    "type": "line",
                    "data": options.get("series_data", []),
                    "smooth": options.get("smooth", True),
                    "itemStyle": {
                        "color": options.get("color", "#5470C6")
                    }
                }],
                "title": {
                    "text": options.get("title", ""),
                    "left": "center"
                }
            }
        }


class PieChartRenderer(ChartRenderer):
    """饼图渲染器"""

    def render(self, data: Any, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """渲染饼图"""
        options = options or {}

        return {
            "type": "pie",
            "echarts_option": {
                "tooltip": {"trigger": "item"},
                "legend": {
                    "orient": "vertical",
                    "left": "left"
                },
                "series": [{
                    "type": "pie",
                    "radius": options.get("radius", "50%"),
                    "data": options.get("pie_data", []),
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": "rgba(0, 0, 0, 0.5)"
                        }
                    }
                }],
                "title": {
                    "text": options.get("title", ""),
                    "left": "center"
                }
            }
        }


class ChartGenerator:
    """图表生成器"""

    _renderers: dict[str, ChartRenderer] = {
        "table": TableRenderer(),
        "bar": BarChartRenderer(),
        "line": LineChartRenderer(),
        "pie": PieChartRenderer(),
    }

    @classmethod
    def render(cls, data: Any, result_type: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """根据结果类型渲染图表"""
        renderer = cls._renderers.get(result_type)
        if renderer is None:
            # 默认返回表格
            renderer = cls._renderers["table"]

        return renderer.render(data, options)

    @classmethod
    def register_renderer(cls, result_type: str, renderer: ChartRenderer) -> None:
        """注册新的渲染器"""
        cls._renderers[result_type] = renderer

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """获取支持的图表类型"""
        return list(cls._renderers.keys())
