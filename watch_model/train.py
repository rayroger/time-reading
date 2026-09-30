#!/usr/bin/env python3
"""Train and export a watch-angle regressor from a generated CSV dataset."""

import argparse
import csv
import math
from pathlib import Path

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
            if split is not None and row.get("split") != split:
                continue
            image_path = Path(row["image"])
            if not image_path.is_absolute():
                image_path = image_root / image_path
            if not image_path.is_file():
                raise FileNotFoundError(f"Image listed in manifest does not exist: {image_path}")
            angles = [float(row[column]) for column in ANGLE_COLUMNS]
            confidence = float(row["confidence"])
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"confidence must be in [0, 1]: {row}")
            if confidence > 0.0 and any(not 0.0 <= angle < 360.0 for angle in angles[:2]):
                raise ValueError(f"usable examples need hour/minute angles in [0, 360): {row}")
            examples.append((str(image_path), angles + [confidence]))
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
    raw = tf.keras.layers.Dense(4, activation="sigmoid", name="normalized_outputs")(x)
    angles = tf.keras.layers.Lambda(lambda values: values[:, :3] * 360.0)(raw)
    confidence = tf.keras.layers.Lambda(lambda values: values[:, 3:4])(raw)
    outputs = tf.keras.layers.Concatenate(name="output")([angles, confidence])
    return tf.keras.Model(inputs=inputs, outputs=outputs, name="watch_time_reader")


def watch_loss(y_true, y_pred):
    confidence = y_true[:, 3]
    angle_delta = (y_pred[:, :3] - y_true[:, :3]) * (math.pi / 180.0)
    circular_error = 1.0 - tf.cos(angle_delta)
    second_valid = tf.cast(y_true[:, 2] >= 0.0, tf.float32)
    angle_weights = tf.stack((confidence, confidence, confidence * second_valid), axis=1)
    angle_loss = tf.reduce_sum(circular_error * angle_weights, axis=1)
    angle_loss /= tf.maximum(tf.reduce_sum(angle_weights, axis=1), 1.0)
    confidence_loss = tf.keras.losses.binary_crossentropy(
        confidence[:, tf.newaxis], y_pred[:, 3:4]
    )
    confidence_loss = tf.squeeze(confidence_loss, axis=-1)
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
    if output_details["shape"].tolist() != [1, 4] or output_details["dtype"] != np.float32:
        raise ValueError(
            f"Expected float32 [1, 4] output, got "
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
    print(f"{split_name}: {len(examples)} images; detection accuracy={detection_accuracy:.4f}")

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
        "--real-test-manifest",
        type=Path,
        help="Optional separate CSV of labeled real photos (must not overlap training data)",
    )
    parser.add_argument(
        "--real-image-root",
        type=Path,
        help="Root for relative image paths in --real-test-manifest",
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
    validation = read_split(manifest, image_root, "validation")
    test = read_split(manifest, image_root, "test")

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

    for split_name, examples in (("validation", validation), ("test", test)):
        report_metrics(split_name, examples, decode_tflite_predictions(args.output, examples))
    if args.real_test_manifest:
        real_manifest = args.real_test_manifest.resolve()
        real_root = (args.real_image_root or real_manifest.parent).resolve()
        real_examples = read_split(real_manifest, real_root, split=None)
        report_metrics(
            "held-out real-photo test",
            real_examples,
            decode_tflite_predictions(args.output, real_examples),
        )
    print(f"TensorFlow Lite model written to {args.output}")
    print("These metrics use generated images only; they do not establish real-photo accuracy.")


if __name__ == "__main__":
    main()
