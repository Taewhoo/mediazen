from pathlib import Path 
import librosa
from multiprocessing import Pool

def check_duration(target):
    total = 0
    wavfiles = Path(target).rglob('*.wav')
    for wav in wavfiles:
        duration = librosa.get_duration(filename=wav)
        total += duration
    result = target + '\t' + str(total)
    return result

if __name__ == '__main__':
    targets=[
        '/mnt/data1/taewhoo/ASR/calldata/ak/main/ak_20191104_wav',
        '/mnt/data1/taewhoo/ASR/calldata/ak/main/ubase_ak_0622',
        '/mnt/data1/taewhoo/ASR/calldata/coway/test4ubase/old_version',
        '/mnt/data1/taewhoo/ASR/calldata/daemyungsangjo/main/220101',
        '/mnt/data1/taewhoo/ASR/calldata/dlive/dlive_data/221125',
        '/mnt/data1/taewhoo/ASR/calldata/dyson/main/ubase_dyson_data',
        '/mnt/data1/taewhoo/ASR/calldata/nespresso/main',
        '/mnt/data1/taewhoo/ASR/calldata/ssg/main',
        '/mnt/data1/taewhoo/ASR/calldata/yogiote/main/ubase_yogiote_data'
    ]
    with Pool(5) as p:
        print('\n'.join(p.map(check_duration, targets)))