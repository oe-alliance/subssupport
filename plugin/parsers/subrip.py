import re

from .baseparser import BaseParser, ParseError, HEX_COLORS


class SubRipParser(BaseParser):
    format = "SubRip"
    parsing = ('.srt', '.sub')  # some providers ship SubRip as .sub, MicroDVD/SubViewer are tried next

    def _parse(self, text, fps):
        return self._srt_to_dict(text)

    def _removeTags(self, text):
        # First, split by lines to handle multi-line content within tags
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Remove HTML tags from each line
            line = re.sub('<[^>]*>', '', line)
            # Remove SSA/ASS positioning tags like {\an8}
            line = re.sub(r'\{.*?\}', '', line)
            line = re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', '', line.replace('\t', ' ')).strip()
            cleaned_lines.append(line)

        # Join back with newlines to preserve the multi-line structure, without empty lines
        return '\n'.join(filter(None, cleaned_lines))

    def _getColor(self, text, color):
        # color: still open <font> colour of the previous row (row parsing)
        color = color or 'default'
        colorMatch = re.search('<[Ff]ont [Cc]olor=(.+?)>', text, re.DOTALL)
        if colorMatch:
            colorText = colorMatch.group(1).replace("'", "").replace('"', '').strip()
            hexColor = re.search(r"#([0-9a-fA-F]{6})", colorText)
            if hexColor:
                color = hexColor.group(1)
            elif colorText.lower() in HEX_COLORS:
                color = HEX_COLORS[colorText.lower()][1:]
        newColor = 'default' if '</font>' in text.lower() else color
        return color, newColor

    def _getStyle(self, text, style):
        newStyle = style
        endTag = False
        # looking for end tag
        if not style:
            if self.italicStart(text):
                style = 'italic'
                newStyle = style
                endTag = self.italicEnd(text)
            elif self.boldStart(text):
                style = 'bold'
                newStyle = style
                endTag = self.boldEnd(text)
            elif self.underlineStart(text):
                style = 'regular'
                newStyle = style
        else:
            if style == 'italic':
                endTag = self.italicEnd(text)
            elif style == 'bold':
                endTag = self.boldEnd(text)
            elif style == 'underline':
                endTag = True
            # looking for start/end tag on the same line
            else:
                if self.italicStart(text):
                    style = 'italic'
                    newStyle = style
                    endTag = self.italicEnd(text)
                elif self.boldStart(text):
                    style = 'bold'
                    newStyle = style
                    endTag = self.boldEnd(text)
                elif self.underlineStart(text):
                    style = 'regular'
                    newStyle = style

        if endTag:
            newStyle = 'regular'
        return style, newStyle

    def _srt_to_dict(self, srtText):
        subs = []
        srtText = srtText.replace('\r\n', '\n').strip() + "\n"
        # the text of a cue runs up to the next timing line, without the number line in front of it
        timings = list(re.finditer(r'^[ \t]*(\d+):(\d+):(\d+),(\d+)[ \t]*-->[ \t]*(\d+):(\d+):(\d+),(\d+)[^\n]*$', srtText, re.MULTILINE))
        for idx, s in enumerate(timings):
            try:
                shour, smin, ssec, smsec = int(s.group(1)), int(s.group(2)), int(s.group(3)), int(s.group(4))
                start_time = int((shour * 3600 + smin * 60 + ssec) * 1000 + smsec)
                ehour, emin, esec, emsec = int(s.group(5)), int(s.group(6)), int(s.group(7)), int(s.group(8))
                end_time = int((ehour * 3600 + emin * 60 + esec) * 1000 + emsec)
                lines = srtText[s.end():timings[idx + 1].start() if idx + 1 < len(timings) else len(srtText)].strip('\n').split('\n')
                if idx + 1 < len(timings) and lines[-1].strip().isdigit():
                    lines.pop()
                sub_text = '\n'.join(lines).strip()
                if sub_text:  # empty cue
                    subs.append(self.createSub(sub_text, start_time, end_time))
            except Exception as e:
                raise ParseError(str(e) + ', subtitle_index: %d' % (idx + 1))

        return subs

    def italicStart(self, text):
        return text.lower().find('<i>') != -1

    def italicEnd(self, text):
        return text.lower().find('</i>') != -1

    def boldStart(self, text):
        return text.lower().find('<b>') != -1

    def boldEnd(self, text):
        return text.lower().find('</b>') != -1

    def underlineStart(self, text):
        return text.lower().find('<u>') != -1

    def underlineEnd(self, text):
        return text.lower().find('</u>') != -1


parserClass = SubRipParser
