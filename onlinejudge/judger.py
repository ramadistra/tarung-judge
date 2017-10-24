import json
import requests

from django.conf import settings

from .models import Attempt


STATUS = {
    'OK': Attempt.ACCEPTED,
    'Runtime Error': Attempt.RUNTIME_ERROR,
    'Server Error': Attempt.SERVER_ERROR,
    'Timed Out': Attempt.TIMED_OUT
}


def judge(source, question):
    """
    Judge runs the source submit by user and gets the verdict
    Parameters
    ----------
    source : string
        The source code submitted by the user
    question : Question
        The question that the user is attempting to solve.
    Returns
    -------
    result : dict
        A dictionary containing the test cases and verdict.

    """
    cases = question.case_set.all()
    stdin = [case.stdin.replace("\r", "") + "\n" for case in cases]
    expected_output = [case.stdout.replace("\r", "") + "\n" for case in cases]

    data = {'source': source, 'stdin': stdin, 'timeout': 2000}
    r = requests.post(settings.JUDGER_URL+"python3", json=data)
    response = json.loads(r.text)
    cases, verdict = match(expected_output, response)
    result = {'cases': cases, 'verdict': verdict}
    return result


def match(expected_output, response):
    """Matches the output with expected output"""
    result = []
    response_output = parse_stdout(response['stdout'])
    status = response['status']
    verdict = STATUS[status]
    for expected, got in zip(expected_output, response_output):
        if expected.strip() == got.strip():
            result.append(Attempt.ACCEPTED if status == 'OK' else Attempt.RUNTIME_ERROR)
        else:
            result.append(Attempt.WRONG_ANSWER if status == 'OK' else Attempt.RUNTIME_ERROR)
            if verdict == Attempt.ACCEPTED:
                verdict = Attempt.WRONG_ANSWER

    return result, verdict


def parse_stdout(output):
    """
    Parse stdout from judger.

    Example
    -------
    Input:
        "1.in\nHello\n2.in\nWorld\n"
    Output:
        ["Hello\n", "World\n"]

    """
    i = 1
    stdouts, stdout = [], ""
    # Compensate for new line at end of file.
    # Ignore first line: 1.in.
    for line in output[:-1].split('\n')[1:]:
        if line == "%d.in" % (i+1):
            stdouts.append(stdout[:-1])
            i += 1
            stdout = ""
            continue
        stdout += line + "\n"
    stdouts.append(stdout[:-1])

    return stdouts
