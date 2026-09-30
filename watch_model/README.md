# Synthetic watch dataset generator

`generate_dataset.py` is a standalone, procedural analog-watch renderer. It uses
only Python's standard library: Pillow, NumPy, OpenCV, and other optional image
packages are not required. It writes RGB PNG images and JSON Lines metadata.

```sh
python watch_model/generate_dataset.py \
  --output watch_model/dataset --samples-per-split 900 --seed 42
```

The default produces 900 images in **each** of `train/`, `val/`, and `test/`.
The count per split must be divisible by three; each split has equal numbers of
`readable`, `negative`, and `unreadable` examples. `manifest.json` records the
generation configuration. Each split contains PNGs and a `labels.jsonl` file
with one record per image. The output directory is generated data and is not
created by merely importing the script.

## Labels and inference contract

Images are 224x224 RGB PNGs by default. For the proposed Android inference
interface, decode RGB and convert each byte value to `float32(pixel) / 255` to
obtain a 224x224x3 tensor in `[0,1]`. Labels use `status` values:

* `readable`: angle targets and `timestamp_utc` are provided.
* `negative`: no watch; timestamp and angles are `null`.
* `unreadable`: a watch is present but rendered with severe obstruction; timestamp
  and angles are `null`.

For readable samples, `angles_degrees` has `hour`, `minute`, and `second` values
in degrees clockwise from 12 o'clock, modulo 360. These are calculated from the
same UTC timestamp used to draw the hands (including continuous hour/minute
movement). `confidence_target` is 1 for readable and 0 for either non-readable
status. A downstream model should expose a status/classification result and
confidence, and should not present angle predictions as valid for negatives or
unreadable images.

## Procedural variation and split policy

Styles vary dial and case colors, bezel/tick treatments, Arabic/Roman/dot
indices, and dauphine/baton/syringe hands. Camera variation includes rotation,
projective perspective, lighting/tint, blur, sensor noise, specular-like
reflection, and (for unreadable examples) hand/dial occlusion. Negative samples
are non-watch scenes.

Style families and render-profile families are deliberately disjoint across
train, validation, and test: validation and test therefore measure generalizing
to held-out synthetic appearances/effects, not just new images of training
styles. Seeded generation is reproducible. This is a synthetic benchmark, not a
claim that synthetic-only training yields a model usable on real photographs.
Real-photo usability requires representative real data, evaluation, and
appropriate training/validation.

The renderer intentionally has no external dependencies. It generates simple
pixel-art/vector-like images and approximates camera/reflection effects; its
limited visual realism and balanced synthetic class proportions do not model
real-world capture conditions or prevalence.
