import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Tuple
from core.config import global_config

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

class DeepSeekEngine:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key if api_key is not None else global_config.get("deepseek_api_key", "")
        self.model = model if model is not None else global_config.get("deepseek_model", "deepseek-chat")

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def test_connection(self, test_key: str = None) -> Tuple[bool, str]:
        """Teste la validité de la clé API auprès des serveurs DeepSeek."""
        key_to_test = test_key if test_key else self.api_key
        if not key_to_test:
            return False, "Aucune clé API DeepSeek n'a été saisie."

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Réponds avec 'OK' si le test réussi."},
                {"role": "user", "content": "Ping"}
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key_to_test.strip()}"
        }

        try:
            req = urllib.request.Request(
                DEEPSEEK_API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return True, "Connexion réussie à l'API DeepSeek ! Clé valide."
                else:
                    return False, f"Erreur serveur DeepSeek (Code {response.status})"
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, "Clé API DeepSeek invalide (401 Non autorisé)."
            elif e.code == 402:
                return False, "Crédits DeepSeek insuffisants (402 Solde épuisé)."
            else:
                return False, f"Erreur HTTP DeepSeek ({e.code}) : {e.reason}"
        except Exception as e:
            return False, f"Impossible de contacter l'API DeepSeek : {str(e)}"

    def categorize_files(self, files_info: List[Dict[str, Any]], custom_prompt: str = "") -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Analyse un lot de fichiers via DeepSeek et suggère des catégories sémantiques et sous-dossiers.
        
        files_info: list of dict [{"name": "facture_edf_2026.pdf", "extension": "pdf", "size_formatted": "250 KB", ...}]
        returns: (success, list_of_ai_recommendations, message)
        """
        if not self.is_configured():
            return False, [], "Clé API DeepSeek absente. Veuillez configurer la clé API dans les paramètres."

        if not files_info:
            return True, [], "Aucun fichier à analyser."

        prompt_instruction = custom_prompt if custom_prompt else global_config.get("deepseek_custom_prompt", "")

        system_prompt = (
            "Tu es un assistant IA expert en organisation chirurgicale et sémantique de fichiers.\n"
            "Ta mission est d'analyser la liste de fichiers transmise par l'utilisateur et d'attribuer à CHAQUE fichier :\n"
            "1. 'category' : un sous-dossier clair et sémantique (ex: 'Projets/Python', 'Factures/2026', 'Médias/Photos_Pro', 'Documents/Administratif').\n"
            "2. 'suggested_name' : un nom de fichier nettoyé et explicite (conserve TOUJOURS la même extension d'origine).\n"
            "3. 'explanation' : une courte explication (1 phrase) justifiant ce classement.\n\n"
            f"Instruction utilisateur spécifique : {prompt_instruction}\n\n"
            "RÈGLE STRICTE DE FORMAT :\n"
            "Tu dois impérativement répondre UNIQUEMENT sous forme d'un objet JSON valide au format exact suivant, sans texte avant ni après :\n"
            "{\n"
            "  \"items\": [\n"
            "    {\n"
            "      \"file_name\": \"nom_origine.ext\",\n"
            "      \"category\": \"SousDossier/Categorie\",\n"
            "      \"suggested_name\": \"nom_propre.ext\",\n"
            "      \"explanation\": \"Raison du tri...\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        user_content = json.dumps({"files": files_info}, ensure_ascii=False)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key.strip()}"
        }

        try:
            req = urllib.request.Request(
                DEEPSEEK_API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result_bytes = response.read()
                result_json = json.loads(result_bytes.decode("utf-8"))

                content = result_json["choices"][0]["message"]["content"]
                
                # Tentative d'extraction du JSON
                parsed = json.loads(content)
                items = parsed.get("items", [])
                
                return True, items, f"Analyse IA DeepSeek terminée avec succès pour {len(items)} fichier(s)."

        except urllib.error.HTTPError as e:
            return False, [], f"Erreur HTTP DeepSeek ({e.code}) : {e.reason}"
        except json.JSONDecodeError:
            return False, [], "L'API DeepSeek a retourné une réponse au format JSON invalide."
        except Exception as e:
            return False, [], f"Erreur lors de l'analyse IA DeepSeek : {str(e)}"
