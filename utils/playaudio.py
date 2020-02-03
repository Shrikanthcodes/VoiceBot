from utils.config import sound_src

class Playaudio():
    audioflag = True

    @classmethod
    def holdmusic(self, agi, audio):
        agi.stream_file(sound_src + audio, escape_digits='', sample_offset=0)
        while Playaudio.audioflag:
            agi.stream_file(sound_src + 'holdmusic', escape_digits='', sample_offset=0)

