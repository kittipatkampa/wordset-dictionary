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
        
    def get(self, word: str, speech_parts: List[str]=None, metadata: bool=False) -> dict:
        if word not in self.db:
            return {
                'status': 0,
                'err_msg': 'The word does not exist in the dictionary',
                'hints': f'''1) Please check if you have included the letter "{word[0]}" in your database yet. If not, use method `add_dicts_to_db`.\n2) You can add a new word into `data/<letter>.json`'''
            }

        payload = {}
        vocab = copy.deepcopy(self.db[word])
        
        # group meaning by pos
        meanings_by_pos = {}
        for meaning in vocab['meanings']:
            pos = meaning['speech_part']
            if pos not in meanings_by_pos:
                meanings_by_pos[pos] = []
            meanings_by_pos[pos].append(meaning)
        
        ##################################
        ### construct payload
        ##################################
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
        
if __name__ == '__main__':
    data_dir = './data'
    EngDict = WordSetDictionary(data_dir, ['a', 'b', 'c'])
    
    payload = EngDict.get('air')
    print(json.dumps(payload, indent=2))

    payload = EngDict.get('air', speech_parts=['noun'], metadata=False)
    print(json.dumps(payload, indent=2))

    payload = EngDict.get('air', speech_parts=['gb'], metadata=True)
    print(json.dumps(payload, indent=2))

    payload = EngDict.get('mama', speech_parts=['noun'], metadata=True)
    print(json.dumps(payload, indent=2))

