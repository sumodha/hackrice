import pandas as pd
import numpy as np


class WelfareProgramEligibilityOptimizer:
    """
    A class to optimize the selection of questions for determining eligibility
    for social welfare programs.
    """

    def __init__(self, eligibility_data_path='/Users/stevenzhang/Downloads/Eligibility_Data.csv', field_weights=None):
        """
        Initializes the optimizer with eligibility data and optional field weights.

        Args:
            eligibility_data_path (str): Path to the CSV file containing eligibility data.
            field_weights (dict): A dictionary mapping field names to weights (float).
            If None, all fields have a weight of 1.0.
        """
        self.df = pd.read_csv(eligibility_data_path)
        # Set the program name as the index for easier filtering
        self.df.set_index('program', inplace=True)

        # Store all fields (columns)
        self.all_fields = set(self.df.columns)

        # Set default weights if none provided
        if field_weights is None:
            self.field_weights = {
                'is_only_for_citizens_and_lawful_residents': 0.5,  # Half as important
                'household_size_considered': 1.5,  # 50% more important
                'employment_required': 1.2,  # Slightly more important
                'is_veteran': 1.1,  # Slightly less important
                'is_for_children' : 1.2,
                'criminal_record_disqualifying' : 1.2
        }
        else:
            # Ensure all fields have a weight, defaulting to 1.0 if not specified
            self.field_weights = custom_weights = {
            'is_only_for_citizens_and_lawful_residents': 0.5,  # Half as important
            'household_size_considered': 1.5,  # 50% more important
            'employment_required': 1.2,  # Slightly more important
            'is_veteran': 1.1,  # Slightly less important
            'is_for_children' : 1.2,
            'criminal_record_disqualifying' : 1.2

            }

    def _apply_blacklists(self, field_blacklist, program_blacklist):
        """
        Applies the blacklists to filter the dataframe.

        Args:
            field_blacklist (list): List of field names already asked.
            program_blacklist (list): List of program names already deemed ineligible.

        Returns:
            pd.DataFrame: A filtered dataframe.
        """
        # Start with the full dataframe
        filtered_df = self.df.copy()

        # Remove ineligible programs
        if program_blacklist:
            valid_programs_to_drop = set(program_blacklist).intersection(filtered_df.index)
            filtered_df = filtered_df.drop(index=valid_programs_to_drop, errors='ignore')

        # Remove already asked fields (columns)
        if field_blacklist:
            valid_fields_to_drop = set(field_blacklist).intersection(filtered_df.columns)
            filtered_df = filtered_df.drop(columns=valid_fields_to_drop, errors='ignore')

        return filtered_df

    def _calculate_information_gain(self, filtered_df, candidate_field):
        """
        Calculates a score representing the information gain for a candidate field.
        The score is based on how much the field can reduce the number of potential programs.

        Args:
            filtered_df (pd.DataFrame): The current dataframe after applying blacklists.
            candidate_field (str): The field to evaluate.

        Returns:
            float: The information gain score.
        """
        if candidate_field not in filtered_df.columns:
            return 0

        # Get unique, non-null values in this field for the remaining programs
        unique_values = filtered_df[candidate_field].dropna().unique()

        # If all remaining programs have the same value (or are null), this field is not helpful
        if len(unique_values) <= 1:
            return 0

        total_programs = len(filtered_df)
        if total_programs == 0:
            return 0

        # Calculate the reduction in search space
        value_counts = filtered_df[candidate_field].value_counts(dropna=False)

        # The maximum number of programs sharing a single value for this field
        max_in_single_group = value_counts.max() if not value_counts.empty else 0

        # Score based on programs that can potentially be ruled out
        # This rewards fields where the max group is small (more even distribution)
        programs_ruled_out_score = total_programs - max_in_single_group

        # Normalize by total programs to get a relative score
        normalized_score = programs_ruled_out_score / total_programs if total_programs > 0 else 0

        # Bonus for having many distinct values (more potential to differentiate)
        distinct_value_bonus = len(unique_values) / len(self.df[candidate_field].dropna().unique())

        # Combine the two metrics
        final_score = normalized_score * (1 + 0.1 * distinct_value_bonus)

        return final_score

    def get_next_fields(self, field_blacklist, program_blacklist, top_n=3):
        """
        Determines the top N fields to ask next to narrow down the search.

        Args:
            field_blacklist (list): List of field names already asked.
            program_blacklist (list): List of program names already deemed ineligible.
            top_n (int): The number of top fields to return.

        Returns:
            list: A list of the top N field names.
        """
        # 1. Apply blacklists to get the current search space
        current_df = self._apply_blacklists(field_blacklist, program_blacklist)

        # 2. Determine candidate fields (remaining fields not in the field_blacklist)
        candidate_fields = list(set(current_df.columns) - set(field_blacklist))

        # 3. Calculate weighted information gain for each candidate field
        weighted_scores = {}
        for field in candidate_fields:
            info_gain = self._calculate_information_gain(current_df, field)
            weight = self.field_weights.get(field, 1.0)
            weighted_scores[field] = info_gain * weight

        # 4. Sort fields by their weighted score in descending order and return top N
        sorted_fields = sorted(weighted_scores.items(), key=lambda item: item[1], reverse=True)

        # Extract just the field names for the top N results
        top_fields = [field for field, score in sorted_fields[:top_n]]

        return top_fields