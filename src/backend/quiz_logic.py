import os
import json

class QuizFileManager:
    @staticmethod
    def get_available_pdfs(base_path):
        if not os.path.exists(base_path):
            return []
        return [f for f in os.listdir(base_path) if f.lower().endswith(".pdf")]

class QuizEvaluator:
    @staticmethod
    def evaluate_quiz(quiz_data, user_answers, raw_folder_path=None, pdf_neve=None): # <--- Így már jó lesz!
        ossz_pont = len(quiz_data)
        elert_pont = 0
        eredmenyek = {}

        for kerdes_adat in quiz_data:
            k_id = kerdes_adat.get("id")
            tipus = kerdes_adat.get("type")
            tema = kerdes_adat.get("tema")
            valasz = user_answers.get(k_id) 

            helyes_e = False
            feedback = {}

            if tipus == "single_choice":
                helyes_valasz = kerdes_adat.get("correct_answer")
                helyes_e = (valasz == helyes_valasz)
                feedback["correct_answer"] = helyes_valasz

            elif tipus == "multiple_choice":
                helyes_valaszok = set(kerdes_adat.get("correct_answers", []))
                user_set = set(valasz) if valasz else set()
                helyes_e = (user_set == helyes_valaszok)
                feedback["correct_answers"] = helyes_valaszok

            elif tipus == "short_answer":
                elfogadott = [k.lower() for k in kerdes_adat.get("accepted_keywords", [])]
                beirt = valasz.strip().lower() if valasz else ""
                helyes_e = any(k in beirt for k in elfogadott)
                feedback["accepted_keywords"] = elfogadott

            elif tipus == "matching":
                eredeti_parok = kerdes_adat.get("pairs", {})
                valasz_dict = valasz if valasz else {}
                
                minden_jo = True
                for bal, jobb in valasz_dict.items():
                    if eredeti_parok.get(bal) != jobb:
                        minden_jo = False
                        break
                helyes_e = minden_jo
                feedback["pairs"] = eredeti_parok

            elif tipus == "ordering":
                eredeti_sorrend = kerdes_adat.get("ordered_items", [])
                valasz_lista = valasz if valasz else []
                helyes_e = (valasz_lista == eredeti_sorrend)
                feedback["ordered_items"] = eredeti_sorrend

            if helyes_e:
                elert_pont += 1

            eredmenyek[k_id] = {
                "helyes": helyes_e,
                "feedback": feedback,
                "tema": tema
            }

        if raw_folder_path and pdf_neve:
            QuizEvaluator._update_progress(raw_folder_path, pdf_neve, eredmenyek)

        return elert_pont, ossz_pont, eredmenyek
    @staticmethod
    def _update_progress(raw_folder_path, pdf_neve, eredmenyek):
        subject_folder = os.path.dirname(raw_folder_path)
        progress_folder = os.path.join(subject_folder, "progress")
        json_path = os.path.join(progress_folder, f"{pdf_neve}_progress.json")
        
        if not os.path.exists(json_path):
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                temak = json.load(f)
                
            for k_id, adat in eredmenyek.items():
                tema_neve = adat.get("tema")
                helyes_e = adat.get("helyes")
                
                if tema_neve and tema_neve in temak:
                    if helyes_e:

                        if temak[tema_neve]["valaszok"] > 0:
                            temak[tema_neve]["valaszok"] -= 1
                            
                        if temak[tema_neve]["valaszok"] == 0:
                            temak[tema_neve]["elsajatitva"] = True
                    else:
                        
                        if temak[tema_neve]["valaszok"] < 5:
                            temak[tema_neve]["valaszok"] += 1
                        temak[tema_neve]["elsajatitva"] = False
                        
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(temak, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"Hiba a haladás mentésekor: {e}")

    @staticmethod
    def get_evaluation_summary(elert_pont, ossz_pont):
        szazalek = (elert_pont / ossz_pont) * 100 if ossz_pont > 0 else 0
        
        if szazalek == 100:
            return "tokeletes", "Hibátlan munka!", szazalek
        elif szazalek >= 60:
            return "kozepes", "Szép eredmény, de van még mit tanulni!", szazalek
        else:
            return "rossz", "Ezt még át kell ismételned!", szazalek