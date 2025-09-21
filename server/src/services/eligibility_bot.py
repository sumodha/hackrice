import eligibility_optimizer
import pandas as pd
import numpy as np
import os
from google import genai
from dotenv import load_dotenv
from src.models.user import User

class WelfareProgramEligibilityBot:
    """
    A bot to interactively determine eligibility for social welfare programs
    by asking the most informative questions.
    """ 

    def __init__(self, optimizer: eligibility_optimizer.WelfareProgramEligibilityOptimizer = None, *, eligibility_data_path: str = None, df: pd.DataFrame = None, field_weights: dict = None):
        """
        Initializes the bot with an eligibility optimizer.

        Args:
            optimizer (WelfareProgramEligibilityOptimizer): An instance of the optimizer class. If
                not provided, one will be constructed using `eligibility_data_path` or `df`.
            eligibility_data_path (str): Optional CSV path to load into a DataFrame.
            df (pd.DataFrame): Optional DataFrame to pass to the optimizer directly.
            field_weights (dict): Optional field weights to pass to optimizer.
        """
        # Initialize container fields
        self.df = None
        self.program_blacklist = []
        self.field_blacklist = []
        self.user = User()

        # If optimizer not provided, construct it with the provided df/path
        if optimizer is not None:
            self.optimizer = optimizer
            # try to capture dataframe from optimizer if present
            try:
                self.df = getattr(optimizer, 'df', None)
            except Exception:
                self.df = None
        else:
            # Load DataFrame here (bot responsibility)
            if df is not None:
                data_df = df
            elif eligibility_data_path is not None:
                data_df = pd.read_csv(eligibility_data_path)
            else:
                raise ValueError('Must provide either an optimizer instance, a DataFrame `df`, or an `eligibility_data_path`.')

            # Store df and pass it into optimizer
            self.df = data_df
            self.optimizer = eligibility_optimizer.WelfareProgramEligibilityOptimizer(df=data_df, field_weights=field_weights)

    def generate_program_blacklist(self, whitelist: list[str], df: pd.DataFrame) -> list:
        """
        Generate a program_blacklist list from the given whitelist and dataframe.

        Args:
            whitelist (list[str]): Programs to keep (case-insensitive).
            df (pd.DataFrame): DataFrame of programs (one program per row). The program
                name is expected in the first column or a column named 'program'.

        Returns:
            list: List of program names (as they appear in the DataFrame index or column)
            that are NOT in the whitelist. This can be passed as program_blacklist.
        """
        if whitelist is None:
            whitelist = []

        # Normalize whitelist for comparison
        normalized_whitelist = {str(x).strip().lower() for x in whitelist}

        # Determine program names in dataframe
        program_names = []
        # If df has an index named 'program' or has been indexed by program, use the index
        if df.index is not None and df.index.name == 'program':
            program_names = list(df.index.astype(str))
        else:
            # Prefer a column explicitly named 'program'
            if 'program' in df.columns:
                program_names = list(df['program'].astype(str))
            else:
                # Fallback to first column
                if len(df.columns) > 0:
                    first_col = df.columns[0]
                    program_names = list(df[first_col].astype(str))
                else:
                    return []

        # Build blacklist: programs present in df but not in whitelist
        blacklist = []
        for name in program_names:
            if name is None:
                continue
            if str(name).strip().lower() not in normalized_whitelist:
                blacklist.append(name)

        # Update instance program_blacklist field
        try:
            self.program_blacklist = blacklist
        except Exception:
            # If assignment fails for any reason, ignore and return
            pass

        return None

    def parse_user_from_transcript(self, transcript: str) -> None:
        """
        Parse an aggregated transcript string using Gemma and populate the instance's User object.

        Args:
            transcript (str): Aggregated user Q&A or free-text responses.
        """
        if not transcript or not transcript.strip():
            return

        # Build prompt to ask Gemma to extract only the known User fields as JSON
        user_fields = [
            "age",
            "citizen_or_lawful_resident",
            "has_permanent_address",
            "lives_with_people",
            "monthly_income",
            "employed",
            "disabled",
            "is_veteran",
            "has_criminal_record",
            "has_children",
            "is_refugee",
        ]

        prompt = (
            "You are given a transcript of user Q&A pairs or free-form text. "
            "Extract values for the following fields if present and return a single JSON object: "
            f"{user_fields}. Use integers for numeric fields and booleans for yes/no fields. "
            "If a field cannot be determined, omit it. Respond only with the JSON object.\n\n"
            f"Transcript:\n{transcript}"
        )

        # Load environment and call Gemma
        load_dotenv()
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            # No API key: can't call Gemma; return early
            return

        client = genai.Client(api_key=GEMINI_API_KEY)

        try:
            resp = client.models.generate_content(model="gemma-3-27b-it", contents=prompt)
            text = getattr(resp, "text", str(resp)).strip()

            # Extract first JSON object
            import json, re

            m = re.search(r"\{[\s\S]*\}", text)
            if not m:
                return

            parsed = json.loads(m.group(0))

            # Populate User fields using set_field and collect populated keys
            populated_keys = []
            for k, v in parsed.items():
                try:
                    if hasattr(self.user, 'set_field'):
                        self.user.set_field(k, v)
                    else:
                        setattr(self.user, k, v)
                    populated_keys.append(k)
                except Exception:
                    # ignore invalid fields or values
                    continue

            # Update the bot's field_blacklist to include fields we populated
            try:
                # Keep only unique values and preserve order
                seen = set()
                ordered = []
                for f in populated_keys:
                    if f not in seen:
                        ordered.append(f)
                        seen.add(f)
                self.field_blacklist = ordered
            except Exception:
                pass
        except Exception:
            # On any error, return without modification
            return

    def get_next_field(self, field_blacklist=None, program_blacklist=None):
        """
        Determines the next best field to ask about based on current blacklists.

        Args:
            field_blacklist (list): List of field names already asked.
            program_blacklist (list): List of program names already deemed ineligible.

        Returns:
            str: The next best question (field name) to ask.
        """
        if field_blacklist is None:
            field_blacklist = []
        if program_blacklist is None:
            program_blacklist = []

        # Apply blacklists to filter the dataframe
        filtered_df = self.optimizer._apply_blacklists(field_blacklist, program_blacklist)

        if filtered_df.empty or filtered_df.shape[1] == 0:
            return None  # No more questions can be asked

        # Calculate information gain for each remaining field
        info_gains = {}
        for field in filtered_df.columns:
            info_gain = self.optimizer._calculate_information_gain(filtered_df, field)
            weighted_info_gain = info_gain * self.optimizer.field_weights.get(field, 1.0)
            info_gains[field] = weighted_info_gain

        # Select the field with the highest weighted information gain
        next_question = max(info_gains, key=info_gains.get)
        return next_question

    def ask_next_field_with_gemma(self, field_blacklist=None, program_blacklist=None):
        """
        Use the Gemma model to produce a concise, user-facing question that asks
        for the value of the next-most-informative field.

        This reuses the project's Gemma/GenAI call pattern (same as in `app.py`).

        Returns:
            str | None: A short question string suitable for presenting to the user,
                        or None if no next field is available.
        """
        if field_blacklist is None:
            field_blacklist = []
        if program_blacklist is None:
            program_blacklist = []

        # Prefer using the optimizer's top field(s) if available
        try:
            top_fields = self.optimizer.get_next_fields(field_blacklist, program_blacklist, top_n=1)
        except Exception:
            # Fallback to the heuristic single-field method
            next_field = self.get_next_field(field_blacklist, program_blacklist)
            top_fields = [next_field] if next_field else []

        if not top_fields:
            return None

        field = top_fields[0]

        # Craft a short prompt asking for that field
        prompt = (
            f"Please write a concise, user-facing question to collect the user's '{field}' value. "
            "Keep the question short and easy to answer (one sentence)."
        )

        # Load environment and call Gemma (same pattern as app.py)
        load_dotenv()
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            # If API key is not available, return the raw prompt as a fallback question
            return f"What is your {field}?"
        client = genai.Client(api_key=GEMINI_API_KEY)

        try:
            response = client.models.generate_content(
                model="gemma-3-27b-it",
                contents=prompt,
            )
            # response.text is used elsewhere in the project
            return getattr(response, "text", str(response)).strip()
        except Exception:
            # On any error, return a simple fallback question
            return f"What is your {field}?"

    def ask_questions(self, field_blacklist=None, program_blacklist=None, num_questions: int = 4):
        """
    Ask `num_questions` questions by repeatedly calling `ask_next_field_with_gemma`,
    collect the user's answers into a running string, then call Gemma to map
    collected answers into the target schema. Update the instance's User object
    with any fields that have values using `user.set_field(field_name, value)`.

        Args:
            field_blacklist (list): Fields already asked.
            program_blacklist (list): Programs already excluded.
            num_questions (int): Number of questions to ask (default 4).
        """
        if field_blacklist is None:
            field_blacklist = []
        if program_blacklist is None:
            program_blacklist = []

        # Keep a running transcript of questions and answers
        running_answers = ""

        # Ask questions and append each asked field to the blacklist
        asked_fields = []

        # The caller must provide real user responses either as a list `answers`
        # or as an `answer_callback(question)` callable.
        # We'll accept these via keyword-only parameters `answers` or `answer_callback`.
        # To maintain backward compatibility, allow them as attributes on self if set.
        answers = None
        answer_callback = None
        # attempt to pull provided values from attributes if present
        if hasattr(self, "_ask_questions_answers"):
            answers = getattr(self, "_ask_questions_answers")
        if hasattr(self, "_ask_questions_callback"):
            answer_callback = getattr(self, "_ask_questions_callback")

        # If neither interface is provided, raise an error so callers must supply real input
        if answers is None and answer_callback is None:
            raise ValueError("ask_questions requires either 'answers' list or 'answer_callback' callable.\n" \
                    "Set them as attributes on the bot instance or pass via provided interface.")

        for i in range(num_questions):
            question = self.ask_next_field_with_gemma(field_blacklist, program_blacklist)
            if not question:
                break

            # Obtain the real user answer via callback or from the answers list
            user_answer = ""
            if answer_callback is not None:
                try:
                    user_answer = answer_callback(question)
                except Exception:
                    user_answer = ""
            elif answers is not None:
                if i < len(answers):
                    user_answer = answers[i]
                else:
                    user_answer = ""

            # If still empty, use a placeholder but we prefer real inputs
            if not user_answer:
                user_answer = "[no answer provided]"

            running_answers += f"Q: {question}\nA: {user_answer}\n"

            # Attempt to infer the field name from the question text
            inferred_field = None
            if "'" in question:
                start = question.find("'")
                end = question.find("'", start+1)
                if start != -1 and end != -1:
                    inferred_field = question[start+1:end]
            elif question.lower().startswith("what is your "):
                inferred_field = question[len("what is your "):].strip(' ?')

            if inferred_field:
                field_blacklist.append(inferred_field)
                asked_fields.append(inferred_field)
            else:
                field_blacklist.append(user_answer)

    # After collecting answers, ask Gemma to populate the target fields as JSON
    # The response will be parsed and mapped into the project's `User` model
    # using `user.set_field(field_name, value)`. The `target_fields` list
    # corresponds to attributes defined on `src.models.user.User`.
        target_fields = [
            "age",
            "citizen_or_lawful_resident",
            "has_permanent_address",
            "lives_with_people",
            "monthly_income",
            "employed",
            "disabled",
            "is_veteran",
            "has_criminal_record",
            "has_children",
            "is_refugee",
        ]

        populate_prompt = (
            "You are given a transcript of short user Q&A pairs. Using only information present, "
            "extract and populate the following fields if there is enough information: "
            f"{target_fields}.\nRespond with a JSON object mapping field names to values. "
            "Use integers for numbers and booleans for yes/no fields. If a field cannot be determined, omit it.\n\n"
            f"Transcript:\n{running_answers}"
        )

        populated = {}
        load_dotenv()
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            # No API key: return early without modification
            return

        client = genai.Client(api_key=GEMINI_API_KEY)
        try:
            resp = client.models.generate_content(model="gemma-3-27b-it", contents=populate_prompt)
            text = getattr(resp, "text", str(resp)).strip()

            # Attempt to parse a JSON substring from the response
            import json, re

            json_text = None
            # Find the first { ... } block
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                json_text = m.group(0)

            if json_text:
                parsed = json.loads(json_text)
                # Normalize keys and map to only the expected keys
                for k, v in parsed.items():
                    if k in target_fields and v is not None and v != "":
                        populated[k] = v
                        # Update instance User object using set_field where possible
                        try:
                            # Use self.user.set_field to assign values; this will safely ignore unknown fields
                            self.user.set_field(k, v)
                        except Exception:
                            # If updating fails, ignore and continue
                            pass
        except Exception:
            # On error, return without modification
            return