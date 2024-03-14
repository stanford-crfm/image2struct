from PIL import Image
from torchvision import transforms, models
import torch
import os


class SheetMusicClassifier:
    """
    A simple classifier to determine if an image is a sheet music or not.
    """

    def __init__(self):
        path_to_model = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "sheet_music_classifier.pt",
        )
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Assume you have a model defined (or modified) as `model`
        model = models.resnet18(weights=None)  # Example: ResNet-18
        num_ftrs = model.fc.in_features
        model.fc = torch.nn.Linear(num_ftrs, 2)  # Adjusting for binary classification

        # Load the trained model weights
        model.load_state_dict(torch.load(path_to_model, map_location=self._device))

        # Set the model to evaluation mode
        model.eval()

        self._model = model.to(self._device)
        self._transform = transforms.Compose(
            [
                transforms.Resize(1024),
                transforms.CenterCrop(512),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

    def is_sheet_music(self, image: Image.Image) -> bool:
        with torch.no_grad():
            # Convert the image to RGB if it's not already (important for RGBA or grayscale images)
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Apply transformations and move to the appropriate device
            image_tensor = self._transform(image).unsqueeze(0).to(self._device)

            # Perform inference
            outputs = self._model(image_tensor)
            _, predicted = torch.max(outputs, 1)

            # Return True if predicted class is 1 (sheet music), else False
            return predicted.item() == 1
