#!/bin/bash
# generate HCLG.fst

# Check input arguments.
if [ $# -ne 3 ]; then
    echo "Three arguments should be assigned."
    echo "1. lang directory"
    echo "2. am directory"
    echo "3. save(graph) directory"
    exit 1
fi

# Set kaldi directory
KALDI_ROOT=/home/kaldi
. path.sh $KALDI_ROOT

# Set input arguments.
lang_dir=$1
am_dir=$2
save_dir=$3

echo "start: "`date`

# Make G.fst
g_exist=`ls $lang_dir | grep "G.fst"`
if [ "$g_exist" == "" ]; then
    echo "make G.fst "`date`
    cat $lang_dir/lm.arpa | $KALDI_ROOT/src/lmbin/arpa2fst --disambig-symbol=#0 --read-symbol-table=$lang_dir/words.txt - $lang_dir/G.fst
    echo "finish G.fst"`date`
else
    echo "G.fst is already in the lang directory. It will be selected in the combining HCLG stage directly."
fi  

# Make HCLG.fst
echo "make HCLG.fst"`date`
# When you select AM, you have to choose which AM model needed to be composed.  
utils/mkgraph.sh --remove-oov $lang_dir $am_dir $save_dir
echo "finish HCLG.fst"`date`

echo "end: "`date`
echo "DONE"

