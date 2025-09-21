import models.user as user_model

class RankProgramsBot:
    """
    A bot that ranks welfare programs based on user eligibility and preferences.
    """
    def __init__(self, df=None, program_whitelist=None, user=None):
        """
        Initialize the RankProgramsBot.

        Args:
            df (pd.DataFrame): DataFrame of welfare programs (rows = programs).
            program_whitelist (list[str]): List of program names to include.
        """

        self.user = user_model.User() if user is None else user
        self.programs_ranking = {}
        # Lazy import to avoid circular imports at module load time
        import pandas as pd

        if df is None:
            self.df = pd.DataFrame()
        else:
            # copy to avoid mutating caller's df
            self.df = df.copy()

        if program_whitelist is None:
            program_whitelist = []

        # Normalize whitelist to strings
        program_whitelist = [str(x).strip() for x in program_whitelist]

        # Attempt to determine program identifier column (index named 'program', column 'program', or first column)
        if hasattr(self.df, 'index') and self.df.index.name == 'program':
            # filter by index
            self.filtered_df = self.df.loc[[p for p in program_whitelist if p in self.df.index]]
        else:
            # Try 'program' column
            if 'program' in self.df.columns:
                self.filtered_df = self.df[self.df['program'].astype(str).isin(program_whitelist)].copy()
            elif len(self.df.columns) > 0:
                first_col = self.df.columns[0]
                self.filtered_df = self.df[self.df[first_col].astype(str).isin(program_whitelist)].copy()
            else:
                self.filtered_df = self.df.copy()

        # Ensure filtered_df is a DataFrame object
        if not isinstance(self.filtered_df, pd.DataFrame):
            self.filtered_df = pd.DataFrame(self.filtered_df)
            
            
    def rank_programs(self):
        """
        Rank welfare programs based on user eligibility and preferences.

        Args:
            programs_ranking (dict): A dictionary containing program names as keys and their
            corresponding eligibility scores as values.

        Returns:
            pd.DataFrame: A DataFrame of ranked programs.
        """

        # Sort programs by their eligibility scores
        programs_count = len(self.filtered_df)
        for i in range(programs_count):
            program_name = self.filtered_df.iloc[i, 0]  # Assuming the first column contains program names
            score = 5000 # initialize score to 0
            # Initialize fields for each program
            age_range = (self.filtered_df.iloc[i, 1], self.filtered_df.iloc[i, 2])
            is_only_for_citizens_and_lawful_residents = self.filtered_df.iloc[i, 3]
            needs_permanent_address = self.filtered_df.iloc[i, 4]
            household_size_considered = self.filtered_df.iloc[i, 5]
            max_monthly_income = self.filtered_df.iloc[i, 6]
            employment_required = self.filtered_df.iloc[i, 7]
            disability_status_considered = self.filtered_df.iloc[i, 8]
            is_veteran = self.filtered_df.iloc[i, 9]
            criminal_record_disqualifying = self.filtered_df.iloc[i, 10]
            is_for_children = self.filtered_df.iloc[i, 11]
            is_for_refugees = self.filtered_df.iloc[i, 12]
            if self.user.age is not None and age_range[0] is not None and age_range[1] is not None:
                if age_range[0] <= self.user.age <= age_range[1]:
                    score += 2
            if self.user.citizen_or_lawful_resident is not None and is_only_for_citizens_and_lawful_residents is not None:
                if self.user.citizen_or_lawful_resident != is_only_for_citizens_and_lawful_residents:
                    score -= 100
            if self.user.has_permanent_address is not None and needs_permanent_address is not None:
                if self.user.has_permanent_address != needs_permanent_address:
                    score -= 50
            if self.user.lives_with_people is not None and household_size_considered is not None:
                if self.user.lives_with_people == household_size_considered:
                    score += 1
            if self.user.monthly_income is not None and max_monthly_income is not None:
                if self.user.monthly_income <= max_monthly_income:
                    score += 3
                else:
                    score -= 9
            if self.user.employed is not None and employment_required is not None:
                if self.user.employed == employment_required:
                    score += 1
                else:
                    score -= 3
            if self.user.disabled is not None and disability_status_considered is not None:
                if self.user.disabled == disability_status_considered:
                    score += 4
            if self.user.is_veteran is not None and is_veteran is not None:
                if self.user.is_veteran != is_veteran:
                    score -= 100
            if self.user.has_criminal_record is not None and criminal_record_disqualifying is not None:
                if self.user.has_criminal_record == criminal_record_disqualifying:
                    score -= 100
            if self.user.has_children is not None and is_for_children is not None:
                if self.user.has_children == is_for_children:
                    score += 3
            if self.user.is_refugee is not None and is_for_refugees is not None:
                if self.user.is_refugee != is_for_refugees:
                    score += 100
            if score > 0:
                
                self.programs_ranking[program_name] = score
        return [k for k, v in sorted(self.programs_ranking.items(), key=lambda x: x[1], reverse=True)]
