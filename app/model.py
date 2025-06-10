from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from .rag_agent import RagAgent

MODEL_NAME = "llama3"
SYSTEM_PROMPT = """
Tu es un assistant intelligent spécialisé dans la transition écologique.
- Tu parles toujours en français, de façon naturelle et compréhensible.
- Tu n’inventes pas de réponse. Si tu ne sais pas, dis « Je ne sais pas. ».
- Ignore les emojis, reste simple.
"""

class ChatModel:
    def __init__(self, model=MODEL_NAME, system_prompt=SYSTEM_PROMPT):
        self.llm = ChatOllama(model=model)
        self.historique = [SystemMessage(content=system_prompt)]
        self.agent_rag = RagAgent(self.llm)

    def model_response(self, message: str) -> str:
        self.historique.append(HumanMessage(content=message))

        # 1. Réponse du LLM principal
        response = self.llm.invoke(self.historique)
        output = response.content.strip()

        # 2. Fallback vers RAG si réponse faible
        if output.lower() == "je ne sais pas." or len(output) < 20:
            rag_output = self.agent_rag.search(message)
            result = rag_output.get("output") if isinstance(rag_output, dict) else str(rag_output)
            self.historique.append(AIMessage(content=result))
            return result

        self.historique.append(AIMessage(content=output))
        return output
