from typing import List
import json
import os
import glob
import copy

class WordSetDictionary():
    def __init__(self, data_dir: str, letters: list=None):
        self.db = {}
        self.data_dir = data_dir
        if letters:
            self.letters = letters
        else:
            # list all json files under the directory
            letter_files = glob.glob(os.path.join(data_dir, '*.json'))
            self.letters = [os.path.splitext(item.split('/')[-1])[0] for item in letter_files]
            
        self.import_dictionary_files()

    def clear_db(self):
        self.db = {}
        
    def add_dicts_to_db(self, letters: list):
        for letter in letters:
            with open(os.path.join(self.data_dir, f'{letter}.json')) as f:
                json_chunk = json.load(f)
            self.db.update(json_chunk)

    def import_dictionary_files(self):
        self.add_dicts_to_db(self.letters)
        
    def group_meanings_by_speech_part(self, meanings: List[dict]) -> dict:
        meanings_by_pos = {}
        for meaning in meanings:
            pos = meaning['speech_part']
            if pos not in meanings_by_pos:
                meanings_by_pos[pos] = []
            meanings_by_pos[pos].append(meaning)

        return meanings_by_pos

    def get(self, word: str, speech_parts: List[str]=None, metadata: bool=False) -> dict:
        if word not in self.db:
            return {
                'status': 0,
                'err_msg': 'The word does not exist in the dictionary',
                'hints': f'''1) Please check if you have included the letter "{word[0]}" in your database yet. If not, use method `add_dicts_to_db`.\n2) You can add a new word into `data/<letter>.json`'''
            }

        # This is essentially the JSON blob of the word
        vocab = copy.deepcopy(self.db[word])

        meanings_by_pos = self.group_meanings_by_speech_part(vocab['meanings'])
        
        ##################################
        ### construct payload
        ##################################
        payload = {}
        payload['wordset_id'] = vocab['wordset_id']

        # filter meanings by speech parts
        if speech_parts is None:
            # get all parts of speech
            payload['meaning'] = meanings_by_pos
            success_speech_parts = list(meanings_by_pos.keys())
        else:
            # get part of speech one by one
            payload['meaning'] = {}
            success_speech_parts = []
            for speech_part in speech_parts:
                if speech_part in meanings_by_pos:
                    payload['meaning'][speech_part] = meanings_by_pos[speech_part]
                    success_speech_parts.append(speech_part)

        # metadata
        if metadata:
            payload['editors'] = vocab['editors']
            payload['contributors'] = vocab['contributors']

        # determine the status
        if len(success_speech_parts) == 0:
            payload['status'] = 2
            payload['err_msg'] = 'The word exists but does not have the requested speach parts'
            payload['hints'] = 'Please try to remove parameter `speech_parts` from your request and rerun'
        
        elif len(success_speech_parts) > 0:
            payload['status'] = 1

        return payload

    def list_words(self):
        all_words = list(self.db.keys())
        return {
            "words": all_words,
        }

    def count_words(self):
        all_words = self.list_words()['words']
        return {
            "count": len(all_words),
        }

if __name__ == '__main__':
    import random
    import time

    # path to the data
    data_dir = './data'

    t0 = time.time()
    # To import only letters a, b and c for demo
    # EngDict = WordSetDictionary(data_dir, ['a', 'b', 'c'])
    # To import all letters there are, use this instead
    EngDict = WordSetDictionary(data_dir)
    print(f'Initiating dictionary takes: {int(1000*(time.time() - t0))} milliseconds')

    # Show some examples
    all_words = EngDict.list_words()["words"]
    selected_words = []
    for n in range(0, 5):
        selected_words.append(
            all_words[ random.randint(0, len(all_words)-1) ]
            )    

    print(f'''
    There are {EngDict.count_words()["count"]} words in this dictionary.
    Here are some examples picked randomly: {', '.join(selected_words)}
    ''')

    print('And you may be surprised by how many meanings "cat" has:')
    payload = EngDict.get('cat')
    print(json.dumps(payload, indent=2))

    # payload = EngDict.get('air')
    # print(json.dumps(payload, indent=2))

    # payload = EngDict.get('air', speech_parts=['noun'], metadata=False)
    # print(json.dumps(payload, indent=2))

    # payload = EngDict.get('air', speech_parts=['gb'], metadata=True)
    # print(json.dumps(payload, indent=2))

    # payload = EngDict.get('mama', speech_parts=['noun'], metadata=True)
    # print(json.dumps(payload, indent=2))

