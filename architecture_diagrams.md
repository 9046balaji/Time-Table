# 🏛️ SmartClass Platform: Reference Architecture & Systems Diagrams

> **Document Class:** Systems Architecture Reference & Diagrams Manual  
> **System Scope:** Edge Vision Engine (`src/`), Central FastAPI API (`services/app/`), Multi-Agent Ecosystem (`services/app/ai/`), Client Applications (`smartclass/` & `frontend/`), and Shared Libraries (`smartclass_common/`)  
> **Author:** Principal AI Systems Architect & Lead Embedded Vision Engineer  
> **Date:** July 2026  
> **Baseline Release:** SmartClass Platform v2.1

---

## 1. High-Level End-to-End Platform Topology

The **SmartClass Attendance Platform** decouples edge-based real-time video capture and face recognition from central business logic APIs, stateful multi-agent decision workflows, and administrative reporting dashboards.

```mermaid
graph TD
    subgraph Edge Classroom Deployment Tier
        E1["RTSP Camera 01 (Door)"] -->|H.264 Video Stream| MC["MultiCameraCapture Pool"]
        E2["RTSP Camera 02 (Hall)"] -->|H.264 Video Stream| MC
        MC --> SG["Stream Governor: Temp & FPS Scaling"]
        SG --> DET["SCRFD Face Detector (TensorRT FP16)"]
        DET --> TRK["ByteTrack Multi-Object Tracker"]
        TRK --> ALN["ArcFace 5-Point Affine Alignment"]
        ALN --> QUA["Face Quality & Passive Liveness Gate"]
        QUA -->|Pass (Q >= 0.25)| ENC["Ensemble Feature Extractor (AdaFace)"]
        ENC -->|512-D L2 Vector| FSS["Encrypted FAISS Search Index"]
        FSS --> EVE["Identity Evidence Engine"]
        EVE --> ATT["Ed25519 Hardware Attestation Signer"]
        ATT -->|Healthy Link| RDS["Redis Stream Gateway (XADD)"]
        ATT -->|Network Drop| SQL["SQLite WAL Offline Queue"]
        SQL -->|Reconnected| RDS
    end

    subgraph API Gateway & Administrative Control Tier
        RDS --> FAPI["FastAPI Central Backend Gateway"]
        WEB["React 18 Dashboard (Web/Admin)"] -->|REST / WebSockets| FAPI
        ANDR["Android Student App (Kotlin/Compose)"] -->|mTLS REST API| FAPI
        FAPI --> PII["PII Redaction & Security Middleware"]
        PII --> CACHE["Redis Semantic Vector Cache"]
        CACHE -->|Cache Miss| SV["Master Supervisor Orchestrator Agent"]
    end

    subgraph LangGraph Multi-Agent Execution Engine
        SV -->|Route Intent| A1["Agent 1: VLM Judge Graph"]
        SV -->|Route Intent| A2["Agent 2: OD Verifier Graph"]
        SV -->|Route Intent| A3["Agent 3: Substitute Dispatcher"]
        SV -->|Route Intent| A4["Agent 4: Dispute Resolver Graph"]
        SV -->|Route Intent| A5["Agent 5: DPDP Erasure Graph"]
        SV -->|Route Intent| A7["Agent 7: Student RAG Graph"]
    end

    subgraph Model Serving & Multi-Store Persistence
        A1 -->|Inference Call| TRITON["NVIDIA Triton Inference Pool"]
        A4 -->|Inference Call| TRITON
        A1 <--->|State Persist| DB[("PostgreSQL DB (checkpoints & events)")]
        A2 <--->|State Persist| DB
        A4 <--->|State Persist| DB
        A5 <--->|Purge Embeddings| VDB[("FAISS / Milvus Vector Store")]
        A5 <--->|Purge Cache Keys| CACHE
        A5 <--->|Purge DB Records| DB
    end
```

---

## 2. Edge Vision Processing Pipeline Architecture

The Edge Vision Engine operates within a **33.33ms execution budget** per frame to sustain real-time processing at **30 FPS**.

```mermaid
graph TD
    A[Raw RTSP Ingestion] --> B[GStreamer CUDA Frame Decoder]
    B --> C{Stream Governor Status}
    C -->|Normal Temp < 70C| D[Process Full 1080p Stream]
    C -->|Warning Temp 70-80C| E[Scale to 720p & Skip Alternate Frames]
    C -->|Critical Temp >= 80C| F[Drop to 10 FPS & Run Light MFN Model]
    
    D --> G[SCRFD Face Detection (TensorRT FP16)]
    E --> G
    F --> G
    
    G -->|BBox & Keypoints| H[ByteTrack Kalman-Filtered Tracker]
    H -->|Confirmed Track ID| I[ArcFace 5-Point Affine Alignment (112x112)]
    I --> J[Laplacian Blur Quality & Motion Liveness Check]
    
    J -->|Pass Q >= 0.25| K[AdaFace + MobileFaceNet Feature Extraction]
    J -->|Fail Q < 0.25| L[Drop Frame Crop]
    
    K -->|512-D L2 Vector| M[FAISS Vector Index Similarity Search]
    M --> N[9-Feature Identity Evidence Engine]
    N -->|Aggregate Score >= 0.85| O[Ed25519 TPM Attestation Signature]
    O --> P{Check Connection Health}
    P -->|Online| Q[Push to Redis Stream]
    P -->|Offline| R[Buffer in SQLite WAL Offline Queue]
```

---

## 3. LangGraph Stateful Multi-Agent Orchestration

The platform integrates **7 stateful autonomous agents** coordinates using LangGraph state graphs with native PostgreSQL database checkpointing (`AsyncPostgresSaver`).

### 3.1 LangGraph State Checkpoint & HITL Lifecycle

Low-confidence inferences ($P < 0.85$) or high-risk DB actions automatically trigger human-in-the-loop validation via `interrupt()`.

```mermaid
stateDiagram-v2
    [*] --> PENDING : API POST Trigger Request
    PENDING --> RUNNING : Initialize checkpointer & thread_id
    
    state RUNNING {
        [*] --> InspectGuardrails
        InspectGuardrails --> ParseIntent : Passed Security Checks
        ParseIntent --> ExecuteNodeStep : Intent Target Resolved
        ExecuteNodeStep --> EvaluateConfidence : Step Execution Completed
    }
    
    EvaluateConfidence --> COMPLETED : Confidence >= 0.85 & Low Risk
    EvaluateConfidence --> INTERRUPTED_HITL : Confidence < 0.85 or HIGH_MUTATE Action
    
    state INTERRUPTED_HITL {
        [*] --> NativeInterruptGate : Call interrupt()
        NativeInterruptGate --> PostgresSnapshot : Save State to checkpoints Table
        PostgresSnapshot --> AwaitingHumanReview : Thread Awaiting Resume
    }
    
    AwaitingHumanReview --> RESUMED : POST /api/v1/agents/resume/{thread_id}
    RESUMED --> RUNNING : Load Snapshot & Pass Command(resume=True)
    
    RUNNING --> FAILED : Timeout / Max Steps Exceeded
    COMPLETED --> [*] : Commit Attendance Update
    FAILED --> [*] : Log Error Telemetry
```

### 3.2 Target Agent Workflows

#### Agent 1: VLM Borderline Verification Judge
Visually compares borderline crops ($0.50 \le P < 0.85$) against enrolled photos using Qwen2.5-VL.

```mermaid
graph TD
    A[Start: Ingest Review Item] --> B[Retrieve Reference Enrollment Crops]
    B --> C[Invoke Qwen2.5-VL Visual Comparison]
    C --> D{Evaluate Similarity Score}
    D -->|Score >= 0.85| E[Commit Attendance Event Override]
    D -->|0.50 <= Score < 0.85| F[Call interrupt() Awaiting Admin Review]
    D -->|Score < 0.50| G[Reject Match Event]
    F -->|Admin Approves| E
    F -->|Admin Rejects| G
```

#### Agent 4: Attendance Dispute Resolver
Audits student attendance complaints, re-runs AdaFace recognition, and generates SHAP attribution heatmaps.

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (Web/Mobile App)
    participant API as FastAPI Backend (/api/v1/agents/trigger)
    participant Agent as Agent 4: Dispute Resolver Graph
    participant FrameTool as RTSP Frame Retriever
    participant Model as AdaFace Model Server
    participant SHAP as SHAP Heatmap Visualizer
    participant DB as PostgreSQL Database

    Student->>API: Submit Dispute Claim (session_id, timestamp)
    API->>Agent: ainvoke(initial_state, thread_id)
    Agent->>FrameTool: Fetch Video Frame Crops
    FrameTool-->>Agent: Return Frame Crops
    Agent->>Model: Compute Cosine Similarity (crop vs reference)
    Model-->>Agent: Return Similarity Score
    
    alt Score >= 0.80
        Agent->>SHAP: Generate Feature Attribution Heatmap
        SHAP-->>Agent: Return Heatmap URL
        Agent->>DB: Override Attendance Record (Set status=PRESENT)
        DB-->>Agent: Transaction Committed
        Agent-->>API: Resolution: UPDATED_PRESENT
        API-->>Student: Display Present Status & SHAP Proof
    else Score < 0.80
        Agent->>DB: Record Dispute Rejection (Set status=ABSENT)
        Agent-->>API: Resolution: REJECTED_ABSENT
        API-->>Student: Dispute Rejected
    end
```

#### Agent 5: DPDP Act 2023 Compliance & Data Erasure
Transactionally erases student biometric data across all persistence layers with rollback capability.

```mermaid
graph TD
    subgraph Deletion Pipeline
        REQ[Erasure Request] --> VAL[Validate Superadmin Role]
        VAL --> LOCK[Lock Student Record in PostgreSQL]
        LOCK --> P1[Execute SQL Database Purge]
        P1 --> P2[Execute FAISS Index Vector Purge]
        P2 --> P3[Execute S3 Media Object Purge]
        P3 --> P4[Execute Redis Cache Eviction]
    end

    subgraph Verification & Rollback Coordinator
        P4 --> VERIFY{Zero Residual Data Check?}
        VERIFY -->|Pass: Count == 0| COMMIT[Write Cryptographic Compliance Log]
        VERIFY -->|Fail: Count > 0| ROLLBACK[Execute Compensating Transaction Rollback]
    end
```

---

## 4. Client Applications & Interfaces

### 4.1 CameraX Face Quality Gate (Mobile App)
Performs real-time face pre-processing on the user's mobile device to ensure high-quality enrollment crops.

```mermaid
stateDiagram-v2
    [*] --> LAUNCH_CAMERA
    LAUNCH_CAMERA --> CAPTURE_PREVIEW : CameraX Ingestion Active
    
    state CAPTURE_PREVIEW {
        [*] --> CHECK_FACE_COUNT
        CHECK_FACE_COUNT -->|Exactly 1 Face| CHECK_POSE_LIGHTING
        CHECK_FACE_COUNT -->|0 or >1 Faces| SHOW_WARNING_FACE_COUNT
        CHECK_POSE_LIGHTING -->|Pitch/Yaw < 15 Deg & Exposure OK| QUALITY_PASS
        CHECK_POSE_LIGHTING -->|Quality Check Failed| SHOW_WARNING_ALIGNMENT
    }
    
    CAPTURE_PREVIEW --> HIGH_RES_JPEG : Capture Pressed & Quality Passed
    HIGH_RES_JPEG --> GEOFENCE_CHECK : Verify WGS-84 Coordinates
    GEOFENCE_CHECK -->|Inside Campus Bounds| UPLOAD_API : POST /api/v1/enrollment
    GEOFENCE_CHECK -->|Outside Campus Bounds| REJECT_OUTSIDE : Alert User Outside Campus
    UPLOAD_API --> [*] : Enrollment Succeeded
```

### 4.2 BLE Beacon & Geofenced Mobile Attendance Scanner
Ensures students cannot mark attendance unless they are physically located inside the target classroom.

```mermaid
sequenceDiagram
    autonumber
    participant App as Mobile App (smartclass/)
    participant GPS as LocationManager (WGS-84)
    participant BLE as BluetoothLeScanner
    participant API as Central FastAPI Server
    participant DB as PostgreSQL Database

    App->>GPS: Request Current Coordinates
    GPS-->>App: Return (Lat, Lon, Accuracy)
    App->>App: Verify Haversine Distance to Room Center <= 100m
    App->>BLE: Scan for Classroom BLE Beacon (UUID: 0xFD12)
    BLE-->>App: Beacon Discovered (EDGE-A101, RSSI >= -75dBm)
    App->>API: POST /api/v1/attendance/mobile-mark (Student_ID, Beacon_ID)
    API->>API: Validate HMAC Signature & Timetable Slot
    API->>DB: Insert Event Record (status='PRESENT_MOBILE_VERIFIED')
    DB-->>API: Transaction Committed
    API-->>App: HTTP 200 OK
```

---

## 5. Enterprise Cloud & Edge Hybrid Deployment Topology

For enterprise multi-campus deployments, model serving and vector search scale out dynamically on cloud-native GPU nodes.

```
                        [ 🏢 EDGE NODES (100+ Campuses) ]
                                       │
                    RTSP / gRPC Encrypted Edge Streaming
                                       │
                                       ▼
             ┌──────────────────────────────────────────────────┐
             │       [ Apache Kafka / Redpanda Bus ]            │
             └────────────────────────┬─────────────────────────┘
                                       │
                                       ▼
             ┌──────────────────────────────────────────────────┐
             │     [ Ray Serve Orchestration Cluster ]          │
             └────────────────────────┬─────────────────────────┘
                                       │
                                       ▼
             ┌──────────────────────────────────────────────────┐
             │  [ NVIDIA Triton Inference Server GPU Pool ]     │
             │  - AdaFace IR-100 FP16 Engine (TensorRT)         │
             │  - CodeFormer Restoration & Depth-Anything V2    │
             │  - Dynamic Batching & GPU Instance Sharing       │
             └────────────────────────┬─────────────────────────┘
                                       │
                                       ▼
             ┌──────────────────────────────────────────────────┐
             │   [ Milvus / Qdrant Distributed Vector Cluster ] │
             │   - HNSW Index / GPU Acceleration                │
             │   - 100,000+ Student Vectors (<3ms Search)       │
             └────────────────────────┬─────────────────────────┘
                                       │
                                       ▼
             ┌──────────────────────────────────────────────────┐
             │  [ FastAPI Microservices + Async PostgreSQL ]    │
             │  - Polars High-Speed Analytics Engine            │
             │  - LangGraph Multi-Agent Workflows               │
             └──────────────────────────────────────────────────┘
```

---

## 6. Database Schema Checkpointing Tables

The system's PostgreSQL backend (`init.sql` & Alembic Migration 0016) utilizes the following checkpoint schema to persist LangGraph execution states:

```sql
-- LangGraph Checkpointer State Snapshot Store
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint BYTEA NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- LangGraph Node Executions Output Store
CREATE TABLE IF NOT EXISTS checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INT NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    value BYTEA NOT NULL,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
```
