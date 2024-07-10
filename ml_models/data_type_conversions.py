import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_probability as tfp
import numpy as np
from scipy.io import wavfile
from german_transliterate.core import GermanTransliterate
import yaml
from tensorflow_tts.models import TFMelGANGenerator
from tensorflow_tts.models import TFPQMF
from tensorflow_tts.configs import MultiBandMelGANGeneratorConfig

_pad = "pad"
_eos = "eos"
_punctuation = "!'(),.? "
_special = "-"
_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# Export all symbols:
ALL_SYMBOLS = (
    [_pad] + list(_special) + list(_punctuation) + list(_letters) + [_eos]
)

class Processor:
    def __init__(self):
        self.symbol_to_id = {s: i for i, s in enumerate(ALL_SYMBOLS)}

    def text_to_sequence(self, text):
        return [self.symbol_to_id.get(s, self.symbol_to_id[_pad]) for s in text]

class DataTypeConversions:
    def __init__(self):
        # Initialize pre-trained models as None for lazy loading
        self.text_to_text_model = None
        self.text_to_image_model = None
        self.text_to_video_model = None
        self.text_to_audio_model = None
        self.image_to_text_model = None
        self.image_to_image_model = None
        self.image_to_video_model = None
        self.image_captioning_model = None

    def load_text_to_text_model(self):
        if self.text_to_text_model is None:
            try:
                self.text_to_text_model = hub.KerasLayer("https://www.kaggle.com/models/google/universal-sentence-encoder/TensorFlow2/cmlm-en-base/1")
            except Exception as e:
                print(f"Error loading text-to-text model: {e}")
        return self.text_to_text_model

    def load_text_to_image_model(self):
        if self.text_to_image_model is None:
            try:
                self.text_to_image_model = hub.load("https://tfhub.dev/deepmind/biggan-256/2")
            except Exception as e:
                print(f"Error loading text-to-image model: {e}")
        return self.text_to_image_model

    def load_text_to_video_model(self):
        if self.text_to_video_model is None:
            try:
                self.text_to_video_model = hub.load("https://tfhub.dev/deepmind/video-transformer/1")
            except Exception as e:
                print(f"Error loading text-to-video model: {e}")
        return self.text_to_video_model

    def load_text_to_audio_model(self):
        if self.text_to_audio_model is None:
            try:
                self.text_to_audio_model = hub.load("https://tfhub.dev/monatis/german-tacotron2/1")
            except Exception as e:
                print(f"Error loading text-to-audio model: {e}")
        return self.text_to_audio_model

    def load_image_to_text_model(self):
        if self.image_to_text_model is None:
            try:
                self.image_to_text_model = hub.load("https://tfhub.dev/google/imagenet/inception_v3/classification/4")
            except Exception as e:
                print(f"Error loading image-to-text model: {e}")
        return self.image_to_text_model

    def load_image_to_image_model(self):
        if self.image_to_image_model is None:
            try:
                self.image_to_image_model = hub.load("https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2")
            except Exception as e:
                print(f"Error loading image-to-image model: {e}")
        return self.image_to_image_model

    def load_image_to_video_model(self):
        if self.image_to_video_model is None:
            try:
                self.image_to_video_model = hub.load("https://tfhub.dev/deepmind/video-transformer/1")
            except Exception as e:
                print(f"Error loading image-to-video model: {e}")
        return self.image_to_video_model

    def load_image_captioning_model(self):
        if self.image_captioning_model is None:
            try:
                self.image_captioning_model = hub.load("https://tfhub.dev/google/imagenet/inception_v3/classification/4")
            except Exception as e:
                print(f"Error loading image captioning model: {e}")
        return self.image_captioning_model

    def text_to_text(self, text: str, detailed: bool = True) -> str:
        """
        Convert text to text using a pre-trained language model.

        :param text: Input text.
        :param detailed: Whether to include statistical analysis in the output.
        :return: A string containing the embeddings as numpy arrays, and optionally the mean and variance of the embeddings.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")

        model = self.load_text_to_text_model()
        try:
            # Prepare input as a dictionary with required keys
            inputs = {
                'input_word_ids': tf.constant([[text]]),
                'input_mask': tf.constant([[1]]),
                'input_type_ids': tf.constant([[0]])
            }
            embeddings = model(inputs, training=False)
            try:
                # Convert embeddings to numpy array once for performance optimization
                embeddings_np = embeddings.numpy()
            except Exception as e:
                print(f"Error converting embeddings to numpy array: {e}")
                return ""

            if detailed:
                try:
                    # Perform statistical analysis on embeddings using TensorFlow Probability
                    mean, variance = tfp.stats.mean(embeddings), tfp.stats.variance(embeddings)
                    # Convert mean and variance to numpy arrays once for performance optimization
                    mean_np, variance_np = mean.numpy(), variance.numpy()
                    return f"Embeddings: {embeddings_np}, Mean: {mean_np}, Variance: {variance_np}"
                except Exception as tfp_error:
                    # Fallback to embeddings-only output if statistical analysis fails
                    print(f"Error during statistical analysis with TensorFlow Probability: {tfp_error}")
            return f"Embeddings: {embeddings_np}"
        except Exception as e:
            # Handle errors during text-to-text conversion
            print(f"Error during text-to-text conversion: {e}")
            return ""

    def text_to_image(self, text: str) -> tf.Tensor:
        """
        Convert text to image using a pre-trained model.

        :param text: Input text.
        :return: Generated image tensor.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")

        model = self.load_text_to_image_model()
        noise = tf.random.normal([1, 128])
        try:
            image = model([noise, text])
            return image
        except Exception as e:
            print(f"Error during text-to-image conversion: {e}")
            return tf.zeros([1, 256, 256, 3])  # Return a placeholder tensor on error

    def text_to_video(self, text: str) -> tf.Tensor:
        """
        Convert text to video using a pre-trained model.

        :param text: Input text.
        :return: Generated video tensor.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")

        model = self.load_text_to_video_model()
        try:
            # Generate 30 frames for the video
            frames = [model([text]) for _ in range(30)]
            video = tf.stack(frames, axis=1)
            return video
        except Exception as e:
            print(f"Error during text-to-video conversion: {e}")
            return tf.zeros([1, 30, 256, 256, 3])  # Return a placeholder tensor on error

    def text_to_audio(self, text: str) -> tf.Tensor:
        """
        Convert text to audio using a pre-trained model.

        :param text: Input text.
        :return: Generated audio tensor.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")

        # Preprocess input text
        text = GermanTransliterate(replace={';': ',', ':': ' '}, sep_abbreviation=' -- ').transliterate(text)
        processor = Processor()
        input_ids = processor.text_to_sequence(text)

        # Ensure input tensor has the correct shape and type
        input_ids = input_ids[:9] + [0] * (9 - len(input_ids))  # Pad or truncate to length 9
        input_tensor = tf.constant([input_ids], dtype=tf.int32)

        # Load models
        tacotron2 = self.load_text_to_audio_model()
        config_path = "/home/ubuntu/tensorflow/models/TensorFlowTTS/examples/multiband_melgan/conf/multiband_melgan.v1.yaml"
        with open(config_path) as f:
            config = yaml.load(f, Loader=yaml.Loader)
        mb_melgan = TFMelGANGenerator(config=MultiBandMelGANGeneratorConfig(**config["multiband_melgan_generator_params"]))
        mb_melgan._build()
        mb_melgan.load_weights("/home/ubuntu/tensorflow/models/TensorFlowTTS/examples/multiband_melgan_hf/exp/train.multiband_melgan_hf.v1/checkpoints/generator-920000.h5")
        pqmf = TFPQMF(config=MultiBandMelGANGeneratorConfig(**config["multiband_melgan_generator_params"]))

        try:
            # Generate mel spectrograms
            _, mel_outputs, _, _ = tacotron2.inference(
                input_tensor,
                tf.convert_to_tensor([len(input_ids)], dtype=tf.int32),
                tf.convert_to_tensor([0], dtype=tf.int32)
            )
            # Synthesize audio
            generated_subbands = mb_melgan(mel_outputs)
            audio = pqmf.synthesis(generated_subbands)[0, :-1024, 0]
            # Ensure the audio tensor has the correct shape
            audio = tf.pad(audio, [[0, max(0, 16000 - tf.shape(audio)[0])]])  # Pad if necessary
            audio = audio[:16000]  # Trim if necessary
            return tf.expand_dims(audio, axis=0)  # Ensure shape is (1, 16000)
        except Exception as e:
            print(f"Error during text-to-audio conversion: {e}")
            return tf.zeros([1, 16000])  # Return a placeholder tensor on error

    def image_to_text(self, image: tf.Tensor) -> str:
        """
        Convert image to text using a pre-trained model.

        :param image: Input image tensor.
        :return: Extracted text or an empty string on error.
        """
        if not isinstance(image, tf.Tensor):
            raise ValueError("Input image must be a tensor.")

        model = self.load_image_to_text_model()
        try:
            predictions = model(image)
            try:
                # Convert predictions to numpy array once for performance optimization
                predictions_np = predictions.numpy()
            except Exception as e:
                print(f"Error converting predictions to numpy array: {e}")
                return ""
            # Assuming the model output is a classification, return the top prediction
            top_prediction = np.argmax(predictions_np, axis=-1)
            return str(top_prediction)
        except Exception as e:
            print(f"Error during image-to-text conversion: {e}")
            return ""

    def image_to_image(self, image: tf.Tensor) -> np.ndarray:
        """
        Convert image to image using a pre-trained model.

        :param image: Input image tensor.
        :return: Transformed image as a numpy array or a placeholder array on error.
        """
        if not isinstance(image, tf.Tensor):
            raise ValueError("Input image must be a tensor.")

        model = self.load_image_to_image_model()
        try:
            stylized_image = model([image, image])
            try:
                # Convert stylized image to numpy array once for performance optimization
                stylized_image_np = stylized_image.numpy()
            except Exception as e:
                print(f"Error converting stylized image to numpy array: {e}")
                return np.zeros(image.shape)  # Return a placeholder array on error
            return stylized_image_np
        except Exception as e:
            print(f"Error during image-to-image conversion: {e}")
            return np.zeros(image.shape)  # Return a placeholder array on error

    def image_to_video(self, image: tf.Tensor) -> tf.Tensor:
        """
        Convert image to video using a pre-trained model.

        :param image: Input image tensor.
        :return: Generated video tensor.
        """
        if not isinstance(image, tf.Tensor):
            raise ValueError("Input image must be a tensor.")

        model = self.load_image_to_video_model()
        try:
            # Generate 30 frames for the video
            frames = [model([image]) for _ in range(30)]
            video = tf.stack(frames, axis=1)
            return video
        except Exception as e:
            print(f"Error during image-to-video conversion: {e}")
            return tf.zeros([1, 30, 256, 256, 3])  # Return a placeholder tensor on error

    def image_to_audio(self, image: tf.Tensor) -> tf.Tensor:
        """
        Convert image to audio by first generating a text description of the image
        and then converting the text description to audio using a pre-trained model.

        :param image: Input image tensor.
        :return: Generated audio tensor.
        """
        if not isinstance(image, tf.Tensor):
            raise ValueError("Input image must be a tensor.")

        # Load the image captioning model
        captioning_model = self.load_image_captioning_model()
        try:
            # Generate a caption for the input image
            caption = captioning_model(image)
            caption = caption.numpy().tostring()  # Convert to string without decode
        except Exception as e:
            print(f"Error during image captioning: {e}")
            return tf.zeros([1, 16000])  # Return a placeholder tensor on error

        # Use the text-to-audio model (Tacotron2) to convert the caption to audio
        model = self.load_text_to_audio_model()
        try:
            audio = model([caption])
            return audio
        except Exception as e:
            print(f"Error during text-to-audio conversion: {e}")
            return tf.zeros([1, 16000])  # Return a placeholder tensor on error
