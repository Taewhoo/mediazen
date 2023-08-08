#!/usr/bin/env bash
# hyungwon yang
# this script for nnet3 training. (multi-languages) edited wsj/s5/run.sh

# 데이터 준비 사항
# data
#    train: trainset, trainset_medium, trainset_small (wuts를 포함, segments는 없어도 됨, small -> medium -> trainset 순으로 학습을 진행한다. 데이터 양은 각각 10%, 20~30%, 100%로 설정)
#    test: testset (wuts를 포함, segments는 없어도 됨.)
# lang: 
#    lang: prepare_lang.sh 이용해서 만든 lang 준비. 내부에는 훈련된 lm.arpa로 생성한 G.fst 넣을 것.
#    lang_test: 위에서 만든 lang을 이름만 lang_test로 바꿔서 준비.
# 스크립트 실행 전, 완전히 처음부터라면 모든 스크립트에서 stage가 0으로 설정.
#    run_kor_ivector_common.sh에서 stage는 변경할 필요가 없음. local/nnet3/{run_kor_tdnn_lstm.sh,run_kor_tdnn.sh}에서 설정한 stage값이 자동으로 부여되기 때문.

stage=0

# pitch parameter.
use_pitch=false # adjust pitch srate before running a train process.
# gpu numjob.
ngpu_initial=4
ngpu_final=6
# cpu numjob.
nj=30


. ./cmd.sh ## You'll want to change cmd.sh to something that will work on your system.
           ## This relates to the queue.
. utils/parse_options.sh  # e.g. this parses the --stage option if supplied.


if [ $stage -le 0 ]; then
  echo "start data prep"
  # check wuts condition.
  for x in trainset_small trainset_medium trainset testset; do
    utils/fix_data_dir.sh data/$x || exit 1;
    utils/validate_data_dir.sh --no-feats data/$x || exit 1;
  done

  # check lang preparation.
  for l in lang lang_test; do 
    for f in data/$l/G.fst data/$l/L.fst data/$l/L_disambig.fst data/$l/oov.int \
        data/$l/oov.txt data/$l/phones.txt data/$l/topo data/$l/words.txt; do 
      [ ! -f $f ] && echo "$0: expected file $f to exist" && exit 1;
    done
  done

  # remove pre-made dataset
  for d in trainset_sp trainset_sp_hires testset_hires; do
    [ -d data/$d ] && echo "$0: remove folder $d" && rm -r data/$d;
  done

  # Now make MFCC features.
  # mfccdir should be some place with a largish disk where you
  # want to store MFCC features.

  for x in trainset_small trainset_medium trainset testset; do
    if $use_pitch; then
      echo "using pitch information."
      steps/make_mfcc_pitch.sh --pitch-config conf/pitch.conf --cmd "$train_cmd" --nj $nj data/$x || exit 1;
    else
      steps/make_mfcc.sh --cmd "$train_cmd" --nj $nj data/$x || exit 1;
    fi
    steps/compute_cmvn_stats.sh data/$x || exit 1;
  done
fi


# use small set data
if [ $stage -le 1 ]; then
  # monophone
  # Note: the --boost-silence option should probably be omitted by default
  # for normal setups.  It doesn't always help. [it's to discourage non-silence
  # models from modeling silence.]
  steps/train_mono.sh --boost-silence 1.25 --nj $nj --cmd "$train_cmd" \
    data/trainset_small data/lang exp/mono0a || exit 1;

fi

# use mid set data
if [ $stage -le 2 ]; then
  # tri1
  steps/align_si.sh --boost-silence 1.25 --nj $nj --cmd "$train_cmd" \
    data/trainset_medium data/lang exp/mono0a exp/mono0a_ali || exit 1;

  steps/train_deltas.sh --boost-silence 1.25 --cmd "$train_cmd" 2000 10000 \
    data/trainset_medium data/lang exp/mono0a_ali exp/tri1 || exit 1;

fi

# use full set data
if [ $stage -le 3 ]; then
  # tri2b.  there is no special meaning in the "b"-- it's historical.
  steps/align_si.sh --nj $nj --cmd "$train_cmd" \
    data/trainset data/lang exp/tri1 exp/tri1_ali_si84 || exit 1;

  steps/train_lda_mllt.sh --cmd "$train_cmd" \
    --splice-opts "--left-context=3 --right-context=3" 2500 15000 \
    data/trainset data/lang exp/tri1_ali_si84 exp/tri2b || exit 1;
fi

# local/run_delas.sh trains a delta+delta-delta system.  It's not really recommended or
# necessary, but it does contain a demonstration of the decode_fromlats.sh
# script which isn't used elsewhere.
# local/run_deltas.sh

if [ $stage -le 4 ]; then
  # From 2b system, train 3b which is LDA + MLLT + SAT.

  # Align tri2b system with all the si284 data.
  steps/align_si.sh  --nj $nj --cmd "$train_cmd" \
    data/trainset data/lang exp/tri2b exp/tri2b_aliset  || exit 1;

  steps/train_sat.sh --cmd "$train_cmd" 4200 40000 \
    data/trainset data/lang exp/tri2b_aliset exp/tri3b || exit 1;
  # make graph 
  utils/mkgraph.sh data/lang_test \
      exp/tri3b exp/tri3b/graph || exit 1;
fi

# nnet3 recipe.
if [ $stage -le 7 ]; then
  # A nnet3 recipe:
  local/nnet3/run_kor_tdnn_lstm.sh \
    --use_pitch $use_pitch \
    --ngpu_initial $ngpu_initial \
    --ngpu_final $ngpu_final # lstm recipe
  # chain2 recipe:
  # local/chain2/run_kor_tdnn.sh 

fi

exit 0;
