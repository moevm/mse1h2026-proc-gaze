# Usage

Currently implemented functionality can be tested like this:

* Build image with `./scripts/build.sh`.
* Run container with `./scripts/run.sh`.
* Prepare some videos.
* Send them with `curl -F 'webcam=@vid1.mp4' -F 'screencast=@vid2.mp4' localhost:8000/upload`.
  Expect `{"id":12345}`.
* Or send only one of them with `curl -F 'webcam=@vid1.mp4' localhost:8000/upload`.
  Expect `{"error":"Expected 'webcam' and 'screencast' files."}`.
* Or even send empty POST request with `curl -X POST localhost:8000/upload`.
  Expect `{"error":"Expected 'webcam' and 'screencast' files."}`.
* Kill container with `docker container rm -f proc-gaze-backend`.
