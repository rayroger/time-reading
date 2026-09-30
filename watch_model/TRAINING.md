# Train and evaluate the watch-time model

This project creates a synthetic training set and trains a small TensorFlow
Lite model for the Android inference interface. The generated images can verify
the end-to-end pipeline, but they do not establish that the model reads real
watch photographs accurately.

## Generate training images

Install the Python dependencies from the repository root:

```bash
python -m pip install -r model_conversion/requirements.txt
```

Generate a small dataset to check the pipeline, then increase the count for
training experiments:

```bash
python watch_model/generate_dataset.py \
  --output watch_model/dataset \
  --samples-per-split 900 \
  --seed 42
```

The generator writes `train`, `validation`, and `test` images, `dataset.csv`,
JSONL labels, and `manifest.json`. Every split has equal readable, no-watch,
and unreadable samples. Styles and rendering profiles are held out across
splits. `900` images per split is a smoke-test scale, not a recommended final
training size; compare validation/test metrics while increasing dataset size
and changing the seed.

## Train and export

```bash
python watch_model/train.py \
  --manifest watch_model/dataset/dataset.csv \
  --output watch_model/build/watch_detector.tflite \
  --epochs 30
```

The training script uses circular angle loss, a readable-watch confidence
target, and a separate second-hand-presence output. It prints precision/recall
for readable-watch detection, angle errors, and time error on held-out
synthetic validation and test samples. It also checks that the exported model
has the expected TensorFlow Lite signature:

- Input: `[1, 224, 224, 3]`, `float32`, RGB values normalized to `[0, 1]`
- Output: `[1, 5]`, `float32`, `[hourAngle, minuteAngle, secondAngle,
  watchConfidence, secondHandConfidence]`

To try the generated model in the Android app, copy it to
`app/src/main/assets/watch_detector.tflite`, build and install the app, and
exercise camera inference:

```bash
cp watch_model/build/watch_detector.tflite app/src/main/assets/watch_detector.tflite
./gradlew assembleDebug
```

The tracked model asset is a tiny packaging placeholder. Preserve it until a
trained output has passed inference checks; a successful synthetic test is not
a real-photo validation result.

## Evaluate real photos separately

Prepare a separate CSV of manually labeled, held-out real watch photos, using
the same label columns as the generated CSV (`image_path`, `hour_angle`,
`minute_angle`, `second_angle`, and `confidence_target` or `confidence`).
Angles are clockwise degrees relative to the dial's 12 o'clock mark. Set an
unavailable second angle to `-1`, and include `second_present` as 0 or 1 when
known. Real images used for training, validation, and final testing must be
different; never pass the final test set as a training or validation manifest.

To train with labeled real images mixed into the generated training examples,
pass separate real train and validation manifests. Keep the final test set
separate:

```bash
python watch_model/train.py \
  --manifest watch_model/dataset/dataset.csv \
  --output watch_model/build/watch_detector.tflite \
  --real-train-manifest /path/to/real-train.csv \
  --real-validation-manifest /path/to/real-validation.csv \
  --real-test-manifest /path/to/held-out-real-test.csv \
  --real-image-root /path/to/real-images \
  --epochs 30
```

To evaluate a synthetic-trained model on held-out real photos without using
real photos during training or model selection:

```bash
python watch_model/train.py \
  --manifest watch_model/dataset/dataset.csv \
  --output watch_model/build/watch_detector.tflite \
  --real-test-manifest /path/to/held-out-real-watch-labels.csv
```

The real-photo reports are separate from synthetic metrics. Poor results mean
the synthetic model is not ready for real use; collect representative labeled
photos and include a distinct real-photo training/validation set before
retraining. Keep the final real-photo test set untouched until model selection
is complete.
