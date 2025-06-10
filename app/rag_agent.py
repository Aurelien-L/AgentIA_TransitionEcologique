import os
from IPython.display import display, clear_output, Markdown
from dotenv import load_dotenv
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain_deepseek import ChatDeepSeek
from langchain import hub
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
import re
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
#from LLM.utils.rag.document import document_search
#from LLM.utils.rag.web_search import web_search

from app.document import document_search
from app.duck_search import duck_search

class RagAgent: 
    def __init__(self, model):
        # définition des outils 
        self.tools = [
            Tool(
                name="Search documents", 
                func=document_search,
                description=(
                    "Recherche des informations dans les documents internes "
                    "liées à la transition écologique (lois, aides, bonnes pratiques)."
                )
            ),
            Tool(
                name="Search web",
                func=duck_search,
                description=(
                    "Recherche des informations à jour sur le web "
                    "(actualités, événements, faits récents sur la transition écologique)."
                )
            )
        ]

        # Création de prompt spécialisé pour la transition écologique 
        self.prompt_template = """
Tu es un assistant intelligent spécialisé dans la **transition écologique**.  
Ta mission est d’aider les citoyens à comprendre les enjeux environnementaux, les réglementations, les aides financières et les bonnes pratiques.

Lorsque tu reçois une question, tu :
- Utilises d’abord les documents internes (lois, subventions, etc.).
- Si la réponse n’est pas trouvée, tu recherches sur le web.
- Tu réponds toujours en français, de façon claire et naturelle.
- Tu n’inventes jamais de réponse. Si tu ne sais pas, tu dis : « Je ne sais pas. »

Voici la question : {input}

{agent_scratchpad}
"""
        custom_prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad"],
            template=self.prompt_template
        )

        self.agent = create_react_agent(
            llm=model,
            tools=self.tools,
            prompt=custom_prompt
        )

    def search(self, historique): 
        prompt = self.historique_to_prompt(historique)
        executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )
        return executor.invoke({"input": prompt})
    
    def historique_to_prompt(self, historique):
        prompt = ""
        for message in historique:
            if isinstance(message, HumanMessage):
                prompt +=  f"Utilisateur : {message.content}\n"
            elif isinstance(message, AIMessage):
                prompt += f"Assistant : {message.content}\n"
        return prompt


