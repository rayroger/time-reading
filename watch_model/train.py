#!/usr/bin/env python3
"""Train and export a watch-angle regressor from a generated CSV dataset."""

import argparse
import csv
import math
import sys
from pathlib import Path

# Range of Python versions for which TensorFlow currently publishes stable
# wheels (see model_conversion/requirements.txt). Check this before importing
# TensorFlow so unsupported interpreters (e.g. Python 3.14+ on Windows) get an
# actionable error instead of being told to install a dependency that has no
# matching distribution for their interpreter.
_MIN_SUPPORTED_PYTHON = (3, 10)
_MAX_SUPPORTED_PYTHON = (3, 13)

if not _MIN_SUPPORTED_PYTHON <= sys.version_info[:2] <= _MAX_SUPPORTED_PYTHON:
    raise SystemExit(
        "Unsupported Python version "
        f"{sys.version_info.major}.{sys.version_info.minor} detected. "
        "TensorFlow does not currently publish stable wheels outside Python "
        f"{_MIN_SUPPORTED_PYTHON[0]}.{_MIN_SUPPORTED_PYTHON[1]}-"
        f"{_MAX_SUPPORTED_PYTHON[0]}.{_MAX_SUPPORTED_PYTHON[1]}. Install a "
        "supported interpreter (on Windows, run `py -0p` to see installed "
        "versions and `py -3.12 -m venv .venv` to create a virtual "
        "environment with one), activate it, then install the model "
        "conversion requirements: pip install -r "
        "model_conversion/requirements.txt"
    )

try:
    import numpy as np
    import tensorflow as tf
except ImportError as error:
    raise SystemExit(
        "Install the model conversion requirements before training: "
        "pip install -r model_conversion/requirements.txt"
    ) from error


IMAGE_SIZE = (224, 224)
ANGLE_COLUMNS = ("hour_angle", "minute_angle", "second_angle")


def read_split(manifest_path, image_root, split):
    examples = []
    with open(manifest_path, newline="", encoding="utf-8") as manifest_file:
        for row in csv.DictReader(manifest_file):
            row_split = row.get("split")
            if split == "validation":
                split_matches = row_split in ("val", "validation")
            else:
                split_matches = row_split == split
            if split is not None and not split_matches:
                continue
            image_path = Path(row.get("image_path") or row["image"])
            if not image_path.is_absolute():
                image_path = image_root / image_path
            if not image_path.is_file():
                raise FileNotFoundError(f"Image listed in manifest does not exist: {image_path}")
            angles = [
                float(row[column]) if row.get(column, "").strip() else -1.0
                for column in ANGLE_COLUMNS
            ]
            confidence = float(row.get("confidence_target") or row.get("confidence", 0.0))
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"confidence must be in [0, 1]: {row}")
            if confidence > 0.0 and any(not 0.0 <= angle < 360.0 for angle in angles[:2]):
                raise ValueError(f"usable examples need hour/minute angles in [0, 360): {row}")
            second_present = row.get("second_present")
            second_present = (
                float(second_present)
                if second_present not in (None, "")
                else float(angles[2] >= 0.0)
            )
            if not 0.0 <= second_present <= 1.0:
                raise ValueError(f"second_present must be in [0, 1]: {row}")
            if confidence > 0.0 and second_present > 0.0 and angles[2] < 0.0:
                raise ValueError(f"readable second hand needs an angle target: {row}")
            examples.append((str(image_path), angles + [confidence, second_present]))
    if not examples:
        raise ValueError(f"No {split!r} examples found in {manifest_path}")
    return examples


def make_dataset(examples, batch_size, training):
    paths = [example[0] for example in examples]
    labels = np.asarray([example[1] for example in examples], dtype=np.float32)
    dataset = tf.data.Dataset.from_tensor_slices((paths, labels))

    def load_image(path, label):
        image = tf.io.read_file(path)
        image = tf.io.decode_image(image, channels=3, expand_animations=False)
        image.set_shape([None, None, 3])
        image = tf.image.convert_image_dtype(image, tf.float32)
        image = tf.image.resize(image, IMAGE_SIZE)
        return image, label

    dataset = dataset.map(load_image, num_parallel_calls=tf.data.AUTOTUNE)
    if training:
        dataset = dataset.shuffle(min(len(examples), 10_000), reshuffle_each_iteration=True)
    return dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)


def build_model():
    inputs = tf.keras.Input(shape=(*IMAGE_SIZE, 3), name="input_image", dtype=tf.float32)
    x = inputs
    for filters in (24, 48, 96, 160):
        x = tf.keras.layers.Conv2D(filters, 3, strides=2, padding="same", use_bias=False)(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.ReLU()(x)
        x = tf.keras.layers.SeparableConv2D(filters, 3, padding="same", use_bias=False)(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.25)(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    raw = tf.keras.layers.Dense(5, activation="sigmoid", name="normalized_outputs")(x)
    angles = tf.keras.layers.Lambda(lambda values: values[:, :3] * 360.0)(raw)
    confidences = tf.keras.layers.Lambda(lambda values: values[:, 3:5])(raw)
    outputs = tf.keras.layers.Concatenate(name="output")([angles, confidences])
    return tf.keras.Model(inputs=inputs, outputs=outputs, name="watch_time_reader")


def watch_loss(y_true, y_pred):
    confidence = y_true[:, 3]
    angle_delta = (y_pred[:, :3] - y_true[:, :3]) * (math.pi / 180.0)
    circular_error = 1.0 - tf.cos(angle_delta)
    second_valid = y_true[:, 4]
    angle_weights = tf.stack((confidence, confidence, confidence * second_valid), axis=1)
    angle_loss = tf.reduce_sum(circular_error * angle_weights, axis=1)
    angle_loss /= tf.maximum(tf.reduce_sum(angle_weights, axis=1), 1.0)
    confidence_loss = tf.keras.losses.binary_crossentropy(
        confidence[:, tf.newaxis], y_pred[:, 3:4]
    )
    second_confidence_loss = tf.keras.losses.binary_crossentropy(
        second_valid[:, tf.newaxis], y_pred[:, 4:5]
    )
    confidence_loss = tf.squeeze(confidence_loss + second_confidence_loss, axis=-1)
    return angle_loss + confidence_loss


def decode_tflite_predictions(model_path, examples):
    interpreter = tf.lite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]
    if input_details["shape"].tolist() != [1, 224, 224, 3]:
        raise ValueError(f"Unexpected model input shape: {input_details['shape']}")
    if input_details["dtype"] != np.float32:
        raise ValueError(f"Expected float32 input, got {input_details['dtype']}")
    if output_details["shape"].tolist() != [1, 5] or output_details["dtype"] != np.float32:
        raise ValueError(
            f"Expected float32 [1, 5] output, got "
            f"{output_details['shape']} {output_details['dtype']}"
        )

    predictions = []
    for image_path, _ in examples:
        image = tf.io.read_file(image_path)
        image = tf.io.decode_image(image, channels=3, expand_animations=False)
        image.set_shape([None, None, 3])
        image = tf.image.convert_image_dtype(image, tf.float32)
        image = tf.image.resize(image, IMAGE_SIZE)
        interpreter.set_tensor(input_details["index"], image[tf.newaxis, ...].numpy())
        interpreter.invoke()
        predictions.append(interpreter.get_tensor(output_details["index"])[0])
    return np.asarray(predictions)


def report_metrics(split_name, examples, predictions):
    truth = np.asarray([example[1] for example in examples], dtype=np.float32)
    actual_watch = truth[:, 3] >= 0.5
    predicted_watch = predictions[:, 3] >= 0.5
    detection_accuracy = np.mean(actual_watch == predicted_watch)
    true_positive = np.count_nonzero(actual_watch & predicted_watch)
    precision = true_positive / max(np.count_nonzero(predicted_watch), 1)
    recall = true_positive / max(np.count_nonzero(actual_watch), 1)
    print(
        f"{split_name}: {len(examples)} images; "
        f"detection accuracy={detection_accuracy:.4f}, "
        f"precision={precision:.4f}, recall={recall:.4f}"
    )

    usable = actual_watch & predicted_watch
    if not np.any(usable):
        print("  no jointly detected watch examples; angle metrics unavailable")
        return
    for index, column in enumerate(ANGLE_COLUMNS):
        valid_angle = usable & (truth[:, index] >= 0.0)
        if np.any(valid_angle):
            delta = np.abs(predictions[valid_angle, index] - truth[valid_angle, index]) % 360.0
            error = np.minimum(delta, 360.0 - delta)
            print(f"  {column} circular MAE={np.mean(error):.2f}°")
    second_labels = truth[:, 4]
    second_predictions = predictions[:, 4] >= 0.5
    print(
        "  second-hand presence accuracy="
        f"{np.mean(second_predictions == (second_labels >= 0.5)):.4f}"
    )
    time_valid = usable & (truth[:, 0] >= 0.0) & (truth[:, 1] >= 0.0)
    if np.any(time_valid):
        pred_minutes = (
            np.floor(predictions[time_valid, 0] / 30.0) * 60.0
            + predictions[time_valid, 1] / 6.0
        )
        true_minutes = (
            np.floor(truth[time_valid, 0] / 30.0) * 60.0
            + truth[time_valid, 1] / 6.0
        )
        delta = np.abs(pred_minutes - true_minutes) % 720.0
        error = np.minimum(delta, 720.0 - delta)
        print(
            f"  clock-time MAE={np.mean(error):.1f} min; "
            f"within 5 min={np.mean(error <= 5.0):.4f}; "
            f"within 15 min={np.mean(error <= 15.0):.4f}"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="CSV created by generate_dataset.py")
    parser.add_argument("--image-root", type=Path, help="Root for relative image paths")
    parser.add_argument("--output", type=Path, default=Path("build/watch_detector.tflite"))
    parser.add_argument(
        "--real-train-manifest",
        type=Path,
        help="Optional labeled real-photo training CSV, kept separate from synthetic images",
    )
    parser.add_argument(
        "--real-validation-manifest",
        type=Path,
        help="Optional labeled real-photo validation CSV for model selection",
    )
    parser.add_argument(
        "--real-test-manifest",
        type=Path,
        help="Optional separate CSV of labeled real photos (must not overlap training data)",
    )
    parser.add_argument(
        "--real-image-root",
        type=Path,
        help="Root for relative paths in real train/validation/test manifests",
    )
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("--epochs and --batch-size must be positive")

    tf.keras.utils.set_random_seed(args.seed)
    manifest = Path(args.manifest).resolve()
    image_root = (args.image_root or manifest.parent).resolve()
    training = read_split(manifest, image_root, "train")
    synthetic_validation = read_split(manifest, image_root, "validation")
    validation = list(synthetic_validation)
    test = read_split(manifest, image_root, "test")
    real_image_root = (
        args.real_image_root.resolve()
        if args.real_image_root
        else None
    )
    if args.real_train_manifest:
        real_manifest = args.real_train_manifest.resolve()
        training += read_split(
            real_manifest, real_image_root or real_manifest.parent, split=None
        )
    if args.real_validation_manifest:
        real_manifest = args.real_validation_manifest.resolve()
        validation += read_split(
            real_manifest, real_image_root or real_manifest.parent, split=None
        )

    model = build_model()
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3), loss=watch_loss)
    model.fit(
        make_dataset(training, args.batch_size, training=True),
        validation_data=make_dataset(validation, args.batch_size, training=False),
        epochs=args.epochs,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=5, restore_best_weights=True
            )
        ],
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    with open(args.output, "wb") as output_file:
        output_file.write(converter.convert())

    for split_name, examples in (
        ("synthetic validation", synthetic_validation),
        ("synthetic test", test),
    ):
        report_metrics(split_name, examples, decode_tflite_predictions(args.output, examples))
    if args.real_validation_manifest:
        real_manifest = args.real_validation_manifest.resolve()
        real_examples = read_split(
            real_manifest, real_image_root or real_manifest.parent, split=None
        )
        report_metrics(
            "real-photo validation",
            real_examples,
            decode_tflite_predictions(args.output, real_examples),
        )
    if args.real_test_manifest:
        real_manifest = args.real_test_manifest.resolve()
        real_root = real_image_root or real_manifest.parent
        real_examples = read_split(real_manifest, real_root, split=None)
        report_metrics(
            "held-out real-photo test",
            real_examples,
            decode_tflite_predictions(args.output, real_examples),
        )
    print(f"TensorFlow Lite model written to {args.output}")
    print(
        "Synthetic metrics do not establish real-photo accuracy; "
        "use a separate held-out real-photo set for that assessment."
    )


if __name__ == "__main__":
    main()
