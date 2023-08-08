#!/bin/bash

if [ $# -ne 2 ]
then
    echo "usage : $0 [input : input directory(include lexicon.txt)] [output : output directory]"
    exit 0;
fi



# Input path setting
in_dir=$1
in_lexicon=${in_dir}/lexicon.txt
in_lexiconp=${in_dir}/lexiconp.txt
out_dir=$2

##########################################
# Kaldi path setting
. ./path.sh || exit 1

# if [ ! -L ./utils ]
# then
#     rm -rf ./utils
#     ln -sf $KALDI_ROOT/egs/wsj/s5/utils ./utils    
# fi

# if [ ! -L ./steps ]
# then
#     rm -rf ./steps
#     ln -sf $KALDI_ROOT/egs/wsj/s5/steps ./steps    
# fi

##########################################
### 0. Input(given) data check ###
##########################################

for x in "$in_lexicon"
do
    if [ ! -f $x ]
    then
    echo "No file - $x"
    exit 0;
    fi
done

##########################################
### 0. Set default paths and make dirs ###
##########################################

# train_created=./outputs/tmp

lang_dir=${out_dir}/lang_train

tmp_dir=${out_dir}/tmp_train

startdate=`date '+%y%m%d%H%M%S'`
# logfile=`echo "prepare${startdate}.log"`
#logfile=./prepare.log

for x in $lang_dir $tmp_dir
do
    if [ ! -d $x ]
    then
       mkdir -p $x
    else
        rm -r $x
        mkdir $x
    fi
done


##########################################
echo "### 1. Lexicon / LM preparation"
##########################################

echo "Start." `date` # > $logfile

# Fix data before getting started
# utils/fix_data_dir.sh $train_given


echo "# 1) lexicon.txt (temporary)"
# Remove <unk> from lexicon.txt
sed '/<unk>/d' $in_lexicon > $tmp_dir/tmp.txt
cp $tmp_dir/tmp.txt $in_lexicon

if [ -f $in_lexiconp ]; then
    cp $in_lexiconp $tmp_dir
fi

echo "# 2) nonsilence_phones.txt"
# Create nonsilence_phones.txt from lexicon.txt
cut -d ' ' -f 2- $in_lexicon | tr ' ' '\n' | sed '/^$/d' | sort -u > $tmp_dir/nonsilence_phones.txt
sed '/sil/d' $tmp_dir/nonsilence_phones.txt > $tmp_dir/tmp.txt
mv $tmp_dir/tmp.txt $tmp_dir/nonsilence_phones.txt

echo "# 3) optional_silence.txt"
# Create optional_silence.txt ('sil')
echo "sil" > $tmp_dir/optional_silence.txt

echo "# 4) silence_phones.txt"
# Create silence_phones.txt ('sil' and '<unk>')
echo -e "sil\n<unk>" > $tmp_dir/silence_phones.txt

echo "# 5) extra_questions.txt"
# Create extra_questions.txt from {nonsilence,silence}_phones.txt
cat $tmp_dir/silence_phones.txt| awk '{printf("%s ", $1);} END{printf "\n";}' > $tmp_dir/extra_questions.txt || exit 1;    
cat $tmp_dir/nonsilence_phones.txt | perl -e 'while(<>){ foreach $p (split(" ", $_)) {  $p =~ m:^([^\d]+)(\d*)$: || die "Bad phone $_"; $q{$2} .= "$p "; } } foreach $l (values %q) {print "$l\n";}' >> $tmp_dir/extra_questions.txt || exit 1;    

echo "# 6) lexicon.txt (final touch)"
# Add a line of '<unk> <unk>' to lexicon.txt
ed -s $in_lexicon <<< $'1i\n<unk> <unk>\n.\nwq'
cp $in_lexicon $tmp_dir

echo "data & language part" `date` #>> $logfile


##########################################
echo "### 2. L & G.fst"
##########################################

echo "# L.fst and {phones,words,...}.txt"
# Create L.fst and a set of relevant files by prepare_lang.sh
utils/prepare_lang.sh \
    $tmp_dir "<unk>" \
    $tmp_dir/tmp \
    $lang_dir


########## end ##########

mv $lang_dir/* $out_dir
rm -rf $tmp_dir $lang_dir


echo "End." `date`
echo "DONE."

