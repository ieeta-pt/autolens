import sys
sys.path.insert(0, "../")

from autolens.LUDWIG.run import main

main(
    "resources/metadata_brain_multiclass.csv",
    "../../brain_mri/",
    1,
    (256, 256),
    0.227,
    0.1
    )
