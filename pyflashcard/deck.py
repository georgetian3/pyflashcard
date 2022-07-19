import json
import queue
import random
from sys import maxsize
from sqlitedict import SqliteDict


""" class RandomList:
    # O(1) insertion of an item and O(1) pop of a random item
    def __init__(self, items = []):
        self._items = list(items)
    def append(self, item):
        self._items.append(item)
    def extend(self, items):
        self._items.extend(items)
    def clear(self):
        self._items.clear()
    def pop_random(self):
        # only deletes from end of list to ensure O(1) pop
        index = random.randint(0, len(self._items) - 1)
        item = self._items[index]
        self._items[index] = self._items[-1]
        self._items.pop()
        return item
    def __len__(self):
        return len(self._items)
    def __list__(self):
        return self._items
    def __iter__(self):
        return self._items.__iter__() """


class RandomList(list):
    # O(1) insertion of an item and O(1) pop of a random item
    def pop_random(self):
        # swaps the randomly selected element to the end of the list to ensure O(1) pop
        index = random.randint(0, len(self) - 1)
        item = self[index]
        self[index] = self[-1]
        self.pop()
        return item


class DeckBuilder:

    def __init__(self, levels_file, default_level=1, weights=[]):

        self._leveldb = SqliteDict(
            filename=levels_file,
            tablename='levels',
            autocommit=True,
            encode=json.dumps,
            decode=json.loads,
        )

        self._weights = SqliteDict(
            filename=levels_file,
            tablename='weights',
            decode=json.loads,
        )['weights']

        if len(weights) > 0:
            self._leveldb['__weights__'] = weights
            self._weights = weights
        else:
            raise ValueError('At least one weight is needed')

        self.set_default_level(default_level)

    def set_default_level(self, new_default_level):
        if new_default_level < 0:
            raise ValueError('Default level must be positive')
        elif new_default_level + 1 > len(self._weights):
            raise ValueError('Default level must be less than the max level')
        self._default_level = new_default_level

    def update_weights(self, new_weights: list) -> None:
        if len(new_weights) < 1:
            raise ValueError('Number of weights must be greater or equal to 1')
        elif len(new_weights) < self._default_level + 1:
            raise ValueError('Number of weights must be greater than default level')
        elif len(new_weights) < len(self._weights):
            '''
            If there are n levels in new_weighs and m levels in self._weights and n < m, then move all keys with level >=n to level n - 1
            '''
            for level in range(len(new_weights), len(self._weights)):
                self._levels[len(new_weights - 1)].update(self._levels[level])
                self._leveldb.update
        else:
            self._levels.extend(RandomList() for _ in range(len(self._levels), len(new_weights)))
        self._weights = new_weights

class Deck:

    def __init__(self,
            levels_file,
            default_level=1,
            weights=None,
            history_size=5):

        # no need to know the words that have been deleted or completed, only the amount of each
        self._deleted_count = 0
        self._completed_count = 0

        '''
        levels_file: an SQLite database with tables `weights` and `levels`
        `levels`:
            column 1: contains unique keys that identify each flashcard
            column 2: contains the level of each flashcard:
                -2: deleted
                -1: completed
              >= 0: actual level
        `weights`: weight of each level is stored under the key `weights`
        with the value being a list where each element are real numbers
        in the range [0, n - 1] representing the relative probability of
        selecting that level
        '''

        self._leveldb = SqliteDict(
            filename=levels_file,
            tablename='levels',
            autocommit=True,
            encode=json.dumps,
            decode=json.loads,
        )

        self._weights = SqliteDict(
            filename=levels_file,
            tablename='weights',
            decode=json.loads,
        )['weights']
        
        self._weights = self._leveldb['__weights__']
        if len(self._weights) < 1:
            raise ValueError('At least one weight is needed')

        self._levels = [RandomList() for _ in range(len(self._weights))]

        for key, level in self._leveldb.items():
            if not -2 <= level < len(self._weights):
                raise ValueError(f'Key "{key}" has invalid level "{level}"')
            elif 0 <= level < len(self._weights):
                self._levels[level].append(key)
            elif level == -1:
                self._completed_count += 1
            elif level == -2:
                self._deleted_count += 1

        self._drawn = {}
        self._history_size = history_size
        self._history_set = set()
        self._history_queue = queue(maxsize=history_size)


    def draw(self) -> str:
        '''
        Returns a string of the drawn key; returns `None` if all keys are either deleted or completed
        '''

        # make the weight of a level 0 if there are no keys with that level
        temp_weights = [self._weights[i] * bool(len(self._levels[i])) for i in range(len(self._weights))]
        if sum(temp_weights) == 0:
            return None
        
        level = random.choices(range(len(self._weights)), weights=temp_weights)[0]
        key = self._levels[level].pop_random()

        self._drawn[key] = level

        if len(self._history_queue) >= self._history_size:
            old_key = self._history_queue.get()
            self._history_set.remove(old_key)

        self._history_queue.put(key)
        self._history_set.add(key)

        return key

    def answer(self, key, correct) -> None:
        '''
        `correct=True` if the user answered correctly, otherwise `False`
        '''
        if key not in self._drawn:
            raise Exception(f'{key} has not been drawn')

        if correct:
            # if the key's level is not already at max, increment the key's level
            if self._drawn[key] + 1 < len(self._weights):
                self._levels[self._level + 1].append(self._key)
                self._leveldb[self._key] += 1
            # else mark the key as completed
            else:
                self._completed_count += 1
                self._leveldb[key] = -1
        else:
            self._levels[0].append(key)
            # only update database if the old level wasn't 0
            if self._drawn[key] != 0:
                self._leveldb[self._key] = 0

        del self._drawn[key]

    def add(self, key) -> None:
        if key not in self._leveldb:
            self._levels[self._default_level].append(key)
            self._leveldb[key] = self._default_level

    def update(self, keys) -> None:
        self._levels[self._default_level].extend(keys)
        self._leveldb.update((key, self._default_level) for key in keys)

    def delete(self, key) -> None:
        self._leveldb[key] = -2
        self._deleted_count += 1

    def reset(self) -> None:
        '''
        update every key's level to the default level
        '''
        for level in range(len(self._weights)):
            if level != self._default_level:
                self._levels[self._default_level].extend(self._levels[level])
                self._levels[level].clear()

        self._leveldb.update((key, self._default_level) for key in self._leveldb.keys())
        
    def progress(self) -> tuple:
        '''
        returns tuple containing the number of words at each level
        first item is number of deleted cards, last item is number of completed cards, the n items in between are the number of cards at levels 0 to n - 1
        '''
        return (self._deleted_count, *tuple(len(level) for level in self._levels), self._completed_count)


from django.http import HttpResponse, JsonResponse

class DeckWeb:

    def __init__(
        self,
        deck: Deck,
        dict_search, # function, parameter: key, returns: value of key, raises KeyError if key is not found
        format_key=lambda x: x, # function, parameter: key, returns: html code formatting the key
        format_value=lambda x: x # function, parameter: value, returns: html code formatting the value
    ):
        if type(deck) != Deck:
            raise ValueError('Pass a valid Deck object')
        self._deck = deck
        self._dict_search = dict_search
        self._format_key = format_key
        self._format_value = format_value

    def respond(self, request):

        if request.method == 'POST':
            try:
                json_data = json.loads(request.body.replace(b'\\x', b'\\u'))
                cmd, arg = json_data['cmd'], json_data['arg']
            except Exception as e:
                print('Response: invalid post\nError:', e)
                return JsonResponse('Invalid post')

            response = {'key': None, 'value': None}
            if cmd == 'draw':
                if self._deck.draw():
                    response['key'] = self._format_key(self._deck.draw())
                    try:
                        response['value'] = self._format_value(self._dict_search(self._deck.draw()))
                    except KeyError:
                        response['value'] = 'KeyError'
                else:
                    response['key'] = None
            elif cmd == 'progress':
                response['key'] = 'progress'
                response['value'] = self._deck.progress()
            elif cmd == 'answer':
                self._deck.answer(bool(arg))
            elif cmd == 'delete':
                self._deck.delete()
            elif cmd == 'add':
                response['key'] = 'valid'
                try:
                    self._deck.add(arg)
                    response['value'] = True
                except KeyError:
                    response['value'] = False
            else:
                raise NotImplementedError()

            print('Response:', response)
            return JsonResponse(response)

        elif request.method == 'GET':
            with open('index.html', encoding='utf8') as f:
                return HttpResponse(f.read())
        else:
            return HttpResponse('Invalid request')
            

if __name__ == '__main__':
    a = RandomList([6, 4])
    a.append(5)
    print(a)
    """ dict = SqliteDict(
        filename='cedict.db',
        tablename='dict',
        flag='r',
        decode=json.loads,
    )
    deck = Deck('hsk_levels.db', weights=[1000, 1000, 500, 100, 10, 1])
    from chinesetools import hsk_words
    deck.update(hsk_words) """

