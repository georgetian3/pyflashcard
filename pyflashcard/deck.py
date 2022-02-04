import json
import random
from sqlitedict import SqliteDict

class RandomList:
    # O(1) insertion of an item and O(1) pop of a random item
    def __init__(self, items = []):
        self._items = list(items)
    def append(self, item):
        self._items.append(item)
    def extend(self, items):
        self._items.extend(items)
    def clear(self):
        self._items.clear()
    def pop_random(self, item):
        # choose a random index
        index = random.randint(0, len(self._items) - 1)
        # save the item at that index
        item = self._items[index]
        # replace that index with the last item
        self._items[index] = self._items[-1]
        # shorten the list by 1
        self._items.pop()
        # return the saved item
        return item
    def __len__(self):
        return len(self._items)
    def __list__(self):
        return self._items

class Deck:
    def __init__(self, dict_search, levels_file, default_level=1, weights=None):

        # user-defined function which returns the associated value given the key, and raises KeyError if the key does not exist
        self._dict_search = dict_search
        self._drew = False

        # no need to know the words that have been deleted or completed, only the amount of each
        self._deleted_count = 0
        self._completed_count = 0

        '''
        levels_file: an SQLite database with a table named `levels`, which has two columns:
            column 1: contains unique keys that identify each flashcard
            column 2: contains the level of each flashcard:
                -2: deleted
                -1: completed
                >= 0: actual level
        In addition to keys, the weights of each level is stored under the key __weights__ with the value being a list from 0 to n - 1 of real numbers representing the relative probability of selecting that level
        '''

        self._leveldb = SqliteDict(
            filename=levels_file,
            tablename='levels',
            autocommit=True,
            encode=json.dumps,
            decode=json.loads,
        )
        
        try:
            self._weights = self._leveldb['__weights__']
        except KeyError:
            if weights:
                if len(weights) > 0:
                    self._leveldb['__weights__'] = weights
                    self._weights = weights
                else:
                    raise ValueError('At least one weight is needed')
            else:
                raise KeyError('Weights not in level_file, nor is it provided')

        self.set_default_level(default_level)

        self._levels = [RandomList() for _ in range(len(self._weights))]

        for key in self._leveldb:

            if key == '__weights__':
                continue

            # ensure missing keys are found
            self._dict_search(key)

            level = self._level[key]


            if level >= len(self._weights) or level < -2:
                raise ValueError(f'Key "{key}" has invalid level "{level}"')
            elif 0 <= level < len(self._weights):
                self._levels[level].append(key)
            elif level == -1:
                self._completed_count += 1
            elif level == -2:
                self._deleted_count += 1
 

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


    def draw(self) -> tuple:
        '''
        Returns a 2-tuple (key, value), if all keys are either deleted or completed, then return (None, None)
        '''

        if self._drew:
            raise Exception('Call `answer` or `delete` before calling `draw`')

        # make the weight of level n 0 if no keys are of level n
        temp_weights = [self._weights[i] * bool(len(self._levels[i])) for i in range(len(self._weights))]
        if sum(temp_weights) == 0:
            return (None, None)
        
        self._level = random.choices(range(len(self.weights)), weights=temp_weights)[0]
        self._key = self._levels[self._level].pop_random()
        self._drew = True
        return (self._key, self._dict_search(self._key))

    def answer(self, correct) -> None:
        '''
        correct=True if the user answered correctly, otherwise False
        '''
        if not self._drew:
            raise Exception('Call `draw` before calling answer')

        if correct:
            # if the key's level is not already at max, increment the key's level
            if self._level + 1 < len(self._weights):
                self._levels[self._level + 1].append(self._key)
                self._leveldb[self._key] += 1
            # else mark the key as completed
            else:
                self._completed_count += 1
                self._leveldb[self._key] = -1
        # if the user answered incorrectly and the key's level is greater than 0 ...
        elif self._level > 0:
            # ... set its level to 0
            self._levels[0].append(self._key)
            self._levels[self._key] = 0

    def add(self, key) -> None:
        # ensures KeyError is raised if key doesn't exist in dict
        self._dict_search(key)

        if key not in self._leveldb:
            self._levels[1].append(key)
            self._leveldb[key] = self._default_level

    def update(self, keys) -> None:
        for key in keys:
            self._dict_search(key)

        self._levels[self._default_level].extend(keys)
        self._leveldb.update((key, self._default_level) for key in keys)

    def delete(self) -> None:
        '''
        deletes the currently drawn card
        '''
        self._deleted_count += 1
        self._leveldb[self._key] = -2
        self._drew = False

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
        return tuple(self._deleted_count, *(len(x) for x in self._levels), self._completed_count)

if __name__ == '__main__':
    dict = SqliteDict(
        filename='cedict.db',
        tablename='dict',
        flag='r',
        decode=json.loads,
    )
    deck = Deck(lambda key: dict[key], 'levels.db', weights=[100, 50, 10, 1, 0.1])
    from chinesetools import hsk_words
    deck.update(hsk_words)

