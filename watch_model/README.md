# Synthetic watch dataset generator

`generate_dataset.py` is a standalone, procedural analog-watch renderer. It uses
only Python's standard library; Pillow, NumPy, OpenCV, and other image packages
are not required. It writes RGB PNG images and JSON Lines metadata.

```sh
python watch_model/generate_dataset.py \
  --output watch_model/dataset --samples-per-split 900 --seed 42
```

The default produces 900 images in **each** of `train/`, `validation/` (the val
split), and `test/`.
The count per split must be divisible by three; each split has equal numbers of
`readable`, `negative`, and `unreadable` examples. `manifest.json` records the
generation configuration. Each split contains PNGs and a `labels.jsonl` file
with one record per image. The root also contains `dataset.csv`, with one row
per image and a fixed column order:

```text
split,image,image_path,hour_angle,minute_angle,second_angle,confidence,confidence_target,second_present,usable,status,hour_label,minute_label,style_id,render_id,timestamp_utc
```

`image` and `image_path` both contain the image path relative to the dataset
output root (for example, `train/000123.png`); `image` is provided for
`train.py` compatibility. `confidence` (compatibility alias for `confidence_target`) and `usable` are `1`
only for readable samples and `0` otherwise. `second_present` is an independent
0/1 physical-presence label: the second hand is randomly omitted from 20% of
watch renderings, and negatives always have `0`. It remains `1` for unreadable
watch images when that sample's second hand was rendered, even though unreadable
angle labels are blank. Readable samples without a second hand have a blank
JSONL second-angle target and `-1.0` in the CSV `second_angle` column. Other
non-readable angle columns also use `-1.0`, allowing numeric CSV parsing;
`confidence_target` controls angle usability while `second_present` supervises
the second-hand output. `status` separately distinguishes `readable`,
`unreadable` (watch present), and `negative` (no watch), so watch-presence
classification can be derived independently. Timestamp and discrete
hour/minute labels are empty for non-readable samples. `hour_label` is the
displayed 12-hour numeral (1–12); `minute_label` is the timestamp's minute mark
(0–59). Use the continuous angle columns for regression targets.
`render_id` identifies the held-out render profile and `style_id` identifies
the watch style family. The output directory is generated data and is not
created by merely importing the script.

## Labels and inference contract

Images are 224x224 RGB PNGs by default. For the proposed Android inference
interface, decode RGB and convert each byte value to `float32(pixel) / 255` to
obtain a 224x224x3 tensor in `[0,1]`. Labels use `status` values:

* `readable`: hour/minute angle targets and `timestamp_utc` are provided; the
  second-angle target is present only when `second_present` is true.
* `negative`: no watch; timestamp and angles are `null`.
* `unreadable`: a watch is present but rendered with severe obstruction; timestamp
  and angles are `null`, while `second_present` preserves the rendered watch's
  physical second-hand presence label.

For readable samples, non-null values in `angles_degrees` are degrees clockwise
from 12 o'clock, modulo 360. They are calculated from the same UTC timestamp
used to draw the hands (including continuous hour/minute movement).
`confidence_target` is 1 for readable and 0 for either non-readable status;
`second_present` independently labels second-hand presence. Status labels
distinguish unreadable watches from scenes without a watch in the metadata; the
included trainer learns readable confidence and second-hand presence. A
downstream model should not present angle predictions as valid for negatives or
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
