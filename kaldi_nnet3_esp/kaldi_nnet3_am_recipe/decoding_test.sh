#/bin/bash
# decode generated model with test data

# Begin configuration section.
decoder_type=nnet3
## nnet2 variables.
stage=0
nj=12
cmd=run.pl
max_active=7000
threaded=false
modify_ivector_config=false #  only relevant to threaded decoder.
beam=20.0
lattice_beam=10.0
acwt=0.1   # note: only really affects adaptation and pruning (scoring is on
# lattices).
per_utt=true
online=true  # only relevant to non-threaded decoder.
do_endpointing=false
do_speex_compressing=false
scoring_opts=
silence_weight=1.0  # set this to a value less than 1 (e.g. 0) to enable silence weighting.
max_state_duration=40 # This only has an effect if you are doing silence
# weighting.  This default is probably reasonable.  transition-ids repeated
# more than this many times in an alignment are treated as silence.
iter=final
# End configuration section.

## nnet3 variables.
frames_per_chunk=20
extra_left_context_initial=0
min_active=200
max_active=7000
post_decode_acwt=1.0  # can be used in 'chain' systems to scale acoustics by 10 so the
                      # regular scoring script works.
online_config=

# Check input arguments.
if [ $# -ne 4 ]; then
    echo "Four arguments should be assigned."
    echo "1. graph directory"
    echo "2. nnet_ms_a_online directory"
    echo "3. test file directory"
    echo "4. save(decoding result) directory"
    exit 1
fi

# Set input arguments.
graphdir=$1
srcdir=$2
data=$3
dir=$4
if $per_utt; then
  utt_suffix=utt
  utt_opt="--per-utt"
else
  utt_suffix=
  utt_opt=
fi

echo "start: "`date`
echo "$0 $1 $2 $3 $4"
# Set kaldi directory
KALDI_ROOT=/home/kaldi
. path.sh $KALDI_ROOT
. parse_options.sh || exit 1;

sdata=$data/split${nj}${utt_suffix};
mkdir -p $dir/log
split_data.sh $utt_opt $data $nj || exit 1;
echo $nj > $dir/num_jobs

if [ "$online_config" == "" ]; then
    online_config=$srcdir/conf/online.conf
fi

for f in $srcdir/${iter}.mdl $graphdir/HCLG.fst $graphdir/words.txt $data/wav.scp; do
    if [ ! -f $f ]; then
	echo "$0: no such file $f"
	exit 1;
    fi
done

if [ $decoder_type == "nnet2" ]; then
    if [ ! -f $srcdir/conf/online_nnet2_decoding.conf ]; then
        echo "$0: no such file $srcdir/conf/online_nnet2_decoding.conf"
        exit 1;
    fi
fi
if [ $decoder_type == "nnet3" ]; then
    if [ ! -f $online_config ]; then
        echo "$0: no such file $online_config"
        exit 1;
    fi  
fi

if ! $per_utt; then
    spk2utt_rspecifier="ark:$sdata/JOB/spk2utt"
else
    mkdir -p $dir/per_utt
    for j in $(seq $nj); do
	awk '{print $1, $1}' <$sdata/$j/utt2spk >$dir/per_utt/utt2spk.$j || exit 1;
    done
    spk2utt_rspecifier="ark:$dir/per_utt/utt2spk.JOB"
fi

if [ -f $data/segments ]; then
    wav_rspecifier="ark,s,cs:extract-segments scp,p:$sdata/JOB/wav.scp $sdata/JOB/segments ark:- |"
else
    wav_rspecifier="ark,s,cs:wav-copy scp,p:$sdata/JOB/wav.scp ark:- |"
fi
if $do_speex_compressing; then
    wav_rspecifier="$wav_rspecifier compress-uncompress-speex ark:- ark:- |"
fi
if $do_endpointing; then
    wav_rspecifier="$wav_rspecifier extend-wav-with-silence ark:- ark:- |"
fi

if [ "$silence_weight" != "1.0" ]; then
    silphones=$(cat $graphdir/phones/silence.csl) || exit 1
      silence_weighting_opts="--ivector-silence-weighting.max-state-duration=$max_state_duration --ivector-silence-weighting.si\
lence_phones=$silphones --ivector-silence-weighting.silence-weight=$silence_weight"
else
    silence_weighting_opts=
fi


if [ "$post_decode_acwt" == 1.0 ]; then
  lat_wspecifier="ark:|gzip -c >$dir/lat.JOB.gz"
else
  lat_wspecifier="ark:|lattice-scale --acoustic-scale=$post_decode_acwt ark:- ark:- | gzip -c >$dir/lat.JOB.gz"
fi

if [ -f $srcdir/frame_subsampling_factor ]; then
  # e.g. for 'chain' systems
  frame_subsampling_opt="--frame-subsampling-factor=$(cat $srcdir/frame_subsampling_factor)"
fi

if $threaded; then
    decoder=online2-wav-nnet2-latgen-threaded
    # note: the decoder actually uses 4 threads, but the average usage will normally
    # be more like 2.
    parallel_opts="--num-threads 2"
    opts="--modify-ivector-config=$modify_ivector_config --verbose=1"
else
    decoder=online2-wav-nnet2-latgen-faster
    parallel_opts=
    opts="--online=$online"
fi

echo "Start decoding"
if [ $stage -le 0 ]; then
    if [ $decoder_type == "nnet2" ]; then
        $cmd $parallel_opts JOB=1:$nj $dir/log/decode.JOB.log \
        $decoder $opts $silence_weighting_opts --do-endpointing=$do_endpointing \
        --config=$srcdir/conf/online_nnet2_decoding.conf \
        --max-active=$max_active --beam=$beam --lattice-beam=$lattice_beam \
        --acoustic-scale=$acwt --word-symbol-table=$graphdir/words.txt \
        $srcdir/${iter}.mdl $graphdir/HCLG.fst $spk2utt_rspecifier "$wav_rspecifier" \
        "ark:|gzip -c > $dir/lat.JOB.gz" || exit 1;
    elif [ $decoder_type == "nnet3" ]; then
        $cmd JOB=1:$nj $dir/log/decode.JOB.log \
        online2-wav-nnet3-latgen-faster $silence_weighting_opts --do-endpointing=$do_endpointing \
        --frames-per-chunk=$frames_per_chunk \
        --extra-left-context-initial=$extra_left_context_initial \
        --online=$online \
        $frame_subsampling_opt \
        --config=$online_config \
        --min-active=$min_active --max-active=$max_active --beam=$beam --lattice-beam=$lattice_beam \
        --acoustic-scale=$acwt --word-symbol-table=$graphdir/words.txt \
        $srcdir/${iter}.mdl $graphdir/HCLG.fst $spk2utt_rspecifier "$wav_rspecifier" \
        "$lat_wspecifier" || exit 1;
    fi
fi
# nnet3 decoder.
#     online2-wav-nnet3-latgen-faster 
#     --frames-per-chunk=$frames_per_chunk \
#     --extra-left-context-initial=$extra_left_context_initial \
#        $frame_subsampling_opt \
#      --min-active=$min_active 
#       "$lat_wspecifier" || exit 1;
# fi

echo "Start scoring"
local/score.sh --cmd "$cmd" $scoring_opts $data $graphdir $dir
# get cer
echo "cer scroing"
steps/scoring/score_kaldi_cer.sh --cmd "$cmd" --stage 2 $scoring_opts $data $graphdir $dir

echo "end: "`date`
echo "DONE"

