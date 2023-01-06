#!/usr/bin/env python3


"""
This is a pre-commit-msg hook that uses the OpenAI API to get a suggested commit message
for the diff that is about to be committed.

To use this hook, you will need to:
- Set the OPENAI_API_KEY environment variable to your OpenAI API key.

To install this hook, follow these steps:
1. Place this file in the `.git/hooks` directory in your Git repository.
2. Make sure the file is executable. You can do this by running the following command:
   `chmod +x .git/hooks/pre-commit-msg`

This hook is invoked by Git just before the commit message editor is launched,
and it is passed the name of the file that holds the commit message.
The hook should edit this file in place and then exit.
If the hook exits non-zero, Git aborts the commit process.
"""

import http.client
import json
import os
import re
import socket
import subprocess
import sys
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse


class CommitMessage:
    """A commit message consists of a description and one or more subject lines.

    Attributes:
        description (str): A brief description of the commit.
        subject_lines (list(str)): One or more lines describing the changes made in the commit.
        text (str): The full commit message, including both the description and the subject lines.
    """

    def __init__(self, description: str, subject_lines: List[str], text: str):
        self.description = description
        self.subject_lines = subject_lines
        self.text = text


class Completion:
    """Stores a text completion with its associated score and model.

    Attributes:
        text (str): The completion text.
        index (int): The index of the completion in the list of completions returned by the API.
        logprobs (list(float)): The log probabilities of each token in the completion.
        finish_reason (str): The reason the completion finished.
    """

    def __init__(
        self, text: str, index: int, logprobs: List[float], finish_reason: str
    ):
        self.text = text
        self.index = index
        self.logprobs = logprobs
        self.finish_reason = finish_reason

    def text_lines(self):
        """Return the completion text as a list of lines."""
        return self.text.splitlines()


class CompletionRequest:
    """Stores the parameters used to generate a completion."""

    def __init__(self, prompt: str, model: str, max_tokens: int, temperature: float):
        self.prompt = prompt
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def to_dict(self) -> Dict:
        """Convert the completion request to a dictionary."""
        return {
            "prompt": self.prompt,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


class CompletionResponse:
    """Stores a list of completions generated by an AI model.

    Attributes:
        completions (list(Completion)): The list of completions generated by the model.
    """

    def __init__(self, completions: List[Completion]):
        self.completions = completions


class OpenAIApiException(Exception):
    """
    An exception that is raised when the OpenAI API returns an error.
    """

    pass


class OpenAIModelOverloadException(OpenAIApiException):
    """
    An exception that is raised when the OpenAI API returns a model overload error.
    """

    pass


class OpenAIBadCompletionException(OpenAIApiException):
    """
    An exception that is raised when the OpenAI API returns a bad completion.
    """

    pass


class OpenAIApiClient:
    """
    A simple wrapper around the OpenAI API
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Constructor for the OpenApiClient class.

        Parameters:
        api_key (str, optional): The OpenAI API key to be used. If not provided, the value of the
            OPENAI_API_KEY environment variable will be used.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.host: str = "api.openai.com"
        self.conn = http.client.HTTPSConnection(host=self.host, port=443, timeout=10)
        self.route_completion = "/v1/completions"

    def _create_headers(self) -> Dict[str, str]:
        """Create the headers for the request to the OpenAI API."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _send_request(
        self, request: CompletionRequest, headers: Dict[str, str]
    ) -> CompletionResponse:
        """Send a POST request to the OpenAI API and return the response data as a CompletionResponse object."""
        data: bytes = json.dumps(request.to_dict()).encode("utf-8")
        self.conn.request("POST", self.route_completion, body=data, headers=headers)
        response: http.client.HTTPResponse = self.conn.getresponse()
        response_data = response.read()
        try:
            # {'id': 'cmpl-6ViayJ6ZhIl5HmAOpiA23oX4naca9', 'object': 'text_completion', 'created': 1673017612, 'model': 'text-davinci-003', 'choices': [{'text': 'response', 'index': 0, 'logprobs': None, 'finish_reason': 'length'}], 'usage': {'prompt_tokens': 3759, 'completion_tokens': 300, 'total_tokens': 4059}}
            response_data = json.loads(response_data)
            # {'error': {'message': 'That model is currently overloaded with other requests. You can retry your request, or contact us through our help center at help.openai.com if the error persists. (Please include the request ID 44fa8f95f731a58124b775d316c1b044 in your message.)', 'type': 'server_error', 'param': None, 'code': None}}
            if "error" in response_data:
                print(
                    f"\033[01;31mError: {response_data['error']['message']}\033[0;0m",
                    file=sys.stderr,
                )
                # try again
                if response_data["error"]["message"].startswith(
                    "That model is currently overloaded"
                ):
                    raise OpenAIModelOverloadException(
                        response_data["error"]["message"]
                    )

            completions = [
                Completion(c["text"], c["index"], c["logprobs"], c["finish_reason"])
                for c in response_data["choices"]
            ]
            return CompletionResponse(completions)
        except json.JSONDecodeError:
            print(
                f"\033[01;31mError: Invalid JSON response from the API\033[0;0m",
                file=sys.stderr,
            )
            print(f"\033[01;31m{response_data}\033[0;0m", file=sys.stderr)
            raise OpenAIApiException("Error decoding JSON response from OpenAI API")
        except KeyError:
            print(
                f"\033[01;31mError: Invalid response from the API\033[0;0m",
                file=sys.stderr,
            )
            print(f"\033[01;31m{response_data}\033[0;0m", file=sys.stderr)
            raise OpenAIApiException("Error parsing JSON response from OpenAI API")

    def _check_response(self, response: CompletionResponse) -> bool:
        """Check if the response from the OpenAI API is valid."""
        if not response.completions:
            print(
                "\033[01;31mError: No completions returned from the API\033[0;0m",
                file=sys.stderr,
            )
            return False
        return True

    def parse_commit_message(self, completion: Completion) -> CommitMessage:
        # Initialize variables to store the three sections
        description = ""
        subject_lines = []
        commit_message = ""

        # Iterate through the lines and extract the three sections
        section = None
        for line in completion.text_lines():
            if line.startswith("Subject lines:"):
                section = "subject_lines"
            elif line.startswith("Suggested commit message:"):
                section = "commit_message"
            elif line.startswith("- ") and section == "subject_lines":
                subject_lines.append(line[2:])
            elif section == "commit_message":
                commit_message += line + "\n"
            else:
                description += line + "\n"

        # Strip leading/trailing white space and remove the "(commit message written by OpenAI text-davinci-003)" line
        description = description.strip()
        commit_message = commit_message.strip()
        commit_message = re.sub(
            r"\(commit message written by OpenAI text-davinci-003\)", "", commit_message
        )

        # Return an instance of the CommitMessage class
        return CommitMessage(description, subject_lines, commit_message)

    def get_suggested_commit_message(
        self,
        prompt: str,
        model: str = "text-davinci-003",
        max_tokens: int = 300,
        temperature: float = 0.9,
    ) -> CommitMessage:
        """
        Get a completion from the OpenAI API.

        Parameters:
        prompt (str): The prompt to complete.
        model (str, optional): The name of the model to use for generating the completion.
            Defaults to "text-davinci-003".
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 64.
        temperature (float, optional): The temperature to use for generating the completion.
            Defaults to 0.9.

        Returns:
        str: The completion generated by the OpenAI API.
        """
        MAX_RETRIES = 3
        TIMEOUT = 10

        delay = 1
        for i in range(MAX_RETRIES):
            if i > 0:
                delay *= 2
                time.sleep(delay)
                print(f"Retrying...")

            try:
                request_data: CompletionRequest = CompletionRequest(
                    prompt, model, max_tokens, temperature
                )
                headers: Dict[str, str] = self._create_headers()
                response: CompletionResponse = self._send_request(request_data, headers)
                if not self._check_response(response):
                    raise OpenAIApiException("OpenAI API returned an invalid response")
                completion: Completion = response.completions[0]
                with open(".prompt", "a") as f:
                    f.write(completion.text)

                commit_message: CommitMessage = self.parse_commit_message(completion)

                return commit_message
            except socket.timeout:
                if time.time() > TIMEOUT:
                    raise e
                else:
                    print(f"\033[01;31mError: {e}\033[0;0m", file=sys.stderr)
            except Exception as e:
                if time.time() > TIMEOUT:
                    raise e
                else:
                    print(f"\033[01;31mError: {e}\033[0;0m", file=sys.stderr)

        raise OpenAIApiException("OpenAI API returned an invalid response")


def get_prompt(model: str, status_text: str, diff_text: str) -> str:
    return f"""
I want you to act as a technical writer for software engineers, your
primary responsibility is to write clear and concise commit messages
for code changes. Your job is to communicate the purpose and impact
of code changes to other members of the development team.

A good commit message has the following characteristics:
- It is concise and accurate.
- It is written in the imperative mood and begins with a verb
- It explains why the change was made, rather than how it was made.
- It includes a signature at the end of the message.

Here is an example of a good commit message:
```
🤖 Ensure non-empty password during login

The login form was submitting even if the password field was empty.
This commit fixes the bug by checking that the password field is not
empty before allowing the form to be submitted.


(commit message written by OpenAI {model})
```

Here is an example of a good commit message:
```text
🤖 Include latest dependencies for eslint, prettier

Updates the package.json file to include the latest
dependencies for prettier and eslint for code formatting.

prettier is a code formatter that automatically formats code to
conform to a consistent style. It is configured to use the
recommended settings for the JavaScript Standard Style.

eslint is a linter that checks for common errors and code smells.
It is configured to use the recommended settings for the
JavaScript Standard Style.


(commit message written by OpenAI {model})
```

Some other tips for writing good commit messages:
- Begin with "🤖 "
- Keep the subject line (the first line) to 50 characters or less
- Separate subject from body with a blank line
- Use the body of the message to explain the details of the commit
- Wrap the body at 72 characters                              like this
- Avoid words like "Update", "Refactor", "Fix", "Add", "Remove" in the
    subject line

At the end of the commit message, add two blank lines followed by a
signature:
```text
(commit message written by OpenAI {model})
```

Your first task is to review staged changes and suggest a commit
message for the latest patch.

Files changed:
```
// git status -s
{status_text}
```

Files diff:
```diff
// git diff --cached --no-color --no-ext-diff --unified=0 --no-prefix
{diff_text}
```

Choose a unique and stylish first line in the imperative tense
that concisely describes the changes made in the commit.
This line should be no more than 50 characters.

Now, please write a suggested commit message below that is clear,
concise, and colorful, following the rules described above,
beginning with "🤖 " and ending with the signature
"(commit message written by OpenAI {model})":

Respond with:
- A detailed paragraph explaining WHY the changes were made
- Ten unique, stylish, colorful, and concise subject lines
- A suggested commit message enclosed in ```text ... ```

Detailed explanation:
"""


def check_abort() -> None:
    """
    Check if the commit message file is not empty or if the OPENAI_API_KEY environment variable is not set.

    If the commit message file is not empty, print a message and exit.
    If the OPENAI_API_KEY environment variable is not set, print an error message in red and exit.
    """
    # Check if the commit message file is not empty
    with open(sys.argv[1], "r") as f:
        if f.readline().strip():
            print("Commit message already exists, exiting")
            exit(0)

    # Check if the OPENAI_API_KEY environment variable is not set
    if "OPENAI_API_KEY" not in os.environ:
        # Print an error message in red
        print("\033[0;31mOpenAI suggestion failed: OPENAI_API_KEY not set\033[0m")
        exit(1)


def get_status_text() -> str:
    """
    Get the status text for the staged changes in the current Git repository.

    The `--short` option tells `git status` to output the status in a shorter format.
    The `--untracked-files=no` option tells `git status` to ignore untracked files.
    Together, these options limit the output of `git status` to only report files which are staged for commit.

    Returns:
    str: The status text for the staged changes in the current Git repository.
    """
    # Get the status text for the staged changes in the current Git repository
    result: subprocess.CompletedProcess = subprocess.run(
        ["git", "status", "--short", "--untracked-files=no"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    if result.stderr:
        print("\033[0;31m", result.stderr, "\033[0m")
    if result.returncode != 0:
        raise Exception("git diff failed")

    return result.stdout


def get_diff_text(excluded=["package-lock.json", "yarn.lock"]) -> str:
    """
    Get the diff text for the staged changes in the current Git repository.

    Returns:
    str: The diff text for the staged changes in the current Git
        repository, with a maximum length of 10000 characters.
    """
    # Find the filenames of the staged changes in the current Git
    # repository, excluding package-lock.json and yarn.lock
    # diff-filter=ACMRTUXB means: Added (A), Copied (C), Modified (M),
    # Renamed (R), Changed (T), Updated but unmerged (U), eXisting (X),
    # Broken (B)
    result: subprocess.CompletedProcess = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    if result.stderr:
        print("\033[0;31m", result.stderr, "\033[0m")
    if result.returncode != 0:
        raise Exception("git diff failed")

    # Get the diff text for the staged changes in the current Git repository
    staged_changes = [
        filename for filename in result.stdout.splitlines() if filename not in excluded
    ]
    args = [
        "git",
        "diff",
        "--cached",
        "--no-color",
        "--no-ext-diff",
        "--unified=0",
        "--no-prefix",
    ] + staged_changes
    result: subprocess.CompletedProcess = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    if result.stderr:
        print("\033[0;31m", result.stderr, "\033[0m")
    if result.returncode != 0:
        raise Exception("git diff failed")

    # the output may be too long so we will take the first 10000 characters
    LIMIT = 9000
    output = result.stdout
    if len(output) > LIMIT:
        output = output[:LIMIT] + "\n...(truncated)"
    return output


def main() -> None:
    """
    Use the OpenAI API to get a suggested commit message for the diff that is about to be committed.
    """
    # Check if the commit should be aborted
    check_abort()

    # Get the status text and diff text for the staged changes in the
    # current Git repository
    git_status_text: str = get_status_text()
    git_diff_text: str = get_diff_text()

    model: str = "text-davinci-003"

    # Get the prompt
    prompt: str = get_prompt(
        model=model, status_text=git_status_text, diff_text=git_diff_text
    )
    # save prompt to debug file
    with open(".prompt", "w") as f:
        f.write(prompt)

    # Get the suggested commit message
    print("Getting suggested commit message...")
    suggested_commit_message: CommitMessage = (
        OpenAIApiClient().get_suggested_commit_message(prompt=prompt, model=model)
    )
    # delete the commit message file
    os.remove(sys.argv[1])

    # directly run gitf  commit -m "suggested_commit_message"
    # write commit message to file
    with open(sys.argv[1], "w") as f:
        f.write(suggested_commit_message.text)

    print()
    print(f"Wrote suggested commit message to {sys.argv[1]}")
    print()
    for line in suggested_commit_message.text.splitlines():
        # color code \033[0;90m
        print(f"> \033[0;90m{line}\033[0m")
    print()


if __name__ == "__main__":
    """
    Run the main function.
    """
    main()
