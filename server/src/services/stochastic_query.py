import pandas as pd
import random

all_questions = [
    [
        "How old are you?",
        "Can you tell me your age?",
        "What’s your current age?",
        "How many years old are you?",
        "Please share your age.",
        "Could you tell me your age in years?",
        "What age are you right now?",
        "How many years have you lived?",
        "May I ask your age?",
        "What is your age today?",
        "Tell me your age, please.",
        "About how old are you?",
        "Can you give me your age?",
        "What’s your exact age in years?", 
        "How old are you?",
        "Can you tell me your age?",
        "What’s your current age?",
        "How many years old are you?",
        "Please share your age.",
        "Could you tell me your age in years?",
        "What age are you right now?",
        "How many years have you lived?",
        "May I ask your age?",
        "What is your age today?",
        "Tell me your age, please.",
        "About how old are you?",
        "Can you give me your age?",
        "What’s your exact age in years?"
    ],
    [
        "Do you have legal status to live in the United States?",
        "Are you officially a citizen or lawful resident of the U.S.?",
        "Do you hold a U.S. passport or a green card?",
        "Do you have permission to permanently live in the U.S.?",
        "Are you considered a citizen or legal resident here in the U.S.?",
        "Do you currently have U.S. citizenship or permanent residency?",
        "Do you hold U.S. citizenship or lawful permanent resident status?",
        "Do you have the right to live here as a citizen or resident?",
        "Are you recognized as a U.S. citizen or a green card holder?"
    ],
    [
        "Do you have a permanent place to live?",
        "Do you have a place you stay most of the time?",
        "Do you have a home you can list as your address?",
        "Do you stay at a stable address right now?",
        "Do you currently live at a fixed address?",
        "Is there a main address where you live?",
        "Do you have housing you consider permanent?",
        "Do you live somewhere with a mailing address?",
        "Do you have your own place or live at someone else’s regularly?",
        "Do you have a usual place of residence?"
    ],
    [
        "Do you live by yourself or with other people?",
        "Are there other people living with you?",
        "Do you share your home with family, friends, or others?",
        "Do you live alone or not?",
        "Are you living in the same place with others?",
        "Do you have housemates, relatives, or others at home?",
        "Is your household just you, or are there others?",
        "Do you stay alone or with people?",
        "Are there others living in your home?",
        "Do you currently live with anyone else?",
        "Do you share your housing with others?",
        "Do you have family members or roommates living with you?",
        "Are you living together with other people?",
        "Do you live solo or with company?",
        "Is anyone else staying where you live?", 
        "Do you live by yourself or with other people?",
        "Are there other people living with you?",
        "Do you share your home with family, friends, or others?",
        "Do you live alone or not?",
        "Are you living in the same place with others?",
        "Do you have housemates, relatives, or others at home?",
        "Is your household just you, or are there others?"
    ],

    [
        "Are you currently working a job?",
        "Do you have a job right now?",
        "Are you employed at the moment?",
        "Do you have paid work right now?",
        "Do you have work you get paid for?",
        "Are you employed either part-time or full-time?",
        "Are you in any kind of paid employment?",
        "Do you have active work right now?",
    ],
    [
        "Do you have a disability?",
        "Do you have a condition that counts as a disability?",
        "Do you have health issues that limit daily activities?",
        "Are you currently disabled?",
        "Do you have a physical or mental condition that makes daily life harder?",
        "Have doctors or agencies said you have a disability?",
        "Are you living with a disabling condition?",
        "Do you deal with a long-term disability?"
    ],
    [
        "Have you ever served in the U.S. military?",
        "Are you a military veteran?",
        "Have you been part of the U.S. military before?",
        "Did you ever join the military?",
        "Did you serve in the U.S. military in the past?",
        "Have you been in the Army, Navy, Air Force, Marines, or Coast Guard?",
        "Are you a former service member?",
        "Did you previously serve in the U.S. military?",
    ],
    [
        "Have you ever been convicted of a crime?",
        "Do you have a criminal record?",
        "Have you been arrested and convicted before?",
        "Do you have a history of criminal charges?",
        "Have you had any criminal offenses?",
        "Have you ever been found guilty of a crime?",
        "Do you have any past criminal history?",
    ],
    [
        "Do you have children?",
        "Are you a parent?",
        "Do you have kids you care for?",
        "Do you have any sons or daughters?",
        "Are you responsible for raising children?",
        "Do you live with your children?",
        "Do you currently take care of kids?",
        "Do you have children in your household?",
        "Are you a mother or father?",
        "Do you have children depending on you?",
        "Do you look after any children?",
        "Are there children you are caring for?",
        "Do you have any kids of your own?",
        "Are you raising children?",
        "Do you have children living with you?", 
        "Do you have children?",
        "Are you a parent?",
        "Do you have kids you care for?",
        "Do you have any sons or daughters?",
        "Are you responsible for raising children?",
        "Do you live with your children?",
        "Do you currently take care of kids?",
        "Do you have children in your household?",
        "Are you a mother or father?",
        "Do you have children depending on you?",
        "Do you look after any children?",
        "Are there children you are caring for?"],
    [
        "Have you been granted refugee status in the U.S.?",
        "Have you come to the U.S. as a refugee?",
        "Do you have refugee status?",
        "Were you admitted to the U.S. as a refugee?",
        "Are you officially a refugee?",
        
    ]]


class query_user:
    def __init__(self):
        self.questions = all_questions
        self.all_responses = "Question: What's your monthly income?"

    def next_question(self):
        cache = self.questions.pop(random.randint(0, len(self.questions) - 1))

        return cache[random.randint(0, len(cache) - 1)]

    def update_responses(self, input_str): 
        self.all_responses += str(input_str)

