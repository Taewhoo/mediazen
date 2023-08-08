'''
Sangjoon Kim
23.01.23
MediaZen

inspecting followings
    1. outer folder ordering
    2. inner folder ordering
    3. is any of the outer folders empty?
    4. text file encoding is utf-8 or not 
    5. Print all unique chars in text. Check if text file is empty or not.
    6. text-wav pair check
    7. Print all unique extra_info keys.
    8. audio info check(sampling-rate, bit-rate, num-channel, file-size, duration).
    9. Is wav header appropriate to be read with python (if not, prints ERROR message and keep goes with soxi.)
    10. wav file length is longer than 0.3 sec or not (you can change code if you want to set max_duration.)

    EACH-AND-EVERY FILES-AND-FOLDERS WILL GO THROUGH ALL THE INSPECTIONS.
    Automatically judges to Inner or Outer Multi-Process.

    Generally, -nj 10 ~ 20 is recommended
'''

# execute following line, for a test.
# python v2_validate_namz.py -sr 16000 -nj 20 -d /mnt/nasdata1/NAMZ_DATA/ENGLISH_PROCESSED_DATA/BCS
# feel free to add quiet option (-q) if you want output to be compact.



import os
import re
import time
import wave
import pprint
import argparse
import subprocess
from multiprocessing import Pool



class inspect_namz():
    def __init__(self):

##################### get argparse.arguments ##############################################################  
        parser = argparse.ArgumentParser()
        parser.add_argument('-sr', '--sample_rate', type=int,
                            required=True, help='sampling rate for inspection (necessary)')
        parser.add_argument('-nj', '--num_job', type=int,
                            help='number of jobs. If not given, inspection will be done with a single-process')
        parser.add_argument('-d', '--directory',
                            required=True, help='path for inspection (necessary)')
        parser.add_argument('-q', '--quiet', 
                            help="if you want quiet inspection.", action="store_false")
        self.args = parser.parse_args()
##################### variables given by arguments #############################################        
        self.root = self.args.directory                                 
        self.sr = self.args.sample_rate
        if self.args.num_job:
            self.num_job = self.args.num_job
        else:
            self.num_job=1                                    
################################################################################################

        
        self.channel = 1
        self.bit = 16
        self.min_dur = 1
        self.max_dur = 30
        self.cur_dur = float()
        self.sr_problem = False
        self.outers = os.listdir(self.root)
        self.outers.sort()
        self.len_outer = len(self.outers)
        self.break_main = False
        self.channel_problem = False
        self.bit_problem = False
        self.uniq_chars = set()
        self.uniq_extra_info = set()
        self.OUTER_MULTI_PROCESS = True
        self.continue_outer = False

        self.outer_cnt=int()
        self.skipped_cnt=int()
        self.inner_cnt=int()

        self.total_dur=float()
        self.total_size=float()
        self.total_uniq_chars=set()
        self.total_extra_infos=set()

        print(f"#######################  INSPECTION STARTED  #########################\nCurrent Time: [{time.strftime('%Y-%m-%d %H:%M:%S')}]\nINSPECTING DIRECTORY : {self.root}")
        self.start_time = time.time()

    def text_check(self, text_path):
        try:
            text = open(text_path, encoding='utf-8').read()
            [self.uniq_chars.add(t) for t in text]

        except UnicodeError:
            print(f'------------ERROR: {text_path} has "wrong_encoding" problem.---------------')
        
        #### change if language differs
        if not re.search('\w', text):
            print(f'------------ERROR: {text_path} "is empty".---------------')
        if text != text.strip():
            print(f'------------ERROR: {text_path} "needs strip()".---------------')
        if re.search('\s{2,}', text):
            print(f'------------ERROR: {text_path} "has double spaces".---------------')
        return None

    # kaa-0001-facd 등 외부 폴더의 ordering이 잘 되어 있는지, 빠진 숫자는 없는지 검사한다.
    def outer_folder_check(self, outer):
        if re.search("^"+self.outer_regex+"$", outer):
            extra_info = re.search("[a-z0-9]+$", outer).group(0)
            [self.uniq_extra_info.add(i) for i in extra_info]
            return "PASS"
        return "FAIL"


    ''' kaa-0001-facd-002345.wav / kaa-0001-facd-002345.txt 등 내부 파일의 ordering이 잘 되어 있는지, 
        빠진 숫자는 없는지, pair로 존재하는지 한번에 검사한다.
    '''
    def inner_folder_check(self, inner_regex, inner):
        if re.search('^'+self.outer_regex+inner_regex+'(\.txt|\.wav)$', inner):
            return "PASS"
        return "FAIL"
    
    def txt_pair_check(self, txt_path):
        pair_wav = re.sub("\.txt$", '.wav', txt_path)
        if os.path.isfile(pair_wav):
            return "PASS"
        return "FAIL"

    def wav_pair_check(self, wav_path):
        pair_txt = re.sub("\.wav$", '.txt', wav_path)
        if os.path.isfile(pair_txt):
            return "PASS"
        return "FAIL"

    # wave_inspection: num_channels, sampling_rate, bit_rate, dur check
    # generally wave is faster than scipy.io.wavfile cuz it is written in C.
    def wave_check(self, wav_path):
        try:
            with wave.open(wav_path, "r") as wav_file:
                cur_channel = wav_file.getnchannels()
                cur_sr = wav_file.getframerate()
                cur_bit = wav_file.getsampwidth() * 8
                cur_dur = wav_file.getnframes() / cur_sr

                if cur_channel != self.channel:
                    print(f'------------ERROR: {wav_path} has "num_channels" problem. num_channels : {cur_channel}---------------')
                    self.channel_problem=True
                if cur_sr != self.sr:
                    print(f'------------ERROR: {wav_path} has "sampling rate" problem. sampling_rate : {cur_sr}---------------')
                    self.sr_problem=True
                if cur_bit != self.bit:
                    print(f'------------ERROR: {wav_path} has "bit-rate" problem. bit_rate : {cur_bit}---------------')
                    self.bit_problem=True
                if cur_dur < self.min_dur:
                    print(f'------------ERROR: {wav_path} "is too short". less than 0.3 sec. duration: {cur_dur}---------------')
                self.cur_dur += cur_dur
            return None
        except:
            print(f"'------------ERROR: Cannot Read Wav file with python Wave package. {wav_path} is the format of this?")
            self.soxi_check(wav_path)
            return None

            
    def soxi_check(self, wav_path):
        cmd = f'soxi {wav_path}'
        soxi_info = subprocess.check_output(cmd.split()).decode('utf-8').split('\n')

        cur_channel = int(re.sub('[^0-9]+', '', soxi_info[2]))
        cur_sr = int(re.sub('[^0-9]+', '', soxi_info[3]))
        cur_bit = int(re.sub('[^0-9]+', '', soxi_info[4]))
        cur_dur = float(int(soxi_info[5].split()[4]) / cur_sr)

        if cur_channel != self.channel:
            print(f'------------ERROR: {wav_path} has "num_channels" problem. num_channels : {cur_channel}---------------')
            self.channel_problem=True
        if cur_sr != self.sr:
            print(f'------------ERROR: {wav_path} has "sampling rate" problem. sampling_rate : {cur_sr}---------------')
            self.sr_problem=True
        if cur_bit != self.bit:
            print(f'------------ERROR: {wav_path} has "bit-rate" problem. bit_rate : {cur_bit}---------------')
            self.bit_problem=True
        if cur_dur < self.min_dur:
            print(f'------------ERROR: {wav_path} "is too short". less than 0.3 sec. duration: {cur_dur}---------------')
        if cur_dur > self.max_dur:
            print(f'------------ERROR: {wav_path} "is too long". longer than 20 sec. duration: {cur_dur}---------------')
        self.cur_dur += cur_dur
        return None
    
    # get split points for multi-process.
    def get_split_points(self, process_size):
        return [[process_size*i, 'to_the_end'] if i+1 == self.num_job else [process_size*i, process_size*(i+1)] for i in range(self.num_job)]

    def main(self, start_point, end_point):

        if self.break_main:
            return None

        # split self.outers for multi-processing
        if end_point == 'to_the_end':
            cur_outers = self.outers[start_point:]

        elif self.OUTER_MULTI_PROCESS:
            cur_outers = self.outers[start_point:end_point]
        
        # in case of inner_multi_process
        else:
            cur_outers = self.outers
        
        if self.OUTER_MULTI_PROCESS:
            cur_dur, cur_split_points, uniq_chars, uniq_extra_info = self.outer_main(cur_outers)
            return cur_dur, cur_split_points, uniq_chars, uniq_extra_info

        self.outer_main(cur_outers)
        return None

    def outer_main(self, cur_outers):

        self.skipped_cnt=0
        start_outer = self.outer_cnt
        for idx, outer in enumerate(cur_outers):

            self.p1 = os.path.join(self.root, outer)
            if not os.path.isdir(self.p1):
                print(f"this is a file, not a directory: '{outer}' passing without inspection")
                self.skipped_cnt+=1
                continue
            if idx == 0 or idx == self.skipped_cnt:
                # std_format을 outers[0]으로 하는 것에 대한 개선 방안 필요
                self.std_format = outer.split('-')
                start_outer = int(re.search('-([0-9]+)-', outer).group(1))
                self.outer_cnt = start_outer

            prv_outer_num = None
            if idx > 0:
                try:
                    prv_outer_num = re.search('-[0-9]+-', cur_outers[idx-1]).group(0)
                except:
                    pass
            
            '''
                prv_outer_num의 용도: 같은 번호(화자)의 폴더가 2개 이상일 경우. ex) [kap-0021-xx, kap-0021-yy]
                앞의 폴더 번호를 참고하고 outer_cnt -= 1을 하여, 잘못된 에러를 방지하고자 함.  
            '''
            if prv_outer_num:
                if re.search(prv_outer_num, outer) and self.outer_cnt > start_outer:
                    self.outer_cnt-=1
            # outer_regex: 외부 폴더의 ordering을 점검하기 위한 정규표현식. ex) kap-0{3}1-[a-z0-9]{5}
            self.outer_regex = self.std_format[0]+"-0{"+str(len(self.std_format[1])-len(str(self.outer_cnt)))+"}"+str(self.outer_cnt)+"-[a-z0-9]{"+str(len(self.std_format[2]))+"}"
            
            # pass_or_not: outer_folder_check() 함수 검사 결과
            pass_or_not = self.outer_folder_check(outer)
            if pass_or_not == "FAIL":
                print(f'------------ERROR: {outer} has "outer_folder_check" problem---------------')
                # if outer-folder problem exists, print the ERROR above; prevent repeatedly printing inner-folder problem.
                self.outer_regex = outer
            self.inner_multi_process()
            if self.continue_outer:
                self.continue_outer = False
                continue
            self.outer_cnt+=1
            if self.args.quiet:
                print(f'{outer} is inspected')
        cur_split_points = [start_outer, self.outer_cnt-1]
        self.outer_cnt = 1

        # if outer-multi-process, return results in outer_main.
        # elif inner-multi-process, return results in inner_main.    
        if self.OUTER_MULTI_PROCESS:
            return self.cur_dur, cur_split_points, self.uniq_chars, self.uniq_extra_info

    def inner_main(self, start_point, end_point):

        if end_point == 'to_the_end':
            cur_inners = self.inners[start_point:]
        else:
            cur_inners = self.inners[start_point:end_point]
        self.inner_cnt = int(start_point/2)+1

        for inner in cur_inners:
            # inner_regex: 내부 파일의 ordering을 점검하기 위한 정규표현식. (앞에 outer_regex를 붙여서 사용한다.)
            inner_regex = "-0{"+str(self.inner_num_len-len(str(self.inner_cnt)))+"}"+str(self.inner_cnt)

            # pass_or_not: inner_folder_check() 함수 검사 결과
            pass_or_not = self.inner_folder_check(inner_regex, inner) 
            if pass_or_not == "FAIL":
                print(f'------------ERROR: {inner} has "inner_folder_check" problem.---------------')

            inner_path = os.path.join(self.p1, inner)
            # text file inspect
            if inner.endswith('.txt'):
                self.text_check(inner_path)
                pass_or_not = self.txt_pair_check(inner_path)
                if pass_or_not == "FAIL":
                    print(f'------------ERROR: {inner} has "pair_check" problem. no wav pair for the text file.---------------')
                    self.inner_cnt+=1

            # wav file inspect
            if inner.endswith('.wav'):
                self.wave_check(inner_path)
                pass_or_not = self.wav_pair_check(inner_path)
                if pass_or_not == "FAIL":
                    print(f'------------ERROR: {inner} has "pair_check" problem. no txt pair for the wav file.---------------')
                self.inner_cnt+=1

        # verbose for inner inspection
        if not self.OUTER_MULTI_PROCESS and self.args.quiet:
            print(f"inner inspection: from index {start_point} to {end_point} is done")
        
        if not self.OUTER_MULTI_PROCESS:
            cur_split_points = [start_point, end_point]
            return self.cur_dur, cur_split_points, self.uniq_chars, self.uniq_extra_info
        return None

    def outer_multi_process(self):

        process_size = int(self.len_outer / self.num_job)
        split_points = self.get_split_points(process_size)
        print(f"\n\n################## inspecting with OUTER_MULTI_PROCESS ################\nnum_job:{self.num_job}")
        with Pool(self.num_job) as p:
            try:
                # multi-process 핵심: self.main([100,200]) 이런 식으로 인자값 전달. (2개 이상의 인자를 전달하기 위해 starmap 사용)
                all_results = p.starmap(self.main, split_points)
                p.close()
                p.join()
            # In case parent process is intentionally killed by KeyboardInterrupt, kill all the lasting children processes.
            except:
                p.terminate()

        return all_results

    def inner_multi_process(self):

        self.inner_cnt=1
        self.inners = os.listdir(self.p1)
        self.inners.sort()
        self.len_inner = len(self.inners)
        if not self.inners:
            print(f'------------ERROR: {self.p1} is empty---------------------------------------')
            self.outer_cnt+=1
            self.continue_outer=True
            return None
        self.inner_num_len = len(re.sub(self.outer_regex+'-([0-9]+)(\.txt|\.wav)', '\\1', self.inners[0]))

        # in case of inner multi process
        if not self.OUTER_MULTI_PROCESS:
            process_size = int(self.len_inner / self.num_job)
            split_points = self.get_split_points(process_size)
            print(f"\n\nthe Number of Num_Job is bigger than the Number of Outer Folder.\nInspecting with INNER_MULTI_PROCESS : num_job : {self.num_job}")
            print(f"\n\n################## inspecting with INNER_MULTI_PROCESS ################\nsplit points: {split_points}")
            
            with Pool(self.num_job) as p:
                try:
                    # multi-process 핵심: self.main([100,200]) 이런 식으로 인자값 전달. (2개 이상의 인자를 전달하기 위해 starmap 사용)
                    all_results = p.starmap(self.inner_main, split_points)
                    self.collect_all_results(all_results)
                    p.close()
                    p.join()
                # In case parent process is intentionally killed by KeyboardInterrupt, kill all the lasting children processes.
                except:
                    p.terminate()
                
        else:
            self.inner_main(0, self.len_inner)
    

    def multi_process_main(self):

        # if num_job bigger than the length of outer_folder is given, do inner-multi-processing 
        if self.len_outer <= self.num_job:
            self.OUTER_MULTI_PROCESS = False
            self.main(0, self.len_outer)
            print("inspection terminated")

        # else do outer_multi_process.
        else:
            all_results = self.outer_multi_process()
            self.collect_all_results(all_results)

        self.total_uniq_chars = list(self.total_uniq_chars)
        self.total_uniq_chars.sort()
        self.total_extra_infos = list(self.total_extra_infos)
        self.total_extra_infos.sort()

        self.terminate_inspection()
            
        return None


    def collect_all_results(self, all_results):

        for i, result in enumerate(all_results):
            self.total_dur += result[0]
            cur_outer_cnt = result[1][0]
            self.total_uniq_chars = self.total_uniq_chars.union(result[2])
            self.total_extra_infos = self.total_extra_infos.union(result[3])
            '''
            when multi-processing, outer_check가 [1,2,3,4,5]   //   [6,7,8,9,10] 이렇게 나눠서 이뤄짐.
            각 outer_check의 시작점을 모아서 최종적으로 합당한지 확인 필요. (앞 뒤 지점의 차이가 1 이내인지 검사 필요)
            '''
            if len(all_results)-1 > i > 0:
                prv_outer_cnt=all_results[i-1][1][1]
                if not (cur_outer_cnt - prv_outer_cnt) <= 1 and prv_outer_cnt > 0:
                    if self.OUTER_MULTI_PROCESS:
                        print(f'------------ERROR: "outer_folder_check" problem at outer_point : {cur_outer_cnt}---------------\n for accurate inspection, reinspect with "-nj 1"')
                    else:
                        print(f'------------ERROR: "inner_folder_check" problem at inner_point : {cur_outer_cnt}---------------\n for accurate inspection, reinspect with "-nj 1"')
        if self.OUTER_MULTI_PROCESS:
            self.num_speakers = all_results[i][1][1]
        # 수정 필요
        else:
            self.num_speakers = "I believe you can check this by yourself."
        return None

    def terminate_inspection(self):

        end_time = time.time()
        elapsed_time = end_time - self.start_time

        print("\nAll the folders are inspected. Inspection is terminated")
        print("\nSpent time: %dhr %02dmin %02dsec" % (elapsed_time // 3600, (elapsed_time % 3600 // 60), (elapsed_time % 60)))
        print(f"#######################  INSPECTION TERMINATED  #########################\nCurrent Time: [{time.strftime('%Y-%m-%d %H:%M:%S')}]")

        print("\n\n#######################  TEXT INFO  #####################################")
        print("Uniq Chars:")
        pprint.pprint(self.total_uniq_chars, compact=True)
        print(f"\nUniq Extra Info Keys: {self.total_extra_infos}")

        print("\n\n#######################  AUDIO INFO  ####################################")

        if not self.sr_problem:
            print(f"\nSamplig Rate: {self.sr}")
        if not self.channel_problem:
            print(f"\nNumber of Channels: {self.channel}")
        if not self.bit_problem:
            print(f"\nBit Rate: {self.bit}")
        print("\nTotal Duration: %dhr %02dmin %02dsec" % (self.total_dur // 3600, (self.total_dur % 3600 // 60), (self.total_dur % 60)))
        print(f"\nNumber of Unique Speakers: {self.num_speakers}")

        print("\n\n#########  note  #########################################################\n\nif some of the information among ['Sampling Rate', 'Number of Channels', 'Bit Rate', 'Total Duration', 'Number of Unique Speakers'] is inappropriate, problem exists. Go check ERRORs.")

        return None

if __name__ == '__main__':

    inspect = inspect_namz()
    inspect.multi_process_main()