"""图表生成器测试"""
import pytest

from app.tools.chart_generator import (
    ChartGenerator,
    TableRenderer,
    BarChartRenderer,
    LineChartRenderer,
    PieChartRenderer,
)


class TestChartGenerator:
    """图表生成器测试"""

    def test_table_renderer(self):
        """测试表格渲染"""
        data = [
            {"name": "资产1", "attacks": 100},
            {"name": "资产2", "attacks": 80},
        ]
        renderer = TableRenderer()
        result = renderer.render(data)

        assert result["type"] == "table"
        assert len(result["data"]) == 2
        assert "columns" in result

    def test_bar_chart_renderer(self):
        """测试柱状图渲染"""
        data = [
            {"category": "类型A", "count": 100},
            {"category": "类型B", "count": 80},
        ]
        renderer = BarChartRenderer()
        result = renderer.render(
            data,
            options={
                "x_axis_data": ["类型A", "类型B"],
                "series_data": [100, 80],
            }
        )

        assert result["type"] == "bar"
        assert "echarts_option" in result

    def test_line_chart_renderer(self):
        """测试折线图渲染"""
        renderer = LineChartRenderer()
        result = renderer.render(
            [],
            options={
                "x_axis_data": ["周一", "周二", "周三"],
                "series_data": [10, 20, 15],
            }
        )

        assert result["type"] == "line"
        assert "echarts_option" in result

    def test_pie_chart_renderer(self):
        """测试饼图渲染"""
        renderer = PieChartRenderer()
        result = renderer.render(
            [],
            options={
                "pie_data": [
                    {"name": "类型A", "value": 100},
                    {"name": "类型B", "value": 80},
                ],
            }
        )

        assert result["type"] == "pie"
        assert "echarts_option" in result

    def test_chart_generator_render(self):
        """测试图表生成器"""
        data = [{"a": 1, "b": 2}]

        result = ChartGenerator.render(data, "table")
        assert result["type"] == "table"

        result = ChartGenerator.render(data, "bar", {"x_axis_data": ["A"], "series_data": [1]})
        assert result["type"] == "bar"

    def test_supported_types(self):
        """测试支持的图表类型"""
        types = ChartGenerator.get_supported_types()
        assert "table" in types
        assert "bar" in types
        assert "line" in types
        assert "pie" in types
