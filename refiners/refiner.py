import os, re
from pathlib import Path
import shutil
import json
from collections import defaultdict
import librosa
import glob

class Refiner():

    def __init__(self):
        
        self.curpath = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir))) # ~/calldata_refine
        self.srcpath = os.path.join(self.curpath, 'ak', 'main')
        # self.infopath = os.path.join(self.srcpath, 'info')
        self.finalpath = os.path.join(self.curpath, 'KCD_sr8000')

        os.makedirs(self.finalpath, exist_ok=True)

        self.company = 'a' #ak
        self.rtdict = defaultdict(lambda:'u', {'rx':'a', 'tx':'b'})

        self.speaker_namz_format = "kcd-{0:05}-{1}"
        self.speaker_namz_dict = dict() # id-namzid pair
        self.speaker_number = 1
        self.utt_format = "{0}-{1:03}"
        # self.utt_namz_dict = defaultdict(int)
        # namzid-uttnum pair. 용량 때문에 화자 폴더 삭제-생성 반복할 경우 활용.
    
    def refine(self):
        
        for spk in os.listdir(self.srcpath):
            
            try:
                print(f'{spk} 정제 시작...')
                
                spkpath = os.path.join(self.srcpath, spk)
                rt = re.match('\w{2}', spk).group() # a, b or u
                extra_info = self.company + self.rtdict[rt]
                
                utt_number = 1 # spk 바뀔 때마다 초기화
                speaker_namz = self.speaker_namz_format.format(self.speaker_number, extra_info) # kcd-0001-ga
                
                os.makedirs(os.path.join(self.finalpath, speaker_namz), exist_ok=True)
                print(f'{spk} -> {speaker_namz}')

                for wavpath in glob.glob(f'{spkpath}/*wav'):

                    txtpath = re.sub('\.wav', '.txt', wavpath)
                    duration = librosa.get_duration(path=wavpath)

                    if duration < 0.3 or duration > 30:

                        continue
                    
                    with open(txtpath) as rf:

                        text = rf.read()
                    
                    text = re.sub('\s+', ' ', text) # 모든 double+ space : single-space로 치환
                    text = text.strip()

                    if len(text) == 0:
                        
                        continue

                    utt_namz = self.utt_format.format(speaker_namz, utt_number)
                    new_wavpath = os.path.join(self.finalpath, speaker_namz, utt_namz + '.wav')
                    new_txtpath = os.path.join(self.finalpath, speaker_namz, utt_namz + '.txt')
                    
                    if re.search('[^가-힣 ]', text): # 특수문자 있으면 일단 정제 후 나중에 손수 고치기
                        
                        print(f'non-kor char in text : {new_txtpath}')   

                    with open(new_txtpath, 'w') as wf:

                        wf.write(text)
                    
                    os.system(f'ffmpeg -i {wavpath} -ac 1 -ar 8000 {new_wavpath} -hide_banner -loglevel error')

                    utt_number += 1
                
                self.speaker_number +=1

            except Exception as e:

                print(f'error while processing {spk}!')
                print(e)
                