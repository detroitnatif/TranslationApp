import os
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from langchain_groq import ChatGroq
from langchain import hub
from langchain.agents import load_tools, AgentExecutor, create_react_agent
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
import asyncio

class LangchainSearchApp:
    def __init__(self):
        load_dotenv(find_dotenv())
        groq_api_key = os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(temperature=0.5, model_name="mixtral-8x7b-32768", groq_api_key=groq_api_key)
        self.tools = load_tools(["ddg-search"])
        self.prompt = hub.pull("hwchase17/react")
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
        self.st_callback = StreamlitCallbackHandler(st.container())

    def enrich_query_with_context(self, prompt):
        # Extract the last agent response from the conversation history
        last_response = ""
        if st.session_state.conversation_history:
            for entry in reversed(st.session_state.conversation_history):
                if 'agent' in entry:
                    last_response = entry['agent']
                    break
        # Combine the last response with the new prompt for enriched context
        enriched_prompt = f"{last_response} {prompt}" if last_response else prompt
        return enriched_prompt

    def invoke_agent(self, prompt):
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []

        enriched_prompt = self.enrich_query_with_context(prompt)
        
        response = self.agent_executor.invoke(
            {"input": enriched_prompt},
            {"callbacks": [self.st_callback]}
        )
        
        st.session_state.conversation_history.append({'user': prompt})
        
        if response and "output" in response:
            st.session_state.conversation_history.append({'agent': response["output"]})
            return response["output"]
        else:
            return "An error occurred, or the response was not in the expected format."

    def run(self):
        st.title("GroqSearch")
        if 'conversation_history' in st.session_state:
            for interaction in st.session_state.conversation_history:
                if 'user' in interaction:
                    st.text_area("User", value=interaction['user'], disabled=True, height=100)
                if 'agent' in interaction:
                    st.text_area("Assistant", value=interaction['agent'], disabled=True, height=100)

        user_input = st.text_input("Ask me anything:", key="new_prompt")

        submit_button = st.button("Submit")

        if submit_button:
            response_output = self.invoke_agent(user_input)
            st.experimental_rerun()

import pkg_resources
import importlib



if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # List of imported modules in your script
    imported_modules = [
    'os',
    'streamlit',
    'dotenv',
    'langchain_groq',
    'langchain',
    'asyncio'
    ]

    for module_name in imported_modules:
        try:
            # Attempt to import the module to ensure it's a valid import
            module = importlib.import_module(module_name)
            # Get the version of the module
            version = pkg_resources.get_distribution(module_name).version
            print(f"{module_name}: {version}")
        except ImportError:
            print(f"{module_name}: Module not found.")
        except Exception as e:
            print(f"Error retrieving version for {module_name}: {e}")   



    app = LangchainSearchApp()
    app.run()