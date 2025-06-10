from langchain.memory import ConversationBufferMemory

class SafeConversationMemory(ConversationBufferMemory):
    def load_memory_variables(self, inputs):
        try:
            return super().load_memory_variables(inputs)
        except Exception as e:
            print(f"[⚠️ Mémoire inaccessible] Erreur : {e}")
            return {self.memory_key: []}
