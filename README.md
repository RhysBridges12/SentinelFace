# SentinelFace

A desktop face recognition application developed as a final-year Computer Science project.

## Features

- Facial enrolment using a quality-controlled processing pipeline
- Face detection using RetinaFace
- Automatic facial alignment using detected landmarks
- Face quality assessment based on:
  - Detection confidence
  - Face resolution
  - Brightness
  - Sharpness
  - Facial pose (Yaw)
- Deep-learning facial embeddings generated using ArcFace through InsightFace
- Cosine similarity-based face matching
- SQLite database with encrypted storage
- Role-based user authentication and management
- Desktop graphical user interface built with PySide6
- Image and video searching

---

## Information

### Languages

- Python
- SQL

### Libraries (Requirements)

- PySide6
- OpenCV
- InsightFace
- ONNX Runtime
- FAISS
- NumPy
- Pillow
- SQLCipher
- Argon2

### Development Tools

- VS Code
- Git

---

## System Architecture

SentinelFace follows a modular software architecture, separating the application into independent components responsible for:

- User Interface
- Face Detection
- Face Processing
- Embedding Generation
- Identity Matching
- Database Management
- User Management
- Search Processing

This separation improves maintainability, readability and future extensibility.

---

## How It Works

### Enrolment Pipeline

1. Detect faces using RetinaFace.
2. Evaluate the quality of detected faces.
3. Reject images that fail the defined quality thresholds.
4. Align facial landmarks using a predefined reference template.
5. Generate a facial embedding using ArcFace.
6. Compare the embedding against existing profiles.
7. Create or update the relevant profile.
8. Store the facial representation in the encrypted database.

### Matching Pipeline

1. Detect faces within the input image or video.
2. Align detected faces.
3. Generate ArcFace embeddings.
4. Compare embeddings against stored facial representations.
5. Calculate cosine similarity.
6. Return the most similar identities based on the configured matching thresholds.

Unlike the enrolment pipeline, quality filtering is not applied during matching, allowing the system to search using lower-quality inputs representative of surveillance conditions.

---

## Face Quality Assessment

SentinelFace evaluates detected faces during enrolment using five quality metrics:

- Detection confidence
- Face resolution
- Brightness
- Sharpness
- Facial pose

Thresholds for these metrics were determined through system experimentation and evaluation. Low-quality inputs are rejected before embedding generation to reduce variation in the facial representations stored within the database.

---

## Recognition Model

SentinelFace uses the **ArcFace** model through the InsightFace framework to generate 512-dimensional facial embeddings.

The embeddings are L2-normalised and compared using **cosine similarity**, allowing facial representations to be compared within a high-dimensional feature space.

---

## Database

SentinelFace uses a relational SQLite database to manage system data and user profiles.

Sensitive data is protected through database encryption, while role-based access controls restrict functionality according to the user's permissions.

The database is generated locally by the application.
