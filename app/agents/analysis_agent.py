"""分析Agent - 负责数据分析"""
import asyncio
import time
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import get_settings


class AnalysisAgent:
    """
    分析Agent

    职责：
    1. 对查询结果进行趋势分析
    2. 异常检测
    3. 生成自然语言总结
    """

    def __init__(self, llm: ChatOpenAI | None = None):
        settings = get_settings()

        self._llm = llm or ChatOpenAI(
            model=settings.llm.model,
            temperature=settings.llm.temperature,
            api_key=settings.llm.api_key,
        )

        # 分析提示模板
        self._trend_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的安全运营分析师。你需要分析提供的数据，发现趋势、异常和规律。

请分析以下数据：
{data}

你需要输出：
1. 主要发现（3-5条）
2. 趋势分析
3. 异常点（如有）
4. 简短总结（1-2句话）"""),
            ("human", "请分析这些数据"),
        ])

        self._summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的安全运营分析师。你需要根据数据和分析结果，生成简明的总结。

请根据以下内容生成总结：
{data}

要求：
- 语言简洁专业
- 突出关键发现
- 如有建议，一并给出"""),
            ("human", "请生成总结"),
        ])

    async def analyze_trend(self, data: Any, context: str | None = None) -> dict[str, Any]:
        """
        趋势分析

        Args:
            data: 查询结果数据
            context: 上下文信息（如查询条件等）

        Returns:
            分析结果
        """
        # 简单的趋势分析逻辑
        if not isinstance(data, list) or len(data) < 2:
            return {
                "type": "trend_analysis",
                "summary": "数据量不足以进行趋势分析",
                "findings": [],
            }

        # 使用LLM进行深度分析
        chain = self._trend_analysis_prompt | self._llm
        result = await chain.ainvoke({"data": str(data)})

        return {
            "type": "trend_analysis",
            "summary": result.content if hasattr(result, 'content') else str(result),
            "findings": self._extract_findings(result),
        }

    async def detect_anomaly(self, data: Any) -> dict[str, Any]:
        """
        异常检测

        Args:
            data: 查询结果数据

        Returns:
            异常检测结果
        """
        if not isinstance(data, list):
            return {
                "type": "anomaly_detection",
                "has_anomaly": False,
                "anomalies": [],
            }

        # 简单的异常检测：检测数值偏离超过2个标准差的点
        anomalies = []
        numeric_data = [d for d in data if isinstance(d, (int, float))]

        if numeric_data:
            import statistics
            if len(numeric_data) >= 3:
                mean = statistics.mean(numeric_data)
                stdev = statistics.stdev(numeric_data)

                for i, val in enumerate(numeric_data):
                    if abs(val - mean) > 2 * stdev:
                        anomalies.append({
                            "index": i,
                            "value": val,
                            "deviation": abs(val - mean) / stdev if stdev > 0 else 0,
                        })

        return {
            "type": "anomaly_detection",
            "has_anomaly": len(anomalies) > 0,
            "anomalies": anomalies,
        }

    async def summarize(self, data: Any, analysis_result: dict[str, Any] | None = None) -> str:
        """
        生成总结

        Args:
            data: 原始数据
            analysis_result: 分析结果（可选）

        Returns:
            总结文本
        """
        content = {
            "data": data,
            "analysis": analysis_result or {},
        }

        chain = self._summary_prompt | self._llm
        result = await chain.ainvoke({"data": str(content)})

        return result.content if hasattr(result, 'content') else str(result)

    def _extract_findings(self, llm_result) -> list[str]:
        """从LLM结果中提取发现"""
        if hasattr(llm_result, 'content'):
            content = llm_result.content
            # 简单的文本解析
            findings = []
            lines = content.split("\n")
            for line in lines:
                if line.strip() and (line.strip().startswith("-") or line[0].isdigit()):
                    findings.append(line.strip())
            return findings[:5]  # 最多5条
        return []


# 全局实例
_analysis_agent: AnalysisAgent | None = None


def get_analysis_agent() -> AnalysisAgent:
    """获取分析Agent实例"""
    global _analysis_agent
    if _analysis_agent is None:
        _analysis_agent = AnalysisAgent()
    return _analysis_agent
