from pathlib import Path
import re

path = "/mnt/nasdata1/NAMZ_DATA/SPANISH_PROCESSED_DATA/SCV"
searchpath = Path(path)
wavlist = searchpath.rglob('*.wav')

wav_scp_result = []
utt2spk_result = []
text_result = []

for wavfile in wavlist:
    
    wavfile = str(wavfile)
    txtfile = re.sub('wav', 'txt', wavfile)
    
    with open(txtfile) as rt:

        text = rt.read()
        
    audioname = re.search("\w{3}-\d{5}-\w{4}-\d{5}", wavfile).group()
    spkname = re.search("\w{3}-\d{5}-\w{4}", wavfile).group()

    audioname_wavpath = audioname + ' ' + wavfile
    audioname_spkname = audioname + ' ' + spkname
    audioname_text = audioname + ' ' + text

    wav_scp_result.append(audioname_wavpath)
    utt2spk_result.append(audioname_spkname)
    text_result.append(audioname_text)

    print(f"{wavfile} done")

with open("wav_scp.txt", "w") as f:

    f.write('\n'.join(wav_scp_result))

with open("utt2spk.txt", "w") as f:

    f.write('\n'.join(utt2spk_result))

with open("text.txt", "w") as f:

    f.write('\n'.join(text_result))


    