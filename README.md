LAMPORT MUTUAL EXCLUSION STIMULATOR

An interactive, software-based simulation and experimentation environment for studying, visualizing, explaining, and verifying Lamport Mutual Exclusion in a distributed-process setting.

Team: SYNSPHERE
Subject: Distributed Computing

1. Project Overview

LAMPORT MUTUAL EXCLUSION STIMULATOR is an academic simulation and experimentation environment designed to make Lamport's Mutual Exclusion algorithm easier to understand, observe, and experiment with.

The simulator models multiple distributed processes on a single laptop. Each process maintains its own logical clock, request queue, and protocol state while communicating through simulated REQUEST, REPLY, and RELEASE messages.

The project goes beyond displaying a final result. It provides an interactive environment in which users can:

Generate and observe critical-section requests.

Study Lamport logical-clock updates.

Observe request ordering.

Inspect distributed message flow.

Introduce network delays and controlled node silence.

Experiment with message-arrival conditions.

Step through execution events.

Observe process states and queues.

Inspect a space-time representation of execution.

Understand why a process is waiting or why a particular request has priority.

Verify important safety, ordering, and liveness properties.

Academic scope: This is an educational and experimental simulator. It is not a production distributed locking system.

2. Problem Statement

In a distributed system, multiple processes may need access to a shared resource. Since there is no single global clock or centralized controller, coordinating access to the critical section is challenging.

A mutual exclusion mechanism must ensure that:

Multiple processes can request access independently.

Requests can be ordered consistently.

A process does not enter the critical section while another higher-priority request is eligible.

Processes exchange the required protocol messages.

Delays and message-arrival conditions can be studied.

The execution can be verified for correctness.

Traditional textbook explanations often describe the algorithm using static diagrams and message sequences. This makes it difficult to observe how logical clocks, queues, messages, process states, delays, and critical-section access interact during an actual execution.

This project addresses that learning gap through an interactive simulation and experimentation environment.

3. Why Lamport Mutual Exclusion?

Lamport Mutual Exclusion is particularly useful for studying distributed coordination because it demonstrates several fundamental distributed-computing concepts together:

Logical time

Distributed event ordering

Request prioritization

Message-based coordination

Critical-section management

Safety

Liveness

Effects of communication delays

The algorithm provides a practical example of how processes can establish a consistent logical ordering without relying on a shared physical clock.

4. Project Objectives

The main objectives of the project are to:

Simulate multiple distributed processes on a single machine.

Implement Lamport logical-clock behavior.

Simulate REQUEST, REPLY, and RELEASE messages.

Maintain request queues for participating processes.

Apply Lamport request ordering.

Provide interactive experiment scenarios.

Demonstrate concurrent and tied requests.

Experiment with delayed and out-of-order message arrival.

Provide controlled node-silence experimentation.

Visualize events through a timeline and space-time diagram.

Explain protocol decisions through a WHY DID THIS HAPPEN? feature.

Verify mutual exclusion and other protocol properties.

Provide an educational environment for studying distributed mutual exclusion.

5. Core Concept

The simulator models a set of distributed processes:

       ┌─────────┐
       │   P1    │
       └────┬────┘
            │
       REQUEST / REPLY
            │
     ┌──────▼──────┐
     │ Distributed │
     │ Simulation  │
     │   Engine    │
     └──────┬──────┘
            │
       REQUEST / REPLY
            │
       ┌────▼────┐
       │   P2    │
       └─────────┘

            ...
            
       ┌─────────┐
       │   P3    │
       └─────────┘

Each process maintains:

A logical clock

A process state

A request queue

Pending replies

Protocol-related events

The simulator then coordinates these processes through simulated messages.

6. Lamport Logical Clock

Lamport logical clocks provide a mechanism for ordering events in a distributed system.

Each process maintains an integer logical clock.

When a process creates an event such as a critical-section request, its logical clock is incremented.

For a received message, the receiving process updates its clock according to Lamport's logical-clock rule:

Clock(receiver) =
    max(Clock(receiver), received_timestamp) + 1

This allows the simulator to establish a consistent logical ordering of events, even though the processes do not share a physical global clock.

Important distinction

A Lamport timestamp represents logical ordering, not physical time.

Therefore:

Logical time ≠ real-world time

7. Request Ordering Using (timestamp, process ID)

Each critical-section request is ordered using:

(timestamp, process ID)

The timestamp provides the primary ordering criterion.

The process ID acts as a deterministic tie-breaker when two requests have the same timestamp.

Example

Consider:

P1 clock = 4  → (5, P1)
P2 clock = 0  → (1, P2)
P3 clock = 2  → (3, P3)

Therefore:

(1, P2) < (3, P3) < (5, P1)

The resulting logical priority is:

P2 → P3 → P1

Equal timestamp example

If two requests have the same timestamp:

(5, P1)
(5, P2)

The process ID is used as the tie-breaker.

The important point is that request ordering is determined by the Lamport ordering rule, not simply by the order in which messages happen to arrive at the receiver.

8. How the Lamport Mutual Exclusion Protocol Works

The simulator follows the conceptual protocol flow:

Process requests critical section
            ↓
Increment logical clock
            ↓
Create request
            ↓
Add request to local queue
            ↓
Send REQUEST
            ↓
Other process receives REQUEST
            ↓
Update logical clock
            ↓
Update local queue
            ↓
Send REPLY
            ↓
Check queue priority
and required replies
            ↓
Enter critical section
            ↓
Perform shared-resource work
            ↓
Send RELEASE
            ↓
Update queues
            ↓
Allow next eligible request

A process does not simply enter the critical section because it generated a request.

The simulator evaluates the protocol state, including request ordering and required replies, before allowing critical-section entry.

9. REQUEST / REPLY / RELEASE Message Flow

The core protocol uses three message types.

REQUEST

A process broadcasts a request when it wants to enter the critical section.

P1 ── REQUEST ──► P2
 │
 └── REQUEST ──► P3

The receiving processes:

Update their logical clocks.

Add the request to their local request queues.

Send a REPLY.

REPLY

A REPLY acknowledges the request.

P2 ── REPLY ──► P1
P3 ── REPLY ──► P1

The requesting process tracks the replies it still needs.

RELEASE

After completing its critical-section execution, the process broadcasts a RELEASE.

P1 ── RELEASE ──► P2
 │
 └── RELEASE ──► P3

Other processes update their queues and the next eligible request can proceed.

10. System Architecture

The project follows a frontend-backend architecture.

flowchart LR
    U[User] --> F[React Frontend]

    F -->|REST API| B[FastAPI Backend]

    B --> E[Simulation Engine]
    B --> V[Verification]
    B --> X[Explanation]
    B --> M[Models]
    B --> D[(SQLite)]

    E --> M
    E --> V
    E --> X
    E --> D

Main layers

Layer

Responsibility

React Frontend

Interactive simulator interface and visualization

REST API

Frontend-backend communication

FastAPI Backend

Simulation control and API endpoints

Simulation Engine

Logical clocks, queues, messages and execution

Verification

Safety, liveness, ordering and invariant checks

Explanation

Human-readable reasoning about execution

Models

Structured simulation data

SQLite

Local experiment storage

11. Frontend Architecture / Responsibilities

The frontend is implemented using React, Vite, JavaScript/JSX, and CSS.

The frontend provides the interactive user interface for controlling and observing the simulator.

Main responsibilities

Display process states.

Display logical clocks.

Display request and queue information.

Provide simulation controls.

Select experiment scenarios.

Configure network behavior.

Display event timelines.

Display request ordering.

Display verification results.

Display the space-time diagram.

Display explainability information.

Communicate with the backend using REST APIs.

Frontend components

Component

Responsibility

Controls.jsx

Simulation and experiment controls

EventTimeline.jsx

Displays execution events

Header.jsx

Application header

OrderPanel.jsx

Displays request ordering

ProcessCards.jsx

Displays process-level information

SpaceTime.jsx

Space-time execution visualization

VerificationPanel.jsx

Displays verification information

WhyPanel.jsx

Displays execution explanations

12. Backend Architecture / Responsibilities

The backend is implemented using:

Python

FastAPI

Pydantic

SQLite

The backend manages the simulation state and exposes REST API endpoints to the frontend.

Main backend responsibilities

Manage experiments.

Manage simulation state.

Maintain process information.

Handle logical-clock updates.

Manage request queues.

Simulate messages.

Schedule events.

Apply scenario conditions.

Handle delay experimentation.

Handle controlled node silence.

Run verification checks.

Provide explanations.

Store local experiment information.

13. Module-wise Explanation

The backend is organized into functional modules.

database/

Responsible for local SQLite-based experiment storage.

SQLite is used as local experiment storage. It is not a cloud database.

engine/

Contains the simulation logic.

The engine is responsible for concepts such as:

Process behavior

Logical clocks

Requests

Request queues

Message handling

Event scheduling

Critical-section execution

Release processing

explanation/

Supports the explainability layer.

It helps translate simulation state into understandable reasons such as:

Why a process is waiting.

Why a request has priority.

Why a reply is still missing.

Why a message has not been delivered.

Why a process changed state.

models/

Contains structured data models used by the backend.

Pydantic models are used to represent and validate structured API and simulation data.

verification/

Contains correctness-related checks.

The verification layer examines properties including:

Mutual exclusion

Lamport clock consistency

Request ordering

Reply completion

Liveness

14. Process State Management

Each simulated process moves through protocol-related states.

A simplified conceptual lifecycle is:

stateDiagram-v2
    [*] --> IDLE
    IDLE --> WAITING: Generate Request
    WAITING --> CRITICAL: Conditions satisfied
    CRITICAL --> IDLE: Release
    WAITING --> WAITING: Waiting for reply / priority

IDLE

The process is not currently requesting or executing the critical section.

WAITING

The process has requested access but cannot yet enter the critical section.

Possible reasons include:

Required REPLY messages are still missing.

Another request has higher logical priority.

A relevant message is delayed.

Another process is currently in the critical section.

CRITICAL

The process has entered the simulated critical section.

After completing its work, it generates a RELEASE.

15. Live Execution Summary

During an experiment, the simulator provides a live view of the execution state.

The interface can expose information such as:

Current process states

Logical clocks

Active requests

Request ordering

Waiting conditions

Pending replies

Events

Message activity

Verification status

This allows users to observe the simulation while it is progressing rather than only inspecting the final result.

16. Experiment Scenarios

The simulator provides multiple experiment scenarios for studying different execution conditions.

Scenario

Purpose

Single Request

Observe basic mutual-exclusion execution

Concurrent Requests

Study multiple simultaneous requests

Same Timestamp Tie

Demonstrate process-ID tie-breaking

Delayed Message

Study the effect of message delay

Out-of-Order Message Arrival

Study arrival order versus logical order

Multiple Waiting Processes

Observe queue competition

High Contention

Study many competing requests

Controlled Node Silence

Experiment with an unresponsive/silent process

These scenarios provide different conditions under which the same underlying protocol can be observed.

17. Network Delay and Fault Experimentation

The simulator includes experimental controls for communication behavior.

Network modes

Normal network

Fixed delay

Random delay

Selected message delay

Delay controls

A delay rule can be applied to specific communication paths, such as:

From: P1
To:   P3
Message: REQUEST
Delay: 8 time units

The simulator can then observe the effect of the delayed message on the requesting process and overall execution.

Fault-oriented controls

The interface provides controls for:

Add delay rule

Resume delivery

Silence node

Resume node

These controls are intended for experimentation and educational observation, not for simulating production network failures with production-level guarantees.

18. FIFO and Non-FIFO Experimentation

The normal conceptual model assumes ordered communication behavior where applicable.

The simulator also provides an experimental condition for studying Non-FIFO message arrival.

FIFO

FIFO means messages sent over a communication path preserve their sending order.

For example:

REQUEST → REPLY → RELEASE

may be observed in that same communication order.

Non-FIFO experimental condition

In a Non-FIFO experiment, messages may arrive in an order different from their sending order.

For example:

Sent:
M1 → M2

Arrived:
M2 → M1

This allows users to study an important distinction:

Message arrival order is not the same as Lamport logical ordering.

The request ordering mechanism still uses:

(timestamp, process ID)

rather than simply trusting arrival order.

The Non-FIFO condition is therefore documented as an experimental condition, not as a replacement for the normal FIFO assumption.

19. Event Timeline

The event timeline presents the chronological sequence of simulated events.

Typical events may include:

REQUEST
RECEIVE_REQUEST
REPLY
RECEIVE_REPLY
ENTER_CRITICAL_SECTION
RELEASE

The timeline helps users trace:

What happened?
        ↓
When did the simulated event occur?
        ↓
Which process generated it?
        ↓
What was the logical clock?
        ↓
What state changed?

This is particularly useful when debugging or explaining an experiment.

20. Space-Time Diagram

The space-time diagram provides a visual representation of distributed execution.

Process

P1  ──●──────────────●──────────────●────
      │       ↘       │              │
      │        ↘      │              │
P2  ──●─────────●─────┼──────●───────●────
               ↗      │      ↗
              ↗       │     ↗
P3  ──●───────────────●──────────────●────

Diagram interpretation

Each horizontal lane represents a process.

Dots represent events.

Arrows represent messages.

Lamport timestamps are shown on events.

Critical-section intervals are highlighted.

Delayed or in-flight messages can be inspected.

Message and event details are available.

The diagram makes the distributed nature of the protocol easier to understand because events are shown across multiple process timelines.

21. WHY DID THIS HAPPEN? — Explainability

One of the key features of the project is:

WHY DID THIS HAPPEN?

A simulator can show that a process is waiting. However, understanding why it is waiting is more important for an academic learning environment.

The explainability feature helps connect the visible state to the underlying protocol conditions.

For example, it can help explain:

Why is a process WAITING?

Possible protocol reasons include:

A required reply has not arrived.

A higher-priority request is ahead in the queue.

A relevant message is delayed.

Another process is currently in the critical section.

Why does a request have priority?

The request ordering is based on:

(timestamp, process ID)

The explanation can therefore connect the observed ordering to the actual Lamport ordering rule.

Why is a reply missing?

The simulator can expose the relevant message/execution state so that the user can identify whether the reply is:

Not yet generated.

In transit.

Delayed.

Affected by an experimental node condition.

Why did the state change?

The simulator connects state transitions to events and protocol conditions instead of treating the interface as a black box.

This makes the project an explainable experimentation environment, rather than only a visual animation.

22. Verification and Correctness

The simulator includes verification mechanisms for important distributed mutual-exclusion properties.

Mutual Exclusion

The simulator checks that multiple processes do not simultaneously occupy the critical section.

Conceptually:

Number of processes in CS ≤ 1

A violation indicates that the observed simulation state does not satisfy the mutual-exclusion invariant.

Lamport Clock Consistency

The simulator checks logical-clock behavior associated with distributed events and message reception.

The purpose is to ensure that logical timestamps follow the intended Lamport clock rules.

Request Ordering

Requests are evaluated according to:

(timestamp, process ID)

This ensures that logical priority is deterministic, including when timestamps are equal.

Reply Completion

The simulator tracks the replies required by a requesting process.

A process cannot satisfy the protocol's reply condition until the required replies have been received.

Liveness

The simulator can be used to observe whether waiting processes eventually progress under the relevant experiment conditions.

Delays and controlled node silence are particularly useful for demonstrating why progress can be affected by communication conditions.

23. Safety vs Liveness

Safety and liveness represent different correctness concerns.

Property

Meaning

Safety

Prevent an invalid state, such as two processes simultaneously entering the critical section

Liveness

Allow an eligible request to eventually make progress under the applicable assumptions

Safety

The key safety requirement is:

At most one process
        ↓
in the critical section
        ↓
at any simulated point

Liveness

Liveness concerns whether a waiting request can eventually progress.

For example, an intentionally delayed message may cause a process to remain waiting until the message is delivered.

This makes the simulator useful for understanding that correctness depends not only on the protocol logic but also on the assumptions under which it operates.

24. End-to-End Workflow

The overall system workflow can be summarized as:

flowchart TD
    A[Open Simulator] --> B[Select Scenario]
    B --> C[Configure Network / Experiment]
    C --> D[Start Experiment]
    D --> E[Generate Request]
    E --> F[Update Lamport Clock]
    F --> G[Add Request to Queue]
    G --> H[Send REQUEST]
    H --> I[Receive REQUEST]
    I --> J[Update Receiver Clock]
    J --> K[Update Receiver Queue]
    K --> L[Send REPLY]
    L --> M[Track Required Replies]
    M --> N{Priority + Replies Satisfied?}
    N -- No --> O[Remain WAITING]
    O --> H
    N -- Yes --> P[Enter Critical Section]
    P --> Q[Perform Simulated Work]
    Q --> R[Send RELEASE]
    R --> S[Update Queues]
    S --> T[Verification + Explanation]
    T --> U[Next Eligible Request]

25. Simulation Controls

The interface provides controls for managing an experiment.

Control

Purpose

Start

Start the selected experiment

Step

Advance the simulation step-by-step

Run to End

Execute the experiment until its end condition

Play

Continue simulation execution

Pause

Pause execution

Reset

Reset the current experiment

Generate Request

Generate a process request

Add delay rule

Configure a message delay condition

Resume delivery

Resume delayed message delivery

Silence node

Place a process into the experimental silent condition

Resume node

Resume a previously silenced process

These controls allow both continuous execution and detailed step-by-step investigation.

26. Technology Stack

Layer

Technology

Frontend

React

Build Tool

Vite

Frontend Language

JavaScript / JSX

Styling

CSS

Backend

Python

API Framework

FastAPI

Data Validation

Pydantic

Communication

REST API

Storage

SQLite

Simulation

Lamport Logical Clock, request queues, message simulation, event scheduling

Verification

Safety, liveness, ordering, invariant checking

No AI/ML, blockchain, IoT, cloud infrastructure, or hardware implementation is part of the documented project scope.

27. Project Structure

lamport-simulator/
│
├── backend/
│   ├── database/
│   ├── engine/
│   ├── explanation/
│   ├── models/
│   ├── tests/
│   ├── verification/
│   ├── app.py
│   ├── requirements.txt
│   └── run_randomized.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Controls.jsx
│   │   │   ├── EventTimeline.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── OrderPanel.jsx
│   │   │   ├── ProcessCards.jsx
│   │   │   ├── SpaceTime.jsx
│   │   │   ├── VerificationPanel.jsx
│   │   │   └── WhyPanel.jsx
│   │   │
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── main.jsx
│   │   └── styles.css
│   │
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md

28. Installation and Setup

Prerequisites

The project requires a local development environment with:

Python

Node.js and npm

Git

A modern web browser

The following commands use Windows PowerShell.

Clone the Repository

git clone <repository-url>
cd lamport-simulator

Replace <repository-url> with the repository's actual Git URL.

29. Running the Backend

Open PowerShell and navigate to the backend directory:

cd backend

Create a Python virtual environment:

python -m venv venv

Activate it:

.\venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Start the FastAPI backend:

uvicorn app:app --reload --port 8000

The backend will be available at:

http://localhost:8000

If PowerShell blocks virtual-environment activation

Run:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Then activate the environment again:

.\venv\Scripts\Activate.ps1

30. Running the Frontend

Open a second PowerShell window.

Navigate to the frontend:

cd frontend

Install JavaScript dependencies:

npm install

Start the Vite development server:

npm run dev

The frontend will normally be available at:

http://localhost:5173

The frontend communicates with the backend through the REST API.

31. API Documentation

The FastAPI backend provides interactive API documentation.

Swagger UI

http://localhost:8000/docs

Implemented API paths

The project includes API paths for:

GET  /api/health
GET  /api/scenarios
GET  /api/experiments
GET  /api/experiments/{exp_id}

Experiment execution/state operations are exposed under the experiment API, including:

state
start
step
play
pause

The exact request and response schemas can be inspected through the FastAPI documentation at:

http://localhost:8000/docs

Health Check

The health endpoint provides a basic backend availability check:

/api/health

A successful backend health response is represented by:

{
  "status": "ok"
}

32. Running Tests

From the backend directory, with the virtual environment activated:

python -m pytest -q

The repository also includes a randomized-experiment runner:

python run_randomized.py

The README intentionally does not state a fixed test count or performance metric so that the documentation does not claim results that may change with the current repository state.

33. Research and Implementation Contribution

The overall research and implementation work for the project was handled by:

Gayathri S

This included:

Problem research

Study of Lamport Mutual Exclusion

Distributed-computing concept analysis

Architecture design

Backend implementation

Frontend implementation

Frontend-backend integration

Simulation integration

Experimentation

Visualization

Explainability

Verification

The project was developed as a team project under the team name SYNSPHERE.

34. Project Significance

The project provides an interactive way to study distributed mutual exclusion rather than relying only on static theoretical descriptions.

Its significance lies in bringing together:

Distributed-process simulation

Logical clocks

Request ordering

Message-based coordination

Queue management

Network experimentation

Event visualization

Explainability

Verification

The combination allows students to connect the theoretical Lamport Mutual Exclusion algorithm with observable execution behavior.

In particular, the WHY DID THIS HAPPEN? feature helps bridge the gap between:

Algorithm Rule
      ↓
Simulation Event
      ↓
Process State
      ↓
Observed Result

35. Limitations

The project has several intentional limitations.

It is an academic simulator, not a production distributed locking system.

Multiple distributed processes are simulated on a single laptop.

The communication environment is simulated rather than representing independent physical machines.

SQLite is used only for local experiment storage.

The simulator does not claim production-grade distributed fault tolerance.

Network delay and node-silence controls are experimental mechanisms for studying protocol behavior.

The Non-FIFO condition is an experimental condition and should be distinguished from the normal FIFO communication assumption.

The simulator does not represent a production deployment environment.

The results of an experiment depend on the selected scenario and configured conditions.

36. Future Scope

Potential future extensions include:

More distributed-process models.

Additional message-failure scenarios.

More configurable network conditions.

Expanded experiment recording and comparison.

Additional visualization controls.

More detailed event replay capabilities.

Additional verification properties.

Extended protocol experimentation.

Support for more distributed mutual-exclusion algorithms for comparative academic study.

These are future possibilities and are not claimed as currently implemented features.

37. Conclusion

LAMPORT MUTUAL EXCLUSION STIMULATOR provides an interactive academic environment for understanding Lamport Mutual Exclusion through simulation, experimentation, visualization, explainability, and verification.

The project demonstrates how:

Logical Clocks
      +
Request Ordering
      +
REQUEST / REPLY / RELEASE
      +
Request Queues
      +
Event Scheduling
      +
Network Experimentation
      +
Verification
      +
Explainability

come together to model distributed mutual exclusion.

Rather than only showing whether a process enters the critical section, the simulator allows users to investigate how the protocol reached that state and why a particular decision occurred.

This makes the project suitable for academic learning, experimentation, demonstrations, and deeper study of distributed mutual exclusion concepts.

38. Team

SYNSPHERE

Member

Role

Gayathri S

Team Leader

Divyamithra

Team Member

Vishnuprasath

Team Member

Sivarao

Team Member

Project

LAMPORT MUTUAL EXCLUSION STIMULATOR

Subject

Distributed Computing
