import re, os
import glob
from pathlib import Path
from tqdm import tqdm

class Extra_refiner():
    
    '''
    추가 정제 스크립트.
    사용 전 꼭 샘플 폴더에 시험해볼것..
    '''

    def __init__(self):
        
        # 직접 작성
        self.srcpath = "/mnt/data1/taewhoo/ASR/calldata_refine/KCD_tmp"
        self.speaker_namz_format = "kcd-{0:05}"
        self.utt_format = "{0}-{1:03}" 

    def change_format(self, spk_num, utt_num, downgrade_spk=True, downgrade_utt=True):

        '''
        화자수 / 발화수를 잘못 계산한 경우 수정한다. 

        downgrade_spk=True : 화자 자릿수를 내린다.
        downgrade_utt=True : 발화 자릿수를 내린다. 
        spk_num : 새로운 화자 자릿수 (e.g. 4)
        utt_num : 새로운 발화 자릿수 (e.g. 5)   
        '''
        
        for spk in os.listdir(self.srcpath):
            
            print(f'changing format of {spk}...')

            spk_format = re.search('-(\d+)-', spk).group(1) #ex. 00023
            
            if downgrade_spk:

                zeros_to_lose = int(len(spk_format)) - spk_num #ex. 1
                new_spk_format = spk_format[zeros_to_lose:] #ex. 00023 -> 0023
            
            else:

                zeros_to_gain = spk_num - int(len(spk_format))
                new_spk_format = '0'*zeros_to_gain + spk_format
            
            new_spk = re.sub(spk_format, new_spk_format, spk)
            old_spk_path = os.path.join(self.srcpath, spk)
            new_spk_path = os.path.join(self.srcpath, new_spk)

            os.rename(old_spk_path, new_spk_path)
            
            # 파일명에도 새로운 화자수 반영하고, 발화수까지 반영
            filelist = glob.glob(f'{self.srcpath}/{spk}/*')

            for old_filepath in filelist:
                
                old_file = os.path.basename(old_filepath) #ex. kar-00023-dbbba-0023.txt / kar-00023-dbbba-0024.txt
                old_spk = re.search('\w+-\d+-\w+', old_file).group() # kar-00023-dbbba
                new_file = re.sub(old_spk, new_spk, old_file) #ex. (00023->0023 in old_file) kar-0023-dbbba-0023.txt / kar-0023-dbbba-0024.txt
                utt_format = re.search('.+-(\d+)', old_filepath).group(1) #ex. 0023 / 0024
                
                if downgrade_utt:

                    zeros_to_lose = int(len(utt_format)) - utt_num
                    new_utt_format = utt_format[zeros_to_lose:]
                
                else:

                    zeros_to_gain = utt_num - int(len(utt_format))
                    new_utt_format = '0'*zeros_to_gain + utt_format #ex. 00023 / 00024
                
                new_file = re.sub(utt_format+'\.', new_utt_format+'.', old_file) #(0023 to 00023 in kar-0023-dbbba-0023.txt) kar-00023-dbbba-00023.txt가 되어버림;; / (0024 to 00024 in kar-0023-dbbba-0024.txt) kar-0023-dbbba-00024.txt
                new_filepath = re.sub(old_file, new_file, old_filepath)

                os.rename(old_filepath, new_filepath)
            
            print(f'{spk} format updated')

        return


    def reorder_files(self, mildcheck=True):
        
        '''
        utt 순서를 재배열한다.
        ** reordering 전 포맷화가 잘 되었는지 확인하고, 수정이 필요할 경우 change_format()부터 진행할 것 **
        ** utt 순서 확인 전, wav이나 txt'만' 존재하는 파일들은 삭제된다. 이게 싫을 경우 pair 채워주고 진행할 것 **

        mildcheck=True : reordering 진행 전 (파일 개수 = 마지막 uttnum * 2)일 경우 넘어간다.
        '''
        
        i=1
        for spk in sorted(os.listdir(self.srcpath)): 
            
            if spk == "README.md":
                continue
                
            print(f'reordering files in {spk}...')

            idx = 1
            filelist = sorted(os.listdir(f'{self.srcpath}/{spk}'))

            if len(filelist) == 0:

                print(f'{spk} folder empty, moving on...')
                continue

            last_file = filelist[-1]
            last_file_idx = re.search('.+-(\d+)', last_file).group(1)
            idset = set()

            if mildcheck == True and int(len(filelist)) == 2 * int(last_file_idx):

                print(f'mild check : nothing wrong in order with {spk}!')
                continue

            for file_ in filelist:

                fileid = re.search('(.+?)\.', file_).group(1)

                if fileid in idset:

                    continue

                oldtxt = fileid + '.txt'
                oldwav = fileid + '.wav'

                if oldtxt not in filelist or oldwav not in filelist:
                    
                    print(f'removing {file_}: not in pair')
                    os.remove(os.path.join(self.srcpath, spk, file_))
                    continue
                
                newid = self.utt_format.format(spk, idx)
                newtxt = newid + '.txt'
                newwav = newid + '.wav'

                os.rename(os.path.join(self.srcpath, spk, oldtxt), os.path.join(self.srcpath, spk, newtxt))
                os.rename(os.path.join(self.srcpath, spk, oldwav), os.path.join(self.srcpath, spk, newwav))
                
                idx += 1
                idset.add(fileid)
            
            print(f'reordering {spk} done')
        
        return


    def rename_files(self):

        '''
        폴더가 중간중간 삭제된 경우, spk_number를 재배열하고 파일명도 변경한다.
        '''
        speaker_number = 1
        for spk in tqdm(sorted(os.listdir(self.srcpath))):

            oldpart = re.search('\w{3}-\d{5}', spk).group()
            spk_format = self.speaker_namz_format.format(speaker_number)
            
            # rename spk folder TO PARENT DIR (avoid overlapping names)
            newname = re.sub(oldpart, spk_format, spk)
            os.rename(os.path.join(self.srcpath, spk), os.path.join(self.srcpath, os.pardir, newname))
            speaker_number += 1

            # match file name with new directory name
            files = sorted(os.listdir(os.path.join(self.srcpath, os.pardir, newname)))
            for f in files:
                oldpart = re.search('\w{3}-\d{5}-\w{2}', f).group()
                newf = re.sub(oldpart, newname, f)
                os.rename(os.path.join(f'{self.srcpath}', os.pardir, newname, f), os.path.join(f'{self.srcpath}', os.pardir, newname, newf))

            



if __name__ == '__main__':
    
    refiner = Extra_refiner()
    # refiner.change_format(4, 5, downgrade_spk=True, downgrade_utt=False)
    refiner.rename_files()