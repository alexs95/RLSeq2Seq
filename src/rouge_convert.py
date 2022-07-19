from argparse import ArgumentParser
from pathlib import Path
import glob
import os
from shutil import copy2


def prepare(experiment):
    # Create new directory for files
    output_dir = os.path.join(os.path.dirname(experiment), "rouge_" + os.path.basename(experiment))
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Move files into new directory
    ids = {}
    for inx, file in enumerate(glob.iglob(os.path.join(experiment, 'decoded/*.txt'), recursive=True)):
        identifier = os.path.basename(file).split("_")[0]
        ids[identifier] = inx
        dirname = os.path.dirname(file.replace(experiment, output_dir))
        Path(dirname).mkdir(parents=True, exist_ok=True)
        copy2(file, os.path.join(dirname, "%06d_decoded.txt" % inx))

    for file in glob.iglob(os.path.join(experiment, 'reference/*.txt'), recursive=True):
        identifier = os.path.basename(file).split("_")[0]
        inx = ids[identifier]
        dirname = os.path.dirname(file.replace(experiment, output_dir))
        Path(dirname).mkdir(parents=True, exist_ok=True)
        copy2(file, os.path.join(dirname, "%06d_reference.txt" % inx))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-p", "--path", required=True, dest="path")
    args = parser.parse_args()
    prepare(args.path)

