import os

class QuizFileManager:
    @staticmethod
    def get_available_pdfs(base_path):
        if not os.path.exists(base_path):
            return []
        return [f for f in os.listdir(base_path) if f.lower().endswith(".pdf")]

class QuizEvaluator:
    @staticmethod
    def evaluate_quiz(quiz_data, user_answers):
        ossz_pont = len(quiz_data)
        elert_pont = 0
        eredmenyek = {}

        for kerdes_adat in quiz_data:
            k_id = kerdes_adat.get("id")
            tipus = kerdes_adat.get("type")
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
                "feedback": feedback
            }

        return elert_pont, ossz_pont, eredmenyek
    
    @staticmethod
    def get_evaluation_summary(elert_pont, ossz_pont):
        szazalek = (elert_pont / ossz_pont) * 100 if ossz_pont > 0 else 0
        
        if szazalek == 100:
            return "tokeletes", "Hibátlan munka!", szazalek
        elif szazalek >= 60:
            return "kozepes", "Szép eredmény, de van még mit tanulni!", szazalek
        else:
            return "rossz", "Ezt még át kell ismételned!", szazalek