from random import choice as random_choice
from subprocess import check_output

__all__ = ['get_zen', 'ZEN', 'ZENLIST', 'ZENSETS', 'ZENLIST_I', 'ZENSETS_I', 'zen']

def get_zen(python='python'):
    """Capture the output of `import this` and return it."""
    return check_output([python, '-m', 'this'])[:-1] # remove the last newline

ZEN = get_zen()
ZENLIST = ZEN.split('\n')[2:] # Remove the first two lines (title and empty)
ZENSETS = [set(w for w in line.split() if w) for line in ZENLIST]

# lower-case versions
ZENLIST_I = [l.lower() for l in ZENLIST]
ZENSETS_I = [set(w for w in line.split() if w) for line in ZENLIST_I]

def zen(query='', choice=random_choice):
    """Find a sentence in the zen that correponds to a given string.
    
    The search is case-insensitive and operates in five steps:
        1. If no search string is given, return a random line.
        2. If the search string contains only one word and that word is found on
            a line, return it.
        3. If the string matches against a line, it is returned.
        4. If each word in the query match a word on the line, it is returned.
        5. If each word in the string is present on a line, it is returned.
    
    At step 2, 3, 4, and 5, if multiple lines are found, a random one is returned.
    If no line is found, None is returned.
    
    """
    # normalize
    query = query.lower().strip()
    query_words = set(w for w in query.split() if w) # remove empty words

    # 1
    if not query:
        return choice(ZENLIST)

    # 2
    if len(query_words) == 1:
        word = list(query_words)[0]
        l = [line for line, s in zip(ZENLIST, ZENSETS_I) if word in s]
        if l:
            return choice(l)

    # 3
    l = [line for line, line_i in zip(ZENLIST, ZENLIST_I) if query in line_i]
    if l:
        return choice(l)

    # 4
    l = [line for line, s in zip(ZENLIST, ZENSETS_I) if query_words.issubset(s)]
    if l:
        return choice(l)

    # 5
    test_line = lambda line: all(w in line for w in query_words)
    l = [line for line, line_i in zip(ZENLIST, ZENLIST_I) if test_line(line_i)]
    if l:
        return choice(l)

    return None
