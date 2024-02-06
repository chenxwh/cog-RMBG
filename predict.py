# Prediction interface for Cog ⚙️
# https://github.com/replicate/cog/blob/main/docs/python.md

from skimage import io
import torch
from PIL import Image
from briarmbg import BriaRMBG
from utilities import preprocess_image, postprocess_image
from huggingface_hub import hf_hub_download
from cog import BasePredictor, Input, Path


class Predictor(BasePredictor):
    def setup(self) -> None:
        """Load the model into memory to make running multiple predictions efficient"""
        model_path = "checkpoints/model.pth" # download from https://huggingface.co/briaai/RMBG-1.4
        self.net = BriaRMBG()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.net.load_state_dict(torch.load(model_path, map_location=self.device))
        self.net.to(self.device).eval()

    def predict(
        self,
        image: Path = Input(description="Input image"),
    ) -> Path:
        """Run a single prediction on the model"""

        # prepare input
        model_input_size = [1024, 1024]
        orig_im = io.imread(str(image))
        orig_im_size = orig_im.shape[0:2]
        img = preprocess_image(orig_im, model_input_size).to(self.device)

        # inference
        result = self.net(img)

        # post process
        result_image = postprocess_image(result[0][0], orig_im_size)

        # save result
        pil_im = Image.fromarray(result_image)
        no_bg_image = Image.new("RGBA", pil_im.size, (0, 0, 0, 0))
        orig_image = Image.open(str(image))
        no_bg_image.paste(orig_image, mask=pil_im)

        out_path = "/tmp/out.png"
        no_bg_image.save(out_path)
        return Path(out_path)
