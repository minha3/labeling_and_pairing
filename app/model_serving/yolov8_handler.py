import base64
import io

import torch
import numpy as np
from PIL import Image
from ts.torch_handler.vision_handler import VisionHandler

from ultralytics.nn.autobackend import AutoBackend
from ultralytics.yolo.data import load_inference_source
from ultralytics.yolo.data.augment import LetterBox
from ultralytics.yolo.utils import DEFAULT_CFG, ops
from ultralytics.yolo.cfg import get_cfg
from ultralytics.yolo.engine.results import Boxes


class Yolov8Detector(VisionHandler):

    def initialize(self, context):
        super().initialize(context)
        if self.model_pt_path.endswith('.onnx'):
            del self.model
            self.model = AutoBackend(self.model_pt_path, device=self.device)
            self.model.eval()

    def _load_torchscript_model(self, model_pt_path):
        """Loads the PyTorch model and returns the NN model object.
        Args:
            model_pt_path (str): denotes the path of the model file.
        Returns:
            (NN Model Object) : Loads the model object.
        """
        return AutoBackend(model_pt_path, device=self.device)

    def yolov8_prepare_input(self, im):
        """Prepares input image before inference.

        Args:
            im (torch.Tensor | List(np.ndarray)): (N, 3, h, w) for tensor, [(h, w, 3) x N] for list.
        """
        if not isinstance(im, torch.Tensor):
            auto = all(x.shape == im[0].shape for x in im) and self.model.pt
            im = np.stack([LetterBox(self.model.imgsz, auto=auto, stride=self.model.stride)(image=x) for x in im])
            im = im[..., ::-1].transpose((0, 3, 1, 2))  # BGR to RGB, BHWC to BCHW, (n, 3, h, w)
            im = np.ascontiguousarray(im)  # contiguous
            im = torch.from_numpy(im)
        # NOTE: assuming im with (b, 3, h, w) if it's a tensor
        img = im.to(self.device)
        img = img.half() if self.model.fp16 else img.float()  # uint8 to fp16/32
        img /= 255  # 0 - 255 to 0.0 - 1.0
        return img

    def preprocess(self, data):
        """The preprocess function of MNIST program converts the input data to a float tensor

        Args:
            data (List): Input data from the request is in the form of a Tensor

        Returns:
            list : The preprocess function returns the input image as a list of float tensors.
        """
        images = []

        for row in data:
            # Compat layer: normally the envelope should just return the data
            # directly, but older versions of Torchserve didn't have envelope.
            image = row.get("data") or row.get("body")
            if isinstance(image, str):
                # if the image is a string of bytesarray.
                image = base64.b64decode(image)

            # If the image is sent as bytesarray
            if isinstance(image, (bytearray, bytes)):
                image = Image.open(io.BytesIO(image))
            else:
                # if the image is a list
                image = torch.FloatTensor(image)

            images.append(image)

        dataset = load_inference_source(source=images, imgsz=self.model.imgsz)

        data = []
        for batch in dataset:
            _, im0s, _, _ = batch
            """Convert an image to PyTorch tensor and normalize pixel values."""
            im = self.yolov8_prepare_input(im0s)
            if len(im.shape) == 3:
                im = im[None]  # expand for batch dim
            data.append((im0s, im))
        return data

    def inference(self, data, *args, **kwargs):
        """
        The Inference Function is used to make a prediction call on the given input request.
        The user needs to override the inference function to customize it.
        Args:
            data (Torch Tensor): A Torch Tensor is passed to make the Inference Request.
            The shape should match the model input shape.
        Returns:
            Torch Tensor : The Predicted Torch Tensor is returned in this function.
        """
        results = []
        with torch.no_grad():
            for im0s, im in data:
                preds = self.model(im, *args, **kwargs)
                results.append((preds, im, im0s))
        return results

    def postprocess(self, data):
        """Postprocesses predictions and returns a list of Results objects."""
        args = get_cfg(DEFAULT_CFG)
        results = []
        for preds, img, orig_imgs in data:
            preds = ops.non_max_suppression(preds,
                                            args.conf or 0.25,
                                            args.iou,
                                            agnostic=args.agnostic_nms,
                                            max_det=args.max_det,
                                            classes=args.classes)

            batch_result = []
            for i, pred in enumerate(preds):
                orig_img = orig_imgs[i] if isinstance(orig_imgs, list) else orig_imgs
                orig_shape = orig_img.shape[:2]
                if not isinstance(orig_imgs, torch.Tensor):
                    pred[:, :4] = ops.scale_boxes(img.shape[2:], pred[:, :4], orig_img.shape)
                boxes = Boxes(boxes=pred, orig_shape=orig_shape)
                batch_result.append(self.yolov8_boxes_to_dict(boxes, orig_shape))
            results.append(batch_result)
        return results

    def yolov8_boxes_to_dict(self, boxes, orig_shape, normalize=False):
        """Convert the object to JSON format."""
        results = []
        data = boxes.data.cpu().tolist()
        h, w = orig_shape if normalize else (1, 1)
        for i, row in enumerate(data):
            box = {'x1': row[0] / w, 'y1': row[1] / h, 'x2': row[2] / w, 'y2': row[3] / h}
            conf = row[4]
            id = int(row[5])
            name = self.model.names[id]
            result = {'name': name, 'class': id, 'confidence': conf, 'box': box}
            results.append(result)

        return results
