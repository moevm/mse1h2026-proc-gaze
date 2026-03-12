# Usage

* Start backend and DB with `docker compose up -d`
* Create student with `curl -X POST localhost:8000/student`
* Expect output like `{"student_id":"691adb4f-f1af-42dc-ac3a-928555f461cc"}`
* Upload recording with `curl -F 'webcam=@vid1.mp4' -F 'screencast=@vid2.mp4' -F 'student_id=691adb4f-f1af-42dc-ac3a-928555f461cc' localhost:8000/recording/upload`
* Expect output like `{"id":"c9fe5f08-d241-44ca-bd0b-6571975ced7c"}`
* Shutdown backend and DB with `docker compose down`

You can inspect DB with `docker exec -it postgres-db psql -U postgres -d gaze`.
