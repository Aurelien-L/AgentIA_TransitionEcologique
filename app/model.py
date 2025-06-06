from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableLambda, RunnableBranch
from app.rag_agent import RagAgent

MODEL_NAME="llama3"
SYSTEM_PROMPT="""
Tu es un assistant intelligent spécialisé dans la transition écologique.  
- Tu parles toujours en français, de façon naturelle et compréhensible.
- Tu n’inventes pas de réponse. Si tu ne sais pas, dis « Je ne sais pas. ».
- Ignore les emojis, reste simple.
"""

class ChatModel: 
    def __init__(self, model=MODEL_NAME, system_prompt=SYSTEM_PROMPT):
        self.llm = ChatOllama(model=model)
        self.historique = [SystemMessage(content=system_prompt)]

    def model_response(self, message: str) -> str:
        self.historique.append(HumanMessage(content=message))

        base_chain = (
            RunnableLambda(lambda x:self.llm.invoke(x))
            | RunnableBranch(lambda message: message.content.strip() if hasattr(message, "content") else str(message).strip())
        )

        def should_fallback(output: str) -> bool: 
            return output.lower()== "je ne sais pas." or len(output.strip()) < 20 

        fallback_chain = RunnableLambda(lambda _: self.agent_rag())

        final_chain = base_chain | RunnableBranch(
            (should_fallback, fallback_chain),
            RunnableLambda(lambda x: x)
        ) 

        result_test = final_chain.invoke(self.historique)
        self.historique.append(AIMessage(content=result_test))
        return result_test
    
    def agent_rag(self):
        agent_rag= RagAgent(self.llm)
        rag_result = agent_rag.search(self.historique)
        return rag_result["output"] if isinstance(rag_result, dict) else str(rag_result)