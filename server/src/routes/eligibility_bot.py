import eligibility_optimizer
import pandas as pd
import numpy as np
import os
from google import genai
from dotenv import load_dotenv

class WelfareProgramEligibilityBot:
    """
    A bot to interactively determine eligibility for social welfare programs
    by asking the most informative questions.
    """

    def __init__(self, optimizer: eligibility_optimizer.WelfareProgramEligibilityOptimizer):
        """
        Initializes the bot with an eligibility optimizer.

        Args:
            optimizer (WelfareProgramEligibilityOptimizer): An instance of the optimizer class.
        """
        self.optimizer = optimizer

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
            return getattr(response, "text", str(response))
        except Exception:
            # On any error, return a simple fallback question
            return f"What is your {field}?"