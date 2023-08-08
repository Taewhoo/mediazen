#!/bin/bash
# generate lm.arpa

# Check input arguments.
if [ $# -eq 2 ]; then
    text_file=$1
    save_dir=$2
    options=
elif [ $# -eq 3 ]; then
    text_file=$1
    save_dir=$2
    options=$3
else
    echo "Two or Three arguments should be assigned."
    echo "1. textraw file"
    echo "2. save directory"
    echo "3. (optional) lm training parameters"
    exit 1
fi

# Set kaldi directory
KALDI_ROOT=/home/kaldi
. path.sh $KALDI_ROOT

# Set input arguments.
text_file=$1
save_dir=$2
options=$3

# make save directory if it isn't present.
[ ! -d $save_dir ] && mkdir $save_dir

echo "start: "`date`
echo "shell: $@"
# Generate arpa language model.
# Set ngram-count folder.
if [ -z $(find $KALDI_ROOT/tools/srilm/bin -name ngram-count) ]; then
    echo "SRILM might not be installed on your computer. Please find kaldi/tools/install_srilm.sh and install the package." && exit 1
else
    nc=`find $KALDI_ROOT/tools/srilm/bin -name ngram-count`
    # Make lm.arpa from textraw.
    echo "Generating lm.arpa..."
    echo "lm options: $options"
    $nc -text $text_file $options -lm $save_dir/lm.arpa
fi

echo "end: "`date`
echo "DONE"

