from langchain.memory import ConversationBufferMemory

class SafeConversationMemory(ConversationBufferMemory):
    """
    Variante sécurisée de ConversationBufferMemory.

    Cette classe surcharge la méthode `load_memory_variables` pour capturer
    toute exception potentielle lors de la récupération de la mémoire de conversation.

    En cas d'erreur (fichier manquant, corruption, problème IO, etc.),
    elle retourne simplement une mémoire vide au lieu de faire planter l'agent.

    Utile pour des environnements instables ou pour éviter les crashes
    dans des agents en production.

    Paramètres :
    -----------
    Hérite des mêmes paramètres que ConversationBufferMemory.
    """

    def load_memory_variables(self, inputs):
        """
        Tente de charger la mémoire conversationnelle.
        En cas d'échec, retourne une mémoire vide pour éviter l'arrêt de l'agent.
        """
        try:
            return super().load_memory_variables(inputs)
        except Exception as e:
            print(f"[⚠️ Mémoire inaccessible] Erreur : {e}")
            # Renvoie une mémoire vide (structure attendue par l'agent)
            return {self.memory_key: []}