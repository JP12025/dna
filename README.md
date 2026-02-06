# DNA

# What to Do

DNA, the carrier of genetic information in living things, has been used in criminal justice for decades. But how, exactly, does DNA profiling work? Given a sequence of DNA, how can forensic investigators identify to whom it belongs?

In a file called `dna.py`, implement a program that identifies to whom a sequence of DNA belongs.
For this problem, you’ll extend the functionality of code provided in `dna.py`.

# Background

DNA is really just a sequence of molecules called nucleotides. Each nucleotide of DNA contains one of four different bases: adenine (A), cytosine (C), guanine (G), or thymine (T). Some portions of this sequence (i.e., genome) are the same, or at least very similar, across almost all humans, but other portions of the sequence have a higher genetic diversity and thus vary more across the population.

One place where DNA tends to have high genetic diversity is in Short Tandem Repeats (STRs). An STR is a short sequence of DNA bases that tends to repeat consecutively numerous times at specific locations inside of a person’s DNA. The number of times any particular STR repeats varies a lot among individuals. In the DNA samples below, for example, Alice has the STR `AGAT` repeated four times in her DNA, while Bob has the same STR repeated five times.

```
Alice : CTAGATAGATAGATAGATGACTA
          |--||--||--||--|
Bob :   CTAGATAGATAGATAGATAGATT
          |--||--||--||--||--|
```

Using multiple STRs, rather than just one, can improve the accuracy of DNA profiling. If the probability that two people have the same number of repeats for a single STR is 5%, and the analyst looks at 10 different STRs, then the probability that two DNA samples match purely by chance is about 1 in 1 quadrillion (assuming all STRs are independent of each other). So if two DNA samples match in the number of repeats for each of the STRs, the analyst can be pretty confident they came from the same person. CODIS, the FBI’s DNA database, uses 20 different STRs as part of its DNA profiling process.

What might such a DNA database look like? Well, in its simplest form, you could imagine formatting a DNA database as a CSV file, wherein each row corresponds to an individual, and each column corresponds to a particular STR.

```csv
name,    AGAT, AATG, TATC
Alice,   28,   42,   14
Bob,     17,   22,   19
Charlie, 36,   18,   25
```

The data in the above file would suggest that Alice has the sequence AGAT repeated 28 times consecutively somewhere in her DNA, the sequence AATG repeated 42 times, and TATC repeated 14 times. Bob, meanwhile, has those same three STRs repeated 17 times, 22 times, and 19 times, respectively. And Charlie has those same three STRs repeated 36, 18, and 25 times, respectively.

So given a sequence of DNA, how might you identify to whom it belongs? Well, imagine that you looked through the DNA sequence for the longest consecutive sequence of repeated AGATs and found that the longest sequence was 17 repeats long. If you then found that the longest sequence of AATG is 22 repeats long, and the longest sequence of TATC is 19 repeats long, that would provide pretty good evidence that the DNA was Bob’s. Of course, it’s also possible that once you take the counts for each of the STRs, it doesn’t match anyone in your DNA database, in which case you have no match.

In practice, since analysts know on which chromosome and at which location in the DNA an STR will be found, they can localize their search to just a narrow section of DNA. But we’ll ignore that detail for this problem.

Your task is to write a program that will take a sequence of DNA and a CSV file containing STR counts for a list of individuals and then output to whom the DNA (most likely) belongs.

# Specification

- The program should require:
  - the name of a CSV file containing the STR counts for a list of individuals
  - the name of a text file containing the DNA sequence to identify. 
  - Example : `python dna.py databases/small.csv sequences/1.txt`
- If your program is executed with the incorrect number of command-line arguments, your program should print an error message of your choice (with print).
- If the correct number of arguments are provided, you may assume that the first argument is indeed the filename of a valid CSV file and that the second argument is the filename of a valid text file.

- Your program should open the CSV file and read its contents into memory (use `import csv`).
    - You may assume that the first row of the CSV file will be the column names.
    - The first column will be the word name and the remaining columns will be the STR sequences themselves.

- Your program should open the DNA sequence and read its contents into memory. DNA sequences are always one line uppercase text file.

- For each of the STRs (from the first line of the CSV file), your program should compute the longest run of consecutive repeats of the STR in the DNA sequence to identify. Notice that we’ve defined a helper function for you, `longest_match` in file `matcher.py`, which will do just that!
- If the STR counts match exactly with any of the individuals in the CSV file, your program should print out the name of the matching individual.
    - You may assume that the STR counts will not match more than one individual.
    - If the STR counts do not match exactly with any of the individuals in the CSV file, your program should print `No match`.

# Hints

- You may find Python’s `csv` module helpful for reading CSV files into memory. Of particular help might be `csv.DictReader`.
- For instance, if a file like `foo.csv` has a header row, wherein each string is the name of some field, here’s how you might print those `fieldnames` as a `list`:
```python
import csv

with open("foo.csv", "r") as file:
    reader = csv.DictReader(file)
    print(reader.fieldnames)
```
- And here’s how you read all of the (other) rows from a CSV into a `list`, wherein each element is a `dict` that represents that row:
```python
import csv

rows = []
with open("foo.csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        rows.append(row)
```
- While coding, print everything to see what happens.
- The `open` and `read` functions might also prove useful for reading text files into memory.
- Consider what data structures might be helpful for keeping tracking of information in your program. A `list` or a `dict` may prove useful.
- Remember we’ve defined a function `longest_match` that, given both a DNA sequence and an STR as inputs, returns the maximum number of times that the STR repeats. You can then use that function in other parts of your program!

# When to Do it

By Sunday, march 15, 2026 at 11:59 PM

# How to Test

Two directories contain data for testing : `databases` and `sequences`.

Test your script with command `./check dna.py`

Or run tests directly as follows:
```bash
$ python dna.py databases/small.csv sequences/1.txt
Bob
$ python dna.py databases/small.csv sequences/2.txt
No match
$ python dna.py databases/small.csv sequences/3.txt
No match
$ python dna.py databases/small.csv sequences/4.txt
Alice
$ python dna.py databases/large.csv sequences/5.txt
Lavender
$ python dna.py databases/large.csv sequences/6.txt
Luna
$ python dna.py databases/large.csv sequences/7.txt
Ron
$ python dna.py databases/large.csv sequences/8.txt
Ginny
$ python dna.py databases/large.csv sequences/9.txt
Draco
$ python dna.py databases/large.csv sequences/10.txt
Albus
$ python dna.py databases/large.csv sequences/11.txt
Hermione
$ python dna.py databases/large.csv sequences/12.txt
Lily
$ python dna.py databases/large.csv sequences/13.txt
No match
$ python dna.py databases/large.csv sequences/14.txt
Severus
$ python dna.py databases/large.csv sequences/15.txt
Sirius
$ python dna.py databases/large.csv sequences/16.txt
No match
$ python dna.py databases/large.csv sequences/17.txt
Harry
$ python dna.py databases/large.csv sequences/18.txt
No match
$ python dna.py databases/large.csv sequences/19.txt
Fred
$ python dna.py databases/large.csv sequences/20.txt
No match
```

# How to Submit

Once you're done with all tasks, submit all your python files for the week on Moodle.

# Licence

This course is freely inspired from [CS50’s Introduction to Computer Science](https://cs50.harvard.edu/x/2025/) Harvard. It is licensed under a [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) license. 
