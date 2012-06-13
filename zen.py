from subprocess import check_output

def get_zen():
    """Capture the output of `import this` and return it."""
    return check_output(['python', '-m', 'this'])[:-1] # remove the last newline

ZEN = get_zen()
ZENLIST = ZEN.split('\n')[2:] # Remove the first two lines (title and empty)

def find_zen(s):
    """Find a sentence in the zen that correponds to a given string."""
    s = s.lower()
    
    # first, look for a unique sentence that contains the whole string
    l = [line for line in ZENLIST if s in line.lower()]
    if len(l) == 1:
        return l[0]
    
    # second, look for a line that contains all the words in the string
    l = [line for line in ZENLIST if all(word in line.lower() for word in s.split())]
    if len(l) == 1:
        return l[0]
    
    return None
