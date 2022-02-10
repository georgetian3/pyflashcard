from pyflashcard.deck import Deck, DeckWeb
from sqlitedict import SqliteDict
import json

dict_db = SqliteDict(
    filename='cedict.db',
    tablename='dict',
    flag='r',
    decode=json.loads,
)

deck_web = DeckWeb(
    deck=Deck('hsk_levels.db'),
    dict_search=lambda key: dict_db[key],
    format_value=lambda value: '<br><br>'.join(f'{pinyin}: {value[pinyin]}'.replace('\n', '<br>') for pinyin in value)
)

def index(request):
    return deck_web.respond(request)