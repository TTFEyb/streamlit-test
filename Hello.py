# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

 # Importing required packagesc
import streamlit as st
import time
from openai import OpenAI
from streamlit.logger import get_logger

LOGGER = get_logger(__name__)

# Set your OpenAI API key and assistant ID here
api_key         = st.secrets["openai_apikey"]
assistant_id    = st.secrets["assistant_id"]

# Set openAi client , assistant ai and assistant ai thread
@st.cache_resource
def load_openai_client_and_assistant():
    client          = OpenAI(api_key=api_key)
    my_assistant    = client.beta.assistants.retrieve(assistant_id)
    thread          = client.beta.threads.create()

    return client , my_assistant, thread

client,  my_assistant, assistant_thread = load_openai_client_and_assistant()

# check in loop  if assistant ai parse our request
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

# initiate assistant ai response
def get_assistant_response(user_input=""):
    try:
        # Create a message
        message = client.beta.threads.messages.create(
            thread_id=assistant_thread.id,
            role="user",
            content=user_input,
        )
        
        # Create a run
        run = client.beta.threads.runs.create(
            thread_id=assistant_thread.id,
            assistant_id=assistant_id,
        )

        # Wait for the run to finish
        run = wait_on_run(run, assistant_thread)

        # Retrieve all the messages added after our last user message
        messages = client.beta.threads.messages.list(
            thread_id=assistant_thread.id, order="asc", after=message.id
        )

        # Check if messages is empty or not
        if not messages.data:
            return "No response from the assistant."
        
        # Return the content of the latest message
        return messages.data[0].content[0].text.value
    
    except Exception as e:
        return f"An error occurred: {str(e)}"


if 'user_input' not in st.session_state:
    st.session_state.user_input = ''

def submit():
    st.session_state.user_input = st.session_state.query
    st.session_state.query = ''


st.title("ChatGPT integration test")

st.text_input("Awaiting input:", key='query', on_change=submit)

user_input = st.session_state.user_input

st.write("You entered: ", user_input)

if user_input:
    result = get_assistant_response(user_input)
    st.header('Assistant reply:', divider='rainbow')
    st.text(result)