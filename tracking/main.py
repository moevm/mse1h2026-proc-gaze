import asyncio
import logging
import os
from typing import Any
import torch
import numpy as np

from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitQueue

from src.tracker import Tracker
from src.video import Video
from src.gaze_mapper import GazeDataset, calibrate
from torch.utils.data import random_split, DataLoader
from src.constants import PTH2MODELS

logging.basicConfig(level=logging.INFO,
                    format="%(name)s | %(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

AMQP_URL = os.environ["AMQP_URL"]
JOBS_Q = os.environ.get("AMQP_QUEUE", "tracking.jobs")
RESULTS_Q = os.environ.get("AMQP_RESULT_QUEUE", "tracking.results")
CALIBRATION_Q = os.environ.get("AMQP_CALIBRATION_QUEUE", "tracking.jobs.calibration")
CALIBRATION_RESULTS_Q = os.environ.get("AMQP_CALIBRATION_RESULT_QUEUE", "tracking.results.calibration")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
broker = RabbitBroker(AMQP_URL)
app = FastStream(broker)

jobs_queue = RabbitQueue(JOBS_Q, durable=True)
results_queue = RabbitQueue(RESULTS_Q, durable=True)
calibration_queue = RabbitQueue(CALIBRATION_Q, durable=True)
calibration_results_queue = RabbitQueue(CALIBRATION_RESULTS_Q, durable=True)

tracker: Tracker | None = None


@app.on_startup
async def on_startup():
    global tracker
    logger.info("Loading tracker...")
    tracker = Tracker(use_torch_gaze=True)
    tracker.gaze_mapper.eval()
    tracker.gaze_mapper.to(device)
    logger.info("Tracker ready, waiting for messages...")


@broker.subscriber(jobs_queue)
async def handle_job(message: dict[str, Any]):
    try:
        result = await asyncio.to_thread(tracker.process_job, message)
    except Exception as error:
        recording_id = message.get("recording_id") if isinstance(message, dict) else None
        logger.exception("Error processing recording %s", recording_id)
        result = {
            "recording_id": str(recording_id) if recording_id else None,
            "intervals": [],
        }

    await broker.publish(result, queue=results_queue)

@broker.subscriber(calibration_queue)
async def handle_calibration(message: dict[str, Any]):
    try:
        webcam_pth = os.path.join("/data", message["webcam_path"])
        webcam_pth_mp4 = webcam_pth.rstrip(".webm") + "_decoded.mp4"
        clicks = message["calibration_data"]["clicks"]
        
        tracker.convert_codec(webcam_pth, webcam_pth_mp4)
        webcam_video = Video(webcam_pth_mp4)
         
        calibration_data = []
        for click in clicks:
            sec, x, y = float(click["time"]), int(click["x"]), int(click["y"])
            target_point = np.array([x, y, 0.0])
            frame = webcam_video.frame_at_sec(sec)
            gaze_result = await asyncio.to_thread(tracker.gaze_estimator.estimate, frame)
            gaze_vecs = gaze_result[0]
            
            if len(gaze_vecs) == 0:
                raise ValueError("Gaze estimation failed. Frame does not contain detectable gaze vectors.")
                
            calibration_data.append((gaze_vecs[0], target_point))
        
        dataset = GazeDataset(calibration_data)
            
        g = torch.Generator().manual_seed(0)
        train, val = random_split(dataset, [0.9, 0.1], g)
        
        train_loader = DataLoader(train, batch_size=1, shuffle=True, num_workers=0)
        val_loader = DataLoader(val, batch_size=1, shuffle=True, num_workers=0)
        
        epochs = 15
        
        updated_mapper = await asyncio.to_thread(
            calibrate, epochs, tracker.gaze_mapper, train_loader, val_loader
        )
        tracker.gaze_mapper = updated_mapper
        
        torch.save(tracker.gaze_mapper, os.path.join(PTH2MODELS, "resnet", "mapper.pth"))

        result = \
        {
            "student_id": message["student_id"],
            "result": tracker.gaze_mapper.translation_vec.detach().numpy().tolist()
        }
    except Exception as e: 
        logger.exception("Error processing calibration data: %s", e)
        result = \
        {
            "student_id": message["student_id"],
            "result": []
        }
    finally:
        webcam_video.close()
    
    print(result)
    await broker.publish(result, calibration_results_queue)

async def main():
    while True:
        try:
            await broker.start()
            logger.info(f"RabbitMQ broker started at url: {AMQP_URL}")
            break
        except Exception as e:
            logger.warning(f"RabbitMQ not ready: {e}. Retry in 2s...")
            await asyncio.sleep(2)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
