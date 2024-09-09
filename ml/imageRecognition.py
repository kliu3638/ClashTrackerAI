import matplotlib.pyplot as plt
import numpy as np
import os
import PIL
import tensorflow as tf
import keras
import pathlib


from tensorflow import keras
from keras import layers
from keras.models import Sequential
from keras.callbacks import EarlyStopping



dataset_path = "cocData/eagleArtillery"
data_dir = pathlib.Path(dataset_path)


image_count = len(list(data_dir.glob('*/*.jpg')))
print(image_count)

folder = list(data_dir.glob('4/*'))
PIL.Image.open(str(folder[0]))


train_ds, val_ds = tf.keras.utils.image_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    subset="both",
    seed=123,
    image_size=(512, 512),
    batch_size=32)

class_names = train_ds.class_names
print(class_names)

num_classes = len(class_names)

model = Sequential([
	layers.Rescaling(1./255, input_shape=(512,512, 3)),
	layers.Conv2D(16, 3, padding='same', activation='relu'),
	layers.MaxPooling2D(),
	layers.Conv2D(32, 3, padding='same', activation='relu'),
	layers.MaxPooling2D(),
	layers.Conv2D(64, 3, padding='same', activation='relu'),
	layers.MaxPooling2D(),
	layers.Flatten(),
	layers.Dense(128, activation='relu'),
	layers.Dense(num_classes)
])

model.compile(optimizer='adam',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(
                  from_logits=True),
              metrics=['accuracy'])
model.summary()



class PredictionCallback(tf.keras.callbacks.Callback):
    def __init__(self, validation_data):
        self.validation_data = validation_data

    def on_epoch_end(self, epoch, logs={}):
        print("Callback called at epoch:", epoch)
        if self.validation_data is not None and epoch == 9:
            first_batch = val_ds.take(1)

            for images, labels in first_batch:
                labels = np.array(labels)
                # Iterate through the batch and make predictions for each image
                for image, label in zip(images, labels):
                    # Expand the dimensions of the image to match the model's input shape

                    # Make a prediction for the current image
                    prediction = self.model.predict(np.expand_dims(image, axis=0))
                    class_probability = np.exp(prediction) / np.sum(np.exp(prediction), axis=1, keepdims=True)
                    final_prediction = np.argmax(class_probability, axis=1)

                    # You can now work with 'prediction' for this image
                    print("Prediction for current image:", prediction, label, final_prediction)

                    plt.figure(figsize=(1,1))
                    plt.imshow(np.array(image).astype(np.uint8))
                    plt.title(f"  Final Prediction: {final_prediction}  Actual Class: {label}")
                    plt.axis("off")


early_stopping_monitor = EarlyStopping(
    monitor='val_accuracy',
    min_delta=0,
    patience=4,
    verbose=0,
    mode='auto',
    baseline=0,
    restore_best_weights=True,
    start_from_epoch=8
)

# history = model.fit(
#    train_ds,
#    validation_data=val_ds,
#    epochs=10,
#    callbacks=[PredictionCallback(validation_data=val_ds)]
# )


# with tf.device('/gpu:0'):
history = model.fit(
  train_ds,
  validation_data=val_ds,
  epochs=20,
  callbacks=[early_stopping_monitor]
)




# #Accuracy
# acc = history.history['accuracy']
# val_acc = history.history['val_accuracy']
  
# #loss
# loss = history.history['loss']
# val_loss = history.history['val_loss']
  
# #epochs 
# epochs_range = range(20)
  
# #Plotting graphs
# plt.figure(figsize=(8, 8))
# plt.subplot(1, 2, 1)
# plt.plot(epochs_range, acc, label='Training Accuracy')
# plt.plot(epochs_range, val_acc, label='Validation Accuracy')
# plt.legend(loc='lower right')
# plt.title('Training and Validation Accuracy')
  
# plt.subplot(1, 2, 2)
# plt.plot(epochs_range, loss, label='Training Loss')
# plt.plot(epochs_range, val_loss, label='Validation Loss')
# plt.legend(loc='upper right')
# plt.title('Training and Validation Loss')
# plt.show()




folder_path = "cocData/testingImages"
image_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith((".jpg", ".jpeg", ".png"))]

predictions_list = []

for image_file in image_files:
    image = PIL.Image.open(image_file)
    image = image.resize((512, 512))
    image_array = np.array(image)
    image_array = np.expand_dims(image_array, axis=0)

    prediction = model.predict(image_array)
    class_probabilities = np.exp(prediction) / np.sum(np.exp(prediction), axis=1, keepdims=True)
    final_prediction = np.argmax(class_probabilities, axis=1)+1

    # Append the final prediction to the list
    predictions_list.append(final_prediction)

# image = PIL.Image.open("cocData/testingImages/jkim2.jpg")
# image = image.resize((512, 512))
# image_array = np.array(image)
# image_array = np.expand_dims(image_array, axis=0)
# prediction = model.predict(image_array)
# class_probability = np.exp(prediction) / np.sum(np.exp(prediction), axis=1, keepdims=True)
# final_prediction = np.argmax(class_probability, axis=1)+1






# model.save('my_model.keras')
# new_model = tf.keras.models.load_model('my_model.keras')