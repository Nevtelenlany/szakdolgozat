from pathlib import Path
import json
from abc import ABC, abstractmethod

class QuestionEvaluator(ABC):
    @abstractmethod
    def evaluate(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        pass

class SingleChoiceEvaluator(QuestionEvaluator):
    def evaluate(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        helyes_valasz = kerdes_adat.get("correct_answer")
        helyes_e = (valasz == helyes_valasz)
        magyarazat = kerdes_adat.get("explanation", "Nincs elérhető magyarázat.")
        return helyes_e, {"explanation": magyarazat, "correct_answer": helyes_valasz}

class MultipleChoiceEvaluator(QuestionEvaluator):
    def evaluate(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        helyes_valaszok = set(kerdes_adat.get("correct_answers", []))
        user_set = set(valasz or []) 
        helyes_e = (user_set == helyes_valaszok)
        magyarazat = kerdes_adat.get("explanation", "Nincs elérhető magyarázat.")
        return helyes_e, {"explanation": magyarazat, "correct_answers": helyes_valaszok}

class ShortAnswerEvaluator(QuestionEvaluator):
    def evaluate(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        elfogadott = [k.lower() for k in kerdes_adat.get("accepted_keywords", [])]
        beirt = str(valasz or "").strip().lower()
        helyes_e = any(k in beirt for k in elfogadott)
        magyarazat = kerdes_adat.get("explanation", "Nincs elérhető magyarázat.")
        return helyes_e, {"explanation": magyarazat, "accepted_keywords": elfogadott}

class MatchingEvaluator(QuestionEvaluator):
    def evaluate(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        eredeti_parok = kerdes_adat.get("pairs", {})
        valasz_dict = valasz or {}
        minden_jo = all(eredeti_parok.get(bal) == jobb for bal, jobb in valasz_dict.items())
        magyarazat = kerdes_adat.get("explanation", "Nincs elérhető magyarázat.")
        return minden_jo, {"explanation": magyarazat, "pairs": eredeti_parok}

class OrderingEvaluator(QuestionEvaluator):
    def evaluate(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        eredeti_sorrend = kerdes_adat.get("ordered_items", [])
        valasz_lista = valasz or []
        helyes_e = (valasz_lista == eredeti_sorrend)
        magyarazat = kerdes_adat.get("explanation", "Nincs elérhető magyarázat.")
        return helyes_e, {"explanation": magyarazat, "ordered_items": eredeti_sorrend}

EVALUATORS = {
    "single_choice": SingleChoiceEvaluator(),
    "multiple_choice": MultipleChoiceEvaluator(),
    "short_answer": ShortAnswerEvaluator(),
    "matching": MatchingEvaluator(),
    "ordering": OrderingEvaluator()
}

class QuizFileManager:
    @staticmethod
    def get_available_pdfs(base_path: str | Path) -> list[str]:
        mappa = Path(base_path)
        if not (mappa.exists() and mappa.is_dir()):
            return []
        return [f.name for f in mappa.iterdir() if f.is_file() and f.name.lower().endswith(".pdf")]

class QuizEvaluator:
    @staticmethod
    def evaluate_quiz(quiz_data: list[dict], user_answers: dict, raw_folder_path: str | None = None, pdf_neve: str | None = None) -> tuple[int, int, dict]:
        ossz_pont, elert_pont, eredmenyek = QuizEvaluator._kiertekel_valaszokat(quiz_data, user_answers)

        if raw_folder_path and pdf_neve:
            QuizEvaluator._update_progress(raw_folder_path, pdf_neve, eredmenyek)
        return elert_pont, ossz_pont, eredmenyek

    @staticmethod
    def _kiertekel_valaszokat(quiz_data: list[dict], user_answers: dict) -> tuple[int, int, dict]:
        ossz_pont = len(quiz_data)
        elert_pont = 0
        eredmenyek = {}

        for kerdes_adat in quiz_data:
            k_id = kerdes_adat.get("id")
            tipus = kerdes_adat.get("type")
            tema = kerdes_adat.get("tema")
            valasz = user_answers.get(k_id) 
            evaluator = EVALUATORS.get(tipus)

            if evaluator:
                helyes_e, feedback = evaluator.evaluate(kerdes_adat, valasz)
                elert_pont += helyes_e 
            else:
                helyes_e = False
                feedback = {"explanation": f"Ismeretlen kérdéstípus: {tipus}"}
            eredmenyek[k_id] = {"helyes": helyes_e, "feedback": feedback, "tema": tema}

        return ossz_pont, elert_pont, eredmenyek

    @staticmethod
    def _update_progress(raw_folder_path: str | Path, pdf_neve: str, eredmenyek: dict) -> None:
        json_path = QuizEvaluator._get_progress_file_path(raw_folder_path, pdf_neve)
        
        if not json_path.exists(): 
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                temak = json.load(f)               
            frissitett_temak = QuizEvaluator._apply_progress_logic(temak, eredmenyek)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(frissitett_temak, f, ensure_ascii=False, indent=4)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError, OSError) as e:
            print(f"Hiba történt a haladás mentésekor ({type(e).__name__}): {e}")

    @staticmethod
    def _get_progress_file_path(raw_folder_path: str | Path, pdf_neve: str) -> Path:
        raw_path = Path(raw_folder_path)
        return raw_path.parent / "progress" / f"{pdf_neve}_progress.json"

    @staticmethod
    def _apply_progress_logic(temak: dict, eredmenyek: dict) -> dict:
        for _, adat in eredmenyek.items():
            tema_neve = adat.get("tema")
            helyes_e = adat.get("helyes")
            
            if not tema_neve or tema_neve not in temak:
                continue   
            tema_adat = temak[tema_neve]
            
            if helyes_e:
                tema_adat["valaszok"] = max(0, tema_adat["valaszok"] - 1)
                if tema_adat["valaszok"] == 0:
                    tema_adat["elsajatitva"] = True
            else:
                tema_adat["valaszok"] = min(5, tema_adat["valaszok"] + 1)
                tema_adat["elsajatitva"] = False
        return temak

    @staticmethod
    def get_evaluation_summary(elert_pont: int, ossz_pont: int) -> tuple[str, str, float]:
        szazalek = (elert_pont / ossz_pont) * 100 if ossz_pont > 0 else 0
        
        if szazalek == 100:
            return "tokeletes", "Hibátlan munka!", szazalek
        elif szazalek >= 60:
            return "kozepes", "Szép eredmény, de van még mit tanulni!", szazalek
        else:
            return "rossz", "Ezt még át kell ismételned!", szazalek