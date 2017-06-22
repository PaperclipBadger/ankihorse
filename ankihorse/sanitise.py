from anki.utils import stripHTML
import re

cloze = re.compile(r'{{c[0-9]+::(.*?)}}')

def sanitise(field_contents):
    return stripHTML(cloze.sub(r'\1', field_contents))

if __name__=='__main__':
    print(sanitise('horses are {{c1::great!}}') == 'horses are great')
