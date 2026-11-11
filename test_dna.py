"""Acceptance tests for the DNA exercise.

Each test runs your program as a whole, exactly as a user would: it gives
the name of a CSV database and the name of a DNA sequence file on the
command line, then checks what your program prints and tries to explain
what is wrong.

Run the tests from the exercise folder with:

    python test_dna.py
"""

import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path

EXERCISE_DIR = Path(__file__).resolve().parent
SCRIPT = "dna.py"
NO_MATCH = "No match"
TIMEOUT = 10  # seconds
TIMEOUT_MESSAGE = ("Your program did not stop within {} seconds (infinite "
                   "loop?). Check the conditions of your while loops."
                   .format(TIMEOUT))

# Files given with the exercise: (database, sequence).
# The expected answer is computed by the answer() function below.
FILE_CASES = [("databases/small.csv", f"sequences/{i}.txt")
              for i in range(1, 5)]
FILE_CASES += [("databases/large.csv", f"sequences/{i}.txt")
               for i in range(5, 21)]

# Database whose STRs are used by the mistake "the STRs are written in
# the program" (see answer()).
SMALL_DATABASE = "databases/small.csv"

# Small cases written in temporary files:
# (what is checked, rows of the CSV database, DNA sequence).
CASES = [
    ("the example of the README (AGAT repeated 5 times: Bob)", [
        "name,AGAT",
        "Alice,4",
        "Bob,5",
    ], "CTAGATAGATAGATAGATAGATT"),
    ("STRs that are not the ones of small.csv", [
        "name,GATA,TTAGG",
        "Nina,2,3",
        "Omar,3,2",
    ], "CCGATAGATAGATATTTAGGTTAGGCC"),
    ("more STRs than in small.csv (Nina only differs on GATA)", [
        "name,AGATC,GATA,AATG,TATC",
        "Nina,1,1,1,1",
        "Omar,1,2,1,1",
    ], "CCAGATCCCGATAGATACCAATGCCTATCCC"),
    ("only CONSECUTIVE repeats count (two runs of 2 AGAT: 2, not 4)", [
        "name,AGAT",
        "Nina,2",
        "Omar,4",
    ], "CCAGATAGATCCCCAGATAGATCC"),
    ("the longest run is not the first one", [
        "name,AATG",
        "Nina,1",
        "Omar,3",
    ], "AATGCCCAATGAATGAATGCCAATGAATG"),
    ("a STR absent from the sequence (0 repeats)", [
        "name,AGAT,TCTG",
        "Nina,2,1",
        "Omar,2,0",
    ], "GGAGATAGATGG"),
    ("the matching individual is the last one", [
        "name,AGAT,AATG",
        "Nina,1,1",
        "Omar,2,1",
        "Paul,1,2",
        "Rosa,2,2",
    ], "AGATAGATCCAATGAATGCC"),
    ("the matching individual is the first one", [
        "name,AGAT,AATG",
        "Rosa,2,2",
        "Nina,1,1",
        "Omar,2,1",
    ], "AGATAGATCCAATGAATGCC"),
    ("ALL the STRs must match (Nina only differs on the last one)", [
        "name,AGAT,AATG,TATC",
        "Nina,2,1,3",
        "Omar,1,1,1",
    ], "AGATAGATCCAATGCCTATCTATCCC"),
    ("ALL the STRs must match (Omar only has the first one right)", [
        "name,AGAT,AATG",
        "Omar,2,3",
        "Nina,1,1",
    ], "AGATAGATCCAATGCC"),
]

# Invalid command lines: (what is checked, arguments).
# The program must print an error message (of its choice) and stop.
USAGE_CASES = [
    ("no file name", []),
    ("one file name", ["databases/small.csv"]),
    ("three file names",
     ["databases/small.csv", "sequences/1.txt", "sequences/2.txt"]),
]

# Frequent mistakes: (parameters of answer() reproducing the mistake,
# explanation). After all the tests, the explanations of the mistakes
# that give exactly the results printed by the program are shown.
MISTAKES = [
    ({"count": "total"},
     "Your program seems to count ALL the occurrences of each STR in the "
     "sequence (with str.count(), for example). Only the longest run of "
     "CONSECUTIVE repeats counts: use longest_match(sequence, STR) from "
     "matcher.py."),
    ({"types": "str"},
     "Your program never finds a match: maybe it compares str and int. "
     "All the values read from a CSV file are str: row['AGATC'] is '4', "
     "not 4, and '4' == 4 is False. Convert them with int() before "
     "comparing them with the results of longest_match()."),
    ({"name_column": True},
     "Your program never finds a match: maybe it also compares the first "
     "column ('name'), which is not a STR. Only compare the columns "
     "after the first one."),
    ({"strs": "fixed"},
     "Your program seems to always use the STRs of small.csv (AGATC, AATG "
     "and TATC). Do not write the STRs in your program: read them from "
     "the first row of the CSV file (reader.fieldnames, without 'name')."),
    ({"database": "small"},
     "Your program seems to always use databases/small.csv. Open the "
     "database whose name is given on the command line, in sys.argv[1]."),
    ({"columns": "skip_last"},
     "Your program seems to forget the last STR of the database: "
     "range(n) already stops at n - 1, and so does the slice [1:-1]. "
     "To get all the STRs, use fieldnames[1:]."),
    ({"columns": "any"},
     "Your program seems to accept an individual as soon as ONE STR "
     "matches. An individual matches only if ALL the STR counts are "
     "equal."),
    ({"rows": "first"},
     "Your program seems to check only the first individual of the "
     "database: it decides 'No match' too early. Print 'No match' only "
     "after the loop, when ALL the individuals have been checked."),
    ({"rows": "last"},
     "Your program seems to keep only the result of the last individual "
     "of the database: a variable (found = ...) is overwritten at each "
     "turn of the loop. Stop the loop (break) as soon as an individual "
     "matches, or only change the variable when an individual matches."),
]

# Text typed if the program asks something (it should not).
UNEXPECTED_INPUT = ""


# ---------------------------------------------------------------------------
# Expected results
# ---------------------------------------------------------------------------

def longest_run(sequence, str_):
    """Return the length of the longest run of str_ in sequence."""
    longest = 0
    for start in range(len(sequence)):
        count = 0
        while sequence.startswith(str_, start + count * len(str_)):
            count += 1
        longest = max(longest, count)
    return longest


def read_database(path):
    """Return (fieldnames, rows) of a CSV database, rows being dicts."""
    with open(path, encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames, list(reader)


def read_sequence(path):
    """Return the DNA sequence of a file."""
    return Path(path).read_text(encoding="utf-8").strip()


def answer(database, sequence, count="longest", types="int",
           name_column=False, strs="header", columns="all", rows="all"):
    """Return what the program should print for the database and sequence.

    database: (fieldnames, rows) as given by read_database().
    The optional parameters reproduce frequent mistakes:
    - count: "longest" (right) or "total" (all the occurrences);
    - types: "int" (right) or "str" (CSV values not converted: no match);
    - name_column: if True, the name is compared too (no match);
    - strs: "header" (right) or "fixed" (the STRs of small.csv);
      the "database" key, "small", means small.csv is always used;
    - columns: "all" (right), "skip_last" (last STR forgotten) or "any"
      (one equal STR is enough);
    - rows: "all" (right), "first" or "last" (only this row is checked).
    Return None if the mistake makes the program crash.
    """
    fieldnames, people = database
    str_names = fieldnames[1:]
    if strs == "fixed":
        str_names = SMALL_STRS
        if not set(str_names) <= set(fieldnames):
            return None  # KeyError
    if columns == "skip_last":
        str_names = str_names[:-1]
    if types == "str" or name_column:
        return NO_MATCH
    counts = {}
    for str_ in str_names:
        if count == "total":
            counts[str_] = sequence.count(str_)
        else:
            counts[str_] = longest_run(sequence, str_)
    if rows == "first":
        people = people[:1]
    elif rows == "last":
        people = people[-1:]
    for person in people:
        equal = [int(person[str_]) == counts[str_] for str_ in str_names]
        if all(equal) or (columns == "any" and any(equal)):
            return person["name"]
    return NO_MATCH


def answer_with(test, parameters):
    """Return answer() for a test, with the parameters of a mistake."""
    database = test["database"]
    if parameters.get("database") == "small":
        if SMALL_DB is None:
            return None
        database = SMALL_DB
        parameters = {}
    return answer(database, test["sequence"], **parameters)


# ---------------------------------------------------------------------------
# Running the student's program
# ---------------------------------------------------------------------------

def run_program(arguments):
    """Run the program with the arguments.

    Return (stdout, stderr, return code), or None if the program
    did not stop in time.
    """
    try:
        # sys.executable is the Python running the tests,
        # so "python" vs "python3" does not matter.
        result = subprocess.run(
            [sys.executable, SCRIPT] + arguments,
            input=UNEXPECTED_INPUT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=EXERCISE_DIR,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"),
            timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return None
    stdout = result.stdout.replace("\r\n", "\n")
    stderr = result.stderr.replace("\r\n", "\n").strip()
    return stdout, stderr, result.returncode


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def show(text, max_lines=6, max_length=70):
    """Indent the lines of a text, with each line between quotes.

    Only the first lines are shown, and long lines are cut.
    """
    lines = text.splitlines()
    if not lines:
        return "    (nothing)"
    shown_lines = []
    for line in lines[:max_lines]:
        if len(line) > max_length:
            shown_lines.append(f"    {line[:max_length]!r}... (cut)")
        else:
            shown_lines.append(f"    {line!r}")
    if len(lines) > max_lines:
        shown_lines.append(f"    ... ({len(lines) - max_lines} more lines)")
    return "\n".join(shown_lines)


def last_lines(text, nb_lines=4):
    """Return the last lines of a text, indented."""
    lines = text.split("\n")[-nb_lines:]
    return "\n".join("    " + line for line in lines)


def show_counts(str_names, values):
    """Return e.g. 'AGATC 4, AATG 1, TATC 5'."""
    return ", ".join(f"{str_} {values[str_]}" for str_ in str_names)


def explain_expected(test, given):
    """Explain how the expected answer is computed."""
    fieldnames, people = test["database"]
    str_names = fieldnames[1:]
    counts = {str_: longest_run(test["sequence"], str_)
              for str_ in str_names}
    message = ("Longest runs of consecutive repeats in the sequence:\n    "
               + show_counts(str_names, counts))
    expected = answer(test["database"], test["sequence"])
    if expected != NO_MATCH:
        message += f"\n{expected} has exactly these counts in the database."
    else:
        message += "\nNobody in the database has exactly these counts."
    for person in people:
        if person["name"] == given:
            different = [str_ for str_ in str_names
                         if int(person[str_]) != counts[str_]]
            message += (f"\n{given} has different counts for "
                        + ", ".join(f"{str_} ({person[str_]} in the "
                                    f"database, {counts[str_]} in the "
                                    f"sequence)" for str_ in different)
                        + ".")
    return message


def explain_crash(stderr):
    """Explain the most common errors that make the program crash."""
    message = f"Your program crashed:\n{last_lines(stderr)}"
    if "EOFError" in stderr:
        message += ("\nYour program asks the user something with input(). "
                    "It should not: the file names are given on the "
                    "command line, in sys.argv[1] and sys.argv[2].")
    elif "IndexError" in stderr and "argv" in stderr:
        message += ("\nA file name is missing on the command line, so "
                    "sys.argv[1] or sys.argv[2] does not exist. Before "
                    "using them, check len(sys.argv): if it is not 3, "
                    "print an error message and stop.")
    elif "ModuleNotFoundError" in stderr and "matcher" in stderr:
        message += ("\nKeep matcher.py in the same folder as dna.py, "
                    "without changing its name.")
    elif "FileNotFoundError" in stderr:
        message += ("\nYour program tried to open a file that does not "
                    "exist: open the files whose names are in sys.argv[1] "
                    "(database) and sys.argv[2] (sequence).")
    elif "KeyError" in stderr:
        message += ("\nYour program used a key that is not in a dict. If "
                    "it is a STR, do not write the STRs in your program: "
                    "read them from the first row of the CSV file "
                    "(reader.fieldnames). The column of the names is "
                    "'name'.")
    elif "ValueError" in stderr and "int()" in stderr:
        message += ("\nint() was given something that is not a number: "
                    "maybe the name of an individual? The first column "
                    "is the name, the STR counts are in the other "
                    "columns.")
    elif "TypeError" in stderr and "str" in stderr and "int" in stderr:
        message += ("\nYour program mixes str and int: all the values read "
                    "from a CSV file are str ('4'), convert them with "
                    "int() before comparing or computing with them.")
    return message


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_usage(arguments, names):
    """Check that an invalid command line prints an error message only.

    names: names of the individuals of the databases.
    Return None if the test passes, else an error message.
    """
    result = run_program(arguments)
    if result is None:
        return TIMEOUT_MESSAGE
    stdout, stderr, _ = result
    if "Traceback" in stderr:
        return explain_crash(stderr)
    lines = stdout.splitlines()
    printed = "Your program printed:\n" + show(stdout)
    if any(line.strip() in names or line.strip() == NO_MATCH
           for line in lines):
        return ("Your program should check the number of command-line "
                "arguments: there must be exactly 2 file names. If not, "
                "print an error message and stop (e.g. with sys.exit())."
                f"\n{printed}")
    # sys.exit("message") writes the message on stderr: it is accepted too.
    if stdout.strip() == "" and stderr == "":
        return ("Your program should print an error message: there must "
                "be exactly 2 file names on the command line.")
    return None


def check_output(stdout, names):
    """Check that the program printed a name or 'No match'.

    names: names of the individuals of the database.
    Return (error message or None, line printed or None if not valid).
    """
    lines = stdout.splitlines()
    printed = "Your program printed:\n" + show(stdout)
    if not lines:
        return "Your program printed nothing.", None
    if len(lines) > 1:
        if NO_MATCH in lines:
            message = ("Your program printed 'No match' several times, or "
                       "'No match' and a name: it seems to decide for each "
                       "individual. Check ALL the individuals first, and "
                       "print 'No match' only once, after the loop, if "
                       "nobody matched.")
        elif all(line in names for line in lines):
            message = ("Your program printed several names: print only "
                       "the name of the individual who matches, once.")
        else:
            message = ("Your program should print a single line (a name or "
                       "'No match'). Remove your extra print() (database, "
                       "STR counts, debugging...).")
        return f"{message}\n{printed}", None

    line = lines[0]
    if line in names or line == NO_MATCH:
        return None, line
    if line.strip() in names or line.strip() == NO_MATCH:
        return (f"Nothing should be printed before or after the answer "
                f"(not even spaces).\n{printed}"), None
    if line.strip().lower() == NO_MATCH.lower():
        return (f"Check the case and the spelling: the message must be "
                f"exactly {NO_MATCH!r}.\n{printed}"), None
    if line.startswith("{"):
        return (f"Your program printed a whole row of the database (a "
                f"dict): print only the name, row['name'].\n{printed}"), None
    if any(name in line for name in names):
        return (f"Your program should print only the name, without any "
                f"other text or character.\n{printed}"), None
    if line.isalpha():
        # A name that is not in this database: it is a wrong result.
        return None, line
    return (f"Your program should print the name of an individual of the "
            f"database, or {NO_MATCH!r}.\n{printed}"), None


def check_test(test, names):
    """Run one test.

    Return (error message or None if the test passes,
            line printed by the program or None if not valid).
    """
    result = run_program([str(test["database_path"]),
                          str(test["sequence_path"])])
    if result is None:
        return TIMEOUT_MESSAGE, None
    stdout, stderr, _ = result
    if "Traceback" in stderr:
        return explain_crash(stderr), None
    message, given = check_output(stdout, names)
    if message is not None:
        return message, None

    expected = answer(test["database"], test["sequence"])
    if given != expected:
        if given != NO_MATCH and given not in names:
            message = f"{given} is not in the database {test['label']}."
        else:
            message = f"Your program printed {given!r} instead of "
            message += f"{expected!r}.\n" + explain_expected(test, given)
        return message, given
    return None, given


def diagnose(observations):
    """Explain the wrong results, using all the results of the program.

    observations: list of (test, line printed by the program).
    Return the explanations of the frequent mistakes (alone, or else two
    at a time) that give exactly the same results as the program.
    """
    def consistent(parameters):
        for test, given in observations:
            if answer_with(test, parameters) != given:
                return False
        return True

    causes = []
    for parameters, explanation in MISTAKES:
        if consistent(parameters):
            causes.append(explanation)
    if causes:
        return causes
    for i, (parameters_1, explanation_1) in enumerate(MISTAKES):
        for parameters_2, explanation_2 in MISTAKES[i + 1:]:
            if parameters_1.keys() & parameters_2.keys():
                continue  # the two mistakes are about the same thing
            if "database" in parameters_1 | parameters_2:
                continue  # nothing else matters with another database
            if consistent(parameters_1 | parameters_2):
                causes.append(explanation_1 + "\n    AND " + explanation_2)
    if not causes:
        given_lines = {given for _, given in observations}
        if len(observations) > 2 and len(given_lines) == 1:
            causes.append(f"Your program always prints {given_lines.pop()!r}"
                          f": does it really use the files given on the "
                          f"command line, sys.argv[1] and sys.argv[2]?")
    return causes


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def load_small_database():
    """Return small.csv as given by read_database(), or None."""
    path = EXERCISE_DIR / SMALL_DATABASE
    if not path.is_file():
        return None
    return read_database(path)


SMALL_DB = load_small_database()
SMALL_STRS = SMALL_DB[0][1:] if SMALL_DB else ["AGATC", "AATG", "TATC"]


def main():
    sys.stdout.reconfigure(errors="replace")
    use_colors = sys.stdout.isatty() and (
        os.name != "nt" or "WT_SESSION" in os.environ)
    green = "\033[32m" if use_colors else ""
    red = "\033[31m" if use_colors else ""
    reset = "\033[0m" if use_colors else ""

    if not (EXERCISE_DIR / SCRIPT).is_file():
        print(f"No {SCRIPT} found in {EXERCISE_DIR}")
        return 1

    nb_ok = 0
    nb_tests = len(FILE_CASES) + len(CASES) + 1 + len(USAGE_CASES)
    observations = []  # (test, line printed by the program)
    nb_wrong_results = 0
    all_names = set()

    shown = []  # explanations already printed

    def report(description, message, details):
        """Print the result of one test.

        An explanation already printed for a previous test is not
        repeated (nor the details of the test): only what the program
        printed is shown.
        """
        if message is None:
            print(f"{green}✔{reset} {description}")
            return 1
        print(f"{red}✗{reset} {description}")
        explanation, separator, printed = message.partition(
            "\nYour program printed:")
        if explanation in shown:
            message = "Same problem as above." + separator + printed
        else:
            shown.append(explanation)
            for detail in details:
                print("    " + detail.replace("\n", "\n    "))
        print("    " + message.replace("\n", "\n    ") + "\n")
        return 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        tests = []
        for database_name, sequence_name in FILE_CASES:
            database_path = EXERCISE_DIR / database_name
            sequence_path = EXERCISE_DIR / sequence_name
            command = f"python {SCRIPT} {database_name} {sequence_name}"
            missing = [name for name, path in [(database_name, database_path),
                                               (sequence_name, sequence_path)]
                       if not path.is_file()]
            if missing:
                print(f"{red}✗{reset} {command}")
                print(f"    {missing[0]} not found in {EXERCISE_DIR}\n")
                continue
            tests.append({
                "description": command,
                "label": database_name,
                "database_path": database_name,
                "sequence_path": sequence_name,
                "database": read_database(database_path),
                "sequence": read_sequence(sequence_path),
                "details": [f"Command: {command}"],
            })
        cases = CASES + [("a sequence file without a newline at the end",
                          CASES[0][1], CASES[0][2])]
        for number, (description, rows, sequence) in enumerate(cases,
                                                               start=1):
            database_path = Path(tmp_dir) / f"database_{number:02}.csv"
            sequence_path = Path(tmp_dir) / f"sequence_{number:02}.txt"
            database_path.write_text("\n".join(rows) + "\n",
                                     encoding="utf-8")
            if number == len(cases):
                sequence_path.write_text(sequence, encoding="utf-8")
            else:
                sequence_path.write_text(sequence + "\n", encoding="utf-8")
            database = "\n".join("    " + row for row in rows)
            tests.append({
                "description": description,
                "label": f"{database_path.name}",
                "database_path": database_path,
                "sequence_path": sequence_path,
                "database": read_database(database_path),
                "sequence": sequence,
                "details": [f"Database:\n{database}",
                            f"Sequence: {sequence}"],
            })

        for test in tests:
            all_names |= {person["name"] for person in test["database"][1]}

        stopped = False
        for test in tests:
            names = {person["name"] for person in test["database"][1]}
            message, given = check_test(test, names)
            if given is not None:
                observations.append((test, given))
                if message is not None:
                    nb_wrong_results += 1
            nb_ok += report(test["description"], message, test["details"])
            if message == TIMEOUT_MESSAGE:
                print("The other tests are not run: fix this problem "
                      "first.\n")
                stopped = True
                break

    if not stopped:
        for description, arguments in USAGE_CASES:
            message = check_usage(arguments, all_names)
            command = " ".join(["python", SCRIPT] + arguments)
            nb_ok += report(f"error message: {description}", message,
                            [f"Command: {command}"])

    if nb_wrong_results > 0:
        causes = diagnose(observations)
        if not causes:
            print("To find your mistake, take a test that fails, print the "
                  "STR counts computed by your program and compare them "
                  "with the expected ones (and remove these print() "
                  "afterwards).\n")
        else:
            title = "Probable cause" if len(causes) == 1 else "Possible causes"
            print(f"{title} of the wrong results, considering all the tests:")
            for cause in causes:
                print("  - " + cause)
            print()

    color = green if nb_ok == nb_tests else red
    print(f"Validated: {color}{nb_ok}/{nb_tests}{reset}")
    return 0 if nb_ok == nb_tests else 1


if __name__ == "__main__":
    sys.exit(main())
