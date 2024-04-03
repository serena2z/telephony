from typing import Optional, Tuple
import logging
from vocode.streaming.agent.base_agent import BaseAgent, RespondAgent
from vocode.streaming.models.agent import AgentConfig
from vocode.streaming.agent.factory import AgentFactory
import typing
import sqlite3
import re
from word2number import w2n


class InformationCollectorAgentConfig(AgentConfig, type="agent_info_collector"):
    """Configuration for InformationCollectorAgent. Inherits from AgentConfig."""
    pass


class InformationCollectorAgent(RespondAgent[InformationCollectorAgentConfig]):
    """InformationCollectorAgent class. Inherits from RespondAgent.

    This agent collects various pieces of information from the caller in a sequential order.
    """

    def __init__(self, agent_config: InformationCollectorAgentConfig):
        """Initializes InformationCollectorAgent with the given configuration.

        Args:
            agent_config (InformationCollectorAgentConfig): The configuration for this agent.
        """
        super().__init__(agent_config=agent_config)
        self.collected_information = {}
        self.information_sequence = [
            "first name",
            "last name",
            "date of birth",
            "payer name for your insurance",
            "ID number for your insurance",
            "referral information (if any, and to which physician)",
            "reason for visit",
            "address",
            "contact information",
            "preferred appointment",
        ]
        self.appointment_info = {
            "Mark Zuck": "2030-01-01 10:00:00",
            "Bill Gates": "2040-01-02 11:00:00",
            "Elon Musk": "2050-01-03 12:00:00",
            "Jeff Bezos": "2060-01-04 13:00:00",
        }
        self.first_interaction = True

    async def respond(
        self,
        human_input: str,
        conversation_id: str,
        is_interrupt: bool = False,
    ) -> Tuple[Optional[str], bool]:
        """Generates a response from the InformationCollectorAgent.

        The response prompts the caller to provide the next piece of information in the sequence.
        The second element of the tuple indicates whether the agent should stop (False means it should not stop).

        Args:
            human_input (str): The input from the human user.
            conversation_id (str): The ID of the conversation.
            is_interrupt (bool): A flag indicating whether the agent was interrupted.

        Returns:
            Tuple[Optional[str], bool]: The generated response and a flag indicating whether to stop.
        """

        if self.first_interaction:
            self.first_interaction = False
            response = f"Please provide your {self.information_sequence[0]}."
            return response, False

        # Get the next piece of information to collect
        next_information = self.information_sequence[0]

        if next_information == "first name":
            self.collected_information["firstname"] = human_input
        elif next_information == "last name":
            self.collected_information["lastname"] = human_input
        elif next_information == "preferred appointment":
            # parse the human input from letters to numbers
            number = w2n.word_to_num(human_input)
            # Retrieve the appointment corresponding to the input number
            appointment_names = list(self.appointment_info.keys())
            if 1 <= number <= len(appointment_names):
                selected_appointment_name = appointment_names[number - 1]
                selected_appointment_datetime = self.appointment_info[selected_appointment_name]
                self.collected_information["preferred_appointment"] = f"{selected_appointment_name}: {selected_appointment_datetime}"
            else:
                return "Invalid appointment number. Please select a valid appointment.", False

        available_appointments = "\n".join([f"Number {i}: {name} at {datetime}" for i, (name, datetime) in enumerate(self.appointment_info.items(), 1)])
        # Remove the collected information from the sequence
        print(self.collected_information)
        self.information_sequence.pop(0)
        print(self.information_sequence)
        # Generate the response prompt
        if self.information_sequence:
            if self.information_sequence[0] == "preferred appointment":
                # Generate the response prompt for booking appointments
                response = f"Here are your available appointments:\n{available_appointments}\n\n" \
                        "Please select one of the available appointments by providing the corresponding appointment number."
            else:
                response = f"Please provide your {self.information_sequence[0]}."
        else:
            await self.write_to_database(conversation_id)
            response = "Thank you for providing all the information. You will get a text for your appointment shortly when you hang up on this call. Have a good day."

        return response, False
    
    async def write_to_database(self, conversation_id: str):
        # Connect to the database (or create it if it doesn't exist)
        conn = sqlite3.connect('./database/collected_information.db')
        cursor = conn.cursor()

        # Create a table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS collected_information
                        (conversation_id TEXT, name TEXT, preferred_appointment TEXT)''')

        # Insert the collected information into the table
        name = self.collected_information.get("firstname")
        preferred_appointment = self.collected_information.get("preferred_appointment")
        cursor.execute("INSERT INTO collected_information VALUES (?, ?, ?)",
                    (conversation_id, name, preferred_appointment))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()


class InformationCollectorAgentFactory(AgentFactory):
    """Factory class for creating agents based on the provided agent configuration."""

    def create_agent(
        self, agent_config: AgentConfig, logger: Optional[logging.Logger] = None
    ) -> BaseAgent:
        """Creates an agent based on the provided agent configuration.

        Args:
            agent_config (AgentConfig): The configuration for the agent to be created.
            logger (Optional[logging.Logger]): The logger to be used by the agent.

        Returns:
            BaseAgent: The created agent.

        Raises:
            Exception: If the agent configuration type is not recognized.
        """
        # If the agent configuration type is agent_info_collector, create an InformationCollectorAgent.
        if agent_config.type == "agent_info_collector":
            return InformationCollectorAgent(
                # Cast the agent configuration to InformationCollectorAgentConfig as we are sure about the type here.
                agent_config=typing.cast(InformationCollectorAgentConfig, agent_config)
            )
        # If the agent configuration type is not recognized, raise an exception.
        raise Exception("Invalid agent config")
