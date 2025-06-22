# ========================================
# app/agents/research_agent.py - Agente de Investigación
# ========================================

from typing import Dict, Any, List
import asyncio
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..tools.research_tools import PubMedTool, HealthlineTool, ExamineTool


class ResearchAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.2, model="gpt-3.5-turbo")
        
        self.tools = [
            PubMedTool(),
            HealthlineTool(),
            ExamineTool()
        ]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un investigador científico especializado en nutrición y fitness.
            Tu trabajo es:
            - Buscar estudios científicos recientes y relevantes
            - Analizar evidencia científica de manera crítica
            - Proporcionar información basada en investigación peer-reviewed
            - Explicar estudios complejos de manera comprensible
            - Identificar consensos científicos y controversias
            
            Siempre cita las fuentes y fecha de los estudios.
            Explica limitaciones de los estudios cuando sea relevante.
            Prioriza meta-análisis y estudios randomizados controlados.
            """),
            ("human", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    async def process(self, message: str, user_profile: Dict, context: List[Dict]) -> Dict[str, Any]:
        """Procesa consultas de investigación científica"""
        
        try:
            result = await asyncio.to_thread(
                self.executor.invoke,
                {"input": message}
            )
            
            return {
                "content": result["output"],
                "generate_plan": False,
                "metadata": {
                    "tools_used": [tool.name for tool in self.tools],
                    "research_based": True
                }
            }
            
        except Exception as e:
            return {
                "content": f"Lo siento, ha ocurrido un error buscando información científica: {str(e)}",
                "generate_plan": False,
                "metadata": {"error": str(e)}
            }