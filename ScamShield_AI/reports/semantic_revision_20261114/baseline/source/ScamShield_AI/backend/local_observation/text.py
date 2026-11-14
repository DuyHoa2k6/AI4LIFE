"""Match on accent-folded clusters; all public spans index the untouched original."""
from dataclasses import dataclass
import re
import unicodedata


@dataclass
class Normalized:
    text: str
    starts: list[int]
    ends: list[int]

    def original_range(self, start, end):
        if not 0 <= start < end <= len(self.text):
            raise ValueError('Invalid normalized range')
        return self.starts[start], self.ends[end - 1]


def _fold(text):
    chars, starts, ends = [], [], []
    i = 0
    while i < len(text):
        end = i + 1
        while end < len(text) and unicodedata.combining(text[end]):
            end += 1
        folded = ''.join(c for c in unicodedata.normalize('NFD', text[i:end].casefold().replace('đ', 'd'))
                         if not unicodedata.combining(c))
        for char in folded:
            if char.isspace():
                char = ' '
                if chars and chars[-1] == ' ':
                    ends[-1] = end
                    continue
            chars.append(char); starts.append(i); ends.append(end)
        i = end
    return Normalized(''.join(chars), starts, ends)


def normalize(text):
    from .abbreviations import expand_normalized
    return expand_normalized(text,_fold(text))


def quote_ranges(text):
    stack, ranges = [], []
    pairs = {'“': '”', '‘': '’', '"': '"', "'": "'"}
    for i, char in enumerate(text):
        if stack and char == stack[-1][0]:
            _, start = stack.pop(); ranges.append((start, i + 1))
        elif char in pairs:
            stack.append((pairs[char], i))
    ranges.extend((start, len(text)) for _, start in stack)
    return ranges


def units(text):
    from .segmentation import segments
    return [(u.sentence_id,u.context_start,u.context_end,u.start,u.end,u.quoted) for u in segments(text)]
