import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Tuple
from core.config import global_config

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OLLAMA_DEFAULT_URL = "http://localhost:11434/api/chat"

def extract_file_snippet(file_path: Path, max_chars: int = 500) -> str:
    """Extrait un aperçu textuel court d'un fichier pour enrichir le tri IA sémantique (Content-Aware)."""
    try:
        fp = Path(file_path)
        if not fp.exists() or not fp.is_file():
            return ""

        # Ne pas lire des fichiers volumineux (> 5 Mo) pour des raisons de performance
        if fp.stat().st_size > 5 * 1024 * 1024:
            return ""

        suffix = fp.suffix.lower()
        text_extensions = {
            ".txt", ".md", ".json", ".csv", ".log", ".py", ".js", ".ts", ".jsx", ".tsx",
            ".html", ".css", ".xml", ".sql", ".yaml", ".yml", ".sh", ".bat", ".ps1",
            ".env", ".ini", ".conf", ".rst", ".tex", ".c", ".cpp", ".java", ".php"
        }

        if suffix in text_extensions:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(max_chars * 2)
                cleaned = " ".join(content.split())
                return cleaned[:max_chars]
    except Exception:
        pass

    return ""

class DeepSeekEngine:
    """Moteur IA Multi-Fournisseurs (DeepSeek, Ollama local offline, OpenAI, Custom)."""

    def __init__(self, provider: str = None, api_key: str = None, model: str = None, endpoint: str = None):
        self.provider = (provider or global_config.get("ai_provider", "deepseek")).lower()
        
        # Résolution des paramètres en fonction du provider
        if self.provider == "openai":
            self.api_key = api_key if api_key is not None else global_config.get("openai_api_key", "")
            self.model = model if model is not None else global_config.get("openai_model", "gpt-4o-mini")
            self.endpoint = endpoint or OPENAI_API_URL
        elif self.provider == "ollama":
            self.api_key = "ollama"
            self.model = model if model is not None else global_config.get("ollama_model", "llama3:latest")
            base_ep = endpoint or global_config.get("ollama_endpoint", "http://localhost:11434")
            self.endpoint = f"{base_ep.rstrip('/')}/api/chat" if not base_ep.endswith("/chat") else base_ep
        elif self.provider == "custom":
            self.api_key = api_key if api_key is not None else global_config.get("deepseek_api_key", "")
            self.model = model or "custom-model"
            self.endpoint = endpoint or global_config.get("custom_endpoint", DEEPSEEK_API_URL)
        else: # 'deepseek' par défaut
            self.provider = "deepseek"
            self.api_key = api_key if api_key is not None else global_config.get("deepseek_api_key", "")
            self.model = model if model is not None else global_config.get("deepseek_model", "deepseek-chat")
            self.endpoint = DEEPSEEK_API_URL

    def is_configured(self) -> bool:
        if self.provider == "ollama":
            return True # Ollama ne nécessite pas de clé API
        return bool(self.api_key and len(self.api_key.strip()) > 3)

    def test_connection(self, test_key: str = None) -> Tuple[bool, str]:
        """Teste la validité de la connexion auprès du serveur IA sélectionné."""
        if self.provider == "ollama":
            try:
                base_ep = self.endpoint.replace("/api/chat", "").replace("/v1/chat/completions", "")
                req = urllib.request.Request(f"{base_ep}/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        return True, "Connexion réussie au serveur local Ollama ! (Mode 100% Offline)"
                    return False, f"Ollama HTTP Status {response.status}"
            except Exception as e:
                return False, f"Impossible de contacter le serveur Ollama local sur {self.endpoint}. Assurez-vous qu'Ollama est lancé."

        key_to_test = test_key if test_key else self.api_key
        if not key_to_test:
            return False, f"Aucune clé API saisie pour le fournisseur {self.provider.upper()}."

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
                self.endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return True, f"Connexion réussie à l'API {self.provider.capitalize()} ! Clé valide."
                else:
                    return False, f"Erreur serveur {self.provider.capitalize()} (Code {response.status})"
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, f"Clé API {self.provider.capitalize()} invalide (401 Non autorisé)."
            elif e.code == 402:
                return False, "Solde de crédits épuisé (402)."
            else:
                return False, f"Erreur HTTP {self.provider.capitalize()} ({e.code}) : {e.reason}"
        except Exception as e:
            return False, f"Impossible de contacter l'API {self.provider.capitalize()} : {str(e)}"

    def categorize_files(self, files_info: List[Dict[str, Any]], custom_prompt: str = "") -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Analyse un lot de fichiers via le LLM sélectionné et suggère des catégories sémantiques et sous-dossiers.
        Prnd en compte les aperçus de contenu (Content-Aware).
        """
        if not self.is_configured():
            return False, [], f"Clé API absente ou Fournisseur IA '{self.provider.upper()}' non configuré. Veuillez configurer les paramètres."

        if not files_info:
            return True, [], "Aucun fichier à analyser."

        prompt_instruction = custom_prompt if custom_prompt else global_config.get("deepseek_custom_prompt", "")

        system_prompt = (
            "Tu es un assistant IA expert en organisation chirurgicale et sémantique de fichiers.\n"
            "Ta mission est d'analyser la liste de fichiers transmise par l'utilisateur (avec leurs noms, extensions et aperçus de contenu si disponibles) et d'attribuer à CHAQUE fichier :\n"
            "1. 'category' : un sous-dossier clair et sémantique (ex: 'Projets/Python', 'Factures/2026', 'Médias/Photos_Pro', 'Documents/Administratif').\n"
            "2. 'suggested_name' : un nom de fichier nettoyé et explicite (conserve TOUJOURS la même extension d'origine).\n"
            "3. 'explanation' : une courte explication (1 phrase) justifiant ce classement selon le nom et/ou le contenu du fichier.\n\n"
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

        # Structure du payload pour Ollama vs API REST Standard
        if self.provider == "ollama":
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "stream": False,
                "format": "json"
            }
            headers = {"Content-Type": "application/json"}
        else:
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
                self.endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=45) as response:
                result_bytes = response.read()
                result_json = json.loads(result_bytes.decode("utf-8"))

                if self.provider == "ollama":
                    content = result_json.get("message", {}).get("content", "")
                else:
                    content = result_json["choices"][0]["message"]["content"]
                
                # Tentative d'extraction du JSON
                parsed = json.loads(content)
                items = parsed.get("items", [])
                
                return True, items, f"Analyse IA ({self.provider.upper()}) terminée avec succès pour {len(items)} fichier(s)."

        except urllib.error.HTTPError as e:
            return False, [], f"Erreur HTTP IA ({e.code}) : {e.reason}"
        except json.JSONDecodeError:
            return False, [], f"Le fournisseur IA ({self.provider.upper()}) a retourné une réponse au format JSON invalide."
        except Exception as e:
            return False, [], f"Erreur lors de l'analyse IA ({self.provider.upper()}) : {str(e)}"

