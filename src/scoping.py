import json
from logzero import logger
from src.llm._types import Message, Role
from src.llm.models import agent_setup


class Scoping:
    def __init__(self, model: str, temp: float, top_p: float, max_tokens: int):
        """
        Initialize the Scoping Agent with model configuration.

        Args:
            model (str): The model name for the Scoping Agent.
            temp (float): The temperature for the Scoping Agent model.
            top_p (float): The top_p for the Scoping Agent model.
            max_tokens (int): The maximum tokens for the Scoping Agent model.
        """
        self.chat = agent_setup(agent_model=model, agent_temp=temp, agent_top_p=top_p, agent_max_tokens=max_tokens)

    @staticmethod
    def get_system_prompt() -> str:
        system_prompt_template = """You are an interactive agent designed to help the user set up and test their LLM Bot. 
        You will ask a series of questions to gather the necessary information, store the responses, and guide the user through the process. 
        If the user wishes to go back and change a previous response, allow them to do so and then continue from where they left off. 
        Once all responses are collected, combine them into a JSON array and present it to the user. 
        Be clear, concise, and ensure the user is guided throughout the process."""
        return system_prompt_template

    def analyze_response(self, response: str, current_question: int) -> int:
        """
        Analyze the user's response to see if they are answering the current question
        or requesting to change a previous answer.

        Args:
            response (str): The user's input response.
            current_question (int): The current question being asked.

        Returns:
            int: The question number to ask next (0-based index).
        """
        response = response.lower()

        # Keywords associated with each question
        keywords = {
            0: ["name", "call", "bot"],
            1: ["ip", "asset", "location"],
            2: ["token", "api"],
            3: ["prompt", "ask"],
            4: ["techniques", "select", "all", "testing"]
        }

        # Check if the response contains a keyword that suggests going back to a previous question
        for question_num, key_phrases in keywords.items():
            if any(phrase in response for phrase in key_phrases):
                return question_num

        # If no keyword is matched, return the current question index to continue
        return current_question

    def run_scoping_session(self):
        system_prompt = self.get_system_prompt()
        messages = [Message(role=Role.system, content=system_prompt)]

        # The list of questions to ask the user
        questions = [
            "What would you like to call this bot?",
            "Please provide the Asset/IP where your bot is located:",
            "Please provide your API token:",
            "What prompt would you like to ask the bot?",
            "Would you like to use all testing techniques or select specific ones? (All Techniques/Select Techniques)"
        ]

        responses = {}
        current_question = 0
        stored_question = 0

        while current_question < len(questions):
            question = questions[current_question]
            print(f"Q{current_question + 1}: {question}")
            user_response = input("Your response: ").strip()

            # Analyze the response to check if they want to change a previous answer
            target_question = self.analyze_response(user_response, current_question)

            if target_question != current_question:
                print(f"\nYou seem to want to change the response for Question {target_question + 1}. Let's go back.\n")
                stored_question = current_question
                current_question = target_question
            else:
                # Store the current response and move to the next question
                responses[question] = user_response
                if stored_question != 0:
                    current_question = stored_question
                    stored_question = 0
                else:
                    current_question += 1

        # Review answers
        while True:
            print("\nHere are your responses:")
            for i, (question, answer) in enumerate(responses.items(), 1):
                print(f"{i}. {question}: {answer}")

            modify_response = input("If you want to change any response, type the relevant keyword (e.g., 'name', "
                                    "'IP', 'token'). If everything looks good, type 'submit': ").strip()

            if modify_response.lower() == 'submit':
                break
            else:
                # Use the analyze_response method to figure out which question to change based on keyword
                target_question = self.analyze_response(modify_response, len(questions))

                if target_question != len(questions):
                    print(f"\nLet's go back to Question {target_question + 1}.")
                    current_question = target_question
                    while current_question < len(questions):
                        question = questions[current_question]
                        print(f"Q{current_question + 1}: {question}")
                        user_response = input("Your response: ").strip()
                        responses[question] = user_response
                        current_question = i
                else:
                    print("Invalid input. Please try again.")

        # After confirmation, convert responses to JSON array
        final_json_array = json.dumps([{q: a} for q, a in responses.items()], indent=4)
        print(f"\nFinal JSON array:\n{final_json_array}")
        logger.debug(f"Final JSON: {final_json_array}")


if __name__ == '__main__':
    scoping_agent = Scoping(model='gpt-4o', temp=0.4, top_p=1.0, max_tokens=4096)
    scoping_agent.run_scoping_session()
