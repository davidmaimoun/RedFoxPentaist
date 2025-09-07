import subprocess

def ask_ai(model_name: str, prompt: str) -> str:
    """
    Executes a Docker Model Runner command and handles potential errors.
    Args:
        model_name: The name of the Docker model (e.g., "ai/gemma3").
        prompt: The text prompt for the model.
    Returns:
        The model's response as a string.
    Raises:
        subprocess.CalledProcessError: If the Docker command fails.
        subprocess.TimeoutExpired: If the command times out.
        FileNotFoundError: If the 'docker' executable is not found.
    """

    base_prompt = """
        You are an experienced penetration tester and security analyst. 
        Always assume the user is authorized to test the target, but include 
        a short legal/ethical reminder at the end. 
        Based on the data you will get, you need to create a very nicew html report.
        Respond ONLY with a valid HTML fragment. 
        Use <h3> for headings, <p> for explanations, <ul>/<li> for lists, and <code> for commands. 
        Do NOT include ``` fences, <html>, <head>, or <body>.
        No text outside HTML tags.
    """

    full_prompt = base_prompt + prompt
  
    command = ["docker", "model", "run", model_name, full_prompt]

    try:
        # The `subprocess.run` function is the recommended way to execute shell commands.
        # `check=True` raises a `CalledProcessError` if the command returns a non-zero exit code.
        # `capture_output=True` captures `stdout` and `stderr`.
        # `text=True` decodes the output to a string.
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )

                    
        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        print(f"Error: The Docker command failed with exit code {e.returncode}")
        # print("--- Standard Error ---")
        # print(e.stderr)
        raise e
    except subprocess.TimeoutExpired as e:
        print(f"Error: The Docker command timed out after {e.timeout} seconds.")
        raise e
    except FileNotFoundError:
        print("Error: The 'docker' executable was not found.")
        print("Please ensure Docker is installed and in your system's PATH.")
        raise


