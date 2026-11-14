"""RDRSegmenter + slow PhoBERT BPE with explicit original-code-point alignment."""
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from dataclasses import dataclass

class AlignmentError(ValueError):pass
class InputLimit(ValueError):pass

@dataclass
class Word:
    text:str
    start:int
    end:int
    message_id:str=''

def folded(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text).casefold() if not unicodedata.combining(c))

def align(original, segmented):
    # Accent normalization can move a Vietnamese tone within a syllable; use
    # accent-insensitive alignment ONLY to locate the original, never as evidence.
    stream=[]
    for match in re.finditer(r'[^\s_][\u0300-\u036f]*',original):
        stream.extend((c,match.start(),match.end()) for c in folded(match.group()))
    cursor=0;words=[]
    for token in segmented:
        key=folded(token.replace('_',''))
        if not key:raise AlignmentError('empty segmented word')
        part=stream[cursor:cursor+len(key)]
        if ''.join(c for c,_,_ in part)!=key:raise AlignmentError('segmenter changed unalignable content')
        words.append(Word(token,part[0][1],part[-1][2]));cursor+=len(key)
    if cursor!=len(stream):raise AlignmentError('segmenter omitted source content')
    return words

class RDRSegmenter:
    def __init__(self, directory):
        self.directory=Path(directory).resolve();self.jar=self.directory/'VnCoreNLP-1.2.jar'
        if not self.jar.exists():raise FileNotFoundError('VnCoreNLP is not prepared')
    def __call__(self,text):
        with tempfile.TemporaryDirectory(prefix='scamshield-wseg-') as temp:
            source=Path(temp)/'input.txt';target=Path(temp)/'output.txt'
            source.write_text(text,encoding='utf-8')
            run=subprocess.run(['java','-Xmx512m','-jar',str(self.jar),'-fin',str(source),'-fout',str(target),'-annotators','wseg'],cwd=self.directory,capture_output=True,timeout=30)
            if run.returncode or not target.exists():raise AlignmentError('local RDRSegmenter failed')
            tokens=[]
            for line in target.read_text(encoding='utf-8').splitlines():
                columns=line.split('\t')
                if len(columns)>=2 and columns[0].isdigit():tokens.append(columns[1])
            if not tokens:raise AlignmentError('local segmenter returned no aligned words')
            return align(text,tokens)

def windows(words,tokenizer,max_length=256,overlap=24,max_windows=32):
    if not 8<=max_length<=256 or overlap<0:raise ValueError('invalid window configuration')
    pieces=[tokenizer.tokenize(w.text) for w in words]
    if any(not p or len(p)>max_length-2 for p in pieces):raise InputLimit('word cannot fit checkpoint window')
    output=[];start=0
    while start<len(words):
        stop=start;ids=[tokenizer.bos_token_id];ranges=[]
        while stop<len(words):
            boundary=stop>start and words[stop].message_id!=words[stop-1].message_id
            if len(ids)+len(pieces[stop])+int(boundary)+1>max_length:break
            if boundary:ids.append(tokenizer.eos_token_id)
            begin=len(ids);ids.extend(tokenizer.convert_tokens_to_ids(pieces[stop]));ranges.append((begin,len(ids)));stop+=1
        ids.append(tokenizer.eos_token_id)
        output.append({'start_word':start,'stop_word':stop,'input_ids':ids,'word_tokens':ranges})
        if len(output)>max_windows:raise InputLimit('too many windows; input not silently truncated')
        if stop==len(words):break
        start=max(start+1,stop-overlap)
    return output
