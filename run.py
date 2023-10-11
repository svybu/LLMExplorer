import subprocess
import os



def run():

    fastapi_server = subprocess.Popen(["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"])

    streamlit_server = subprocess.Popen(["streamlit", "run", "LLM_Chat_v3.py", "--server.headless", "true"])

    try:

        fastapi_server.wait()
        streamlit_server.wait()
    except KeyboardInterrupt:

        fastapi_server.terminate()
        streamlit_server.terminate()

if __name__ == "__main__":
    run()
