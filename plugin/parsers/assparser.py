import re

from .baseparser import BaseParser, ParseError


class AssParser(BaseParser):
    """Advanced SubStation Alpha / SubStation Alpha (.ass/.ssa), dialogue lines of the [Events] section."""
    format = "ASS/SSA"
    parsing = ('.ass', '.ssa')

    def _removeTags(self, text):
        text = re.sub(r'\{[^}]*\}', '', text)  # override codes like {\an8}, {\i1}
        return text.replace('\\N', '\n').replace('\\n', '\n').replace('\\h', ' ').strip()

    def _getStyle(self, text, style):
        if re.search(r'\{[^}]*\\i1', text):
            return 'italic', style
        if re.search(r'\{[^}]*\\b1', text):
            return 'bold', style
        return '', style

    @staticmethod
    def _time(value):
        h, m, s = value.strip().split(':')
        return int((int(h) * 3600 + int(m) * 60 + float(s)) * 1000)

    def _parse(self, text, fps):
        fields = ['layer', 'start', 'end', 'style', 'name', 'marginl', 'marginr', 'marginv', 'effect', 'text']
        subs = []
        events = False
        for line in text.splitlines():
            line = line.strip()
            if line.startswith('['):
                events = line.lower() == '[events]'
            elif events and line.lower().startswith('format:'):
                fields = [f.strip().lower() for f in line[7:].split(',')]
            elif events and line.lower().startswith('dialogue:'):
                values = line[9:].split(',', len(fields) - 1)
                if len(values) != len(fields):
                    continue
                event = dict(zip(fields, values))
                try:
                    start, end = self._time(event['start']), self._time(event['end'])
                except (KeyError, ValueError) as e:
                    raise ParseError("invalid dialogue line: %s (%s)" % (line, e))
                if self._removeTags(event.get('text', '')):
                    subs.append((start, end, event['text']))
        subs.sort(key=lambda sub: sub[0])  # ass files are not required to be sorted
        return [self.createSub(text, start, end) for start, end, text in subs]

    def _getColor(self, text, color):
        # primary colour {\c&HBBGGRR&} or {\1c&H...&}
        match = re.search(r'\{[^}]*\\1?c&H([0-9a-fA-F]{1,8})&', text)
        if match:
            bgr = match.group(1)[-6:].zfill(6)
            color = bgr[4:6] + bgr[2:4] + bgr[:2]
        # rowParse: the colour continues on the next row until it is reset
        if re.search(r'\{[^}]*\\(?:1?c[\\}]|r)', text):
            return color, ''
        return color, color


parserClass = AssParser
